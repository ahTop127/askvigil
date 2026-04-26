# # Docker extension -> right click askvigil-backend, start new shell. then run:
# # export PYTHONPATH=$PYTHONPATH:.
# # uv run python -m scripts.train_mlp_heads
import random
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
    def __init__(self, input_dim=settings.DIM_TEXT):
        super(ScamPhishingMLP, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.BatchNorm1d(128),  # Vital for cross-dataset stability
            nn.ReLU(),
            nn.Dropout(0.4),  # Primary regularization
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.3),  # Secondary regularization
            nn.Linear(64, 2),  # [Prob_Spam, Prob_Ham]
            nn.Softmax(dim=1),  # Ensures probabilities sum to 1.0
        )

    def forward(self, x):
        return self.net(x)


class StratifiedDataset(Dataset):
    def __init__(
        self, haz_records, safe_records, attr_name, text_attr_name="clean_text"
    ):
        """
        Args:
            haz_records: List of 'Hazard' objects (Spam/Malicious)
            safe_records: List of 'Safe' objects (Ham/Clean)
            attr_name: The embedding attribute (e.g., 'text_embedding')
            text_attr_name: Attribute for length fallback (e.g., 'clean_text')
        """

        def get_bin(record):
            # Fallback Logic: Try database column first, then calculate on the fly
            c_len = getattr(record, "clean_length", None)
            if c_len is None:
                text_val = getattr(record, text_attr_name, "")
                c_len = len(text_val) if text_val else 0

            if c_len <= 500:
                return "short"  # Short-form
            if c_len <= 2000:
                return "medium"  # Medium-form
            return "long"  # Long-form/Windowed

        def bucketize(records, is_hazard: bool):
            buckets = {"short": [], "medium": [], "long": []}
            for r in records:
                # We store a tuple of (record, label) to avoid expensive lookups later
                label = [1.0, 0.0] if is_hazard else [0.0, 1.0]
                buckets[get_bin(r)].append((r, label))
            return buckets

        # 1. Bucketize with Class Tagging
        haz_buckets = bucketize(haz_records, is_hazard=True)
        safe_buckets = bucketize(safe_records, is_hazard=False)

        # 2. Balanced Sampling per Length Bin
        final_pairs = []
        for b in ["short", "medium", "long"]:
            h_list = haz_buckets[b]
            s_list = safe_buckets[b]

            min_count = min(len(h_list), len(s_list))

            if min_count > 0:
                random.shuffle(h_list)
                random.shuffle(s_list)
                final_pairs.extend(h_list[:min_count])
                final_pairs.extend(s_list[:min_count])
            print(f"  [Bucket: {b}] Balanced to {min_count * 2} samples.")

        # 3. Global Shuffle to mix bins and classes
        random.shuffle(final_pairs)

        # 4. Final Feature/Label Allocation
        self.features = []
        self.labels = []

        for record, label in final_pairs:
            emb = getattr(record, attr_name)
            if emb is not None:
                self.features.append(emb)
                self.labels.append(label)

        self.features = np.array(self.features, dtype=np.float32)
        self.labels = np.array(self.labels, dtype=np.float32)

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        return torch.from_numpy(self.features[idx]), torch.from_numpy(self.labels[idx])


async def train_and_export(
    mode="text",
    label_col="label",
    haz_val="spam",
    safe_val="ham",
    attr_name="text_embedding",
):
    print(f"\n--- [INITIATING] {mode.upper()} Training Sequence ---")
    if not Tortoise._inited:
        await Tortoise.init(config=TORTOISE_ORM)

    # 1. Dynamic Data Fetching
    # We use dictionary unpacking to pass the dynamic column name to the filter
    haz = await OpenDataSet.filter(
        **{f"{attr_name}__isnull": False, label_col: haz_val}
    ).all()
    safe = await OpenDataSet.filter(
        **{f"{attr_name}__isnull": False, label_col: safe_val}
    ).all()

    if not haz or not safe:
        print(
            f"CRITICAL: Insufficient data for {mode}. (Haz: {len(haz)}, Safe: {len(safe)})"
        )
        return

    # 2. Dataset Preparation (70/15/15 Sacred Split)
    full_dataset = StratifiedDataset(haz, safe, attr_name)
    total = len(full_dataset)
    train_size = int(0.70 * total)
    val_size = int(0.15 * total)
    test_size = total - train_size - val_size  # Remainder ensures no rounding loss

    train_set, val_set, test_set = random_split(
        full_dataset, [train_size, val_size, test_size]
    )

    train_loader = DataLoader(train_set, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=32)
    test_loader = DataLoader(test_set, batch_size=32)

    # 3. Model & Optimizer
    dim = settings.DIM_TEXT if mode == "text" else settings.DIM_URL
    model = ScamPhishingMLP(dim)
    optimizer = optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-2)
    criterion = nn.BCELoss()

    # 4. Training Loop
    for epoch in range(15):  # Increased epochs for complex URL patterns
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

        # Validation (In-training telemetry)
        model.eval()
        v_loss, v_correct = 0, 0
        with torch.no_grad():
            for feat, target in val_loader:
                out = model(feat)
                v_loss += criterion(out, target).item()
                v_correct += (out.argmax(1) == target.argmax(1)).sum().item()

        print(
            f"Epoch {epoch + 1:02d} | T_Loss: {t_loss / len(train_loader):.4f} | T_Acc: {t_correct / train_size:.3f} | V_Loss: {v_loss / len(val_loader):.4f} | V_Acc: {v_correct / val_size:.3f}"
        )

    # 5. THE SACRED TEST (Final Evaluation)
    print("\n--- [FINAL REPORT] PERFORMANCE ON UNSEEN TEST SET ---")
    model.eval()
    y_true, y_pred = [], []
    with torch.no_grad():
        for feat, target in test_loader:
            out = model(feat)
            y_true.extend(target.argmax(1).tolist())
            y_pred.extend(out.argmax(1).tolist())

    print("--- F1 Metrics Matrix ---")
    print(
        classification_report(
            y_true, y_pred, target_names=[str(haz_val), str(safe_val)]
        )
    )
    print("--- CONFUSION MATRIX ---")
    print(confusion_matrix(y_true, y_pred))

    # 6. ONNX Export
    export_dir = settings.TEXT_MODEL_PATH if mode == "text" else settings.URL_MODEL_PATH
    export_path = export_dir / "classifier.onnx"
    export_path.parent.mkdir(parents=True, exist_ok=True)

    dummy_input = torch.randn(1, dim).float()
    torch.onnx.export(
        model,
        dummy_input,
        str(export_path),
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
        opset_version=18,
    )
    print(f"SUCCESS: {mode.upper()} classifier locked at {export_path}")


