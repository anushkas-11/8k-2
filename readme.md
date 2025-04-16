# Decentralized Video Platform

A complete decentralized video platform that integrates AI video compression, Livepeer streaming, IPFS storage, and Ethereum smart contracts.

## Architecture Overview

This platform combines several technologies to create a fully decentralized video pipeline:

1. **AI Video Compression**: Neural network-based video compression to reduce file size while maintaining quality
2. **Livepeer Integration**: Decentralized video transcoding and streaming
3. **IPFS Storage**: Permanent, content-addressed storage for videos
4. **Ethereum Smart Contract**: Manages video metadata and access control

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Original  │      │     AI      │      │   Livepeer  │      │    IPFS     │
│    Video    │─────▶│ Compression │─────▶│  Streaming  │─────▶│   Storage   │
└─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘
                                                                      │
                                                                      ▼
                                                              ┌─────────────┐
                                                              │  Ethereum   │
                                                              │    Smart    │
                                                              │  Contract   │
                                                              └─────────────┘
```

## Installation

### Prerequisites

- Python 3.8+ with pip
- Node.js 14+ with npm
- FFmpeg
- PyTorch
- CUDA-capable GPU (optional but recommended)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/decentralized-video-platform.git
   cd decentralized-video-platform
   ```

2. Install Python dependencies:
   ```bash
   pip install torch torchvision opencv-python tqdm aiohttp aiofiles
   pip install livepeer-python  # If available, or use API directly
   ```

3. Install Node.js dependencies:
   ```bash
   npm install
   ```

4. Create a `.env` file with your API keys and configuration:
   ```
   LIVEPEER_API_KEY=your_livepeer_api_key
   INFURA_API_KEY=your_infura_project_id
   PRIVATE_KEY=your_ethereum_private_key
   ETHERSCAN_API_KEY=your_etherscan_api_key
   CONTRACT_ADDRESS=deployed_contract_address
   ```

## Usage

### Complete Pipeline

The easiest way to use this platform is through the integrated pipeline:

```bash
python pipeline.py --input path/to/video.mp4 --title "My Video Title" --description "Video description" --price "0.1"
```

Options:
- `--no-stream`: Skip Livepeer streaming
- `--no-ipfs`: Skip IPFS upload
- `--no-blockchain`: Skip blockchain registration
- `--config path/to/config.json`: Use custom configuration file

### Individual Components

You can also use each component separately:

#### 1. AI Video Compression

```bash
python video_model.py --input path/to/video.mp4 --output path/to/output.mp4
```

#### 2. Livepeer Streaming

```bash
python livepeer_handler.py path/to/compressed_video.mp4
```

#### 3. IPFS Upload

```bash
node ipfs_handler.js path/to/compressed_video.mp4 "Video Title" "Video Description"
```

#### 4. Blockchain Registration

```bash
# Deploy the contract first (if not already deployed)
npm run deploy

# Register a video
node web3client.js upload "Video Title" "Video Description" "ipfs_hash" "0.1"
```

## Smart Contract

The `VideoStorage` smart contract manages video metadata and access control:

- `uploadVideo`: Register a new video with metadata and price
- `buyVideo`: Purchase access to a video
- `getVideoDetails`: Get video details (IPFS hash only if authorized)
- `hasAccess`: Check if a user has access to a video

## Directory Structure

```
decentralized-video-platform/
├── contracts/                   # Solidity smart contracts
│   └── VideoStorage.sol
├── scripts/                     # Deployment scripts
│   └── deploy.js
├── model/                       # AI model files
│   └── residual_encoder.pth
├── input/                       # Input video directory
├── output/                      # Output directory for processed videos
├── cache/                       # Cache directory for Livepeer streaming
├── video_model.py               # AI compression module
├── livepeer_handler.py          # Livepeer integration
├── ipfs_handler.js              # IPFS storage module
├── web3client.js                # Ethereum interaction module
├── pipeline.py                  # Integrated pipeline
└── config.json                  # Configuration file
```

## Configuration

The platform uses a central `config.json` file, which can be overridden by environment variables and command-line arguments:

```json
{
  "directories": {
    "input": "input",
    "output": "output",
    "model": "model",
    "cache": "cache"
  },
  "model": {
    "path": "model/residual_encoder.pth",
    "training_video": null
  },
  "livepeer": {
    "api_key": "",
    "stream_name": "decentralized-video-stream",
    "cache_enabled": true,
    "server_port": 8080
  },
  "ipfs": {
    "host": "ipfs.infura.io",
    "port": 5001,
    "protocol": "https",
    "gateway": "https://ipfs.io/ipfs/"
  },
  "ethereum": {
    "provider_url": "http://localhost:8545",
    "contract_address": ""
  }
}
```

## Examples

### Complete Video Processing

```bash
# Process a video through the entire pipeline
python pipeline.py --input samples/my_video.mp4 --title "My Amazing Video" --description "This is a test video for the decentralized platform" --price "0.05"

# Compress only
python pipeline.py --input samples/my_video.mp4 --no-stream --no-ipfs --no-blockchain

# Upload to IPFS and register on blockchain (skip compression and streaming)
python pipeline.py --input samples/already_compressed.mp4 --no-stream
```

### Blockchain Interaction

```bash
# Upload video metadata
node web3client.js upload "Cool Video" "My cool video description" "QmHash123456789" "0.1"

# Get video details
node web3client.js get 1

# Buy video access
node web3client.js buy 1 0.1

# List my videos
node web3client.js myvideos
```

## Limitations and Future Work

- The AI compression model is a simple prototype and can be improved
- Livepeer integration may need adjustments based on their API changes
- Current IPFS implementation uses Infura, could be extended to use local node
- The platform does not yet support video preview/thumbnail generation
- The smart contract could be extended with more features like categories, ratings, etc.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
