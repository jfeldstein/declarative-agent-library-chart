## 1. Runtime: custom tool registration

- [ ] 1.1 Add startup hook (env-driven importable module) that merges custom tool ids into `REGISTERED_MCP_TOOL_IDS` and dispatch maps before app startup
- [ ] 1.2 Ensure LangChain MCP bindings recognize dynamically registered ids or document escape hatch parity with skill-unlocked tools
- [ ] 1.3 Add unit tests covering registration, allowlist denial without `mcp.enabledTools`, and successful invocation when allowlisted

## 2. Helm chart contract

- [ ] 2.1 Document new env var(s) in `helm/chart/values.yaml` comments and extend `values.schema.json` if first-class keys are introduced for mounts or registration
- [ ] 2.2 Wire registration env through `_manifest_deployment.tpl` when values supply it (or rely on `extraEnv` only—pick one consistent approach and document)

## 3. Example application chart

- [ ] 3.1 Create `examples/with_custom_components/` with `Chart.yaml` (dependency `alias: agent`), `values.yaml`, `templates/agent.yaml` (`declarative-agent.system`), and `Chart.lock` via `helm dependency build`
- [ ] 3.2 Add minimal custom Python package in the repo (or Dockerfile path) consumed by the example image build path documented in README—at least one custom tool id demonstrably registered
- [ ] 3.3 Add example `CronJob` (or Helm template fragment) for a custom scraper module using `RAG_SERVICE_URL` and README notes per **[DALC-REQ-APP-CUSTOM-004]**
- [ ] 3.4 Document trigger composition pattern (parent-owned Deployment/Service or forward to `/api/v1/trigger`) per **[DALC-REQ-APP-CUSTOM-003]**

## 4. CI, tests, and traceability prep

- [ ] 4.1 Add `helm/tests/` suite for `with_custom_components` mirroring other examples; extend `.github/workflows/ci.yml` if required
- [ ] 4.2 Run `uv run pytest` for new Python tests and `helm unittest` locally
- [ ] 4.3 After promotion of specs to `openspec/specs/`, update `docs/spec-test-traceability.md`, add pytest/helm unittest evidence IDs, and run `python3 scripts/check_spec_traceability.py`

## 5. Documentation

- [ ] 5.1 Update `examples/README.md` (and root README examples table if present) to list **`with_custom_components`**
- [ ] 5.2 Add short cross-link from `ARCHITECTURE.md` or chart README if that is where extension expectations are summarized today
