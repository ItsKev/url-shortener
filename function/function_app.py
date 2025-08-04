from typing import Any
import azure.functions as func
import logging
import json
import os
import string
import random
from azure.cosmos import CosmosClient, PartitionKey, ContainerProxy
import validators

app = func.FunctionApp()

def get_cosmos_client() -> CosmosClient:
    endpoint = os.environ["COSMOS_DB_ENDPOINT"]
    key = os.environ["COSMOS_DB_KEY"]

    logging.info(f"Connecting to Cosmos DB at {endpoint}")
    return CosmosClient(endpoint, key)

def get_container() -> ContainerProxy:
    client = get_cosmos_client()
    database_name = os.environ["COSMOS_DB_DATABASE_NAME"]
    container_name = os.environ["COSMOS_DB_CONTAINER_NAME"]

    logging.info(f"Accessing and creating database '{database_name}' if it does not exist")
    database = client.create_database_if_not_exists(id=database_name)

    logging.info(f"Accessing and creating container '{container_name}' if it does not exist")
    return database.create_container_if_not_exists(
        id=container_name,
        partition_key=PartitionKey(path="/short_code"),
        offer_throughput=400
    )

def generate_short_code(length: int = 6) -> str:
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@app.route(route="shorten", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def shorten_url(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('URL shortening request received.')
    
    try:
        req_body = req.get_json()
        if not req_body or 'url' not in req_body:
            return func.HttpResponse(
                json.dumps({"error": "Missing 'url' in request body"}),
                status_code=400,
                mimetype="application/json"
            )
        
        original_url = req_body['url']
        
        if not validators.url(original_url):
            return func.HttpResponse(
                json.dumps({"error": "Invalid URL format"}),
                status_code=400,
                mimetype="application/json"
            )
        
        container = get_container()
        
        while True:
            short_code = generate_short_code()
            
            try:
                container.read_item(item=short_code, partition_key=short_code)
            except:
                break
        
        item: dict[str, str] = {
            "id": short_code,
            "short_code": short_code,
            "original_url": original_url
        }
        
        logging.info(f"Storing item with short code: {short_code}")
        container.create_item(body=item)
        
        return func.HttpResponse(
            json.dumps({
                "short_code": short_code,
                "original_url": original_url,
                "short_url": f"http://localhost:7071/api/r/{short_code}"
            }),
            status_code=201,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error shortening URL: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="r/{short_code}", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def redirect_url(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('URL redirect request received.')
    
    try:
        short_code = req.route_params.get('short_code')
        
        if not short_code:
            return func.HttpResponse(
                "Short code not provided",
                status_code=400
            )
        
        container: ContainerProxy = get_container()
        
        try:
            item: dict[str, Any] = container.read_item(item=short_code, partition_key=short_code)
            original_url = item['original_url']
            
            return func.HttpResponse(
                "",
                status_code=302,
                headers={"Location": original_url}
            )
            
        except:
            return func.HttpResponse(
                "Short URL not found",
                status_code=404
            )
            
    except Exception as e:
        logging.error(f"Error redirecting URL: {str(e)}")
        return func.HttpResponse(
            "Internal server error",
            status_code=500
        )
