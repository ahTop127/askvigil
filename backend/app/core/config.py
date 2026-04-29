import os
import glob
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
    DIM_TEXT: int = 384
    DIM_URL: int = 768

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
    def URL_CLASSIFIER_PATH(self) -> Path:
        return self.URL_MODEL_PATH / "classifier.onnx"

    @property
    def OCR_MODEL_DIR(self) -> Path:
        return self.MODEL_DIR / "ocr_onnx"

    def _get_ocr_file(self, pattern: str, extension: str = "onnx") -> str:
        """Helper to find OCR files (onnx models or txt keys)"""
        files = glob.glob(str(self.OCR_MODEL_DIR / f"*{pattern}*.{extension}"))
        return files[0] if files else ""

    @property
    def OCR_DET_PATH(self) -> str:
        return self._get_ocr_file("det")

    @property
    def OCR_CLS_PATH(self) -> str:
        return self._get_ocr_file("cls")

    @property
    def OCR_REC_PATH(self) -> str:
        return self._get_ocr_file("rec")

    @property
    def OCR_KEYS_PATH(self) -> str:
        # This is the character dictionary (keys)
        return self._get_ocr_file("keys", extension="txt")
    
    @property
    def MAX_POSSIBLE_RRF(self) -> float:
        return 2.0 / (self.RRF_CONSTANT + 1)

    # Pydantic Config. Dynamically specify the env file to be loaded
    model_config = SettingsConfigDict(env_file=env_file_name, extra="ignore")


# Instantiate for use
settings = Settings()

print(f"Current operating environment: {env_state.upper()}, Loaded: {env_file_name}")
