from contextlib import asynccontextmanager
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel

# Global Registry
MODEL_REGISTRY = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Should we quantize our models to int8 for 4x faster performance but slightly worse performance?
    # Preload Text Model
    print("Loading MiniLM...")
    text_model = "paraphrase-multilingual-MiniLM-L12-v2"
    MODEL_REGISTRY["text_minilm"] = {
        "model": SentenceTransformer(text_model),
        "type": "nlp",
    }

    # Preload URL Model
    print("Loading URLBERT...")
    url_model = "CrabInHoney/urlbert-tiny-v5"
    MODEL_REGISTRY["url_bert"] = {
        "tokenizer": AutoTokenizer.from_pretrained(url_model),
        "model": AutoModel.from_pretrained(url_model).eval(),
        "type": "url",
    }

    yield
    # Shutdown logic
    MODEL_REGISTRY.clear()
    print("Models unloaded.")
