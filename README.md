# Declarative Agent Library Chart

<!-- Traceability: [DALC-REQ-HELM-UNITTEST-003] [DALC-REQ-CHART-CT-002] [DALC-REQ-O11Y-LOGS-004] -->

This repo is a Helm library chart. Add it as a dependency in `Chart.yaml`, and build your agent by configuring `values.yaml`.

## Examples

### hello-world

To make an agentic Slack bot, you need:

1. Chart.yaml:

    ```yaml
    dependencies:
      - name: declarative-agent-library-chart
        version: 0.1.0
        repository: https://github.com/jfeldstein/declarative-agent-library-chart
        alias: agent
    ```

2. and a values.yaml:

    ```yaml
    agent:
      systemPrompt: |
        Respond, "Hello :wave:"
      presence:
        slackBotId:
          secretName: slack-bot-token
          secretKey: token
    ```

3. Register your bot on Slack

You can now deploy the chart, and @-tag your bot on slack. That's it.

(See [hello-world example](examples/hello-world) for more details.)

### More examples

See the [examples](examples) directory for more examples.

## Architecture

```
+-----------------------------------------------------------------------------+
|                                        |                                    |
|              THE HARNESS               |              THE AGENT             |
|   (HTTP triggers, sources of context)  |  (harness, tools, RLHF / feedback) |
|                                        |                                    |
+-----------------------------------------------------------------------------+
|                                                                             |
|                                       IaC                                   |
|                                                                             |
+-----------------------------------------------------------------------------+
```

### Subcomponents

```
+-------------------------------------------------------------------+
| THE HARNESS                     | AGENTIC                         |
|  + Sources of context           |  + Agent (system prompt,        |
|    (scrapers / ETL -> RAG,      |    config, subagents, skills,   |
|    entities/relationships)      |    chat model, checkpoints,     |
|                                 |    W&B, etc.)                   |
|  + Workflow triggers (webhooks, |  + Tools:                       |
|    bridges, cron->HTTP) ->      |    | RAG (zero-config)          |
|    everything routes to         |    | Built-in (Jira, Slack, …)  |
|    POST /trigger endpoint       |    | Extendable (in your chart) |
|                                 |  + RLHF / feedback (persistence |
|                                 |    & telemetry, experience lib) |
+----------------------------------+--------------------------------+
| IaC                                                               |
| + K8s Resources                                                   |
| + Observability (everything exports metrics, dashboards OOTB)     |
+-------------------------------------------------------------------+
```

### Layout

| Path                        | Purpose                                                      |
|-----------------------------|--------------------------------------------------------------|
| `helm/chart/`               | Declarative Agent Library Helm chart (**`type: library`**; render via parent `templates/agent.yaml` + `declarative-agent.system`) |
| `helm/src/hosted_agents/`   | Python app: FastAPI entry, trigger logic, RAG, scrapers      |
| `examples/hello-world/`     | Minimal example chart, uses the agent subchart               |


## Features:

1. **Baseline observability without writing instrumentation**: the scrapers, agent, and RAG all expose Prometheus metrics, structured logging hooks, and request correlation. 
2. **Zero-config RAG**: the chart deploys a managed RAG HTTP service when you enable scraper jobs.

## Configuration (values.yaml)

Values keys under the **`agent`** subchart (Helm dependency **`alias: agent`**; chart **`name: declarative-agent-library-chart`**) configure these runtime surfaces:

| Values key | Role |
|------------|------|
| `scrapers.X` | **CronJobs** (one per enabled job) push normalized content into RAG. If **at least one** scraper is enabled, the chart deploys the **managed RAG HTTP** Deployment + Service — see [docs/rag-http-api.md](docs/rag-http-api.md). |
| `scrapers.ragService` | Sane by default, but you can tune resource requests.|
| `tools` | Enable tools by name to make them available to the agent. Out of the box, the chart offers: [TODO: list tools]|
| `subagents` | JSON list of specialists compiled into **LangGraph subgraphs** and registered as **LangChain tools** on the root agent ([LangChain subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents)). **Recommended:** **`description`** for each entry (tool schema text). 
| `skills` | JSON catalog `{ "name", "prompt", "extraTools"? }` — load with **`POST /api/v1/trigger`** and `{"load_skill":"<name>"}` (progressive disclosure; aligns with [LangChain Skills](https://docs.langchain.com/oss/python/langchain/multi-agent/skills)). |
| `chatModel` | LiteLLM-compatible model id to be used for the agent(s). |
