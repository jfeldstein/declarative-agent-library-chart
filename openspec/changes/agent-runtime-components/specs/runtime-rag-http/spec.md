## ADDED Requirements

### Requirement: Helm places the managed RAG workload under `scrapers.ragService`

The DALC chart SHALL **not** use a separate top-level **`rag:`** values key for the managed RAG HTTP deployment. Operator tunables for that workload (**replicas, Service, resources**, and related **`scrapers` job wiring**) SHALL live under **`scrapers.ragService`** and **`scrapers` / `scrapers.jobs`** as described in **`dalc-rag-from-scrapers`** ([DALC-REQ-RAG-SCRAPERS-003]). This capability spec defines **HTTP behavior** of the RAG service; chart placement is **nested under scrapers** by design.

#### Scenario: Operators tune RAG without a top-level `rag` key

- **WHEN** an operator configures the chart’s **`scrapers.ragService`** (and enables scraper jobs as needed)
- **THEN** the deployment remains consistent with **`values.schema.json`** and SHALL not require a duplicate **`rag:`** block for the same workload

### Requirement: RAG HTTP service exposes embed and query

The platform SHALL provide a **managed RAG HTTP service** that exposes at minimum:

- An **`/embed`** endpoint that accepts content (or chunk references) to be embedded and stored for later retrieval.
- A **`/query`** endpoint that accepts a search request (natural language and/or structured filters as defined by implementation) and returns retrieval results usable by callers (e.g. text, metadata, scores).

All runtime components that need retrieval SHALL integrate via this service rather than requiring each component to operate its own vector database.

The service SHALL also support **relationships between represented entities** as specified in the requirement **RAG represents entities and relationships** below (not limited to flat chunk metadata).

#### Scenario: Producer indexes content

- **WHEN** an authorized runtime component sends a valid request to **`/embed`**
- **THEN** the service SHALL persist embedded representations associated with supplied metadata (such as source id, collection or namespace identifier, and timestamps) such that subsequent queries can return that content when relevant

#### Scenario: Consumer searches the index

- **WHEN** an authorized runtime component sends a valid request to **`/query`**
- **THEN** the service SHALL return a ranked set of matches from the indexed corpus appropriate to the query, including enough text or identifiers for the caller to use the result (for example in an agent prompt or scraper deduplication logic)

### Requirement: RAG represents entities and relationships

The RAG service SHALL treat **entities** as addressable objects in the knowledge store. Each entity SHALL have a **stable identifier** (and MAY have a type or label) within a defined scope (for example collection or namespace). The service SHALL support **relationships** (edges) between entities, each characterized by **source entity id**, **target entity id**, and a **relationship type** (predicate or edge label).

Callers SHALL be able to:

- **Declare** entities and relationships at ingest time, either as part of **`/embed`** payloads (metadata or nested graph fields) and/or via **additional documented HTTP endpoints** (for example upserting edges without re-embedding text).
- **Use** stored relationships during retrieval: **`/query`** (or documented query parameters / companion endpoints) SHALL support returning **related entities** for hits and/or **filtering or ranking** using relationship type and hop depth (at minimum: direct neighbors; deeper traversal MAY be supported).

Implementation MAY use a property graph, relational tables, or hybrid vector+graph storage; the spec requires **observable behavior** (persisted edges and relationship-aware retrieval), not a specific database product.

#### Scenario: Ingest declares an edge

- **WHEN** a producer indexes content and includes a declaration that entity **E1** has relationship type **R** to entity **E2** (with both ids in scope)
- **THEN** the service SHALL persist **E1—R→E2** such that later operations can resolve **E2** from **E1** (and vice versa if the implementation treats edges as undirected for that type, as documented)

#### Scenario: Query uses relationships

- **WHEN** a consumer issues a **`/query`** (or documented equivalent) that requests matches for a text query and **expansion or inclusion of related entities** within configured limits (relationship types and hop depth)
- **THEN** the response SHALL include enough structured information for the caller to associate hits with **related entity ids and relationship types** (for example nested `related` objects or a graph slice), not solely isolated text chunks without linkage

### Requirement: RAG service exposes Prometheus metrics

The RAG HTTP service SHALL expose a Prometheus text exposition endpoint at **`/metrics`** (on the same listen port as **`/embed`** and **`/query`** unless documentation specifies a dedicated metrics port) and SHALL register at minimum:

- Counter **`agent_runtime_rag_embed_requests_total`** labeled **`result`** with values from the fixed set **`success`**, **`client_error`**, **`server_error`** (mapping **2xx** → `success`, **4xx** → `client_error`, **5xx** and unhandled errors → `server_error`).
- Histogram **`agent_runtime_rag_embed_duration_seconds`** labeled **`result`** with the same value set and semantics as the counter.
- Counter **`agent_runtime_rag_query_requests_total`** with the same **`result`** label semantics.
- Histogram **`agent_runtime_rag_query_duration_seconds`** with the same **`result`** label semantics.

Implementations SHALL NOT use labels derived from query text, tenant ids, or other high-cardinality sources.

#### Scenario: Successful embed is counted

- **WHEN** a producer receives **2xx** from **`/embed`**
- **THEN** **`agent_runtime_rag_embed_requests_total{result="success"}`** SHALL increase and **`agent_runtime_rag_embed_duration_seconds`** SHALL record the handled request duration

#### Scenario: Failed query is classified

- **WHEN** a consumer receives **4xx** from **`/query`**
- **THEN** **`agent_runtime_rag_query_requests_total{result="client_error"}`** SHALL increase

### Requirement: RBAC is out of scope for this capability

Access control, per-tenant isolation, and authorization policies for **`/embed`** and **`/query`** are **not** required by this specification. Deployments MAY restrict access via network policies or future work; behavior in this change assumes a **trusted network** or platform-level guardrails not defined here.

#### Scenario: Spec does not mandate auth

- **WHEN** a deployment exposes the RAG service on a cluster network
- **THEN** this capability’s requirements SHALL still be satisfied whether or not optional authentication is configured, and absence of RBAC SHALL not be considered a spec violation
