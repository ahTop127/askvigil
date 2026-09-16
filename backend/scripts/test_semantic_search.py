import asyncio
from pathlib import Path

import numpy as np
import onnxruntime as ort
from scipy.spatial.distance import cosine
from transformers import AutoTokenizer

# --- CONFIG ---
TEXT_MODEL_PATH = Path("data_persistence/ai_models/text_onnx").resolve()
K_CONSTANT = 60
MAX_POSSIBLE_RRF = (1 / (K_CONSTANT + 1)) + (1 / (K_CONSTANT + 1))

# --- SIMULATED DATASET ---
MOCK_DATA = [
    {
        "id": 1,
        "text": "Please update your Maybank account details immediately.",
        "cat": "Phishing",
    },
    {
        "id": 2,
        "text": "Tahniah! Anda menang hadiah RM10,000 dari Shopee.",
        "cat": "Financial Scam",
    },
    {
        "id": 3,
        "text": "Eh boss, your CIMB account got problem, click here update.",
        "cat": "Phishing (Manglish)",
    },
    {
        "id": 4,
        "text": "I am going to eat chicken rice with my family.",
        "cat": "Safe/Ham",
    },
    {
        "id": 5,
        "text": "Job recruitment: Earn RM500 per day working from home.",
        "cat": "Job Scam",
    },
]


def mean_pooling(last_hidden_state, attention_mask):
    input_mask_expanded = np.expand_dims(attention_mask, -1).astype(float)
    return np.sum(last_hidden_state * input_mask_expanded, 1) / np.clip(
        input_mask_expanded.sum(1), a_min=1e-9, a_max=None
    )


class HybridTester:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(TEXT_MODEL_PATH), local_files_only=True
        )
        self.session = ort.InferenceSession(
            str(TEXT_MODEL_PATH / "model_quantized.onnx"),
            providers=["CPUExecutionProvider"],
        )

        # Pre-cache embeddings for mock data
        print("Pre-vectorizing mock dataset...")
        for item in MOCK_DATA:
            item["vector"] = self._get_vec(item["text"])

    def _get_vec(self, text):
        encoded = self.tokenizer(
            text, padding=True, truncation=True, max_length=512, return_tensors="np"
        )
        outputs = self.session.run(None, dict(encoded))
        return mean_pooling(outputs[0], encoded["attention_mask"]).flatten()

    def get_lexical_score(self, query, doc_text):
        """Simulates BM25 using Jaccard Similarity (Keyword Overlap)."""
        q_words = set(query.lower().split())
        d_words = set(doc_text.lower().split())
        intersection = q_words.intersection(d_words)
        return len(intersection) / len(q_words.union(d_words)) if q_words else 0

    async def run_hybrid_search(self, query):
        query_vec = self._get_vec(query)

        # 1. Semantic Ranking (HNSW Simulation)
        semantic_results = []
        for item in MOCK_DATA:
            sim = 1 - cosine(query_vec, item["vector"])
            semantic_results.append((item["id"], sim))
        semantic_results.sort(key=lambda x: x[1], reverse=True)
        sem_ranks = {id_: rank + 1 for rank, (id_, _) in enumerate(semantic_results)}

        # 2. Lexical Ranking (BM25 Simulation)
        lexical_results = []
        for item in MOCK_DATA:
            score = self.get_lexical_score(query, item["text"])
            lexical_results.append((item["id"], score))
        lexical_results.sort(key=lambda x: x[1], reverse=True)
        lex_ranks = {id_: rank + 1 for rank, (id_, _) in enumerate(lexical_results)}

        # 3. Reciprocal Rank Fusion
        combined = []
        for item in MOCK_DATA:
            id_ = item["id"]
            # 1 / (k + rank)
            score = (1 / (K_CONSTANT + sem_ranks[id_])) + (
                1 / (K_CONSTANT + lex_ranks[id_])
            )

            # Normalization to 1.0 (Percentage)
            normalized_score = (score / MAX_POSSIBLE_RRF) * 100

            combined.append(
                {
                    "text": item["text"],
                    "score": f"{normalized_score:.2f}%",
                    "raw_rrf": score,
                }
            )

        return sorted(combined, key=lambda x: x["raw_rrf"], reverse=True)


async def main():
    tester = HybridTester()
    query = "Eh boss, CIMB bank update account click here"

    print(f"\nQUERY: {query}")
    results = await tester.run_hybrid_search(query)

    for r in results:
        print(f"[{r['score']}] {r['text']}")


if __name__ == "__main__":
    asyncio.run(main())
