# helm/src

The OpenSpec layout calls for runtime source under `helm/src/`. In this repo the **Python implementation** lives under [`runtime/src/hosted_agents/`](../../runtime/src/hosted_agents/) (`runtime/` holds `pyproject.toml`, `uv.lock`, and `tests/`).

The **container image** ([`Dockerfile`](../../Dockerfile) at project root) copies `runtime/pyproject.toml`, `runtime/uv.lock`, and `runtime/src/` into the image consumed by the Helm library chart in [`helm/chart/`](../chart/).
