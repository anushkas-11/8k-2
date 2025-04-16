// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title VideoStorage
 * @dev Manages metadata and access control for videos stored on IPFS
 */
contract VideoStorage {
    struct Video {
        string title;
        string description;
        string ipfsHash;  // IPFS hash for video access
        address payable owner;
        uint256 price;    // Price in wei
        uint256 uploadTime;
        bool isActive;
    }
    
    // Video ID to Video mapping
    mapping(uint256 => Video) public videos;
    // Total number of videos
    uint256 public videoCount = 0;
    // User to purchased video IDs mapping
    mapping(address => mapping(uint256 => bool)) public userPurchases;
    
    // Events
    event VideoUploaded(uint256 indexed videoId, string title, string ipfsHash, address indexed owner, uint256 price);
    event VideoPurchased(uint256 indexed videoId, address indexed buyer, uint256 price);
    event VideoUpdated(uint256 indexed videoId, string title, string description, uint256 price);
    event VideoActivationChanged(uint256 indexed videoId, bool isActive);
    
    /**
     * @dev Upload a new video with metadata and price
     * @param title Title of the video
     * @param description Description of the video
     * @param ipfsHash IPFS hash of the video
     * @param price Price in wei to access the video
     */
    function uploadVideo(
        string memory title, 
        string memory description, 
        string memory ipfsHash, 
        uint256 price
    ) 
        public 
    {
        // Validate inputs
        require(bytes(title).length > 0, "Title cannot be empty");
        require(bytes(ipfsHash).length > 0, "IPFS hash cannot be empty");
        
        // Increment video count
        videoCount++;
        
        // Create new video
        videos[videoCount] = Video({
            title: title,
            description: description,
            ipfsHash: ipfsHash,
            owner: payable(msg.sender),
            price: price,
            uploadTime: block.timestamp,
            isActive: true
        });
        
        // Emit event
        emit VideoUploaded(videoCount, title, ipfsHash, msg.sender, price);
    }
    
    /**
     * @dev Buy access to a video
     * @param videoId ID of the video to purchase
     */
    function buyVideo(uint256 videoId) public payable {
        // Validate video ID
        require(videoId > 0 && videoId <= videoCount, "Invalid video ID");
        
        // Get video
        Video storage video = videos[videoId];
        
        // Check if video is active
        require(video.isActive, "Video is not available for purchase");
        
        // Check if user already purchased
        require(!userPurchases[msg.sender][videoId], "Video already purchased");
        
        // Check payment
        require(msg.value >= video.price, "Insufficient payment");
        
        // Transfer payment to video owner
        video.owner.transfer(msg.value);
        
        // Mark as purchased
        userPurchases[msg.sender][videoId] = true;
        
        // Emit event
        emit VideoPurchased(videoId, msg.sender, msg.value);
    }
    
    /**
     * @dev Check if user has access to a video
     * @param user Address of the user
     * @param videoId ID of the video
     * @return bool True if user has access
     */
    function hasAccess(address user, uint256 videoId) public view returns (bool) {
        // Owner always has access
        if (videos[videoId].owner == user) {
            return true;
        }
        
        // Check if purchased
        return userPurchases[user][videoId];
    }
    
    /**
     * @dev Get video details (without the IPFS hash if not authorized)
     * @param videoId ID of the video
     * @return Video details (ipfsHash is empty if not authorized)
     */
    function getVideoDetails(uint256 videoId) public view returns (
        string memory title,
        string memory description,
        string memory ipfsHash,
        address owner,
        uint256 price,
        uint256 uploadTime,
        bool isActive
    ) {
        // Validate video ID
        require(videoId > 0 && videoId <= videoCount, "Invalid video ID");
        
        // Get video
        Video storage video = videos[videoId];
        
        // Return IPFS hash only if authorized
        string memory hash = "";
        if (hasAccess(msg.sender, videoId)) {
            hash = video.ipfsHash;
        }
        
        return (
            video.title,
            video.description,
            hash,
            video.owner,
            video.price,
            video.uploadTime,
            video.isActive
        );
    }
    
    /**
     * @dev Update video details (only owner)
     * @param videoId ID of the video to update
     * @param title New title
     * @param description New description
     * @param price New price
     */
    function updateVideo(
        uint256 videoId,
        string memory title,
        string memory description,
        uint256 price
    ) 
        public 
    {
        // Validate video ID
        require(videoId > 0 && videoId <= videoCount, "Invalid video ID");
        
        // Get video
        Video storage video = videos[videoId];
        
        // Check ownership
        require(msg.sender == video.owner, "Only owner can update video");
        
        // Update fields
        if (bytes(title).length > 0) {
            video.title = title;
        }
        
        video.description = description;
        video.price = price;
        
        // Emit event
        emit VideoUpdated(videoId, video.title, video.description, video.price);
    }
    
    /**
     * @dev Change video activation status (only owner)
     * @param videoId ID of the video
     * @param isActive New active status
     */
    function setVideoActive(uint256 videoId, bool isActive) public {
        // Validate video ID
        require(videoId > 0 && videoId <= videoCount, "Invalid video ID");
        
        // Get video
        Video storage video = videos[videoId];
        
        // Check ownership
        require(msg.sender == video.owner, "Only owner can change video status");
        
        // Update status
        video.isActive = isActive;
        
        // Emit event
        emit VideoActivationChanged(videoId, isActive);
    }
    
    /**
     * @dev Get count of videos owned by an address
     * @param owner Address to check
     * @return uint256 Number of videos owned
     */
    function getVideoCountByOwner(address owner) public view returns (uint256) {
        uint256 count = 0;
        
        for (uint256 i = 1; i <= videoCount; i++) {
            if (videos[i].owner == owner) {
                count++;
            }
        }
        
        return count;
    }
    
    /**
     * @dev Get IDs of videos owned by an address
     * @param owner Address to check
     * @return uint256[] Array of video IDs
     */
    function getVideoIdsByOwner(address owner) public view returns (uint256[] memory) {
        // Get count first
        uint256 count = getVideoCountByOwner(owner);
        
        // Create array of appropriate size
        uint256[] memory result = new uint256[](count);
        
        // Fill array
        uint256 resultIndex = 0;
        for (uint256 i = 1; i <= videoCount; i++) {
            if (videos[i].owner == owner) {
                result[resultIndex] = i;
                resultIndex++;
            }
        }
        
        return result;
    }
}
