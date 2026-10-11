import os

from dotenv import load_dotenv

# Read the settings from the .env file
load_dotenv()

# Elasticsearch connection
ES_HOST = os.getenv("ES_HOST", "https://localhost:9200")
ES_AUTH_METHOD = os.getenv("ES_AUTH_METHOD", "api_key")  # "api_key" or "basic"
ES_API_KEY = os.getenv("ES_API_KEY", "")
ES_USERNAME = os.getenv("ES_USERNAME", "")
ES_PASSWORD = os.getenv("ES_PASSWORD", "")
ES_IGNORE_SSL = os.getenv("ES_IGNORE_SSL", "false").lower() == "true"

# Max number of queries sent to Elasticsearch at the same time
ES_MAX_CONNECTIONS = int(os.getenv("ES_MAX_CONNECTIONS", "10"))

# Max time for one query, in seconds
QUERY_TIMEOUT = int(os.getenv("QUERY_TIMEOUT", "300"))

# Request log
DB_PATH = os.getenv("DB_PATH", "requests.db")
LOG_QUERY = os.getenv("LOG_QUERY", "false").lower() == "true"
