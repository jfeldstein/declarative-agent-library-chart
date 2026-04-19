## Why

Jira and Slack scrapers each reimplement the same scaffolding: load **`job.json`**, wire **cursor/watermark**, call **RAG `/v1/embed`**, expose **Prometheus** metrics and graceful shutdown, and enforce **bounded labels**. That duplication makes behavioral drift likely and obscures where integration-specific work should live (remote APIs and normalization). Separately, scraper **CronJobs** today use a fixed **`concurrencyPolicy`**; operators sometimes need **`Allow`** for overlapping windows or **`Replace`** for long-running jobs, without forking the chart.

## What Changes

- Introduce a **`BaseScraper`** (abstract base class or **`typing.Protocol`**) in **`hosted_agents.scrapers`**: shared **`run()`** orchestration (config, metrics HTTP lifecycle, RAG client, cursor store hooks) calling integration methods for **fetch → map → embed** only.
- Refactor **`jira_job`** and **`slack_job`** to implement the interface (minimal surface: e.g. **`integration_key`**, **`run_sync_cycle`** or iterator of normalized chunks), preserving external behavior and metrics names unless a **BREAKING** note is explicitly accepted later.
- Add optional **per-job** Helm values (under each **`scrapers.<integration>.jobs[]`** entry) for **`concurrencyPolicy`** (and optionally **`startingDeadlineSeconds`** if needed), defaulting to current behavior (**`Forbid`**), rendered on scraper **CronJob** specs.
- Document the contract in **`docs/adrs/`** or extend **ADR 0009** with a pointer to the Python abstraction.

## Capabilities

### New Capabilities

- `scraper-base-runtime`: Normative **`BaseScraper`** / protocol contract; responsibilities split between shared runtime and integration-specific adapters; stable normalized payload shapes toward RAG embed.

### Modified Capabilities

- `dalc-rag-from-scrapers`: Add **SHALL** rows (new stable IDs) for **operator-tunable CronJob `concurrencyPolicy`** per enabled scraper job when the chart exposes those values (defaults preserve **`Forbid`**).

## Impact

- **Python**: **`hosted_agents/scrapers/`** (new module e.g. **`base.py`**, refactors to **`jira_job.py`** / **`slack_job.py`**), tests in **`helm/src/tests/test_*_job.py`** and **`test_scraper_metrics.py`** as needed.
- **Helm**: **`values.yaml`**, **`values.schema.json`**, **`_manifest_scraper_cronjobs.tpl`** (or equivalent), **`helm/tests/with_scrapers_test.yaml`**.
- **OpenSpec**: Promote delta specs after implementation; update **`docs/spec-test-traceability.md`** for new IDs.
