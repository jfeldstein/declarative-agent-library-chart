## Why

Jira and Slack scrapers each reimplement the same scaffolding: load **`job.json`**, **persist cursor/watermark**, **ingest to RAG** via **`POST /v1/embed`**, expose **Prometheus** metrics and graceful shutdown, and enforce **bounded labels**. That duplication makes drift likely and blurs boundaries: **source-specific** code should only talk to upstream APIs and **return normalized data**; **persistence** and **RAG ingest** belong in one shared layer.

Separately, scraper **CronJobs** today use a fixed **`concurrencyPolicy`**; operators sometimes need **`Allow`** or **`Replace`** without forking the chart.

## What Changes

- Introduce a shared runtime ( **`hosted_agents/scrapers/base.py`** ) plus a small **`typing.Protocol`** (or ABC) for **integrations**: the runtime owns **`run()`**, **all `POST /v1/embed`** traffic to the managed RAG service, **cursor/watermark** writes via **`cursor_store`**, metrics listener lifecycle, and exit semantics. **`jira_job`** / **`slack_job`** shrink to **fetch → map → return structures** (and optional proposed watermark values as **data**), with **no** direct RAG HTTP calls and **no** durable state writes inside integration code.
- Refactor **`jira_job`** and **`slack_job`** against that contract; preserve external behavior and metric names unless a **BREAKING** note is explicitly accepted later.
- Add optional **per-job** Helm values (**`scrapers.<integration>.jobs[]`**) for **`concurrencyPolicy`**, defaulting to **`Forbid`**, rendered on scraper **CronJob** specs.
- Extend **ADR 0009** (or companion note) describing the base-vs-integration split.

## Capabilities

### New Capabilities

- `scraper-base-runtime`: Normative split — **runtime** persists incremental state and performs **RAG ingest**; **integrations** return normalized data only.

### Modified Capabilities

- `dalc-rag-from-scrapers`: Add **SHALL** rows (stable IDs) for **operator-tunable CronJob `concurrencyPolicy`** per enabled scraper job when the chart exposes those values (defaults preserve **`Forbid`**).

## Impact

- **Python**: **`hosted_agents/scrapers/base.py`** (new), refactors to **`jira_job.py`** / **`slack_job.py`**, tests in **`helm/src/tests/test_*_job.py`** and **`test_scraper_metrics.py`** as needed.
- **Helm**: **`values.yaml`**, **`values.schema.json`**, **`_manifest_scraper_cronjobs.tpl`** (or equivalent), **`helm/tests/with_scrapers_test.yaml`**.
- **OpenSpec**: Promote delta specs after implementation; update **`docs/spec-test-traceability.md`** for new IDs.
