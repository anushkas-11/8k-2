const { ethers } = require("ethers");
const fs = require("fs");
const path = require("path");

/**
 * Web3 Client for interacting with the VideoStorage smart contract
 * This is a simplified implementation that works with local or test networks
 */
class Web3Client {
  /**
   * Create a new Web3Client instance
   * @param {Object} config - Configuration object
   * @param {string} config.providerUrl - Provider URL (e.g., Infura endpoint)
   * @param {string} config.privateKey - Private key for signing transactions
   * @param {string} config.contractAddress - VideoStorage contract address
   * @param {string} config.contractAbiPath - Path to contract ABI JSON file
   */
  constructor(config) {
    this.config = config;
    this.provider = null;
    this.signer = null;
    this.contract = null;
    
    // Initialize provider, signer, and contract
    this.initialize();
  }
  
  /**
   * Initialize the Ethereum provider, signer, and contract
   */
  initialize() {
    try {
      // Set up provider and signer
      this.provider = new ethers.providers.JsonRpcProvider(this.config.providerUrl);
      
      if (this.config.privateKey) {
        this.signer = new ethers.Wallet(this.config.privateKey, this.provider);
        console.log(`Connected wallet address: ${this.signer.address}`);
      } else {
        console.warn("No private key provided. Read-only mode enabled.");
        this.signer = this.provider;
      }
      
      // Load contract ABI
      let contractABI;
      if (this.config.contractAbi) {
        contractABI = this.config.contractAbi;
      } else if (this.config.contractAbiPath) {
        contractABI = JSON.parse(fs.readFileSync(this.config.contractAbiPath, 'utf8'));
      } else {
        throw new Error("Contract ABI not provided");
      }
      
      // Create contract instance
      this.contract = new ethers.Contract(
        this.config.contractAddress, 
        contractABI, 
        this.signer
      );
      
      console.log(`Connected to VideoStorage contract at ${this.config.contractAddress}`);
    } catch (error) {
      console.error(`Initialization failed: ${error.message}`);
      throw error;
    }
  }
  
  /**
   * Upload video metadata to the blockchain
   * @param {string} title - Video title
   * @param {string} description - Video description
   * @param {string} ipfsHash - IPFS hash of the video
   * @param {string} price - Price in ETH
   * @returns {Promise<Object>} Transaction receipt
   */
  async uploadVideo(title, description, ipfsHash, price) {
    try {
      // Convert price from ETH to Wei
      const priceInWei = ethers.utils.parseEther(price);
      
      console.log(`Uploading video metadata to blockchain:`);
      console.log(`- Title: ${title}`);
      console.log(`- IPFS Hash: ${ipfsHash}`);
      console.log(`- Price: ${price} ETH (${priceInWei.toString()} Wei)`);
      
      // Call the contract method
      const tx = await this.contract.uploadVideo(
        title,
        description,
        ipfsHash,
        priceInWei
      );
      
      console.log(`Transaction submitted: ${tx.hash}`);
      console.log("Waiting for confirmation...");
      
      // Wait for transaction confirmation
      const receipt = await tx.wait();
      console.log(`Transaction confirmed in block ${receipt.blockNumber}`);
      
      // Parse log to get video ID
      const event = receipt.events.find(e => e.event === "VideoUploaded");
      const videoId = event.args.videoId.toString();
      
      console.log(`Video uploaded successfully with ID: ${videoId}`);
      
      return {
        videoId,
        transactionHash: receipt.transactionHash,
        blockNumber: receipt.blockNumber
      };
    } catch (error) {
      console.error(`Failed to upload video: ${error.message}`);
      throw error;
    }
  }
  
  /**
   * Get video details from the blockchain
   * @param {string|number} videoId - ID of the video
   * @returns {Promise<Object>} Video details
   */
  async getVideo(videoId) {
    try {
      console.log(`Fetching details for video ${videoId}...`);
      
      // Call the contract method
      const result = await this.contract.getVideoDetails(videoId);
      
      // Format the response
      const video = {
        id: videoId,
        title: result.title,
        description: result.description,
        ipfsHash: result.ipfsHash,
        owner: result.owner,
        price: ethers.utils.formatEther(result.price),
        uploadTime: new Date(result.uploadTime.toNumber() * 1000).toISOString(),
        isActive: result.isActive
      };
      
      console.log(`Video details retrieved successfully`);
      console.log(`- Title: ${video.title}`);
      console.log(`- IPFS Hash: ${video.ipfsHash || '[Not authorized to view]'}`);
      console.log(`- Owner: ${video.owner}`);
      console.log(`- Price: ${video.price} ETH`);
      
      return video;
    } catch (error) {
      console.error(`Failed to get video details: ${error.message}`);
      throw error;
    }
  }
  
  /**
   * Buy access to a video
   * @param {string|number} videoId - ID of the video to purchase
   * @param {string} price - Price in ETH to pay
   * @returns {Promise<Object>} Transaction receipt
   */
  async buyVideo(videoId, price) {
    try {
      // Convert price from ETH to Wei
      const priceInWei = ethers.utils.parseEther(price);
      
      console.log(`Purchasing video ${videoId} for ${price} ETH...`);
      
      // Call the contract method with payment
      const tx = await this.contract.buyVideo(videoId, {
        value: priceInWei
      });
      
      console.log(`Transaction submitted: ${tx.hash}`);
      console.log("Waiting for confirmation...");
      
      // Wait for transaction confirmation
      const receipt = await tx.wait();
      console.log(`Transaction confirmed in block ${receipt.blockNumber}`);
      console.log(`Video purchased successfully!`);
      
      return {
        videoId,
        transactionHash: receipt.transactionHash,
        blockNumber: receipt.blockNumber
      };
    } catch (error) {
      console.error(`Failed to purchase video: ${error.message}`);
      throw error;
    }
  }
  
