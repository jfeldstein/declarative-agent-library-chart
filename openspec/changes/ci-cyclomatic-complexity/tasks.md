## 1. Baseline and configuration

- 1.1 From `**helm/src**`, run `**ruff check hosted_agents tests**` and trial `**extend-select = ["C901"]**` with candidate `**[tool.ruff.lint.mccabe]**` `max-complexity` values until violations are zero or an explicit per-function `**# noqa: C901**` strategy is documented for rare exceptions.
- 1.2 Add `**complexipy**` to `**helm/src/pyproject.toml**` dev dependencies; add `**[tool.complexipy]**` with `**paths**`, `**max-complexity-allowed**`, and `**exclude**` as needed; run `**uv run complexipy**` (or equivalent) locally and tune thresholds or introduce a **snapshot** workflow per `**design.md`** if the tree cannot meet strict defaults immediately.
- 1.3 Document in `**pyproject.toml**` (short comments) or minimal contributor note how **Ruff `C901`** vs **complexipy** differ so contributors know why both run.

## 2. CI workflow

- 2.1 Update `**.github/workflows/ci.yml`** Python job: ensure `**ruff check**` uses the new config (no extra flags that bypass project config unless justified); add a step to run **complexipy** with the same `**helm/src`** working directory and failing exit behavior as local `**uv run**`.
- 2.2 If using **complexipy** SARIF or artifacts, add upload steps optionally; otherwise keep the minimal failing gate only.

## 3. Spec promotion and traceability (on archive / when promoting)

- 3.1 When promoting `**dalc-python-complexity-ci`** to `**openspec/specs/**`, assign stable IDs per `**dalc-requirement-verification**`, update `**docs/spec-test-traceability.md**`, and add pytest or CI evidence citations per **[DALC-VER-002]** (implementation change may add a small test or document workflow evidence—follow `**scripts/check_spec_traceability.py`**).

## 4. Verification

- 4.1 Run `**uv sync --all-groups**` and `**uv run ruff check**` / `**uv run pytest**` from `**helm/src**`; confirm CI-equivalent commands pass on a clean tree.
- 4.2 Run `**python3 scripts/check_spec_traceability.py**` if `**docs/spec-test-traceability.md**` or promoted specs are touched in the same change set.

## 5. Ratchet (one metric step per task)

**Rule:** each task below changes **exactly one** committed cap in `**helm/src/pyproject.toml`**—either `**[tool.ruff.lint.mccabe] max-complexity**` (McCabe / Ruff `**C901**`) **or** `**[tool.complexipy] max-complexity-allowed`** (cognitive)—by **exactly −1**. Then refactor or narrowly justify exceptions until `**/fix`** parity is green: from repo root follow `**docs/local-ci.md**` ( `**helm/src**`: `uv sync --all-groups`, `uv run ruff check hosted_agents tests`, `uv run complexipy`, `uv run pytest tests/`; `**python3 scripts/check_spec_traceability.py**` if specs/matrix change; `**./scripts/check_adr_numbers.sh**`; example `**helm unittest**` loop + `**ct lint --config ct.yaml --all**`).

**Targets after this ladder:** McCabe **10** (Ruff default culture), complexipy **15** (upstream default culture). Do **not** raise caps in the same task as a ratchet step.

- 5.1 **McCabe `max-complexity`**: **25 → 24**; then `**/fix`** until green.
- 5.2 **complexipy `max-complexity-allowed`**: **40 → 39**; then `**/fix`** until green.
- ~~5.3 **McCabe**: **24 → 23**; then `**/fix`** until green.~~ (split `create_app` into `_register_*` route helpers)
- ~~5.4 **complexipy**: **39 → 38**; then `**/fix`** until green.~~ (cap only; peak cognitive already under 38)
- ~~5.5 **McCabe**: **23 → 22**; then `**/fix`** until green.~~ (cap only; peak McCabe 14)
- 5.6 **complexipy**: **38 → 37**; then `**/fix`** until green.
- 5.7 **McCabe**: **22 → 21**; then `**/fix`** until green.
- 5.8 **complexipy**: **37 → 36**; then `**/fix`** until green.
- 5.9 **McCabe**: **21 → 20**; then `**/fix`** until green.
- 5.10 **complexipy**: **36 → 35**; then `**/fix`** until green.
- 5.11 **McCabe**: **20 → 19**; then `**/fix`** until green.
- 5.12 **complexipy**: **35 → 34**; then `**/fix`** until green.
- 5.13 **McCabe**: **19 → 18**; then `**/fix`** until green.
- 5.14 **complexipy**: **34 → 33**; then `**/fix`** until green.
- 5.15 **McCabe**: **18 → 17**; then `**/fix`** until green.
- 5.16 **complexipy**: **33 → 32**; then `**/fix`** until green.
- 5.17 **McCabe**: **17 → 16**; then `**/fix`** until green.
- 5.18 **complexipy**: **32 → 31**; then `**/fix`** until green.
- 5.19 **McCabe**: **16 → 15**; then `**/fix`** until green.
- 5.20 **complexipy**: **31 → 30**; then `**/fix`** until green.
- 5.21 **McCabe**: **15 → 14**; then `**/fix`** until green.
- 5.22 **complexipy**: **30 → 29**; then `**/fix`** until green.
- 5.23 **McCabe**: **14 → 13**; then `**/fix`** until green.
- 5.24 **complexipy**: **29 → 28**; then `**/fix`** until green.
- 5.25 **McCabe**: **13 → 12**; then `**/fix`** until green.
- 5.26 **complexipy**: **28 → 27**; then `**/fix`** until green.
- 5.27 **McCabe**: **12 → 11**; then `**/fix`** until green.
- 5.28 **complexipy**: **27 → 26**; then `**/fix`** until green.
- 5.29 **McCabe**: **11 → 10**; then `**/fix`** until green.
- 5.30 **complexipy**: **26 → 25**; then `**/fix`** until green.
- 5.31 **complexipy**: **25 → 24**; then `**/fix`** until green.
- 5.32 **complexipy**: **24 → 23**; then `**/fix`** until green.
- 5.33 **complexipy**: **23 → 22**; then `**/fix`** until green.
- 5.34 **complexipy**: **22 → 21**; then `**/fix`** until green.
- 5.35 **complexipy**: **21 → 20**; then `**/fix`** until green.
- 5.36 **complexipy**: **20 → 19**; then `**/fix`** until green.
- 5.37 **complexipy**: **19 → 18**; then `**/fix`** until green.
- 5.38 **complexipy**: **18 → 17**; then `**/fix`** until green.
- 5.39 **complexipy**: **17 → 16**; then `**/fix`** until green.
- 5.40 **complexipy**: **16 → 15**; then `**/fix`** until green.