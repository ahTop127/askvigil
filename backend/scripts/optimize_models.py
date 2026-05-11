# # Docker extension -> right click askvigil-backend, start new shell. then run:
# # export PYTHONPATH=$PYTHONPATH:.
# # uv run python -m scripts.optimize_models
# docker exec -it -e PYTHONPATH="/app" askvigil-backend-1 python /app/scripts/optimize_models.py
from pathlib import Path
from transformers import AutoTokenizer
from optimum.exporters.onnx import main_export
from optimum.onnxruntime import ORTQuantizer
from optimum.onnxruntime.configuration import AutoQuantizationConfig

# --- GLOBAL CONFIG ---
BASE_MODEL_DIR = Path("data_persistence/ai_models")

MODELS = {
    "text": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "url": "CrabInHoney/urlbert-tiny-v5",
}


def export_and_quantize(task_name: str, model_id: str):
    output_dir = BASE_MODEL_DIR / f"{task_name}_onnx"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Export to ONNX (Cleaned for high-throughput)
    print(f"[{task_name}] Exporting {model_id}...")
    main_export(
        model_name_or_path=model_id,
        output=output_dir,
        task="feature-extraction",
        # Feature-extraction natively outputs 'last_hidden_state', 
        # which is all we need for XAI.
        no_post_process=True,
    )

    # 2. Save tokenizer (Enforcing FastTokenizer for XAI Offsets)
    print(f"[{task_name}] Saving Tokenizer files...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_id,
        use_fast=True,           # For offset_mapping during inference
        fix_mistral_regex=True,  # Silences regex warning
    )
    tokenizer.save_pretrained(output_dir)

    # 3. Quantize to INT8
    print(f"[{task_name}] Quantizing...")
    # Explicitly target "model.onnx" so it ignores any old quantized files
    quantizer = ORTQuantizer.from_pretrained(output_dir, file_name="model.onnx")
    dq_config = AutoQuantizationConfig.arm64(is_static=False)  # Optimized for Ampere A1

    quantizer.quantize(
        save_dir=output_dir,
        quantization_config=dq_config,
    )
    print(f"[{task_name}] Success. Files in {output_dir}")


if __name__ == "__main__":
    for task, mid in MODELS.items():
        export_and_quantize(task, mid)
