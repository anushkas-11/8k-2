# Decentralized Video Platform - Quick Start Guide

This updated guide will help you quickly set up and start using the Decentralized Video Platform with the new Web3.Storage (Storacha) integration.

## 1. Installation

### Clone the repository

```bash
git clone https://github.com/yourusername/decentralized-video-platform.git
cd decentralized-video-platform
```

### Install dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Node.js dependencies
npm install
```

### Set up environment

Create a `.env` file in the root directory:

```
LIVEPEER_API_KEY=your_livepeer_api_key
WEB3STORAGE_EMAIL=your-email@example.com
```

## 2. Basic Configuration

Copy the example config:

```bash
cp config.example.json config.json
```

Then edit `config.json` as needed with your email address for Web3.Storage.

## 3. Create Required Directories

```bash
mkdir -p input output model cache
```

## 4. Process Your First Video

### AI Compression Only

For your first test, try just the AI compression to make sure everything is working:

```bash
python pipeline.py --input sample.mp4 --no-stream --no-ipfs --no-blockchain
```

This will compress the video using the AI model and save it to the output directory.

### IPFS Upload - First Time Setup

The first time you upload to Web3.Storage, you'll need to complete an authentication process:

```bash
node ipfs_handler_w3up.js sample.mp4 "Test Video" "Testing IPFS upload"
```

This will:
1. Send an authentication email to your address
2. You'll need to check your email and follow the verification link
3. After verification, the script will create a "Space" for your uploads
4. Continue with the upload process

### Full Pipeline

Once authentication is complete, you can use the full pipeline:

```bash
python pipeline.py --input sample.mp4 --title "My First Video" --description "Testing the decentralized video platform"
```

### See the results

After processing completes, you'll find:
- Compressed video in the `output` directory
- IPFS hash and gateway URL for your video
- Livepeer streaming URLs (if enabled)
- Blockchain transaction details (if enabled)

## 5. Using Individual Components

If you want to use only specific parts of the pipeline:

### AI Compression only

```bash
python pipeline.py --input video.mp4 --no-stream --no-ipfs --no-blockchain
```

### IPFS Upload only (after authentication)

```bash
node ipfs_handler_w3up.js path/to/video.mp4 "Video Title" "Video Description"
```

### Livepeer Streaming only

```bash
python livepeer_handler.py path/to/video.mp4
```

## 6. Optional: Smart Contract Integration

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

## 7. Common Commands

Here are some common commands you might need:

```bash
# Process video and skip blockchain registration
python pipeline.py --input video.mp4 --no-blockchain

# Get details for video ID 1 from blockchain
node web3client.js get 1

# List videos you own
node web3client.js myvideos
```

## 8. Troubleshooting

- **AI model errors**: Make sure you have PyTorch properly installed
- **IPFS authentication issues**: Check your email for the verification link from Web3.Storage
- **Web3.Storage "No space found"**: Complete the email verification process first
- **Livepeer connection issues**: Verify your API key
- **Blockchain errors**: Ensure you have sufficient ETH for gas

## Next Steps

- Check the README.md for a detailed architecture overview
- Read W3UP_SETUP.md for more details on the Web3.Storage integration
- Explore the individual component files to understand how they work
