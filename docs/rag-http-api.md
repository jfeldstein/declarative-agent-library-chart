# RAG HTTP API (managed service)

The in-repo POC implements the **`agent-runtime-components`** RAG contract under `agent.rag`:

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness/readiness |
| `GET` | `/metrics` | Prometheus exposition (`agent_runtime_rag_embed_*`, `agent_runtime_rag_query_*`) |
| `POST` | `/v1/embed` | Upsert **entities**, **relationships**, and **text chunks** (with optional `entity_id` per chunk) |
| `POST` | `/v1/relate` | Append **relationships** only (no new chunk text) |
| `POST` | `/v1/query` | Semantic-ish retrieval (deterministic pseudo-embeddings) + optional **relationship expansion** |

## Scopes

All write/read operations carry a string **`scope`** (default `default`). IDs for entities and edges are unique **within a scope**.

## Entity model

- **Entity**: `{ "id": "<string>", "entity_type": "<optional string>" }` (sent under `entities` on `/v1/embed`).
- **Relationship**: `{ "source": "<entity id>", "target": "<entity id>", "relationship_type": "<predicate>" }`.

## `POST /v1/embed`

JSON body:

- `scope` (optional string)
- `items` (optional array of chunks): each `{ "text", "metadata"?, "entity_id"? }`
- `entities` (optional array)
- `relationships` (optional array)

At least one of `items`, `entities`, or `relationships` is required.

**Response:** `{ "chunk_ids": [...], "entities_upserted": n, "relationships_recorded": n }`

**Errors:** `400` if the body is empty; `422` if validation fails (Pydantic).

## `POST /v1/relate`

JSON body: `{ "scope"?, "relationships": [ ... ] }` (relationship objects as above).

## `POST /v1/query`

JSON body:

- `scope`, `query` (required)
- `top_k` (1–50, default 5)
- `expand_relationships` (bool, default false)
- `relationship_types` (optional filter list)
- `max_hops` (1–3, default 1)

**Response:**

```json
{
  "hits": [
    {
      "chunk_id": "...",
      "score": 0.0,
      "text": "...",
      "metadata": {},
      "entity_id": null
    }
  ],
  "related": [
    {
      "entity_id": "e1",
      "neighbor_id": "e2",
      "relationship_type": "belongs_to"
    }
  ]
}
```

When `expand_relationships` is true, `related` includes **typed edges** adjacent to entities attached to top hits (`entity_id` on chunks).

## Limits (POC)

Payload limits are enforced in `hosted_agents/rag/models.py` (text length, max list sizes). The backing store is **in-memory** (single process); use a real vector + graph database for production.

## Run locally

```bash
cd helm/src
uv sync
uv run uvicorn agent.rag.app:create_app --factory --host 127.0.0.1 --port 8090
```

Smoke (in-process, no server):

```bash
uv run python tests/integration/smoke_rag.py
```
