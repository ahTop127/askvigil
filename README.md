# AskVigil - a Scam Detector website app.

Welcome to AskVigil by SleepUnderflow. We are using a containerized Python stack. This means if it runs on your laptop in Docker, it **will** work on the Oracle server. You must have docker desktop running to run the code. Run `docker compose up --build` to update the running code.

General Syntax for inserting data into cloud storage:  
Just use scripts/upload_assets.py and edit it to the folders you want to upload. Or:
`curl.exe -X PUT --data-binary "@local_file_name" "PAR_URL/remote_file_name"`
PAR_URL goes into the .env file, it is not to be shared publicly.

---
## 🛠 The Tech Stack: Multimodal AI Architecture

### Base website
* **Frontend: React** — Flexible and industry-standard for building the analyst dashboard.
* **Backend: FastAPI** — High-performance Python. Fast to develop with native async support for our concurrent ML and Database pipelines.
* **Proxy: Nginx Proxy Manager** — GUI-based reverse proxy for DuckDNS and automated SSL certificate management.

### 🛡 Core AI Engines
* **URL Intelligence: urlbert-tiny-v5** — A domain-specific transformer model used exclusively for URL analysis. It captures structural nuances (TLDs, subdomains, path entropy) better than generic language models.
* **Text Intelligence: Paraphrase-multilingual-MiniLM-L12-v2** — Specifically chosen for text semantic mapping. Optimized for high-throughput multilingual intent detection.
* **Predictive Head: XGBoost** — The "Generalization Engine." Trained on 120k+ samples to recognize zero-day signatures across URLs and Text.

### 👁 Multimodal Inputs (Computer Vision)
* **High-Speed OCR: RapidOCR (PP-OCRv5)** — Optimized for 2-5x faster inference via a custom **Adaptive Image Router**. 
    * *Adaptive Routing:* Automatically switches between "Light" (mobile-grade) and "Server" (high-accuracy) models based on image complexity analysis (blur, contrast, entropy).
    * *Inference Optimization:* Implements width-bucket batching to minimize padding waste during ONNX execution.
* **QR Logic: OpenCV (cv2.QRCodeDetector)** — Lightweight, low-latency detection that extracts and routes embedded URLs back into the primary scanning pipeline.

### 🏗 Infrastructure & Production Hardening
* **Database: PostgreSQL (pgvector + pg_trgm)** — Dual-method historical memory.
    * *Semantic:* `pgvector` HNSW indexing for text intent.
    * *Lexical:* Trigram-based `pg_trgm` structural search for URL patterns.
* **ARM64 Optimization (Oracle A1):** 
    * Every model is quantized and mapped via ONNX Runtime with hardcoded `intra_op_num_threads` to prevent Linux CFS context-switching lag.
    * Custom `shm_size` allocation in Docker to support parallel HNSW indexing and IPC tensor sharing for RapidOCR.
    * Implemented a **"Triple-Fire" Engine Warmup** script that saturates the CPU L2/L3 caches on startup, entirely eliminating 5-second cold-start penalties for sub-millisecond real-time inference.

---

## 🧠 How It Works: The Dynamic Fusion Architecture

Unlike standard static whitelists or single-model classifiers, this system uses a **Retrieval-Augmented Classification (RAC)** pipeline. It routes inputs through three parallel "brains" and dynamically weights their votes based on mathematical confidence.

1. **The Predictive Brain (XGBoost):** Evaluates the overarching pattern, entropy, and structure of the input to catch novel, zero-day scams that have never been seen before.
2. **The Historical Brain (PostgreSQL Retrieval):** Scans our database of known threats. It uses Semantic Search (Intent) for text, and Lexical Trigrams (Structural Overlap) for URLs.
3. **The Heuristic Brain (Rules Engine):** A hardcoded asymmetric regex defense for immediate, known-bad signatures.

