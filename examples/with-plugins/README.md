# with-plugins example

Demonstrates **`observability.plugins.consumerPlugins`** as a **YAML list of entry-point names** (non-empty ⇒ enabled). Each name must exist under **`[project.entry-points."declarative_agent.observability_plugins"]`** in an **installed** Python distribution (typically a wheel baked into your agent image).

## Aftermarket wheel (`consumer_plugin_wheel/`)

This folder contains a minimal **`pyproject.toml`** plus package **`dalc_consumer_demo`** that registers **`with-plugins-demo`**.

Build a wheel from the repo root:

```bash
cd examples/with-plugins/consumer_plugin_wheel
uv build
# or: pip install build && python -m build
```

Install into the agent image (Dockerfile sketch):

```dockerfile
COPY examples/with-plugins/consumer_plugin_wheel/dist/*.whl /tmp/
RUN pip install --no-deps /tmp/dalc_consumer_demo-*.whl
```

The runtime image must already include **`declarative-agent-library-chart`** (this repo’s **`helm/src`** package); the demo wheel only adds the entry point.

See **`dalc_consumer_demo/plugin.py`** for hook signatures and links to library types (`ObservabilityPluginsConfig`, `SyncEventBus`, `EventName`, etc.).
