from pathlib import Path
from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    app_name: str = "Intelligent Personal Finance Advisor Agent"
    app_version: str = "1.0.0"
    storage_dir: Path = Path("app/storage")
    reports_dir: Path = Path("app/storage/reports")
    logs_dir: Path = Path("app/logs")
    history_file: Path = Path("app/storage/conversation_history.json")
    llm_base_url: str = "http://98.90.16.11:11434/v1"
    llm_model: str = "llama3.2:latest"
    llm_api_key: str = Field(default="ollama")
    llm_timeout_seconds: int = 180
    llm_max_retries: int = 3
    llm_enabled: bool = True
    llm_strict_mode: bool = False


config = AppConfig()
