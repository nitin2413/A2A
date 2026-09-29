# from shared.config import Settings, load_llm_config
#
#
# settings = Settings()
#
# print("Settings loaded successfully")
# print(f"LLM config path: {settings.llm_config_path}")
#
# configs = load_llm_config(settings.llm_config_path)
#
# print("\nAgents configured:")
#
# for name, config in configs.items():
#     print(f"\n{name}")
#     print(f"  provider: {config.provider}")
#     print(f"  model: {config.model}")
#     print(f"  api_key_env: {config.api_key_env}")
#     print(f"  temperature: {config.temperature}")
#     print(f"  max_tokens: {config.max_tokens}")

from shared.llm import get_llm

llm = get_llm("planner")
print("LLM created successfully")
print(type(llm))
print(llm)

response = llm.invoke("Say hello in one sentence.")
print(response.content)