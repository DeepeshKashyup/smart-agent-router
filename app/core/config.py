"""Application configuration via pydantic-settings."""

from functools import lru_cache

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # GCP / Vertex AI
    google_cloud_project: str = Field(default="your-project-id")
    vertex_ai_location: str = Field(default="us-central1")

    # Models
    large_model_name: str = Field(default="gemini-1.5-pro")
    small_model_name: str = Field(default="gemini-1.5-flash")
    routing_model_name: str = Field(default="gemini-1.5-flash")

    # Vector Store
    vectorstore_type: str = Field(default="chroma")
    chroma_persist_dir: str = Field(default="./data/embeddings")

    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    log_level: str = Field(default="INFO")

    # Cost Tracking
    enable_cost_tracking: bool = Field(default=True)
    cost_log_file: str = Field(default="./data/cost_log.jsonl")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


def load_yaml_config(path: str = "configs/config.yaml") -> dict:
    """Load YAML configuration file."""
    with open(path) as f:
        return yaml.safe_load(f)


def load_prompts(path: str = "configs/prompts.yaml") -> dict:
    """Load prompt templates from YAML."""
    with open(path) as f:
        return yaml.safe_load(f)
