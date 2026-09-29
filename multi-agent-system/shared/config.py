from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml
from pathlib import Path

class AgentLLMConfig(BaseModel):
    """
    Configuration for the Agent LLM.
    """
    provider: str
    # base_url : str | None = None
    model: str
    api_key_env: str
    temperature: float = 0.2
    max_tokens: int = 4000

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    redis_url: str
    postgres_url: str
    groq_api_key: str
    langsmith_api_key: str | None = None
    langsmith_project: str | None = None
    langsmith_tracing: bool = False
    langsmith_endpoint: str | None = None

    llm_config_path: str = "llm_config.yaml"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

def load_llm_config(config_path: str) -> dict[str, AgentLLMConfig]:    
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"LLM configuration file not found at {config_path}")

    with open(path,"r") as f:
        config_data = yaml.safe_load(f)

    if not isinstance(config_data, dict):
        raise ValueError("LLM configuration file must contain a YAML mapping.")    

    llm_config: dict[str, AgentLLMConfig] = {}    

    for agent_name,agent_config in config_data.items():
        llm_config[agent_name] = AgentLLMConfig(**agent_config)

    if "default" not in llm_config:
        raise ValueError("LLM configuration must contain a 'default' agent configuration.")

    return llm_config
