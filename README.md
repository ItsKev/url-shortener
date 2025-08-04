# URL Shortener

Azure API management for rate limiting

# Local Development
docker run \
    --publish 8081:8081 \
    --publish 10250-10255:10250-10255 \
    --name azure-cosmos-emulator \
    --detach \
    --env AZURE_COSMOS_EMULATOR_IP_ADDRESS_OVERRIDE=127.0.0.1 \
    mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest
