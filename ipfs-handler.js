// Modern Web3.Storage (Storacha) handler using w3up-client
const fs = require('fs');
const path = require('path');
const { create } = require('@web3-storage/w3up-client');
const { StoreMemory } = require('@web3-storage/w3up-client/stores/memory');

/**
 * IPFS Handler for uploading and retrieving videos
 * Using Web3.Storage w3up client
 */
class W3UPHandler {
  constructor(config = {}) {
    this.config = {
      email: config.email || process.env.WEB3STORAGE_EMAIL || '',
      ...config
    };
    
    this.client = null;
    this.initialized = false;
  }

  /**
   * Initialize the Web3.Storage client
   * @returns {Promise<void>}
   */
  async initialize() {
    if (this.initialized) return;

    try {
      console.log("Initializing Web3.Storage client...");
      
      // Create a store to persist data
      const store = new StoreMemory();
      
      // Create a client
      this.client = await create({ store });
      
      // Check if we need to authenticate
      if (this.config.email) {
        console.log(`Authenticating with email: ${this.config.email}`);
        
        try {
          // Request authentication with email
          await this.client.authorize(this.config.email);
          console.log("Authorization email sent. Please check your email and follow instructions.");
          
          // This would normally be interactive, but in a script we need to wait for user confirmation
          // For a script, we assume the user has already registered and authorized
          try {
            await this.client.capability.access.claim();
            const spaces = await this.client.spaces();
            
            if (spaces.length > 0) {
              const space = spaces[0];
              console.log(`Found space: ${space.did()}`);
              await this.client.setCurrentSpace(space.did());
              console.log("Successfully authenticated with Web3.Storage!");
              this.initialized = true;
            } else {
              console.log("No spaces found. Creating a new space...");
              const space = await this.client.createSpace("My Decentralized Video Space");
              await this.client.setCurrentSpace(space.did());
              
              // Register the space with Web3.Storage
              console.log(`Registering space: ${space.did()}`);
              await this.client.capability.space.register({ did: space.did() });
              
              console.log("Successfully created and registered a new space!");
              this.initialized = true;
            }
          } catch (error) {
            console.error("Error claiming capabilities:", error.message);
            throw new Error("Authentication failed. Please make sure you've completed the email verification.");
          }
        } catch (error) {
          console.error("Error during authentication:", error.message);
          throw new Error("Authentication with Web3.Storage failed.");
        }
      } else {
        console.warn("No email provided for Web3.Storage. Limited functionality available.");
      }
    } catch (error) {
      console.error("Error initializing Web3.Storage client:", error.message);
      throw error;
    }
  }

  /**
   * Upload a file to Web3.Storage
   * @param {string} filePath - Path to the file to upload
   * @returns {Promise<{path: string, cid: string, size: number}>}
   */
  async uploadFile(filePath) {
    try {
      // Initialize client if not already initialized
      if (!this.initialized) {
        await this.initialize();
      }
      
      // Check if file exists
      if (!fs.existsSync(filePath)) {
        throw new Error(`File not found: ${filePath}`);
      }

      console.log(`Reading file: ${filePath}`);
      const fileData = fs.readFileSync(filePath);
      const fileName = path.basename(filePath);
      
      console.log(`Uploading file to Web3.Storage: ${fileName}`);
      console.log(`File size: ${(fileData.length / (1024 * 1024)).toFixed(2)} MB`);
      
      // Upload to Web3.Storage
      const uploadable = new Blob([fileData]);
      const cid = await this.client.uploadFile(uploadable);
      
      console.log(`Successfully uploaded to Web3.Storage`);
      console.log(`CID: ${cid}`);
      console.log(`Gateway URL: https://${cid}.ipfs.w3s.link/${fileName}`);
      
      return {
        path: cid.toString(),
        cid: cid.toString(),
        size: fileData.length,
        url: `https://${cid}.ipfs.w3s.link/${fileName}`
      };
    } catch (error) {
      console.error(`Error uploading to Web3.Storage: ${error.message}`);
      throw error;
    }
  }

