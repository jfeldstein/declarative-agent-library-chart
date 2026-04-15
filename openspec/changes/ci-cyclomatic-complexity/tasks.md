## 1. Baseline and configuration

- [ ] 1.1 From **`helm/src`**, run **`ruff check hosted_agents tests`** and trial **`extend-select = ["C901"]`** with candidate **`[tool.ruff.lint.mccabe]`** `max-complexity` values until violations are zero or an explicit per-function **`# noqa: C901`** strategy is documented for rare exceptions.
- [ ] 1.2 Add **`complexipy`** to **`helm/src/pyproject.toml`** dev dependencies; add **`[tool.complexipy]`** with **`paths`**, **`max-complexity-allowed`**, and **`exclude`** as needed; run **`uv run complexipy`** (or equivalent) locally and tune thresholds or introduce a **snapshot** workflow per **`design.md`** if the tree cannot meet strict defaults immediately.
- [ ] 1.3 Document in **`pyproject.toml`** (short comments) or minimal contributor note how **Ruff `C901`** vs **complexipy** differ so contributors know why both run.

## 2. CI workflow

- [ ] 2.1 Update **`.github/workflows/ci.yml`** Python job: ensure **`ruff check`** uses the new config (no extra flags that bypass project config unless justified); add a step to run **complexipy** with the same **`helm/src`** working directory and failing exit behavior as local **`uv run`**.
- [ ] 2.2 If using **complexipy** SARIF or artifacts, add upload steps optionally; otherwise keep the minimal failing gate only.

## 3. Spec promotion and traceability (on archive / when promoting)

- [ ] 3.1 When promoting **`dalc-python-complexity-ci`** to **`openspec/specs/`**, assign stable IDs per **`dalc-requirement-verification`**, update **`docs/spec-test-traceability.md`**, and add pytest or CI evidence citations per **[DALC-VER-002]** (implementation change may add a small test or document workflow evidence—follow **`scripts/check_spec_traceability.py`**).

## 4. Verification

- [ ] 4.1 Run **`uv sync --all-groups`** and **`uv run ruff check`** / **`uv run pytest`** from **`helm/src`**; confirm CI-equivalent commands pass on a clean tree.
- [ ] 4.2 Run **`python3 scripts/check_spec_traceability.py`** if **`docs/spec-test-traceability.md`** or promoted specs are touched in the same change set.
