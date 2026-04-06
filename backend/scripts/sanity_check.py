# Docker extension -> right click askvigil-backend, start new shell. then run:
# export PYTHONPATH=$PYTHONPATH:.
# uv run python -m scripts.sanity_check
import asyncio
from app.services.nlp_service import scan_text
from app.core.lifespan import MODEL_REGISTRY
from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine

# 1. MANUAL BOOT: Populate the registry for the test environment
# In production, FastAPI's lifespan handles this.
def boot_models():
    if "text_minilm" not in MODEL_REGISTRY:
        print("Pre-loading MiniLM for test...")
        MODEL_REGISTRY["text_minilm"] = {
            "model": SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        }

async def test_similarity(sent1, sent2):
    # Ensure scan_text returns the full vector for internal logic!
    res1 = await scan_text(sent1)
    res2 = await scan_text(sent2)
    
    # Extract the full embeddings from the response
    v1 = res1["embedding"] 
    v2 = res2["embedding"]
    
    return 1 - cosine(v1, v2)

async def main():
    boot_models()
    
    test_cases = [
        ("Please update your bank details here.", "Eh boss, your account got problem, click here update."),
        ("Give me your password.", "I am going to eat chicken rice."),
        ("You won a prize!", "Tahniah! Anda menang hadiah RM10,000!")
    ]

    print("--- NLP Sanity Check (Manglish/Multilingual) ---")
    for s1, s2 in test_cases:
        score = await test_similarity(s1, s2)
        print(f"S1: {s1}\nS2: {s2}\nSimilarity: {score:.4f}\n")

if __name__ == "__main__":
    # The quickest way to run async in a script
    asyncio.run(main())