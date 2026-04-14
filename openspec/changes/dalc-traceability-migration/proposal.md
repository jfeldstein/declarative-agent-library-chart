## Why

Product naming has moved from **config-first hosted agents (CFHA)** to **Declarative Agent Library Chart (DALC)**. Promoted OpenSpec capabilities still use **`cfha-*` folder names** and **`[CFHA-REQ-…]` / `[CFHA-VER-…]`** requirement IDs across specs, contributor docs, CI, and tests. Aligning **folder names** and **ID prefixes** with DALC removes a permanent second vocabulary and matches the dedicated naming work elsewhere.

## What Changes

- **BREAKING (repository contract):** Rename every promoted capability directory **`openspec/specs/cfha-*`** → **`openspec/specs/dalc-*`** (preserving the suffix after the prefix, e.g. `cfha-agent-o11y-scrape` → `dalc-agent-o11y-scrape`).
- **BREAKING (IDs):** Replace **`CFHA-REQ-`** with **`DALC-REQ-`** and **`CFHA-VER-`** with **`DALC-VER-`** everywhere they denote requirement identifiers—**keeping the same middle slug and three-digit number** (e.g. `[CFHA-REQ-O11Y-SCRAPE-001]` → `[DALC-REQ-O11Y-SCRAPE-001]`) so semantics and ordering stay stable.
- Update **`scripts/check_spec_traceability.py`** regexes, comments, and the optional strict-mode environment variable (e.g. **`DALC_TRACEABILITY_STRICT`**, with a documented transition or short-lived alias for **`CFHA_TRACEABILITY_STRICT`** if needed).
- Update **`docs/spec-test-traceability.md`**, **`docs/adrs/0003-spec-test-traceability.md`**, **`AGENTS.md`**, **`docs/AGENTS.md`**, **`.cursor/rules`**, **`.github/workflows`**, **`ct.yaml`**, **`README.md`**, and all **pytest** / **Helm unittest** artifacts that cite old IDs or spec paths.
- Update **in-repo cross-references** inside spec bodies (e.g. capability names like `cfha-agent-o11y-scrape` → `dalc-agent-o11y-scrape` where they refer to a folder/capability).
- **In scope:** Active `openspec/changes/*` that reference promoted spec paths or IDs should be updated in the same migration PR or in a fast follow so `openspec` and docs do not point at removed paths.
- **Out of scope:** Renaming **historical archived** change trees under `openspec/changes/archive/` unless a broken link forces a mechanical fix; **external** URLs or third-party docs outside the repo.

## Capabilities

### New Capabilities

- None (this is a **rename and ID-prefix migration** of existing normative content).

### Modified Capabilities

All promoted capabilities under `openspec/specs/` today:

- `cfha-requirement-verification` → `dalc-requirement-verification`: Normative ID format, folder naming examples, and cross-references to **[DALC-VER-***]**.
- `cfha-chart-testing-ct` → `dalc-chart-testing-ct`: Requirement IDs and prose that says “CFHA Helm charts.”
- `cfha-helm-unittest` → `dalc-helm-unittest`: Requirement IDs.
- `cfha-agent-o11y-scrape` → `dalc-agent-o11y-scrape`: Requirement IDs.
- `cfha-agent-o11y-logs-dashboards` → `dalc-agent-o11y-logs-dashboards`: Requirement IDs; cross-reference to scrape capability path/name.
- `cfha-rag-from-scrapers` → `dalc-rag-from-scrapers`: Requirement IDs.

## Impact

- **CI:** Traceability checker and any workflow comments/env that mention **CFHA** for IDs.
- **Contributors:** All muscle memory for IDs and paths; ADR 0003 and AGENTS instructions.
- **Downstream:** Forks or automation that grep for **`CFHA-REQ`** or **`openspec/specs/cfha-`** must update in lockstep—document in PR description and development log.