**The Dynamic Fusion Engine:** 
The system does not simply average these scores. It uses a **Dimensional Normalization Engine (Weighted Geometric Mean)** to calculate *Effective Confidence*. If the Database pulls a result that has high consensus but poor structural grounding (a hallucination), the math automatically applies a severe penalty, silencing the database and seamlessly offloading the decision to the XGBoost model.

---

## 🔍 Transparent Explainability (XAI)

Most ML security tools act as "black boxes." Our pipeline features a zero-latency, token-level Explainable AI layer that mathematically dissects the risk score and maps it directly to the UI using three distinct layers of proof:

1. **The Model's Intuition (Predictive Deltas):** We execute a highly vectorized Leave-One-Out (LOO) matrix ablation against the XGBoost head to prove exactly which tokens triggered the model's internal threat detection. (For URLs, we natively extract C++ SHAP values for structural heuristics).
2. **The Vibe Check (Semantic Similarity):** We mathematically break the Transformer "Anisotropy Cone" using dynamic mean-centering. We then calculate dot-products between unpooled query tokens and the database embeddings to highlight words that conceptually match historical threats.
3. **The Hard Evidence (Lexical Overlap):** We use memory-efficient set intersections to highlight exact structural overlaps (like typosquatted domains) that directly mirror known historical attacks.

### Architecture Diagram

```mermaid
graph TD
    %% Styling
    classDef multimodal fill:#f1c40f,stroke:#f39c12,stroke-width:2px,color:#000
    classDef router fill:#0984e3,stroke:#74b9ff,stroke-width:2px,color:#fff
    classDef model fill:#6c5ce7,stroke:#a29bfe,stroke-width:2px,color:#fff
    classDef logic fill:#00b894,stroke:#55efc4,stroke-width:2px,color:#fff
    classDef fusion fill:#d63031,stroke:#ff7675,stroke-width:2px,color:#fff
    classDef xai fill:#e84393,stroke:#fd79a8,stroke-width:2px,color:#fff

    %% Input Layer
    INPUT[User Input: Text, URL, or Image]:::multimodal --> ROUTE{Input Router}:::router

    %% Multimodal Pre-processing
    ROUTE -->|Image| QR[cv2 QR Scanner]:::multimodal
    ROUTE -->|Image| OCR[Adaptive RapidOCR Engine]:::multimodal
    OCR -->|Extracted Text/URL| ROUTE
    QR -->|Embedded URL| ROUTE

    %% Specialized Pipelines
    ROUTE -->|URL| U_PIPE[URL Pipeline]:::logic
    ROUTE -->|Text| T_PIPE[Text Pipeline]:::logic

    %% Model Splits
    U_PIPE -->|Structural Metadata| XGB_U[XGBoost Classifier]:::model
    U_PIPE -->|URLBERT Embeddings| DB_U[(PG Lexical Search)]
    
    T_PIPE -->|Regex Rules| REGEX[Heuristic Engine]
    T_PIPE -->|MiniLM Embeddings| DB_T[(PG Semantic Search)]
    T_PIPE -->|Text Content| XGB_T[XGBoost Classifier]:::model

    %% Fusion Engine
    XGB_U & DB_U --> FUSE_U{Dynamic Fusion}:::fusion
    XGB_T & DB_T & REGEX --> FUSE_T{Dynamic Fusion}:::fusion

    %% Explainable AI (XAI) Extraction
    FUSE_U -->|SHAP Feature Contributions + LOO Matrix Ablation| XAI_LAYER{XAI Translation Layer}:::xai
    FUSE_T -->|LOO Matrix Ablation| XAI_LAYER
    XAI_LAYER -->|Mean-Centered Array| OUTPUT[Final Risk Score & UI JSON]
```

## 🚀 Getting Started (Local Development)

### 1. Prerequisites
* Install **Docker Desktop** and **VS Code**. No GPU needed - CPU only, since our server doesn't have GPU anyway.

### 2. Setup
1.  Clone the repo.
2.  Create a `.env` file in the root directory (see the lead for the template).
3.  Fire up the stack:
    ```bash
    docker compose up --build
    ```
    _Note: The first run will take a while to download the AI models and initialize the database, and much longer to regenerate the database vector embeddings_
