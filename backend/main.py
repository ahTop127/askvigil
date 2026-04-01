from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text
from scipy.spatial.distance import cosine
import os
from dotenv import load_dotenv

load_dotenv()

# Get the individual pieces from your existing .env
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "pass")
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "dbname")

# Stitch them into a standard PostgreSQL URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
# New path for the multilingual model
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
MODEL_PATH = os.getenv("MODEL_PATH", f"/app/models/{MODEL_NAME}")

def load_model():
    if os.path.isdir(MODEL_PATH) and os.listdir(MODEL_PATH):
        # Load from the local folder (Fast!)
        print(f"Loading {MODEL_NAME} from local storage...")
        model = SentenceTransformer(MODEL_PATH)
    else:
        # First time: Download and save to the volume
        print(f"Downloading {MODEL_NAME} (this may take a few minutes)...")
        model = SentenceTransformer(MODEL_NAME)
        model.save(MODEL_PATH)
        print(f"Model saved to {MODEL_PATH}")
    return model

# To use it:
# model = load_model()
# embeddings = model.encode(["Eh boss, tapau satu!", "I am hungry"])

app = FastAPI()
model = load_model() # Using the MiniLM loader we wrote earlier
engine = create_engine(DATABASE_URL)

def save_to_db(content_list: list, category: str):
    """
    Takes a list of strings, vectorizes them, and saves to DB.
    Skips any strings that are already in the database.
    """
    # 1. Vectorize everything in one batch (Fastest)
    vectors = model.encode(content_list)
    
    with engine.connect() as conn:
        for content, vec in zip(content_list, vectors):
            # 2. Use 'ON CONFLICT DO NOTHING' to skip duplicates
            query = text("""
                INSERT INTO embeddings (content, vector_data, category)
                VALUES (:content, :vector, :category)
                ON CONFLICT (content) DO NOTHING;
            """)
            conn.execute(query, {
                "content": content, 
                "vector": vec.tolist(), 
                "category": category
            })
        conn.commit()

class TextQuery(BaseModel):
    text: str

class SimilarityQuery(BaseModel):
    text1: str
    text2: str

# Add this block immediately after creating the 'app'
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sleepunderflow.duckdns.org", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    # This proves the backend is alive
    return {"status": "running", "environment": "production"}

@app.get("/api/db-test")
def test_db():
    # In Docker, 'db' is the hostname, not an IP!
    db_url = os.getenv("DATABASE_URL")
    return {"message": f"Connecting to {db_url}"}

@app.post("/api/vectorize")
async def get_vector(query: TextQuery):
    """Returns the raw 384-dimensional vector for a sentence."""
    vector = model.encode(query.text)
    return {
        "text": query.text,
        "vector_sample": vector[:5].tolist(), # Just the first 5 numbers for brevity
        "dimensions": len(vector)
    }

@app.post("/api/compare")
async def compare_sentences(query: SimilarityQuery):
    """Calculates Cosine Similarity between two sentences."""
    # 1. Convert text to vectors
    v1 = model.encode(query.text1)
    v2 = model.encode(query.text2)
    
    # 2. Calculate Cosine Similarity 
    # (1 - distance = similarity)
    similarity = 1 - cosine(v1, v2)
    
    return {
        "text1": query.text1,
        "text2": query.text2,
        "similarity_score": round(float(similarity), 4),
        "verdict": "Very Similar" if similarity > 0.8 else "Related" if similarity > 0.5 else "Unrelated"
    }

@app.get("/api/search")
async def search_similar(query: str, category: str = None, limit: int = 5):
    """
    Finds the most similar entries in the DB.
    Optionally filters by category (subset).
    """
    # Vectorize the user's query
    query_vector = model.encode(query).tolist()
    
    # Build the SQL query
    sql = """
        SELECT content, category, (1 - (vector_data <=> :vec)) as similarity
        FROM embeddings
    """
    
    # Apply subset filtering if a category is provided
    if category:
        sql += " WHERE category = :cat"
    
    sql += " ORDER BY vector_data <=> :vec LIMIT :limit"
    
    with engine.connect() as conn:
        results = conn.execute(text(sql), {
            "vec": query_vector, 
            "cat": category, 
            "limit": limit
        })
        return [dict(row) for row in results]