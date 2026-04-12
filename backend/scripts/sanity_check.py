# Docker extension -> right click askvigil-backend, start new shell. then run:
# export PYTHONPATH=$PYTHONPATH:.
# uv run python -m scripts.sanity_check
import asyncio
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer
from scipy.spatial.distance import cosine
from pathlib import Path

# --- GLOBAL CONFIG ---
BASE_MODEL_DIR = Path("data_persistence/ai_models").resolve()
TEXT_MODEL_PATH = BASE_MODEL_DIR / "text_onnx"

def mean_pooling(last_hidden_state, attention_mask):
    input_mask_expanded = np.expand_dims(attention_mask, -1).astype(float)
    return np.sum(last_hidden_state * input_mask_expanded, 1) / np.clip(input_mask_expanded.sum(1), a_min=1e-9, a_max=None)

class ONNXTestHandler:
    def __init__(self):
        # Load Quantized Model
        model_file = TEXT_MODEL_PATH / "model_quantized.onnx"
        print(f"Booting ONNX Session: {model_file}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(TEXT_MODEL_PATH), 
            local_files_only=True,
            fix_mistral_regex=True 
        )
        self.session = ort.InferenceSession(
            str(model_file), 
            providers=['CPUExecutionProvider']
        )

    async def get_embedding(self, text: str):
        # 1. Tokenize (NumPy format for ORT)
        encoded = self.tokenizer(
            text, 
            padding=True, 
            truncation=True, 
            max_length=512, 
            return_tensors='np'
        )
        
        # 2. Run Inference
        inputs = {k: v for k, v in encoded.items()}
        outputs = self.session.run(None, inputs)
        
        # outputs[0] is 'last_hidden_state'
        # Perform Mean Pooling (for MiniLM)
        # We wrap in to_thread to keep the event loop responsive
        return await asyncio.to_thread(mean_pooling, outputs[0], encoded['attention_mask'])

async def main():
    tester = ONNXTestHandler()
    
    test_cases = [
        ("Please update your bank details here.", "Eh boss, your account got problem, click here update."),
        ("Give me your password.", "I am going to eat chicken rice."),
        ("You won a prize!", "Tahniah! Anda menang hadiah RM10,000!")
    ]

    print("\n--- ONNX INT8 Sanity Check ---")
    for s1, s2 in test_cases:
        v1 = (await tester.get_embedding(s1)).flatten()
        v2 = (await tester.get_embedding(s2)).flatten()
        
        score = 1 - cosine(v1, v2)
        print(f"S1: {s1}\nS2: {s2}\nSimilarity: {score:.4f}\n")

if __name__ == "__main__":
    asyncio.run(main())