4.  The Workflow
    * **Editing Code:** Run docker compose up --build to update the code.
    * **Database:** The database schema is built to be self-healing. Just start the containers and start querying. Database embeddings generation, however, will take a long time if you haven't generated them before.

5.  Production (Oracle Cloud)
    * **Deployment:** Simply git push origin main.
    * **CI/CD:** GitHub Actions will automatically build and deploy to the Oracle server.
    * **Secrets:** Production secrets are managed on the server's .env. Do not push your local .env to Git.

6.  **Verification:**
    * **Local Frontend:** [http://localhost](http://localhost)
    * **Local API Docs:** [http://localhost/docs](http://localhost/docs) (FastAPI generates this automatically!)
    * **Production:** [https://askvigil.duckdns.org]
    * **Docs:** Go to [https://askvigil.duckdns.org] and append /api, /docs, /redoc, or /openapi.json for for whichever ones you want.

---

## ☁️ Deployment (CI/CD)

We are using **GitHub Actions** for "Hands-Off" deployment. 
* **The Flow:** Push your code to the `main` branch → GitHub SSHes into Oracle → Docker rebuilds only what changed.
* **Note:** If you need a new Python library, add it to `backend/pyproject.toml` with `uv add [library]`.

---

## ⚠️ Ground Rules
1. **Never** commit the `.env` file to Git (it’s in the `.gitignore`).
2. **Never** commit large AI model files or datasets. These go into Oracle Object Storage.
3. **Always** test your `docker compose up --build` locally before pushing to `main`.

## Developer Debugging Checklist:
Environment giving import errors after an update?  
Run `docker compose down` followed by `docker compose up --build`.  
If uv.lock died, you can delete it and run uv sync again to regenerate it.  



## 🔍 Known Limitations & Future Roadmap

### 1. Current Limitation: Intent-Blind Semantic Matching
The current iteration uses a high-performance **Bi-Encoder (`paraphrase-multilingual-MiniLM-L12-v2`)** paired with a **Lexical engine (`pg_trgm`)**. 
* **The Challenge:** In specific edge cases—primarily "Scam Warnings" or "Educational Content"—the system may produce a **Confident Hallucination (False Positive)**. This occurs because the retriever identifies high semantic similarity to scam templates but remains "intent-blind" to the context (e.g., a user warning a friend about a virus).
* **The Trade-off:** We have prioritized **Deterministic Latency (<1.0s)** and **Edge-Ready Inference** over generative reasoning to ensure the system remains viable for real-time production environments.

### 2. Future Work: SLM Intent Gating (V2.0 Blueprint)
To resolve the semantic ambiguity between "Scam Content" and "Scam Discussion," we have developed a blueprint for a **Reasoning-Augmented Classification (RAC) Refinement** layer.

#### **A. Probabilistic Intent Calibration**
The proposed upgrade introduces a **Small Language Model (SLM)**—such as *Qwen2.5-0.5B*—acting as a Contextual Prior. This model extracts a **3-Bit Intent Vector** in parallel with retrieval:
1. **Posture:** (Professional vs. Anonymous)
2. **Pressure:** (Neutral vs. Coercive)
3. **Instruction:** (Informational vs. Action-oriented)

#### **B. Conformity-Scaled Fusion**
Instead of a binary veto, we propose a **Non-Linear Conformity Score**:
$$effective\_retrieval\_confidence = base\_retrieval\_confidence \times (1 - |risk - vibe|)^2$$
This ensures that if the SLM detects a "Warning" vibe while the Database retrieves a "Scam" match, the retrieval weight is mathematically neutralized before hitting the XGBoost head.

#### **C. Implementation Constraints**
While this architecture is finalized, it was scoped out of the current MVP to avoid:
* **Generative Latency Tax:** Avoiding the 300-600ms TTFT penalty inherent in LLM inference.
* **Data Preparation Overhead:** Maintaining pipeline agility without the multi-hour inference requirements for retraining the XGBoost feature set.