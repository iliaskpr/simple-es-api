import json
from contextlib import asynccontextmanager

import anyio.to_thread
from elasticsearch import ApiError, ConnectionTimeout, TransportError
from fastapi import Body, FastAPI, Request
from fastapi.responses import Response

from app import config, database
from app.es_client import create_client


@asynccontextmanager
async def lifespan(app):
    # One worker thread per ES connection (the default is 40 threads)
    limiter = anyio.to_thread.current_default_thread_limiter()
    limiter.total_tokens = config.ES_MAX_CONNECTIONS

    database.init_db()
    yield


app = FastAPI(title="Simple ES API", lifespan=lifespan)
es = create_client()


@app.post("/{index}/_search")
def search(index: str, request: Request, query: dict = Body()):
    # Enforce the timeout from .env (replaces any timeout in the query)
    query["timeout"] = f"{config.QUERY_TIMEOUT}s"

    try:
        response = es.search(index=index, body=query)
        status_code = response.meta.status
        content = response.body
    except ApiError as error:
        # Elasticsearch answered with an error (bad query, missing index, ...)
        status_code = error.meta.status
        content = error.body
    except ConnectionTimeout:
        status_code = 504
        content = json.dumps({"error": f"Elasticsearch did not answer within {config.QUERY_TIMEOUT}s"})
    except TransportError as error:
        # Connection refused, SSL error, ...
        status_code = 502
        content = json.dumps({"error": f"Cannot reach Elasticsearch: {error.message}"})

    database.save_request(
        source_ip=request.client.host,
        user_agent=request.headers.get("user-agent"),
        target_index=index,
        status_code=status_code,
        query=query,
    )

    # The ES response goes back as raw bytes, without changes
    return Response(content=content, status_code=status_code, media_type="application/json")
