# Build from project root: docker build -t config-first-hosted-agents:local .
# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1
COPY runtime/pyproject.toml runtime/uv.lock ./
COPY runtime/src ./src
# Optional extra `wandb` enables W&B when HOSTED_AGENT_WANDB_ENABLED is set.
# WITH_WANDB=0 yields a smaller image (kind integration / CI load into the cluster).
ARG WITH_WANDB=1
RUN if [ "${WITH_WANDB}" = "1" ]; then \
      uv sync --frozen --no-dev --extra wandb; \
    else \
      uv sync --frozen --no-dev; \
    fi
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8088
CMD ["uvicorn", "hosted_agents.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8088"]
