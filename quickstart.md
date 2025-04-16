# Decentralized Video Platform - Quick Start Guide

This guide will help you quickly set up and start using the Decentralized Video Platform.

## 1. Installation

### Clone the repository

```bash
git clone https://github.com/yourusername/decentralized-video-platform.git
cd decentralized-video-platform
```

### Install dependencies

```bash
# Python dependencies
pip install torch torchvision opencv-python tqdm aiohttp aiofiles

# Node.js dependencies
npm install
```

### Set up environment

Create a `.env` file in the root directory:

```
LIVEPEER_API_KEY=your_livepeer_api_key
PROVIDER_URL=https://goerli.infura.io/v3/your_infura_project_id
```

## 2. Basic Configuration

The default configuration should work for most users. If you need to customize settings, copy the example config:

```bash
cp config.example.json config.json
```

Then edit `config.json` as needed.

## 3. Process Your First Video

### Single command process

Process a video through the entire pipeline:

```bash
python pipeline.py --input path/to/your/video.mp4 --title "My First Video" --description "Testing the decentralized video platform"
```

### See the results

After processing completes, you'll find:
- Compressed video in the `output` directory
- IPFS hash for your video
- Livepeer streaming URLs

## 4. Using Individual Components

If you want to use only specific parts of the pipeline:

### AI Compression only

```bash
python pipeline.py --input video.mp4 --no-stream --no-ipfs --no-blockchain
```

### IPFS Upload only

```bash
node ipfs_handler.js path/to/video.mp4 "Video Title" "Video Description"
```

### Livepeer Streaming only

```bash
python livepeer_handler.py path/to/video.mp4
```

## 5. Smart Contract Integration (Optional)

If you want to use the blockchain integration:

### Deploy the contract

```bash
# Start a local node for testing
npx hardhat node

# In a new terminal, deploy the contract
npx hardhat run scripts/deploy.js --network localhost
```

### Update your configuration

Add the contract address to your environment:

```
CONTRACT_ADDRESS=your_deployed_contract_address
PRIVATE_KEY=your_ethereum_private_key
```

### Upload video metadata to blockchain

```bash
node web3client.js upload "Video Title" "Description" "ipfs_hash" "0.1"
```

## 6. Common Commands

Here are some common commands you might need:

```bash
# Process video and skip blockchain registration
python pipeline.py --input video.mp4 --no-blockchain

# Get details for video ID 1 from blockchain
node web3client.js get 1

# Buy access to video ID 1
node web3client.js buy 1 0.1

# List videos you own
node web3client.js myvideos
```

## 7. Troubleshooting

- **AI model errors**: Make sure you have PyTorch properly installed and CUDA if using GPU
- **Livepeer connection issues**: Verify your API key and check Livepeer status
- **IPFS upload failures**: Check your internet connection and Infura API limits
- **Blockchain errors**: Ensure you have sufficient ETH for gas and the correct contract address

## Next Steps

- Check the README.md for a detailed architecture overview
- Explore the individual component files to understand how they work
- Read the code comments for additional configuration options
