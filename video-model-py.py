import cv2
import torch
import torch.nn as nn
from torchvision import transforms
import numpy as np
import os
from tqdm import tqdm

class ResidualAutoencoder(nn.Module):
    def __init__(self):
        super(ResidualAutoencoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(3, 16, 4, stride=2, padding=1),  # [B, 16, H/2, W/2]
            nn.ReLU(),
            nn.Conv2d(16, 8, 4, stride=2, padding=1),  # [B, 8, H/4, W/4]
            nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(8, 16, 4, stride=2, padding=1),  # [B, 16, H/2, W/2]
            nn.ReLU(),
            nn.ConvTranspose2d(16, 3, 4, stride=2, padding=1),  # [B, 3, H, W]
            nn.Tanh(),  # normalize to [-1, 1]
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

def preprocess_frame(frame, size=(128, 128)):
    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize(size),
        transforms.ToTensor(),
    ])
    return transform(frame)

def compress_video(model, input_path, output_path, device='cpu'):
    """
    Compress video using the trained residual autoencoder model
    """
    print(f"Compressing video: {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input video file not found: {input_path}")
    
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {input_path}")
    
    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Create output video writer
    output_size = (128, 128)  # Fixed size for compressed output
    out = cv2.VideoWriter(
        output_path,
        cv2.VideoWriter_fourcc(*'mp4v'),
        fps,
        output_size
    )
    
    ret, prev_frame = cap.read()
    if not ret:
        raise ValueError("Failed to read the first frame")
    
    prev_tensor = preprocess_frame(prev_frame).unsqueeze(0).to(device)
    out.write(cv2.resize(prev_frame, output_size))
    
    model.eval()
    with torch.no_grad():
        for _ in tqdm(range(total_frames - 1), desc="Compressing frames"):
            ret, frame = cap.read()
            if not ret:
                break
                
            curr_tensor = preprocess_frame(frame).unsqueeze(0).to(device)
            residual = curr_tensor - prev_tensor
            
            # Run through the model
            encoded_residual = model(residual)
            reconstructed = prev_tensor + encoded_residual
            
            # Convert tensor to image
            reconstructed = reconstructed.squeeze().cpu().clamp(0, 1).permute(1, 2, 0).numpy()
            frame_out = (reconstructed * 255).astype(np.uint8)
            
            # Write to output
            out.write(frame_out)
            prev_tensor = curr_tensor
    
    cap.release()
    out.release()
    print(f"Compressed video saved to: {output_path}")
    return output_path

def load_or_train_model(model_path=None, training_video=None):
    """
    Load a pre-trained model or train a new one if needed
    """
    model = ResidualAutoencoder()
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    if model_path and os.path.exists(model_path):
        print(f"Loading model from {model_path}")
        model.load_state_dict(torch.load(model_path, map_location=device))
    else:
        if training_video and os.path.exists(training_video):
            from torch.utils.data import Dataset, DataLoader
            import torch.optim as optim
            
            print(f"Training new model using {training_video}")
            
            # Define a simple dataset for training
            class ResidualVideoDataset(Dataset):
                def __init__(self, video_path, size=(128, 128)):
                    self.residuals = []
                    transform = transforms.Compose([
                        transforms.ToPILImage(),
                        transforms.Resize(size),
                        transforms.ToTensor(),
                    ])

                    cap = cv2.VideoCapture(video_path)
                    ret, prev = cap.read()
                    if not ret:
                        raise ValueError("Couldn't read video.")

                    prev_tensor = transform(prev)

                    while True:
                        ret, curr = cap.read()
                        if not ret:
                            break
                        curr_tensor = transform(curr)
                        residual = curr_tensor - prev_tensor
                        self.residuals.append(residual)
                        prev_tensor = curr_tensor

                    cap.release()
                    print(f"Created dataset with {len(self.residuals)} frames")

                def __len__(self):
                    return len(self.residuals)

                def __getitem__(self, idx):
                    return self.residuals[idx], self.residuals[idx]  # input == target
            
            # Train the model
            dataset = ResidualVideoDataset(training_video)
            dataloader = DataLoader(dataset, batch_size=16, shuffle=True)
            
            model.to(device)
            criterion = nn.MSELoss()
            optimizer = optim.Adam(model.parameters(), lr=1e-3)
            
            num_epochs = 5  # Quick training for demonstration
            for epoch in range(num_epochs):
                model.train()
                running_loss = 0.0
                for inputs, targets in tqdm(dataloader, desc=f"Epoch {epoch+1}/{num_epochs}"):
                    inputs, targets = inputs.to(device), targets.to(device)
                    optimizer.zero_grad()
                    outputs = model(inputs)
                    loss = criterion(outputs, targets)
                    loss.backward()
                    optimizer.step()
                    running_loss += loss.item()

                avg_loss = running_loss / len(dataloader)
                print(f"Epoch {epoch+1} Loss: {avg_loss:.6f}")
            
            # Save the model
            model_dir = os.path.dirname(os.path.abspath(model_path if model_path else "model/residual_encoder.pth"))
            os.makedirs(model_dir, exist_ok=True)
            model_path = model_path if model_path else "model/residual_encoder.pth"
            torch.save(model.state_dict(), model_path)
            print(f"Model saved to {model_path}")
        else:
            print("No model or training data provided. Using untrained model.")
    
    model.to(device)
    return model, device

if __name__ == "__main__":
    # Example usage
    model_path = "model/residual_encoder.pth"
    training_video = "sample.mp4"  # Use your sample video for training
    
    model, device = load_or_train_model(model_path, training_video)
    
    input_video = "sample.mp4"
    output_video = "output/compressed_video.mp4"
    
    compressed_video_path = compress_video(model, input_video, output_video, device)
    print(f"Video compression complete: {compressed_video_path}")
