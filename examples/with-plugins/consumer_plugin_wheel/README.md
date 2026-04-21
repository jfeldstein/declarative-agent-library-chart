# dalc-consumer-demo

Build with **`uv build`** or **`pip install build && python -m build`** from this directory.

Install the wheel into an image that already contains the **`declarative-agent-library-chart`** runtime (`agent` package).

See **`dalc_consumer_demo/plugin.py`** for a hello-world ``SyncEventBus.subscribe`` example. Event names are defined as **`EventName`** in the runtime at [`helm/src/agent/observability/events/types.py`](../../../helm/src/agent/observability/events/types.py).
