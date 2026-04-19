# Design: `dalc-plugin-log-shipping`

## Helm

- **Template:** `_manifest_deployment.tpl` computes `$wantJsonLogs := structuredLogs.json OR plugins.logShipping.enabled` then emits **`HOSTED_AGENT_LOG_FORMAT=json`** when true.
- **Defaults:** `observability.plugins.logShipping.enabled: false` in **`values.yaml`**; schema documents **`enabled`** under **`observability.plugins.logShipping`**.
- **Compatibility:** **`structuredLogs.json: true`** remains sufficient when **`logShipping.enabled`** is false.

## Documentation

- **`docs/observability.md`:** Cross-link plugin toggle with env table; add minimal snippets per collector family for JSON keys **`level`**, **`message`**, **`service`**, **`request_id`**.

## Traceability

- Requirements **`[DALC-REQ-PLUGIN-LOG-SHIPPING-001]`** … **`003`** in **`openspec/specs/dalc-plugin-log-shipping/spec.md`** with matrix + Helm unittest / pytest / docs evidence.
