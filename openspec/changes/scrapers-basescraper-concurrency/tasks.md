## 1. Scraper runtime (`base.py`)

- [ ] 1.1 Add **`hosted_agents/scrapers/base.py`**: shared **`run()`** orchestration — load **`job.json`**, env validation, metrics HTTP lifecycle, **sole owner of `POST /v1/embed`** to managed RAG, **cursor/watermark read/write** via **`cursor_store`**, bounded **`integration`** label, exit codes
- [ ] 1.2 Define **`ScraperIntegration`** **`Protocol`** (or ABC): methods return **normalized in-memory payloads** (and optional proposed watermark/cursor updates as **data** only); **no** RAG HTTP, **no** persistence side effects inside integration implementations
- [ ] 1.3 Refactor **`jira_job`** to integration-only **return-data** pattern; entrypoint delegates to **`base.py`**; tests green
- [ ] 1.4 Refactor **`slack_job`** the same way; tests green

## 2. Helm: concurrencyPolicy

- [ ] 2.1 Add optional **`concurrencyPolicy`** under **`scrapers.jira.jobs[]`** and **`scrapers.slack.jobs[]`** in **`values.yaml`** and **`values.schema.json`** (enum **`Forbid`**, **`Allow`**, **`Replace`**); strip from **`job.json`** merge in templates
- [ ] 2.2 Render **`spec.concurrencyPolicy`** on scraper CronJobs defaulting **`Forbid`** when unset
- [ ] 2.3 Extend **`helm/tests/with_scrapers_test.yaml`** (and examples README if examples gain the field)

## 3. Spec promotion and CI

- [ ] 3.1 After implementation, merge deltas **`scraper-base-runtime`** and **`dalc-rag-from-scrapers`** **`[DALC-REQ-RAG-SCRAPERS-005]`** into **`openspec/specs/`**, update **`docs/spec-test-traceability.md`**, cite IDs in pytest/Helm unittest
- [ ] 3.2 Run **`python3 scripts/check_spec_traceability.py`**, **`uv run pytest`**, Helm unittest suites per **`docs/local-ci.md`**

## 4. Housekeeping

- [ ] 4.1 Update **`ADR 0009`** with **base.py** vs integration responsibilities (RAG ingest + persistence vs return-data-only)
- [ ] 4.2 Archive **`scrapers-basescraper-concurrency`** when promoted and merged (optional dated **`openspec/changes/archive/`** move)
