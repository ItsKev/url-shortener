import os
from typing import Dict

# Application constants
DEFAULT_SHORT_CODE_LENGTH = 6
DEFAULT_COSMOS_THROUGHPUT = 400
CONTENT_TYPE_JSON = "application/json"
MAX_URL_LENGTH = 2048

# Environment variable keys
ENV_COSMOS_ENDPOINT = "COSMOS_DB_ENDPOINT"
ENV_COSMOS_KEY = "COSMOS_DB_KEY"
ENV_COSMOS_DATABASE = "COSMOS_DB_DATABASE_NAME"
ENV_COSMOS_CONTAINER = "COSMOS_DB_CONTAINER_NAME"


def get_cosmos_config() -> Dict[str, str]:
    return {
        "endpoint": os.environ[ENV_COSMOS_ENDPOINT],
        "key": os.environ[ENV_COSMOS_KEY],
        "database_name": os.environ[ENV_COSMOS_DATABASE],
        "container_name": os.environ[ENV_COSMOS_CONTAINER],
    }
