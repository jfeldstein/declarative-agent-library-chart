# helm/src

The OpenSpec layout places the **Python implementation** in this directory: package code under [`src/hosted_agents/`](src/hosted_agents/), tests under [`tests/`](tests/), and project metadata in `pyproject.toml` / `uv.lock` / `.python-version`.

The **container image** ([`Dockerfile`](../../Dockerfile) at project root) copies `helm/src/pyproject.toml`, `helm/src/uv.lock`, and `helm/src/src/` into the image consumed by the Helm library chart in [`helm/chart/`](../chart/).