# async def train_and_export(mode="text", haz_label="spam", safe_label="ham"):
#     if not Tortoise._inited:
#         await Tortoise.init(config=TORTOISE_ORM)

#     haz = await OpenDataSet.filter(text_embedding__isnull=False, label=haz_label).all()
#     safe = await OpenDataSet.filter(
#         text_embedding__isnull=False, label=safe_label
#     ).all()

#     full_dataset = StratifiedDataset(haz, safe)
#     train_size = int(0.8 * len(full_dataset))
#     val_set_size = len(full_dataset) - train_size
#     train_set, val_set = random_split(full_dataset, [train_size, val_set_size])

#     train_loader = DataLoader(train_set, batch_size=32, shuffle=True)
#     val_loader = DataLoader(val_set, batch_size=32)

#     dim = settings.DIM_TEXT if mode == "text" else settings.DIM_URL
#     model = ScamPhishingMLP(dim)
#     optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-2)
#     criterion = nn.BCELoss()

#     for epoch in range(10):
#         model.train()
#         t_loss, t_correct = 0, 0
#         for feat, target in train_loader:
#             optimizer.zero_grad()
#             out = model(feat)
#             loss = criterion(out, target)
#             loss.backward()
#             optimizer.step()
#             t_loss += loss.item()
#             t_correct += (out.argmax(1) == target.argmax(1)).sum().item()

#         # Validation
#         model.eval()
#         v_loss, v_correct = 0, 0
#         y_true, y_pred = [], []
#         with torch.no_grad():
#             for feat, target in val_loader:
#                 out = model(feat)
#                 v_loss += criterion(out, target).item()
#                 v_correct += (out.argmax(1) == target.argmax(1)).sum().item()
#                 y_true.extend(target.argmax(1).tolist())
#                 y_pred.extend(out.argmax(1).tolist())

#         print(
#             f"Epoch {epoch + 1} | T_Loss: {t_loss / len(train_loader):.4f} | T_Acc: {t_correct / train_size:.4f} | V_Loss: {v_loss / len(val_loader):.4f} | V_Acc: {v_correct / val_set_size:.4f}"
#         )

#     print("\n--- F1 METRICS MATRIX ---")
#     print(classification_report(y_true, y_pred, target_names=[haz_label, safe_label]))
#     print("--- CONFUSION MATRIX ---")
#     print(confusion_matrix(y_true, y_pred))

#     # Export
#     export_dir = settings.TEXT_MODEL_PATH if mode == "text" else settings.URL_MODEL_PATH
#     export_path = export_dir / "classifier.onnx"
#     dummy_input = torch.randn(1, dim).float()
#     torch.onnx.export(
#         model,
#         dummy_input,
#         str(export_path),
#         input_names=["input"],
#         output_names=["output"],
#         dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
#         opset_version=18,
#     )


# if __name__ == "__main__":
#     asyncio.run(train_and_export(mode="text", haz_label="spam", safe_label="ham"))


async def main():
    # RUN TEXT CLASSIFIER (MiniLM-L12)
    await train_and_export(
        mode="text",
        label_col="label",
        haz_val="spam",
        safe_val="ham",
        attr_name="text_embedding",
    )

    # RUN URL CLASSIFIER (URLBert-Tiny)
    # Ensure your 'ensure_architectural_integrity' has added the 'url_embedding' column!
    await train_and_export(
        mode="url",
        label_col="is_malicious",
        haz_val=True,
        safe_val=False,
        attr_name="url_embedding",
    )


if __name__ == "__main__":
    asyncio.run(main())
