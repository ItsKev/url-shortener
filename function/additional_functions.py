import logging
import os
import random
import string
from dataclasses import dataclass
from typing import Any, Dict, Optional

import validators
from azure.cosmos import ContainerProxy, CosmosClient, PartitionKey, exceptions

# Application constants
DEFAULT_SHORT_CODE_LENGTH = 6
DEFAULT_COSMOS_THROUGHPUT = 400
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


@dataclass
class UrlItem:
    id: str
    short_code: str
    original_url: str

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "short_code": self.short_code,
            "original_url": self.original_url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UrlItem":
        return cls(
            id=data["id"],
            short_code=data["short_code"],
            original_url=data["original_url"],
        )


class CosmosDBClient:

    def __init__(self):
        self._client: Optional[CosmosClient] = None
        self._container: Optional[ContainerProxy] = None
        self._config = get_cosmos_config()

    def _get_client(self) -> CosmosClient:
        if self._client is None:
            self._client = CosmosClient(self._config["endpoint"], self._config["key"])
        return self._client

    def _get_container(self) -> ContainerProxy:
        if self._container is None:
            client = self._get_client()
            database = client.create_database_if_not_exists(
                id=self._config["database_name"]
            )
            self._container = database.create_container_if_not_exists(
                id=self._config["container_name"],
                partition_key=PartitionKey(path="/short_code"),
                offer_throughput=DEFAULT_COSMOS_THROUGHPUT,
            )
        return self._container

    def check_short_code_exists(self, short_code: str) -> bool:
        try:
            container = self._get_container()
            container.read_item(item=short_code, partition_key=short_code)
            return True
        except exceptions.CosmosResourceNotFoundError:
            return False

    def create_url_item(self, url_item: UrlItem) -> None:
        container = self._get_container()
        container.create_item(body=url_item.to_dict())
        logging.info(
            f"Created short URL: {url_item.short_code} -> {url_item.original_url}"
        )

    def get_url_item(self, short_code: str) -> Optional[UrlItem]:
        try:
            container = self._get_container()
            item_data = container.read_item(item=short_code, partition_key=short_code)
            return UrlItem.from_dict(item_data)
        except exceptions.CosmosResourceNotFoundError:
            return None


def generate_short_code(length: int = DEFAULT_SHORT_CODE_LENGTH) -> str:
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


def validate_url(url: str) -> Optional[str]:
    if not url:
        return "URL cannot be empty"

    if len(url) > MAX_URL_LENGTH:
        return f"URL too long (max {MAX_URL_LENGTH} characters)"

    if not validators.url(url):
        return "Invalid URL format"

    return None


def validate_short_code(short_code: str) -> Optional[str]:
    if not short_code:
        return "Short code not provided"

    if not short_code.isalnum() or len(short_code) != DEFAULT_SHORT_CODE_LENGTH:
        return "Invalid short code format"

    return None


# Global instance for use across the application
db_client = CosmosDBClient()
