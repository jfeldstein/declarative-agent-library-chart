# helm/src

The **Python** project for the Declarative Agent Library chart: package code under [`agent/`](agent/), tests under [`tests/`](tests/), and metadata in `pyproject.toml`, `uv.lock`, and `.python-version`.

The **container image** is built from the repository root with [`helm/src/Dockerfile`](./Dockerfile) (`docker build -f helm/src/Dockerfile … .`), which copies `helm/src/pyproject.toml`, `helm/src/uv.lock`, and `helm/src/agent/` into the image consumed by the Helm library chart in [`helm/chart/`](../chart/).
