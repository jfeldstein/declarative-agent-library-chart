"""Scheduled scraper entrypoints (invoked from CronJob or locally).

Maintainers: when adding a scraper type, wire it in Helm (``scraper-cronjobs.yaml`` via ``integration`` or
``name: reference``), document
all Helm/env knobs in ``examples/with-scrapers/``, extend ``grafana/dalc-agent-overview.json``
for new metrics, and follow the checklist in ``metrics.py``.
"""
