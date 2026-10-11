from elasticsearch import Elasticsearch, JsonSerializer

from app import config


class RawJsonSerializer(JsonSerializer):
    """Keep ES responses as raw bytes. No parsing, so large responses stay cheap."""

    def loads(self, data):
        return data


def create_client():
    """Create the Elasticsearch client from the .env settings."""
    options = {
        "hosts": config.ES_HOST,
        "request_timeout": config.QUERY_TIMEOUT,
        "connections_per_node": config.ES_MAX_CONNECTIONS,
        # One try per query, so QUERY_TIMEOUT is also the max total wait
        "max_retries": 0,
        "serializers": {"application/json": RawJsonSerializer()},
    }

    if config.ES_AUTH_METHOD == "api_key":
        options["api_key"] = config.ES_API_KEY
    elif config.ES_AUTH_METHOD == "basic":
        options["basic_auth"] = (config.ES_USERNAME, config.ES_PASSWORD)
    else:
        raise ValueError("ES_AUTH_METHOD must be 'api_key' or 'basic'")

    # Custom CA setups: skip the certificate check and hide the warnings
    if config.ES_IGNORE_SSL:
        options["verify_certs"] = False
        options["ssl_show_warn"] = False

    return Elasticsearch(**options)
