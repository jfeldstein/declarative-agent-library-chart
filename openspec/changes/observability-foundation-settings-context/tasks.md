## 1. Coverage + foundation tests

- [x] 1.1 Remove `*/observability/*` from `[tool.coverage.run] omit` in `runtime/pyproject.toml`
- [x] 1.2 Add unit tests for `ObservabilitySettings.from_env` and `hosted_agents.observability.run_context`
- [x] 1.3 Confirm `uv run pytest` meets `fail-under` with observability measured

## 2. Follow-ups (optional)

- [ ] 2.1 Tighten coverage on edge branches (operational mapper parsing, etc.) if regressions appear
