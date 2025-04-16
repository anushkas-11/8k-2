#!/usr/bin/env python3
"""
Decentralized Video Pipeline

This script integrates AI video compression, Livepeer streaming, 
IPFS storage, and Ethereum blockchain for a complete decentralized
video processing and distribution pipeline.
"""

import os
import sys
import json
import asyncio
import argparse
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Import our components
import torch
from video_model import ResidualAutoencoder, load_or_train_model, compress_video
import livepeer_handler as livepeer

class DecentralizedVideoPipeline:
    """Main pipeline orchestrator for decentralized video processing"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the pipeline with configuration
        
        Args:
            config_path: Path to configuration JSON file
        """
        self.config = self._load_config(config_path)
        self.init_directories()
        
        # Initialize AI model
        self.model, self.device = self._init_ai_model()
        
        print("Decentralized Video Pipeline initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file or create default config"""
        
        # Default configuration
        default_config = {
            "directories": {
                "input": "input",
                "output": "output",
                "model": "model",
                "cache": "cache"
            },
            "model": {
                "path": "model/residual_encoder.pth",
                "training_video": None
            },
            "livepeer": {
                "api_key": os.environ.get("LIVEPEER_API_KEY", ""),
                "stream_name": "decentralized-video-stream",
                "cache_enabled": True,
                "server_port": 8080
            },
            "ipfs": {
                "service": "web3.storage",
                "token": os.environ.get("WEB3STORAGE_TOKEN", ""),
                "gateway": "https://{cid}.ipfs.w3s.link"
            },
            "ethereum": {
                "provider_url": os.environ.get("PROVIDER_URL", "http://localhost:8545"),
                "contract_address": os.environ.get("CONTRACT_ADDRESS", ""),
                "private_key": os.environ.get("PRIVATE_KEY", "")
            }
        }
        
        # Try to load from file
        config = default_config
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # Update default with loaded values
                    self._update_nested_dict(config, loaded_config)
                print(f"Loaded configuration from {config_path}")
            else:
                print(f"Configuration file {config_path} not found, using defaults")
                # Save default config for future use
                self._save_config(config, config_path)
        except Exception as e:
            print(f"Error loading configuration: {str(e)}")
        
        # Update with environment variables
        if "LIVEPEER_API_KEY" in os.environ:
            config["livepeer"]["api_key"] = os.environ["LIVEPEER_API_KEY"]
        
        if "WEB3STORAGE_TOKEN" in os.environ:
            config["ipfs"]["token"] = os.environ["WEB3STORAGE_TOKEN"]
        
        return config
    
    def _save_config(self, config: Dict[str, Any], config_path: str) -> None:
        """Save configuration to a JSON file"""
        try:
            # Make sure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
            
            # Save config, excluding sensitive data
            safe_config = self._get_safe_config(config)
            with open(config_path, 'w') as f:
                json.dump(safe_config, f, indent=2)
            print(f"Configuration saved to {config_path}")
        except Exception as e:
            print(f"Error saving configuration: {str(e)}")
            
    def _get_safe_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a copy of config without sensitive data"""
        safe_config = json.loads(json.dumps(config))
        
        # Remove sensitive data
        if "ethereum" in safe_config:
            if "private_key" in safe_config["ethereum"]:
                safe_config["ethereum"]["private_key"] = ""
        
        if "ipfs" in safe_config:
            if "token" in safe_config["ipfs"]:
                safe_config["ipfs"]["token"] = ""
        
        if "livepeer" in safe_config:
            if "api_key" in safe_config["livepeer"]:
                safe_config["livepeer"]["api_key"] = ""
        
        return safe_config
    
    def _update_nested_dict(self, d: Dict[str, Any], u: Dict[str, Any]) -> None:
        """Recursively update nested dictionary"""
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._update_nested_dict(d[k], v)
            else:
                d[k] = v
    
    def init_directories(self) -> None:
        """Create necessary directories if they don't exist"""
        for dir_name, dir_path in self.config["directories"].items():
            os.makedirs(dir_path, exist_ok=True)
            print(f"Directory ensured: {dir_path}")
    
    def _init_ai_model(self) -> tuple:
        """Initialize the AI video compression model"""
        model_path = self.config["model"]["path"]
        training_video = self.config["model"]["training_video"]
        
        return load_or_train_model(model_path, training_video)
    
    async def run_ipfs_upload(self, video_path: str, title: str, description: str) -> Dict[str, Any]:
        """Upload a video to IPFS using Node.js script"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        print(f"Uploading to IPFS: {video_path}")
        
        # Set Web3.Storage token from config or environment
        env = os.environ.copy()
        if "ipfs" in self.config and "token" in self.config["ipfs"]:
            env["WEB3STORAGE_TOKEN"] = self.config["ipfs"]["token"]
        
        # Determine which IPFS handler to use
        ipfs_script = "ipfs_handler_web3storage.js"
        if not os.path.exists(ipfs_script):
            print(f"Warning: {ipfs_script} not found, falling back to default ipfs_handler.js")
            ipfs_script = "ipfs_handler.js"
        
        # Prepare command
        cmd = ["node", ipfs_script, video_path, title, description]
        
        # Execute process
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                print(f"IPFS upload error: {stderr.decode()}")
                raise Exception(f"IPFS upload failed with code {process.returncode}")
            
            output = stdout.decode()
            print(f"IPFS upload output: {output}")
            
            # Try to parse the IPFS hash from output
            ipfs_hash = None
            for line in output.splitlines():
                if "Video IPFS Hash:" in line:
                    ipfs_hash = line.split(":")[-1].strip()
                    break
            
            # Load metadata file
            metadata_path = os.path.join("output", "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                print(f"Loaded metadata from {metadata_path}")
                return metadata
            
            return {"ipfsHash": ipfs_hash, "title": title, "description": description}
        
        except Exception as e:
            print(f"Error uploading to IPFS: {str(e)}")
            raise
    
    async def register_on_blockchain(self, metadata: Dict[str, Any], price: str) -> Dict[str, Any]:
        """Register video metadata on the blockchain"""
        if not self.config["ethereum"]["contract_address"]:
            print("Blockchain registration skipped: No contract address provided")
            return {"registered": False, "reason": "No contract address provided"}
        
        if not self.config["ethereum"]["private_key"]:
            print("Blockchain registration skipped: No private key provided")
            return {"registered": False, "reason": "No private key provided"}
        
        ipfs_hash = metadata.get("ipfsHash")
        title = metadata.get("title")
        description = metadata.get("description", "")
        
        if not ipfs_hash:
            print("Blockchain registration skipped: No IPFS hash in metadata")
            return {"registered": False, "reason": "No IPFS hash in metadata"}
        
        print(f"Registering video on blockchain: {title}")
        
        # Prepare environment variables for web3client.js
        env = os.environ.copy()
        env["PROVIDER_URL"] = self.config["ethereum"]["provider_url"]
        env["CONTRACT_ADDRESS"] = self.config["ethereum"]["contract_address"]
        env["PRIVATE_KEY"] = self.config["ethereum"]["private_key"]
        
        # Prepare command
        web3_script = "web3client.js"
        cmd = ["node", web3_script, "upload", title, description, ipfs_hash, price]
        
        # Execute process
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                print(f"Blockchain registration error: {stderr.decode()}")
                raise Exception(f"Blockchain registration failed with code {process.returncode}")
            
            output = stdout.decode()
            print(f"Blockchain registration output: {output}")
            
            # Try to parse the video ID from output
            video_id = None
            for line in output.splitlines():
                if "Video uploaded successfully with ID:" in line:
                    video_id = line.split(":")[-1].strip()
                    break
            
            return {
                "registered": True,
                "videoId": video_id,
                "output": output
            }
        
        except Exception as e:
            print(f"Error registering on blockchain: {str(e)}")
            return {
                "registered": False,
                "reason": str(e),
                "error": str(e)
            }
    
    async def process_video(self, 
                           input_path: str,
                           title: str = None,
                           description: str = None,
                           price: str = "0.1",
                           stream: bool = True,
                           upload_to_ipfs: bool = True,
                           register_blockchain: bool = True) -> Dict[str, Any]:
        """
        Process a video through the complete pipeline
        
        Args:
            input_path: Path to input video
            title: Video title (defaults to filename)
            description: Video description
            price: Price in ETH (for blockchain registration)
            stream: Whether to stream via Livepeer
            upload_to_ipfs: Whether to upload to IPFS
            register_blockchain: Whether to register on blockchain
            
        Returns:
            Dictionary with results of each step
        """
        result = {
            "input": input_path,
            "compression": None,
            "streaming": None,
            "ipfs": None,
            "blockchain": None
        }
        
        # Check input file
        if not os.path.exists(input_path):
            print(f"Error: Input video not found: {input_path}")
            return result
        
        # Set default title if not provided
        if not title:
            title = os.path.basename(input_path)
            title = os.path.splitext(title)[0]  # Remove extension
        
        # Set default description if not provided
        if not description:
            description = f"Video processed by Decentralized Video Pipeline on {time.strftime('%Y-%m-%d')}"
        
        # Step 1: Compress video with AI model
        try:
            print(f"Step 1: Compressing video with AI model")
            output_path = os.path.join(
                self.config["directories"]["output"],
                f"compressed_{os.path.basename(input_path)}"
            )
            
            compressed_path = compress_video(self.model, input_path, output_path, self.device)
            result["compression"] = {
                "success": True,
                "output_path": compressed_path
            }
            print(f"Compression complete: {compressed_path}")
            
            # Use compressed video for the next steps
            working_video = compressed_path
        except Exception as e:
            print(f"Error in compression step: {str(e)}")
            result["compression"] = {
                "success": False,
                "error": str(e)
            }
            # Use original video for next steps if compression fails
            working_video = input_path
        
        # Step 2: Stream via Livepeer (if enabled)
        if stream:
            try:
                print(f"Step 2: Streaming via Livepeer")
                # Set Livepeer API key
                os.environ["LIVEPEER_API_KEY"] = self.config["livepeer"]["api_key"]
                
                # Update Livepeer configuration
                livepeer.STREAM_NAME = self.config["livepeer"]["stream_name"]
                livepeer.CACHE_ENABLED = self.config["livepeer"]["cache_enabled"]
                livepeer.SERVER_PORT = self.config["livepeer"]["server_port"]
                
                # Start streaming
                stream_result = livepeer.stream_video(working_video)
                result["streaming"] = stream_result
                print(f"Streaming initiated: {stream_result['success']}")
            except Exception as e:
                print(f"Error in streaming step: {str(e)}")
                result["streaming"] = {
                    "success": False,
                    "error": str(e)
                }
        
        # Step 3: Upload to IPFS (if enabled)
        if upload_to_ipfs:
            try:
                print(f"Step 3: Uploading to IPFS")
                ipfs_result = await self.run_ipfs_upload(working_video, title, description)
                result["ipfs"] = {
                    "success": True,
                    **ipfs_result
                }
                print(f"IPFS upload complete: {ipfs_result.get('ipfsHash')}")
            except Exception as e:
                print(f"Error in IPFS upload step: {str(e)}")
                result["ipfs"] = {
                    "success": False,
                    "error": str(e)
                }
        
        # Step 4: Register on blockchain (if enabled)
        if register_blockchain and result["ipfs"] and result["ipfs"]["success"]:
            try:
                print(f"Step 4: Registering on blockchain")
                blockchain_result = await self.register_on_blockchain(result["ipfs"], price)
                result["blockchain"] = blockchain_result
                print(f"Blockchain registration: {blockchain_result.get('registered')}")
            except Exception as e:
                print(f"Error in blockchain registration step: {str(e)}")
                result["blockchain"] = {
                    "success": False,
                    "error": str(e)
                }
        
        return result
    
    def save_result(self, result: Dict[str, Any], output_path: str = None) -> str:
        """Save processing result to a JSON file"""
        if not output_path:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(
                self.config["directories"]["output"],
                f"pipeline_result_{timestamp}.json"
            )
        
        try:
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Result saved to {output_path}")
            return output_path
        except Exception as e:
            print(f"Error saving result: {str(e)}")
            return None

async def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Decentralized Video Pipeline")
    parser.add_argument("--input", "-i", required=True, help="Input video path")
    parser.add_argument("--title", "-t", help="Video title")
    parser.add_argument("--description", "-d", help="Video description")
    parser.add_argument("--price", "-p", default="0.1", help="Video price in ETH")
    parser.add_argument("--config", "-c", default="config.json", help="Configuration file path")
    parser.add_argument("--no-stream", action="store_true", help="Skip Livepeer streaming")
    parser.add_argument("--no-ipfs", action="store_true", help="Skip IPFS upload")
    parser.add_argument("--no-blockchain", action="store_true", help="Skip blockchain registration")
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = DecentralizedVideoPipeline(args.config)
    
    # Process video
    result = await pipeline.process_video(
        input_path=args.input,
        title=args.title,
        description=args.description,
        price=args.price,
        stream=not args.no_stream,
        upload_to_ipfs=not args.no_ipfs,
        register_blockchain=not args.no_blockchain
    )
    
    # Save result
    pipeline.save_result(result)
    
    # Print summary
    print("\n=== Pipeline Execution Summary ===")
    print(f"Input video: {args.input}")
    
    if result["compression"] and result["compression"].get("success"):
        print(f"Compression: SUCCESS - {result['compression']['output_path']}")
    else:
        print(f"Compression: FAILED")
    
    if not args.no_stream:
        if result["streaming"] and result["streaming"].get("success"):
            print(f"Streaming: SUCCESS - Stream ID: {result['streaming'].get('stream_id')}")
        else:
            print(f"Streaming: FAILED")
    else:
        print(f"Streaming: SKIPPED")
    
    if not args.no_ipfs:
        if result["ipfs"] and result["ipfs"].get("success"):
            print(f"IPFS Upload: SUCCESS - Hash: {result['ipfs'].get('ipfsHash')}")
        else:
            print(f"IPFS Upload: FAILED")
    else:
        print(f"IPFS Upload: SKIPPED")
    
    if not args.no_blockchain:
        if result["blockchain"] and result["blockchain"].get("registered"):
            print(f"Blockchain Registration: SUCCESS - Video ID: {result['blockchain'].get('videoId')}")
        else:
            print(f"Blockchain Registration: FAILED")
    else:
        print(f"Blockchain Registration: SKIPPED")

if __name__ == "__main__":
    asyncio.run(main())
