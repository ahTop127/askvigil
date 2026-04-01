from pydantic_settings import BaseSettings, SettingsConfigDict
import os

# 1. Obtain the value of the current system ENVIRONMENT variable "environment".
# If it is not set, it will be regarded as the development environment "dev" by default.
env_state = os.getenv("ENVIRONMENT", "dev")

# 2. Concatenate the file name to be read, such as ".env.dev" or ".env.prod"
env_file_name = f".env.{env_state}"

class Settings(BaseSettings):
    # The variable names here must be exactly the same as those in.env
    DATABASE_URL: str

    # Dynamically specify the env file to be loaded
    model_config = SettingsConfigDict(env_file=env_file_name, extra="ignore")


# Instantiate the configuration object for import and use by other modules
settings = Settings()

print(f"Current operating environment: {env_state.upper()}, Loaded configuration: {env_file_name}")