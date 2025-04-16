const { create } = require('ipfs-http-client');
const fs = require('fs');
const path = require('path');

/**
 * IPFS Handler for uploading and retrieving videos
 * Simplified implementation for a decentralized storage system
 */
class IPFSHandler {
  constructor(config = {}) {
    this.config = {
      host: config.host || 'ipfs.infura.io',
      port: config.port || 5001,
      protocol: config.protocol || 'https',
      apiPath: config.apiPath || '/api/v0',
      ...config
    };

    // Create IPFS client
    this.ipfs = create({
      host: this.config.host,
      port: this.config.port,
      protocol: this.config.protocol,
      apiPath: this.config.apiPath
    });
  }

  /**
   * Upload a file to IPFS
   * @param {string} filePath - Path to the file to upload
   * @returns {Promise<{path: string, cid: string, size: number}>}
   */
  async uploadFile(filePath) {
    try {
      // Check if file exists
      if (!fs.existsSync(filePath)) {
        throw new Error(`File not found: ${filePath}`);
      }

      console.log(`Reading file: ${filePath}`);
      const file = fs.readFileSync(filePath);
      
      console.log(`Uploading file to IPFS: ${path.basename(filePath)}`);
      const result = await this.ipfs.add(file, {
        progress: (bytes) => console.log(`Uploaded ${bytes} bytes`)
      });

      console.log(`Successfully uploaded to IPFS`);
      console.log(`CID: ${result.path}`);
      console.log(`Gateway URL: https://ipfs.io/ipfs/${result.path}`);
      
      return {
        path: result.path,
        cid: result.cid.toString(),
        size: result.size,
        url: `https://ipfs.io/ipfs/${result.path}`
      };
    } catch (error) {
      console.error(`Error uploading to IPFS: ${error.message}`);
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
      
      // Convert metadata to JSON and upload
      const metadataBuffer = Buffer.from(JSON.stringify(videoMetadata, null, 2));
      const metadataResult = await this.ipfs.add(metadataBuffer);
      
      console.log(`Metadata uploaded to IPFS: ${metadataResult.path}`);
      
      return {
        video: videoResult,
        metadata: {
          path: metadataResult.path,
          cid: metadataResult.cid.toString(),
          size: metadataResult.size,
          url: `https://ipfs.io/ipfs/${metadataResult.path}`,
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
  node ipfs_handler.js <videoPath> [title] [description]

Example:
  node ipfs_handler.js ./output/compressed_video.mp4 "My Awesome Video" "This is a compressed video uploaded to IPFS"
    `);
    process.exit(1);
  }
  
  const videoPath = args[0];
  const title = args[1] || path.basename(videoPath, path.extname(videoPath));
  const description = args[2] || `Uploaded on ${new Date().toISOString()}`;
  
  const ipfsHandler = new IPFSHandler();
  
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
module.exports = IPFSHandler;