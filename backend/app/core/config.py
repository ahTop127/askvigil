import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# 1. Obtain the value of the current system ENVIRONMENT variable "environment".
# If it is not set, it will be regarded as the development environment "dev" by default.
env_state = os.getenv("ENVIRONMENT", "dev")

# 2. Concatenate the file name to be read, such as ".env.dev" or ".env.prod"
env_file_name = f".env.{env_state}"


class Settings(BaseSettings):
    # --- ENVIRONMENT VARIABLES (Mapped from .env) ---
    DATABASE_URL: str
    PERSISTENCE_PATH: Path = Path("/app/data_persistence")
    OCI_PAR_URL: str | None = None

    # --- ARCHITECTURAL CONSTANTS ---
    RRF_CONSTANT: int = 60
    RRF_DEPTH: int = 100
    RRF_K: int = 2
    SEARCH_WINDOW: int = 10
    K_SATURATION: float = 0.66 # Maps 1.0 mass to 0.6 momentum
    DIM_TEXT: int = 384
    DIM_URL: int = 768
    # Asymmetric Saturation Constants
    LAMBDA_SPAM: float = 0.8  # More sensitive
    LAMBDA_HAM: float = 1.2   # Harder to satisfy

    # --- COMPUTED PROPERTIES (Paths & Derived Logic) ---
    @property
    def DATASET_DIR(self) -> Path:
        return self.PERSISTENCE_PATH / "datasets"

    @property
    def SCAM_CSV(self) -> Path:
        return self.DATASET_DIR / "scam_dataset.csv"

    @property
    def PHISH_CSV(self) -> Path:
        return self.DATASET_DIR / "phishing_dataset.csv"

    @property
    def MODEL_DIR(self) -> Path:
        return self.PERSISTENCE_PATH / "ai_models"

    @property
    def TEXT_MODEL_PATH(self) -> Path:
        return self.MODEL_DIR / "text_onnx"

    @property
    def TEXT_CLASSIFIER_PATH(self) -> Path:
        return self.TEXT_MODEL_PATH / "classifier.onnx"

    @property
    def URL_MODEL_PATH(self) -> Path:
        return self.MODEL_DIR / "url_onnx"

    @property
    def MAX_POSSIBLE_RRF(self) -> float:
        return 2.0 / (self.RRF_CONSTANT + 1)

    # Pydantic Config. Dynamically specify the env file to be loaded
    model_config = SettingsConfigDict(env_file=env_file_name, extra="ignore")


# Instantiate for use
settings = Settings()

print(f"Current operating environment: {env_state.upper()}, Loaded: {env_file_name}")
