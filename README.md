# simple-es-api

simple-es-api is a small REST API in front of Elasticsearch. The API receives a search query over HTTP, sends it to Elasticsearch with a fixed timeout, and returns the response. It also writes each request to a SQLite log.

## How it works

1. The client sends a query to `POST /{index}/_search`.
2. The API sets the `timeout` field of the query to the `QUERY_TIMEOUT` value.
3. The API sends the query to Elasticsearch and waits for the response.
4. The API returns the response body and status code to the client.
5. The API writes one row to the request log.

## Requirements

- Python 3.10 or later
- Elasticsearch 8.x

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd simple-es-api
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Copy the settings template:

   ```bash
   cp .env.example .env
   ```

5. Set the values in `.env`. See [Configuration](#configuration).

## Configuration

The API reads its settings from the `.env` file in the project root.

| Variable | Default | Description |
| --- | --- | --- |
| `ES_HOST` | `https://localhost:9200` | Elasticsearch URL. |
| `ES_AUTH_METHOD` | `api_key` | Authentication method: `api_key` or `basic`. Any other value stops the API at startup. |
| `ES_API_KEY` | empty | API key in encoded form. This is the `encoded` field that Elasticsearch returns when you create the key. Used when `ES_AUTH_METHOD=api_key`. |
| `ES_USERNAME` | empty | Username. Used when `ES_AUTH_METHOD=basic`. |
| `ES_PASSWORD` | empty | Password. Used when `ES_AUTH_METHOD=basic`. |
| `ES_IGNORE_SSL` | `false` | If `true`, the API does not check the SSL certificate of Elasticsearch and hides the related warnings. Use it for clusters with a self-signed or private CA certificate. |
| `ES_MAX_CONNECTIONS` | `10` | Maximum number of queries that the API sends to Elasticsearch at the same time. See [Limits](#limits). |
| `QUERY_TIMEOUT` | `300` | Maximum time for one query, in seconds. See [Query timeout](#query-timeout). |
| `DB_PATH` | `requests.db` | Path of the SQLite file. A relative path starts from the working directory. |
| `LOG_QUERY` | `false` | If `true`, the API stores the query body in the request log. |

## Run

Run this command from the project root:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

FastAPI serves the interactive API documentation at `/docs`.

## Usage

Send the query to `POST /{index}/_search`. The request body has the same format as the body of the Elasticsearch Search API.

```bash
curl -X POST "http://localhost:8000/my-index/_search" \
  -H "Content-Type: application/json" \
  -d '{"query": {"match": {"message": "error"}}, "size": 10}'
```

The `{index}` value accepts the same index patterns as Elasticsearch, for example `logs-*` or `index-a,index-b`. To search all indices, use `_all`.

### Status codes

| Status | Cause |
| --- | --- |
| Elasticsearch status | The API returns the Elasticsearch status code and response body without changes, for example `200`, `400`, `404`, or `503`. |
| `422` | The request body is missing or is not a JSON object. |
| `502` | The API cannot connect to Elasticsearch, for example because of a refused connection or an SSL error. |
| `504` | Elasticsearch did not send a response within `QUERY_TIMEOUT` seconds. |

## Query timeout

The API applies `QUERY_TIMEOUT` at two levels:

- **Search timeout.** The API sets the `timeout` field of the query, for example `"timeout": "300s"`. This value replaces a `timeout` value from the client. Each shard collects hits only within this time. After the time ends, Elasticsearch returns the hits that it collected and sets `"timed_out": true`.
- **Request timeout.** The API waits a maximum of `QUERY_TIMEOUT` seconds for the full Elasticsearch response. This time includes the download of the response body. If the full response does not arrive in this time, the API returns `504`.

Both levels use the same value. Thus, a search near the limit can end with `504` and not with partial results.

The API sends each query to Elasticsearch only one time. It does not retry a query after an error or a timeout. Thus, `QUERY_TIMEOUT` is also the maximum total wait for one query.

## Request log

The API writes one row to the `requests` table for each search request. A request that fails with `422` does not get a row.

| Column | Description |
| --- | --- |
| `id` | Row ID. |
| `created_at` | Time when the API completed the request, in UTC (ISO 8601). |
| `source_ip` | IP address of the client. |
| `user_agent` | `User-Agent` header of the request. |
| `target_index` | Index or index pattern from the URL. |
| `status_code` | HTTP status code that the API returned. |
| `query` | Query body as JSON, with the `timeout` field. `NULL` if `LOG_QUERY=false`. |

To see the last 10 requests:

```bash
sqlite3 requests.db "SELECT created_at, source_ip, target_index, status_code FROM requests ORDER BY id DESC LIMIT 10;"
```

## Limits

- `ES_MAX_CONNECTIONS` sets the maximum number of queries that the API sends to Elasticsearch at the same time. Other requests wait in a queue. The time in the queue does not count toward `QUERY_TIMEOUT`.
- The API sets no size limit on the query or the response. It sends the Elasticsearch response to the client as raw bytes, without parsing.
- The API keeps each full response in memory before it sends it to the client. Make sure that the server has enough memory for `ES_MAX_CONNECTIONS` large responses at the same time.
- Limits outside this code still apply:
  - `http.max_content_length` in Elasticsearch: maximum request size (default `100mb`).
  - `index.max_result_window` in Elasticsearch: maximum value of `from` + `size` (default `10000`).
  - The timeout of a reverse proxy in front of the API. Set it higher than `QUERY_TIMEOUT`.
- The API accepts only `POST` requests. It does not support `GET` with a request body.

## Security

- The API has no authentication. Any client that can connect to the API can search with the Elasticsearch credentials of the API. Use an API key with read-only privileges on the necessary indices. Limit network access to the API.
- `ES_IGNORE_SSL=true` disables the SSL certificate check. Then, an attacker on the network can intercept the connection. Use this option only on a trusted network.
- Behind a reverse proxy, `source_ip` can contain the IP address of the proxy. Uvicorn reads the `X-Forwarded-For` header only from the addresses in `--forwarded-allow-ips` (default `127.0.0.1`). If the proxy runs on a different host, add its IP address to this option.

## Project structure

```text
app/
  main.py          HTTP endpoint
  es_client.py     Elasticsearch client setup
  database.py      SQLite request log
  config.py        Settings from .env
.env.example       Settings template
requirements.txt   Python dependencies
```

## To do

- [ ] API authentication
- [ ] Rate limiting per client IP address
