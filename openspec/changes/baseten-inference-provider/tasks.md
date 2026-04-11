## 1. Configuration and types

- [ ] 1.1 Add runtime config fields for inference provider (`none` | `baseten`), BaseTen `baseUrl`, `model` (or deployment id), and validation rules (required fields when provider is `baseten`)
- [ ] 1.2 Define env var names and document them alongside existing `HOSTED_AGENT_*` conventions in code comments or README (no new markdown file unless repo already expects one)

## 2. Helm chart

- [ ] 2.1 Add `values.yaml` subtree for inference (provider, baseten URL/model, secret name + key for API token) with safe defaults preserving current behavior
- [ ] 2.2 Update `values.schema.json` with descriptions; ensure API key is Secret-backed only
- [ ] 2.3 Wire `deployment.yaml` (and any helpers) to set env from values and `secretKeyRef` for the token

## 3. Runtime inference client

- [ ] 3.1 Implement OpenAI-compatible chat completion call path (SDK or `httpx`) using configured `baseUrl`, model, and auth header from env
- [ ] 3.2 Integrate with the code path that currently returns subagent text (e.g. replace or branch from `trigger_reply_text` when provider is `baseten`), preserving deterministic behavior when disabled
- [ ] 3.3 Map remote failures to appropriate HTTP errors without leaking secrets; avoid logging tokens

## 4. Tests and dependencies

- [ ] 4.1 Add unit tests with mocked HTTP or patched client covering success and error responses per `baseten-inference` spec
- [ ] 4.2 Add or bump Python dependencies in `pyproject.toml` / lockfile if using `openai` or similar; run full runtime test suite

## 5. Documentation

- [ ] 5.1 Document operator steps: create Secret, set values, expected BaseTen URL shape, and troubleshooting (401/timeout) in existing README or chart README as appropriate for this repo