  /**
   * Check if the current user has access to a video
   * @param {string|number} videoId - ID of the video
   * @returns {Promise<boolean>} True if authorized
   */
  async hasAccessToVideo(videoId) {
    try {
      const userAddress = this.signer.address;
      return await this.contract.hasAccess(userAddress, videoId);
    } catch (error) {
      console.error(`Failed to check access: ${error.message}`);
      throw error;
    }
  }
  
  /**
   * Get videos owned by the current user
   * @returns {Promise<Array>} Array of video IDs
   */
  async getMyVideos() {
    try {
      const userAddress = this.signer.address;
      const videoIds = await this.contract.getVideoIdsByOwner(userAddress);
      
      console.log(`Found ${videoIds.length} videos owned by ${userAddress}`);
      
      // Convert BigNumber to string
      return videoIds.map(id => id.toString());
    } catch (error) {
      console.error(`Failed to get user videos: ${error.message}`);
      throw error;
    }
  }
}

// CLI interface for testing
async function runCLI() {
  const args = process.argv.slice(2);
  const command = args[0] || 'help';
  
  // Load configuration
  let config = {
    providerUrl: "http://localhost:8545",  // Default to local node
    contractAddress: "",
    privateKey: ""
  };
  
  // Try to load from deployment files or environment
  try {
    // Check deployments directory
    const deploymentsDir = path.join(__dirname, 'deployments');
    if (fs.existsSync(deploymentsDir)) {
      const files = fs.readdirSync(deploymentsDir);
      const deploymentFile = files.find(f => f.startsWith('deployment-'));
      
      if (deploymentFile) {
        const deployment = JSON.parse(
          fs.readFileSync(path.join(deploymentsDir, deploymentFile), 'utf8')
        );
        config.contractAddress = deployment.contractAddress;
        console.log(`Loaded contract address from deployment: ${config.contractAddress}`);
      }
    }
    
    // Load ABI
    const abiPath = path.join(__dirname, 'artifacts/contracts/VideoStorage.sol/VideoStorage.json');
    if (fs.existsSync(abiPath)) {
      const artifact = JSON.parse(fs.readFileSync(abiPath, 'utf8'));
      config.contractAbi = artifact.abi;
      console.log(`Loaded contract ABI from artifacts`);
    } else {
      config.contractAbiPath = path.join(__dirname, 'VideoStorageABI.json');
      if (!fs.existsSync(config.contractAbiPath)) {
        console.warn(`ABI file not found at ${config.contractAbiPath}`);
      }
    }
    
    // Check environment variables
    if (process.env.PROVIDER_URL) {
      config.providerUrl = process.env.PROVIDER_URL;
    }
    
    if (process.env.CONTRACT_ADDRESS) {
      config.contractAddress = process.env.CONTRACT_ADDRESS;
    }
    
    if (process.env.PRIVATE_KEY) {
      config.privateKey = process.env.PRIVATE_KEY;
    }
    
    // Check for custom config file
    const configPath = path.join(__dirname, 'config.json');
    if (fs.existsSync(configPath)) {
      const fileConfig = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      config = { ...config, ...fileConfig };
      console.log(`Loaded configuration from config.json`);
    }
  } catch (error) {
    console.warn(`Error loading configuration: ${error.message}`);
  }
  
  // Validate required config
  if (!config.contractAddress) {
    console.error("Error: Contract address not provided");
    console.log("Please set CONTRACT_ADDRESS environment variable or create a config.json file");
    process.exit(1);
  }
  
  // Create client
  const client = new Web3Client(config);
  
  // Process commands
  switch (command) {
    case 'upload':
      // node web3client.js upload "My Video" "Description" QmHash 0.1
      if (args.length < 5) {
        console.log("Usage: node web3client.js upload <title> <description> <ipfsHash> <price>");
        process.exit(1);
      }
      
      await client.uploadVideo(args[1], args[2], args[3], args[4]);
      break;
      
    case 'get':
      // node web3client.js get 1
      if (args.length < 2) {
        console.log("Usage: node web3client.js get <videoId>");
        process.exit(1);
      }
      
      await client.getVideo(args[1]);
      break;
      
    case 'buy':
      // node web3client.js buy 1 0.1
      if (args.length < 3) {
        console.log("Usage: node web3client.js buy <videoId> <price>");
        process.exit(1);
      }
      
      await client.buyVideo(args[1], args[2]);
      break;
      
    case 'myvideos':
      // node web3client.js myvideos
      const videos = await client.getMyVideos();
      console.log("Your videos:", videos);
      break;
      
    case 'help':
    default:
      console.log(`
Web3 Client for VideoStorage

Usage:
  node web3client.js upload <title> <description> <ipfsHash> <price>
  node web3client.js get <videoId>
  node web3client.js buy <videoId> <price>
  node web3client.js myvideos
  node web3client.js help

Configuration:
  Set the following environment variables:
  - PROVIDER_URL: Ethereum provider URL (default: http://localhost:8545)
  - CONTRACT_ADDRESS: VideoStorage contract address
  - PRIVATE_KEY: Private key for signing transactions
  
  Or create a config.json file with these properties:
  {
    "providerUrl": "https://goerli.infura.io/v3/YOUR_INFURA_PROJECT_ID",
    "contractAddress": "YOUR_CONTRACT_ADDRESS",
    "privateKey": "YOUR_PRIVATE_KEY"
  }
      `);
      break;
  }
}

// Run if called directly
if (require.main === module) {
  runCLI()
    .then(() => process.exit(0))
    .catch(error => {
      console.error("Error:", error);
      process.exit(1);
    });
}

// Export for use in other modules
module.exports = Web3Client;
