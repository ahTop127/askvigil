# AskVigil - a Scam Detector website app.

Welcome to AskVigil by SleepUnderflow. We are using a containerized Python stack. This means if it runs on your laptop in Docker, it **will** work on the Oracle server. You must have docker desktop running to run the code. Saving a file will automatically reload the code, you only need to run `docker-compose up --build` if you changed the structure, like a library requirement in requirements.txt.

General Syntax for inserting data into cloud storage:  
`curl.exe -X PUT --data-binary "@local_file_name" "PAR_URL/remote_file_name"`
PAR_URL goes into the .env file, it is not to be shared publicly.

---

## 🛠 The Tech Stack

* **Frontend: React** — Flexible and industry-standard for building our dashboard.
* **Backend: FastAPI** — High-performance Python. It’s fast to develop and has native support for AI libraries like PyTorch.
* **AI: Paraphrase-multilingual-MiniLM-L12-v2 (sentence-transformers)** — The fast choice. Specifically designed to map different languages into the same vector space, crucial for future multilingual support, light enough to run on Oracle Free tier.
* **Database: PostgreSQL + pgvector** — Reliable relational data storage. `pgvector` allows us to store AI embeddings for semantic search or similarity matching. **NOTE:** Vector dimensions are strict, and so is SQL database tables, make sure they match.
* **Containerization: Docker** — Wraps everything in a "bubble" to eliminate "it works on my machine" issues and library conflicts.
* **Proxy: Nginx Proxy Manager** — A GUI that handles our DuckDNS and SSL certificates so we never have to touch a raw `.conf` file again.

---

## 🚀 Getting Started (Local Development)

### 1. Prerequisites
* Install **Docker Desktop** and **VS Code**. 
* NVIDIA GPU Users (Optional): If you want to fine-tune NLP models locally, install NVIDIA Container Toolkit in your WSL terminal. (https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
    * Mac users: Don't. Just let it run on CPU mode.

### 2. Setup
1.  Clone the repo.
2.  Create a `.env` file in the root directory (see the lead for the template).
* **Update**: When you open the project, you should see a prompt to "Reopen in Container?" Say yes, and you don't need to do step 3 and 4.

3.  Fire up the stack:
    ```bash
    docker-compose up --build
    ```
    _Note: The first run will take 5-10 minutes to download the Multilingual MiniLM model and initialize the database._
4.  The Workflow
    * **Editing Code:** Just edit any file in src/ (Frontend) or backend/. The app will auto-reload. You do NOT need to restart Docker.
    * **New Libraries:** If you add something to requirements.txt or package.json, you must re-run:
    ```bash
    docker compose up --build
    ```
    * **Database:** The pgvector extension and embeddings table are pre-configured. Just start the containers and start querying.

5.  Production (Oracle Cloud)
    * **Deployment:** Simply git push origin main.
    * **CI/CD:** GitHub Actions will automatically build and deploy to the Oracle server.
    * **Secrets:** Production secrets are managed on the server's .env. Do not push your local .env to Git.

6.  **Verification:**
    * **Local Frontend:** [http://localhost:3000](http://localhost:3000)
    * **Local API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs) (FastAPI generates this automatically!)
    * **Production:** [https://askvigil.duckdns.org]
    * **Docs:** Go to [https://askvigil.duckdns.org] and append /api, /docs, /redoc, or /openapi.json for for whichever ones you want.

---

## ☁️ Deployment (CI/CD)

We are using **GitHub Actions** for "Hands-Off" deployment. 
* **The Flow:** Push your code to the `main` branch → GitHub SSHes into Oracle → Docker rebuilds only what changed.
* **Note:** If you add a new Python library, add it to `backend/requirements.txt`.

---

## ⚠️ Ground Rules
1. **Never** commit the `.env` file to Git (it’s in the `.gitignore`).
2. **Never** upload large AI model files. We mount them as volumes on the server to keep the repo light.
3. **Always** test your `docker-compose up` locally before pushing to `main`.

## Developer Debugging Checklist:
Environment giving import errors after an update?  
Run `docker-compose down -v` followed by `docker-compose up --build`.  
If uv.lock died, you can delete it and run uv sync again to regenerate it.  