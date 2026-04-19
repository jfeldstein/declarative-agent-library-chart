"""Scheduled scraper entrypoints (invoked from CronJob or locally).

Integration modules (``jira_job``, ``slack_job``) fetch and normalize remote data into
embed payloads; shared RAG ingestion and metrics lifecycle live in ``base``.

Maintainers: when adding a scraper type, wire it in Helm (``scraper-cronjobs.yaml`` /
``scraper-job-configmaps.yaml`` under ``scrapers.jira`` / ``scrapers.slack``), document
all Helm/env knobs in ``examples/with-scrapers/``, extend ``grafana/dalc-overview.json``
for new metrics, and follow the checklist in ``metrics.py``.
"""
