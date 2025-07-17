import os
from dotenv import load_dotenv

src_dir = os.path.dirname(os.path.abspath(__file__))
local_env = "../local.env"

# run init_config as a singleton
init_config_done = os.getenv("INIT_CONFIG_DONE", False)
if not init_config_done:
    local_env_path = os.path.join(src_dir, local_env)
    # Load environment variables from .env file
    load_dotenv()
    if load_dotenv(dotenv_path=local_env_path):
        print(f"* Successfully loaded dotenv {local_env_path}")
    else:
        print(f"* Failed to load dotenv file: {local_env_path}")
        print("Using default configuration.")




class AppConfig:
    @staticmethod
    def get_env_bool(var_name: str, default) -> bool:
        return os.getenv(var_name) in ("1", "true", "yes", "on")

    @staticmethod
    def get_env_int(var_name: str, default) -> int:
        return int(os.getenv(var_name, default))

    dns: str = os.getenv("POSTGRES_DNS", default="postgresql+asyncpg://szn:szn@localhost:5432/stats")


app_config = AppConfig()