  /**
   * Upload a video with metadata
   * @param {string} videoPath - Path to the video file
   * @param {Object} metadata - Video metadata
   * @returns {Promise<{video: Object, metadata: Object}>}
   */
  async uploadVideoWithMetadata(videoPath, metadata = {}) {
    try {
      // Upload the video file first
      const videoResult = await this.uploadFile(videoPath);
      
      // Create a metadata object
      const videoMetadata = {
        title: metadata.title || path.basename(videoPath, path.extname(videoPath)),
        description: metadata.description || '',
        timestamp: metadata.timestamp || new Date().toISOString(),
        videoHash: videoResult.path,
        videoSize: videoResult.size,
        ...metadata
      };
      
      // Upload metadata JSON as a file
      const metadataFilePath = path.join(
        path.dirname(videoPath),
        `metadata_${path.basename(videoPath, path.extname(videoPath))}.json`
      );
      
      // Write metadata to temp file
      fs.writeFileSync(metadataFilePath, JSON.stringify(videoMetadata, null, 2));
      
      // Upload the metadata file
      const metadataResult = await this.uploadFile(metadataFilePath);
      
      // Remove the temp file
      fs.unlinkSync(metadataFilePath);
      
      console.log(`Metadata uploaded to Web3.Storage: ${metadataResult.path}`);
      
      return {
        video: videoResult,
        metadata: {
          path: metadataResult.path,
          cid: metadataResult.cid,
          size: metadataResult.size,
          url: metadataResult.url,
          content: videoMetadata
        }
      };
    } catch (error) {
      console.error(`Error uploading video with metadata: ${error.message}`);
      throw error;
    }
  }

  /**
   * Generate simplified metadata file locally for the uploaded video
   * @param {Object} result - Upload result from uploadVideoWithMetadata
   * @param {string} outputPath - Output path for metadata file
   * @returns {string} Path to the metadata file
   */
  saveMetadataLocally(result, outputPath) {
    const metadata = {
      title: result.metadata.content.title,
      description: result.metadata.content.description,
      timestamp: result.metadata.content.timestamp,
      ipfsHash: result.video.path,
      ipfsUrl: result.video.url,
      metadataHash: result.metadata.path,
      metadataUrl: result.metadata.url
    };
    
    const outputDir = path.dirname(outputPath);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }
    
    fs.writeFileSync(outputPath, JSON.stringify(metadata, null, 2));
    console.log(`Metadata saved to: ${outputPath}`);
    
    return outputPath;
  }
}

// Simple CLI interface
if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args.length < 1) {
    console.log(`
Usage: 
  node ipfs_handler_w3up.js <videoPath> [title] [description]

Example:
  node ipfs_handler_w3up.js ./output/compressed_video.mp4 "My Awesome Video" "This is a compressed video uploaded to IPFS"

Environment variables:
  WEB3STORAGE_EMAIL - The email address registered with Web3.Storage
    `);
    process.exit(1);
  }
  
  const videoPath = args[0];
  const title = args[1] || path.basename(videoPath, path.extname(videoPath));
  const description = args[2] || `Uploaded on ${new Date().toISOString()}`;
  
  const ipfsHandler = new W3UPHandler();
  
  ipfsHandler.uploadVideoWithMetadata(videoPath, { title, description })
    .then(result => {
      const metadataPath = path.join('output', 'metadata.json');
      ipfsHandler.saveMetadataLocally(result, metadataPath);
      
      console.log('\nUpload Summary:');
      console.log('===============');
      console.log(`Title: ${result.metadata.content.title}`);
      console.log(`Video IPFS Hash: ${result.video.path}`);
      console.log(`Video URL: ${result.video.url}`);
      console.log(`Metadata IPFS Hash: ${result.metadata.path}`);
      console.log(`Metadata URL: ${result.metadata.url}`);
      console.log(`Local Metadata: ${metadataPath}`);
    })
    .catch(error => {
      console.error(`Failed to upload: ${error.message}`);
      process.exit(1);
    });
}

// Export the handler for use in other modules
module.exports = W3UPHandler;
