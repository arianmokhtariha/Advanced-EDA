import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_env_variable(var_name, default=None):
    """Get an environment variable or raise an error if missing and no default."""
    value = os.getenv(var_name, default)
    if value is None:
        raise EnvironmentError(f"Missing required environment variable: {var_name}")
    return value

# Database configuration for the target database
try:
    DB_CONFIG = {
        'user': get_env_variable('DB_USER'),
        'password': get_env_variable('DB_PASSWORD'),
        'host': get_env_variable('DB_HOST'),
        'port': get_env_variable('DB_PORT'),
        'dbname': get_env_variable('DB_NAME')
    }

    # Database configuration for initial connection (to create the target DB)
    DB_CONFIG_INIT = {
        'user': get_env_variable('DB_USER'),
        'password': get_env_variable('DB_PASSWORD'),
        'host': get_env_variable('DB_HOST'),
        'port': get_env_variable('DB_PORT'),
        'dbname': 'postgres'  # Default DB for creating new databases
    }
except EnvironmentError as e:
    print(f"❌ Configuration Error: {e}")
    raise
