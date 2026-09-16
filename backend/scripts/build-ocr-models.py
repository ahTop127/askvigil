import shutil
from pathlib import Path

import onnx
import onnxruntime as ort
import requests
from onnx.version_converter import convert_version
from onnxruntime.quantization import QuantType, quantize_dynamic
from onnxruntime.quantization.preprocess import quant_pre_process

# --- CONFIGURATION ---
BASE = Path("data_persistence/ai_models/ocr_onnx")
TEMP = Path("data_persistence/ai_models/temp")
TARGET_OPSET = 12

# The "True North" for PP-OCRv5 Global
DICT_URL = "https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/main/ppocr/utils/dict/ppocrv5_dict.txt"

MODEL_URLS = {
    "det_light": "https://huggingface.co/breezedeus/cnstd-ppocr-ch_PP-OCRv5_det/resolve/main/ch_PP-OCRv5_det_infer.onnx",
    "rec_light": "https://huggingface.co/breezedeus/cnocr-ppocr-ch_PP-OCRv5/resolve/main/ch_PP-OCRv5_rec_infer.onnx",
    "det_server": "https://huggingface.co/breezedeus/cnstd-ppocr-ch_PP-OCRv5_det_server/resolve/main/ch_PP-OCRv5_det_server_infer.onnx",
    "rec_server": "https://huggingface.co/breezedeus/cnocr-ppocr-ch_PP-OCRv5_server/resolve/main/ch_PP-OCRv5_server_rec_infer.onnx",
    # "rec_server": "https://huggingface.co/PaddlePaddle/ch_RepSVTR_rec/resolve/main/ch_RepSVTR_rec_infer.onnx" # RepSVTR could be a good mid-weight, but doesn't have onnx directly
}

model_configs = [
    ("det_light", "v5_det_light"),
    ("rec_light", "v5_rec_light"),
    ("det_server", "v5_det_server"),
    ("rec_server", "v5_rec_server"),
]

# --- CORE UTILITIES ---


def download_file(url, target_path):
    print(f"[*] Downloading: {target_path.name}...")
    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(target_path, "wb") as f:
                f.writelines(r.iter_content(chunk_size=16384))
        return True
    except Exception as e:
        print(f"[!] Download Failed: {e}")
        return False


def upgrade_opset_robust(model_path, target_version):
    model = onnx.load(str(model_path))
    current_opset = model.opset_import[0].version if model.opset_import else 11
    if current_opset < target_version:
        print(f"[*] Upgrading Opset {current_opset} -> {target_version}...")
        try:
            converted_model = convert_version(model, target_version)
            onnx.save(converted_model, str(model_path))
        except Exception as e:
            print(f"[!] Upgrade failed, using original Opset: {e}")


def verify_model(model_path):
    try:
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 1
        ort.InferenceSession(
            str(model_path), sess_options=opts, providers=["CPUExecutionProvider"]
        )
        print(f"[√] Verification Passed: {model_path.name}")
        return True
    except Exception as e:
        print(f"[X] CRITICAL: Verification Failed: {e}")
        return False


def build_pipeline(key, out_name, mode="V0"):
    fp32_raw = TEMP / f"{out_name}_raw.onnx"
    proc_path = TEMP / f"{out_name}_proc.onnx"
    final_int8 = BASE / f"{out_name}_int8.onnx"
    final_fp32 = BASE / f"{out_name}_fp32.onnx"

    if not download_file(MODEL_URLS[key], fp32_raw):
        return

    upgrade_opset_robust(fp32_raw, TARGET_OPSET)

    # -----------------------------
    # V0: PURE FP32 BASELINE
    # -----------------------------
    if mode == "V0":
        shutil.copy(fp32_raw, final_fp32)
        print("[V0] FP32 baseline built")
        return final_fp32

    # -----------------------------
    # V1: FP32 + preprocess only
    # -----------------------------
    if mode == "V1":
        print("[V1] Preprocess only")
        try:
            quant_pre_process(str(fp32_raw), str(proc_path), skip_optimization=False)
            shutil.copy(proc_path, final_fp32)
        except:
            shutil.copy(fp32_raw, final_fp32)
        return final_fp32

    # -----------------------------
    # V2: INT8 + preprocess
    # -----------------------------
    if mode == "V2":
        print("[V2] INT8 + preprocess (CURRENT)")
        try:
            quant_pre_process(str(fp32_raw), str(proc_path), skip_optimization=False)
        except:
            proc_path = fp32_raw

        quantize_dynamic(
            str(proc_path),
            str(final_int8),
            weight_type=QuantType.QInt8,
            per_channel=True,
        )

        verify_model(final_int8)

        if fp32_raw.exists():
            fp32_raw.unlink()
        if proc_path.exists() and proc_path != fp32_raw:
            proc_path.unlink()

        return final_int8

    # -----------------------------
    # V3: INT8 ONLY (NO PREPROCESS)
    # -----------------------------
    if mode == "V3":
        print("[V3] INT8 only (no preprocess)")
        quantize_dynamic(
            str(fp32_raw),
            str(final_int8),
            weight_type=QuantType.QInt8,
            per_channel=False,  # IMPORTANT for stability test
        )

        verify_model(final_int8)
        return final_int8


# --- MAIN EXECUTION ---
def main():
    mode = "V0"  # V0-V3. Surprisingly, V0 is the fastest!
    print("=== STARTING AUTONOMOUS OCR BUILD PIPELINE ===")
    BASE.mkdir(parents=True, exist_ok=True)
    TEMP.mkdir(parents=True, exist_ok=True)
    dict_destination = BASE / "ppocr_keys.txt"

    # --- Phase 1: Model Download (Raw Files) ---
    print("\n--- Phase 1: Downloading Raw Models ---")
    raw_paths = {}
    for key, out_name in model_configs:
        path = TEMP / f"{out_name}_raw.onnx"
        if download_file(MODEL_URLS[key], path):
            raw_paths[key] = path

    if "rec_server" not in raw_paths:
        print("[X] FATAL: Could not download reference recognition model.")
        return

    # --- Phase 2: Dictionary Sync ---
    print("\n--- Phase 2: Dictionary Synchronization ---")
    response = requests.get(DICT_URL, timeout=10)
    response.raise_for_status()

    content = response.text.rstrip("\n")

    with open(dict_destination, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

    # --- Phase 3: Quantization ---
    print("\n--- Phase 3: Model Quantization ---")
    final_models = []
    print(f"\n================ RUNNING {mode} ================\n")
    for key, out_name in model_configs:
        # Assuming build_pipeline handles the download/quant logic
        # and returns the path to the final _int8.onnx file
        final_path = build_pipeline(key, out_name, mode=mode)
        if "rec" in key:  # Only recognition models have a character dictionary
            final_models.append(final_path)
    print("Done")


if __name__ == "__main__":
    main()
