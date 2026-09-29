from functools import lru_cache
from langchain_litellm import ChatLiteLLM
from shared.config import Settings , load_llm_config

settings = Settings()
llm_config = load_llm_config(settings.llm_config_path)

@lru_cache(maxsize=None)
def get_llm(agent_name:str) ->ChatLiteLLM:
    """
    Load the LLM for the given agent name.
    If the agent name is not found in the configuration, use the default configuration.
    """
    config = llm_config.get(agent_name)
    if config is None:
        config = llm_config["default"]

    model = f"{config.provider}/{config.model}"
    api_key = getattr(settings, config.api_key_env.lower(), None)

    if api_key is None:
        raise ValueError(
            f"API key environment variable "
            f"'{config.api_key_env}' was not found."
        )

    return ChatLiteLLM(
        model=model,
        api_key=api_key,
        # api_base=config.base_url,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )    
