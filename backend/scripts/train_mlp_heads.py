# # Docker extension -> right click askvigil-backend, start new shell. then run:
# # export PYTHONPATH=$PYTHONPATH:.
# # uv run python -m scripts.train_mlp_heads

# docker cp ./scripts/train_mlp_heads.py askvigil-backend-1:/app/scripts/train_mlp_heads.py
# docker exec -it askvigil-db-1 psql -U admin -d askvigil -c "SELECT original_text, clean_text FROM open_dataset WHERE clean_text LIKE '%escapenumber%' LIMIT 5;"
# docker exec -it -e PYTHONPATH="/app" askvigil-backend-1 python /app/scripts/train_mlp_heads.py
import random
import asyncio
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, random_split
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
from tortoise import Tortoise
import torch.onnx
from app.core.config import settings

from app.core.database import TORTOISE_ORM
from app.models.open_data import OpenDataSet, PhishingURL


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
        self,
        haz_records,
        safe_records,
        attr_name,
        text_attr_name="clean_text",
        short_max=500,
        med_max=2000,
    ):
        """
        Args:
            haz_records: List of 'Hazard' objects (Spam/Malicious)
            safe_records: List of 'Safe' objects (Ham/Clean)
            attr_name: The embedding attribute (e.g., 'text_embedding')
            text_attr_name: Attribute for length fallback (e.g., 'clean_text')
        """

        def get_bin(record):
            # # --- ONE-TIME INSPECTION BLOCK ---
            # if not hasattr(get_bin, "inspected"):
            #     print("\n" + "="*50)
            #     print("🔍 DEEP INSPECTION: FIRST RECORD DETECTED")
            #     print(f"Model Class: {record.__class__.__name__}")

            #     # List all attributes currently loaded in memory
            #     attrs = {k: type(v).__name__ for k, v in record.__dict__.items() if not k.startswith('_')}
            #     print(f"Available Fields & Types: {attrs}")

            #     # Check specific targets
            #     target_field = text_attr_name # passed from __init__
            #     val = getattr(record, target_field, "MISSING")
            #     print(f"Target Field Name: '{target_field}'")
            #     print(f"Target Value: {repr(val)}") # repr shows if it's None vs ""

            #     if val != "MISSING" and val is not None:
            #         print(f"Calculated Length: {len(str(val))}")

            #     print("="*50 + "\n")
            #     get_bin.inspected = True
            # # --- END INSPECTION BLOCK ---

            # 1. Try to get the pre-calculated length column
            c_len = getattr(record, "clean_length", None)

            # 2. If column is None (or doesn't exist), manually calculate
            if c_len is None or c_len == 0:
                # Get the text field (original_url or clean_text)
                raw_val = getattr(record, text_attr_name, None)

                if raw_val:
                    c_len = len(str(raw_val))
                else:
                    c_len = 0
                    # THIS will tell us if the field name itself is the problem
                    print(
                        f"CRITICAL: Field '{text_attr_name}' returned None for ID {record.id}"
                    )

            # 3. Categorize
            if c_len <= short_max:
                return "short"
            if c_len <= med_max:
                return "medium"
            return "long"

        def bucketize(records, is_hazard: bool):
            buckets = {"short": [], "medium": [], "long": []}
            for r in records:
                # We store a tuple of (record, label) to avoid expensive lookups later
                label = [0.0, 1.0] if is_hazard else [1.0, 0.0]
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
                # Convert the list to a numpy array on the fly here
                # np.array() or np.float32() handles Python lists perfectly
                self.features.append(np.array(emb, dtype=np.float32))
                self.labels.append(label)

        # Use np.stack for better performance with lists of arrays
        self.features = np.stack(self.features)
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

    # 1. Dynamic Model Selection
    # Select the table based on the training mode
    ModelClass = OpenDataSet if mode == "text" else PhishingURL

    # Define text attribute for length fallback in StratifiedDataset
    # Define thresholds based on mode
    if mode == "text":
        s_max, m_max = 200, 1000
        text_attr = "clean_text"
    else:  # URL mode
        s_max, m_max = 50, 150
        text_attr = "original_url"

    # 2. Dynamic Data Fetching
    # Use the selected ModelClass instead of hardcoded OpenDataSet
    haz = await ModelClass.filter(
        **{f"{attr_name}__isnull": False, label_col: haz_val}
    ).all()

    safe = await ModelClass.filter(
        **{f"{attr_name}__isnull": False, label_col: safe_val}
    ).all()

    if not haz or not safe:
        print(
            f"CRITICAL: Insufficient data for {mode}. (Haz: {len(haz)}, Safe: {len(safe)})"
        )
        return

    # 3. Dataset Preparation
    # Pass the text_attr so the length-bucketing knows which column to measure
    full_dataset = StratifiedDataset(
        haz, safe, attr_name, text_attr_name=text_attr, short_max=s_max, med_max=m_max
    )
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
    best_v_loss = float("inf")
    best_model_state = None

    for epoch in range(50):  # Increased epochs for complex URL patterns
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

        avg_v_loss = v_loss / len(val_loader)

        print(
            f"Epoch {epoch + 1:02d} | T_Loss: {t_loss / len(train_loader):.4f} | T_Acc: {t_correct / train_size:.3f} | V_Loss: {v_loss / len(val_loader):.4f} | V_Acc: {v_correct / val_size:.3f}"
        )
        # --- Track Best Model ---
        if avg_v_loss < best_v_loss:
            best_v_loss = avg_v_loss
            # deepcopy or state_dict to save the weights in memory
            best_model_state = {
                k: v.cpu().clone() for k, v in model.state_dict().items()
            }
            print(f"New best model found at Epoch {epoch + 1}")

        # --- Early Stopping ---
        patience = 7
        trigger_times = 0
        if avg_v_loss >= best_v_loss:
            trigger_times += 1
            if trigger_times >= patience:
                print(f"Early stopping: No improvements for {patience} epochs")
                break
        else:
            trigger_times = 0

    # --- Load Best Weights before Export ---
    if best_model_state:
        model.load_state_dict(best_model_state)
        print("Restored best weights for export.")

    # 5. Evaluation Test
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
