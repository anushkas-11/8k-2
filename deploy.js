const hre = require("hardhat");

/**
 * Deploy the VideoStorage contract to a local or test network
 */
async function main() {
  console.log("Starting deployment of VideoStorage contract...");

  // Get the contract factory
  const VideoStorage = await hre.ethers.getContractFactory("VideoStorage");
  
  // Deploy the contract
  console.log("Deploying VideoStorage...");
  const videoStorage = await VideoStorage.deploy();

  // Wait for deployment to complete
  await videoStorage.deployed();
  
  // Log the deployment address
  console.log(`VideoStorage contract deployed at: ${videoStorage.address}`);
  
  // For easier testing, we'll create a JSON file with deployment info
  const fs = require("fs");
  const deploymentInfo = {
    network: hre.network.name,
    contractAddress: videoStorage.address,
    deploymentTime: new Date().toISOString(),
    blockNumber: await hre.ethers.provider.getBlockNumber()
  };
  
  // Save deployment info to file
  const deploymentDir = "./deployments";
  if (!fs.existsSync(deploymentDir)) {
    fs.mkdirSync(deploymentDir, { recursive: true });
  }
  
  fs.writeFileSync(
    `${deploymentDir}/deployment-${hre.network.name}.json`,
    JSON.stringify(deploymentInfo, null, 2)
  );
  
  console.log(`Deployment info saved to: ${deploymentDir}/deployment-${hre.network.name}.json`);
  
  // If on a testnet, verify the contract (skip for local networks)
  if (["goerli", "sepolia", "polygon-mumbai"].includes(hre.network.name)) {
    console.log("Waiting for block confirmations...");
    
    // Wait for 6 block confirmations for verification
    await videoStorage.deployTransaction.wait(6);
    
    console.log("Verifying contract on Etherscan...");
    await hre.run("verify:verify", {
      address: videoStorage.address,
      constructorArguments: [],
    });
  }
}

// Execute the deployment
main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("Deployment failed:", error);
    process.exit(1);
  });
