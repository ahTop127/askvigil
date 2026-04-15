# # Docker extension -> right click askvigil-backend, start new shell. then run:
# # export PYTHONPATH=$PYTHONPATH:.
# # uv run python -m scripts.train_mlp_heads
import asyncio
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, random_split
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
from tortoise import Tortoise

from app.core.config import settings
from app.core.database import TORTOISE_ORM
from app.models.open_data import OpenDataSet


class ScamPhishingMLP(nn.Module):
    def __init__(self, input_dim):
        super(ScamPhishingMLP, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim + settings.RRF_K, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.4),  # Primary regularization
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.3),  # Secondary regularization
            nn.Linear(64, 2),
            nn.Softmax(dim=1),  # Ensures probabilities sum to 1.0
        )

    def forward(self, x):
        return self.net(x)


class UnifiedDataset(Dataset):
    def __init__(self, haz_records, safe_records):
        self.features = []
        self.labels = []
        self._process(haz_records, [1.0, 0.0])  # Hazard (Spam/Phish)
        self._process(safe_records, [0.0, 1.0])  # Safe (Ham)
        self.features = np.array(self.features, dtype=np.float32)
        self.labels = np.array(self.labels, dtype=np.float32)

    def _process(self, records, target_vector):
        """
        Simulates Evidence Density:
        - Correct class gets momentum in [0.2, 1.00] based on 'simulated' match quality.
        - Opposite class gets low noise in [0.0, 0.2].
        - This allows [0, 0] to represent a legitimate 'Novelty' state.
        """
        for r in records:
            if r.text_embedding is None:
                continue
            emb = np.array(r.text_embedding, dtype=np.float32)

            # 2. Simulate Class Momentum [Spam_Momentum, Ham_Momentum]
            # Not all training data has perfect historical matches
            primary_momentum = np.random.uniform(0.2, 1.00)
            secondary_momentum = np.random.uniform(0.0, 0.2)

            if target_vector == [1.0, 0.0]: # Spam
                momentum_vec = np.array(
                    [primary_momentum, secondary_momentum], dtype=np.float32
                )
            else:
                momentum_vec = np.array(
                    [secondary_momentum, primary_momentum], dtype=np.float32
                )

            # 2. Feature blurring/dropout
            if np.random.rand() < 0.4:
                momentum_vec = np.array([0.0, 0.0], dtype=np.float32)

            # 3. Fuse Features (384 + 2 = 386)
            fused = np.concatenate([emb, momentum_vec]).astype(np.float32)

            self.features.append(fused)
            self.labels.append(target_vector)

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        return torch.from_numpy(self.features[idx]).float(), torch.from_numpy(
            self.labels[idx]
        ).float()


async def train_and_export(mode="text", haz_label="spam", safe_label="ham"):
    if not Tortoise._inited:
        await Tortoise.init(config=TORTOISE_ORM)

    haz = await OpenDataSet.filter(text_embedding__isnull=False, label=haz_label).all()
    safe = await OpenDataSet.filter(
        text_embedding__isnull=False, label=safe_label
    ).all()

    full_dataset = UnifiedDataset(haz, safe)
    train_size = int(0.8 * len(full_dataset))
    val_set_size = len(full_dataset) - train_size
    train_set, val_set = random_split(full_dataset, [train_size, val_set_size])

    train_loader = DataLoader(train_set, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=32)

    dim = settings.DIM_TEXT if mode == "text" else settings.DIM_URL
    model = ScamPhishingMLP(dim)
    optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-2)
    criterion = nn.BCELoss()

    for epoch in range(10):
        model.train()
        t_loss, t_correct = 0, 0
        for feat, target in train_loader:
            optimizer.zero_grad()
            out = model(feat)
            loss = criterion(out, target)
            loss.backward()
            optimizer.step()
            t_loss += loss.item()
            t_correct += (out.argmax(1) == target.argmax(1)).sum().item()

        # Validation
        model.eval()
        v_loss, v_correct = 0, 0
        y_true, y_pred = [], []
        with torch.no_grad():
            for feat, target in val_loader:
                out = model(feat)
                v_loss += criterion(out, target).item()
                v_correct += (out.argmax(1) == target.argmax(1)).sum().item()
                y_true.extend(target.argmax(1).tolist())
                y_pred.extend(out.argmax(1).tolist())

        print(
            f"Epoch {epoch + 1} | T_Loss: {t_loss / len(train_loader):.4f} | T_Acc: {t_correct / train_size:.4f} | V_Loss: {v_loss / len(val_loader):.4f} | V_Acc: {v_correct / val_set_size:.4f}"
        )

    print("\n--- F1 METRICS MATRIX ---")
    print(classification_report(y_true, y_pred, target_names=[haz_label, safe_label]))
    print("--- CONFUSION MATRIX ---")
    print(confusion_matrix(y_true, y_pred))

    # Export
    export_dir = settings.TEXT_MODEL_PATH if mode == "text" else settings.URL_MODEL_PATH
    export_path = export_dir / "classifier.onnx"
    dummy_input = torch.randn(1, dim + settings.RRF_K).float()
    torch.onnx.export(
        model,
        dummy_input,
        str(export_path),
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
        opset_version=18,
    )


if __name__ == "__main__":
    asyncio.run(train_and_export(mode="text", haz_label="spam", safe_label="ham"))
