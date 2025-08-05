import logging
from typing import Optional

from azure.cosmos import ContainerProxy, CosmosClient, PartitionKey, exceptions

from .config import DEFAULT_COSMOS_THROUGHPUT, get_cosmos_config
from .models import UrlItem


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


# Global instance for use across the application
db_client = CosmosDBClient()
