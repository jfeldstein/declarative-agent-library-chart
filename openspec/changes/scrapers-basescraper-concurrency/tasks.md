## 1. Scraper runtime extraction

- [ ] 1.1 Add **`hosted_agents.scrapers`** module (e.g. **`runtime.py`** / **`base.py`**) implementing shared **`run()`** flow: load **`job.json`**, env checks, cursor store, RAG client, metrics sidecar, bounded **`integration`** label, exit codes
- [ ] 1.2 Define **`ScraperIntegration`** **`Protocol`** (or ABC) with methods for “execute one sync pass” or chunk iterator; document extension points in module docstring
- [ ] 1.3 Refactor **`jira_job`** to use the runtime; keep **`python -m hosted_agents.scrapers.jira_job`** behavior and tests green
- [ ] 1.4 Refactor **`slack_job`** to use the same runtime; keep tests green

## 2. Helm: concurrencyPolicy

- [ ] 1.5 Add optional **`concurrencyPolicy`** under **`scrapers.jira.jobs[]`** and **`scrapers.slack.jobs[]`** in **`values.yaml`** and **`values.schema.json`** (enum **`Forbid`**, **`Allow`**, **`Replace`**); strip from **`job.json`** merge in templates
- [ ] 1.6 Render **`spec.concurrencyPolicy`** on scraper CronJobs defaulting **`Forbid`** when unset
- [ ] 1.7 Extend **`helm/tests/with_scrapers_test.yaml`** (and examples README if examples gain the field)

## 3. Spec promotion and CI

- [ ] 3.1 After implementation, merge deltas **`scraper-base-runtime`** and **`dalc-rag-from-scrapers`** **`[DALC-REQ-RAG-SCRAPERS-005]`** into **`openspec/specs/`**, update **`docs/spec-test-traceability.md`**, cite IDs in pytest/Helm unittest
- [ ] 3.2 Run **`python3 scripts/check_spec_traceability.py`**, **`uv run pytest`**, Helm unittest suites per **`docs/local-ci.md`**

## 4. Housekeeping

- [ ] 4.1 Update **`ADR 0009`** cross-reference or add a short subsection pointing at **`BaseScraper`** / runtime
- [ ] 4.2 Archive **`scrapers-basescraper-concurrency`** when promoted and merged (optional dated **`openspec/changes/archive/`** move)
