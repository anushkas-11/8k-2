import os
import asyncio
import subprocess
import time
import aiohttp
import aiofiles
import json
from typing import List, Optional, Dict, Any

# Configuration - will be loaded from config file or environment variables
LIVEPEER_API_KEY = os.environ.get("LIVEPEER_API_KEY", "your-api-key-here")
STREAM_NAME = "decentralized-video-stream"
LOCAL_CACHE_DIR = "./cache/livepeer"
LOCAL_PLAYBACK_URL_BASE = "http://localhost:8080/cache/"
SERVER_PORT = 8080
CACHE_ENABLED = True

class StreamProfile:
    def __init__(self, name: str, width: int, height: int, bitrate: int, url: Optional[str] = None):
        self.name = name
        self.width = width
        self.height = height
        self.bitrate = bitrate
        self.url = url

class StreamInfo:
    def __init__(self, id: str, name: str, ingest: str, playback: List[StreamProfile] = None):
        self.id = id
        self.name = name
        self.ingest = ingest
        self.playback = playback or []

class LivepeerClient:
    """Simplified implementation of a Livepeer client"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://livepeer.studio/api"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_stream(self, name: str, profiles: List[StreamProfile]) -> StreamInfo:
        """Create a new stream on Livepeer"""
        async with aiohttp.ClientSession() as session:
            # Format profiles for Livepeer API
            livepeer_profiles = [
                {
                    "name": profile.name,
                    "width": profile.width,
                    "height": profile.height,
                    "bitrate": profile.bitrate
                } 
                for profile in profiles
            ]
            
            payload = {
                "name": name,
                "profiles": livepeer_profiles
            }
            
            async with session.post(
                f"{self.base_url}/stream", 
                headers=self.headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to create stream: {response.status} - {error_text}")
                
                data = await response.json()
                
                # Create StreamInfo object from response
                stream_profiles = []
                for profile in data.get("profiles", []):
                    stream_profiles.append(StreamProfile(
                        name=profile.get("name"),
                        width=profile.get("width"),
                        height=profile.get("height"),
                        bitrate=profile.get("bitrate")
                    ))
                
                # Get playback URLs
                playback_urls = []
                if "playbackId" in data:
                    playback_id = data["playbackId"]
                    
                    # Get HLS playback URLs for all profiles
                    for profile in stream_profiles:
                        profile.url = f"https://cdn.livepeer.studio/hls/{playback_id}/{profile.name}/index.m3u8"
                        playback_urls.append(profile)
                
                return StreamInfo(
                    id=data.get("id", ""),
                    name=data.get("name", ""),
                    ingest=data.get("rtmpIngestUrl", ""),
                    playback=playback_urls
                )

async def push_to_livepeer(ingest_url: str, video_path: str) -> bool:
    """Pushes a local video file to Livepeer using FFmpeg"""
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return False
    
    command = [
        "ffmpeg",
        "-re",  # Read input at native frame rate
        "-i", video_path,
        "-c:v", "libx264",  # Use H.264 codec for video
        "-preset", "medium",  # Encoding speed/quality balance
        "-c:a", "aac",  # Use AAC codec for audio
        "-f", "flv",  # Output format
        ingest_url
    ]
    
    print(f"Starting FFmpeg with command: {' '.join(command)}")
    
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            print("Successfully pushed video to Livepeer")
            return True
        else:
            print(f"Error pushing video to Livepeer (Return Code: {process.returncode}):")
            if stdout:
                print(f"STDOUT: {stdout.decode()}")
            if stderr:
                print(f"STDERR: {stderr.decode()}")
            return False
    except Exception as e:
        print(f"Exception during FFmpeg execution: {str(e)}")
        return False

async def fetch_and_cache_hls(playback_urls: List[StreamProfile]) -> Dict[str, str]:
    """Fetches and caches HLS segments from Livepeer"""
    if not CACHE_ENABLED:
        print("Caching is disabled")
        return {}
    
    if not os.path.exists(LOCAL_CACHE_DIR):
        os.makedirs(LOCAL_CACHE_DIR, exist_ok=True)
    
    local_urls = {}
    
    async with aiohttp.ClientSession() as session:
        for profile in playback_urls:
            if not profile.url:
                continue
                
            playlist_url = profile.url
            print(f"Fetching playlist: {playlist_url}")
            
            try:
                # Create profile directory
                profile_dir = os.path.join(LOCAL_CACHE_DIR, profile.name)
                os.makedirs(profile_dir, exist_ok=True)
                
                # Fetch and save the main playlist
                async with session.get(playlist_url) as resp:
                    if resp.status == 200:
                        playlist_content = await resp.text()
                        local_playlist_path = os.path.join(profile_dir, "index.m3u8")
                        
                        # Fix URLs in the playlist to point to our local cache
                        base_url = playlist_url.rsplit('/', 1)[0]
                        modified_content = playlist_content.replace(
                            base_url + '/', 
                            f"{LOCAL_PLAYBACK_URL_BASE}{profile.name}/"
                        )
                        
                        async with aiofiles.open(local_playlist_path, "w") as f:
                            await f.write(modified_content)
                        
                        local_urls[profile.name] = f"{LOCAL_PLAYBACK_URL_BASE}{profile.name}/index.m3u8"
                        
                        # Download all segments referenced in the playlist
                        for line in playlist_content.splitlines():
                            if line.endswith(".ts") or line.endswith(".m3u8"):
                                # Skip lines that are comments
                                if line.startswith("#"):
                                    continue
                                    
                                segment_url = f"{base_url}/{line}"
                                local_segment_path = os.path.join(profile_dir, line)
                                
                                # Create subdirectories if needed
                                os.makedirs(os.path.dirname(os.path.abspath(local_segment_path)), exist_ok=True)
                                
                                if not os.path.exists(local_segment_path):
                                    print(f"  Downloading segment: {segment_url}")
                                    try:
                                        async with session.get(segment_url) as segment_resp:
                                            if segment_resp.status == 200:
                                                async with aiofiles.open(local_segment_path, "wb") as f:
                                                    await f.write(await segment_resp.read())
                                            else:
                                                print(f"  Error downloading segment {segment_url}: {segment_resp.status}")
                                    except aiohttp.ClientError as e:
                                        print(f"  Client error downloading {segment_url}: {e}")
                    else:
                        print(f"Error fetching playlist {playlist_url}: {resp.status}")
            except aiohttp.ClientError as e:
                print(f"Client error fetching playlist {playlist_url}: {e}")
    
    return local_urls

async def serve_cached_content():
    """Serves the cached HLS content locally"""
    from aiohttp import web
    
    if not CACHE_ENABLED:
        print("Caching is disabled, not starting local server")
        return None
    
    app = web.Application()
    
    async def handle(request):
        filename = request.match_info.get('filename')
        filepath = os.path.join(LOCAL_CACHE_DIR, filename)
        
        if os.path.exists(filepath):
            try:
                if os.path.isfile(filepath):
                    async with aiofiles.open(filepath, 'rb') as f:
                        content = await f.read()
                        content_type = 'application/vnd.apple.mpegurl' if filepath.endswith(".m3u8") else 'video/MP2T'
                        return web.Response(body=content, content_type=content_type)
                else:
                    # Directory listing
                    files = os.listdir(filepath)
                    html = "<html><body><ul>"
                    for file in files:
                        html += f'<li><a href="{file}">{file}</a></li>'
                    html += "</ul></body></html>"
                    return web.Response(text=html, content_type='text/html')
            except Exception as e:
                print(f"Error serving {filename}: {e}")
                return web.Response(status=500, text=str(e))
        return web.Response(status=404, text="File not found")
    
    app.add_routes([
        web.get('/cache/{filename:.*}', handle)
    ])
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', SERVER_PORT)
    await site.start()
    
    print(f"Local HLS server started at http://localhost:{SERVER_PORT}/cache/")
    return runner

async def stream_video_to_livepeer(video_path: str) -> Dict[str, Any]:
    """Main function to handle the entire Livepeer streaming process"""
    result = {
        "success": False,
        "stream_id": None,
        "ingest_url": None,
        "playback_urls": {},
        "local_playback_urls": {}
    }
    
    # Create Livepeer client
    client = LivepeerClient(LIVEPEER_API_KEY)
    
    try:
        # Create stream on Livepeer
        profiles = [
            StreamProfile(name="720p", width=1280, height=720, bitrate=2000000),
            StreamProfile(name="480p", width=854, height=480, bitrate=1000000),
            StreamProfile(name="360p", width=640, height=360, bitrate=500000)
        ]
        
        stream = await client.create_stream(STREAM_NAME, profiles)
        
        print(f"Livepeer stream created:")
        print(f"  ID: {stream.id}")
        print(f"  Ingest URL (RTMP): {stream.ingest}")
        print("  Playback URLs (HLS):")
        for profile in stream.playback:
            print(f"    {profile.name}: {profile.url}")
            result["playback_urls"][profile.name] = profile.url
        
        result["stream_id"] = stream.id
        result["ingest_url"] = stream.ingest
        result["success"] = True
        
        # Start pushing video to Livepeer
        push_task = asyncio.create_task(push_to_livepeer(stream.ingest, video_path))
        
        # Wait a bit for the stream to start
        print("Waiting for stream to initialize...")
        await asyncio.sleep(10)
        
        # Start the local HLS server
        server_runner = await serve_cached_content()
        
        # Start fetching and caching HLS segments
        cache_task = asyncio.create_task(fetch_and_cache_hls(stream.playback))
        
        # Wait for push to complete
        push_success = await push_task
        if not push_success:
            print("Warning: Video push to Livepeer failed or had issues")
        
        # Wait for caching to complete
        local_urls = await cache_task
        result["local_playback_urls"] = local_urls
        
        # Keep server running for a while so user can access streams
        if server_runner:
            print("Local server will remain active for 30 minutes")
            # In a real application, you'd want a better way to handle this
            await asyncio.sleep(1800)  # 30 minutes
            await server_runner.cleanup()
    
    except Exception as e:
        print(f"Error in Livepeer streaming process: {str(e)}")
        result["error"] = str(e)
    
    return result

def stream_video(video_path: str) -> Dict[str, Any]:
    """Synchronous wrapper for the async streaming function"""
    return asyncio.run(stream_video_to_livepeer(video_path))

if __name__ == "__main__":
    # Example usage
    input_video = "output/compressed_video.mp4"
    
    if not os.path.exists(input_video):
        print(f"Error: Input video not found at {input_video}")
    else:
        result = stream_video(input_video)
        
        if result["success"]:
            print("\nStreaming completed successfully")
            print(f"Stream ID: {result['stream_id']}")
            
            print("\nPlayback URLs:")
            for profile, url in result["playback_urls"].items():
                print(f"  {profile}: {url}")
            
            if CACHE_ENABLED:
                print("\nLocal Playback URLs:")
                for profile, url in result["local_playback_urls"].items():
                    print(f"  {profile}: {url}")
        else:
            print("\nStreaming failed")
            if "error" in result:
                print(f"Error: {result['error']}")
