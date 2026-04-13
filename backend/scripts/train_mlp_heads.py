import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
import os
from pathlib import Path

# --- CONFIG ---
DATA_DIR = Path("data_persistence/datasets")
MODEL_EXPORT_DIR = Path("data_persistence/ai_models")
SCAM_CSV = DATA_DIR / "scam_dataset.csv"
PHISH_CSV = DATA_DIR / "phishing_dataset.csv"

# Input Dimensions
DIM_TEXT = 384  # MiniLM
DIM_URL = 768   # URLBert
RRF_K = 5       # Top 5 RRF scores

class ScamPhishingMLP(nn.Module):
    def __init__(self, input_dim):
        super(ScamPhishingMLP, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim + RRF_K, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 2), # Output: [Scam, Phishing]
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.net(x)

class MultiModalDataset(Dataset):
    def __init__(self, csv_path, embedding_dim):
        # TODO: In production, this would load pre-generated embeddings from a .npy or CSV.
        # For this logic check, we simulate the 'Extracted Features' 
        if os.path.exists(csv_path):
            self.df = pd.read_csv(csv_path)
        else:
            print(f"Warning: {csv_path} not found. Using dummy data for architecture testing.")
            self.df = pd.DataFrame(columns=["text", "is_scam", "is_phishing"])
        
        self.emb_dim = embedding_dim

    def __len__(self):
        return len(self.df) if len(self.df) > 0 else 100

    def __getitem__(self, idx):
        # Simulate pre-extracted [Embedding + RRF Scores]
        # In Step 6, replace this with actual data from your 'import_data.py' logic
        emb = np.random.randn(self.emb_dim).astype(np.float32)
        rrf = np.random.rand(RRF_K).astype(np.float32) * 100 # Feature Scaling applied
        
        features = np.concatenate([emb, rrf])
        
        # Targets: [Scam, Phishing]
        target = np.array([1.0, 0.0], dtype=np.float32) # Default dummy
        return torch.from_numpy(features), torch.from_numpy(target)

def train_and_export(mode="text"):
    dim = DIM_TEXT if mode == "text" else DIM_URL
    csv = SCAM_CSV if mode == "text" else PHISH_CSV
    
    model = ScamPhishingMLP(dim)
    dataset = MultiModalDataset(csv, dim)
    loader = DataLoader(dataset, batch_size=32, shuffle=True)
    
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.BCELoss()

    print(f"Training {mode.upper()} MLP Head...")
    model.train()
    for epoch in range(5): # Fast training for MLP heads
        total_loss = 0
        for feat, label in loader:
            optimizer.zero_grad()
            output = model(feat)
            loss = criterion(output, label)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"Epoch {epoch+1} Loss: {total_loss/len(loader):.4f}")

    # --- ONNX EXPORT ---
    export_path = MODEL_EXPORT_DIR / f"{mode}_onnx" / "classifier.onnx"
    export_path.parent.mkdir(parents=True, exist_ok=True)
    
    model.eval()
    dummy_input = torch.randn(1, dim + RRF_K)
    torch.onnx.export(
        model, 
        dummy_input, 
        str(export_path),
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}},
        opset_version=12
    )
    print(f"Exported {mode} classifier to {export_path}")

if __name__ == "__main__":
    train_and_export("text")
    train_and_export("url")