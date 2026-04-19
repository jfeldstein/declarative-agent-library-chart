# Agent image — Python project under helm/src/ (flattened: ./agent at project root).
# Build from repository root (Skaffold / DevSpace use this context):
#   docker build -f helm/src/Dockerfile -t declarative-agent-library-chart:local .
# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1
COPY helm/src/pyproject.toml helm/src/uv.lock ./
COPY helm/src/agent ./agent
# Optional extra `wandb` enables W&B when HOSTED_AGENT_WANDB_ENABLED is set.
RUN uv sync --frozen --no-dev --extra wandb --extra postgres
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8088
CMD ["uvicorn", "agent.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8088"]
