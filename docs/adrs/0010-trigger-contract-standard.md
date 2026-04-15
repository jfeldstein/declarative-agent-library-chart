# ADR 0010: Trigger contract standard

## Status

Accepted

## Context

Hosted agents need one clear way to **start a run** from operators and from **inbound product bridges** (Slack `app_mention`, Jira webhooks). Those bridges differ in transport and verification, but the **execution semantics** should match what an operator gets from the HTTP trigger API so supervisor graphs, tools, and observability stay consistent.

OpenSpec captures this split explicitly: **`slack-trigger`** and **`jira-trigger`** describe inbound normalization into the same trigger outcome as **`POST /api/v1/trigger`**, while **`slack-tools`** / **`jira-tools`** cover LLM-time outbound actions and must stay separate from both **scrapers** (scheduled RAG ingestion) and **trigger-only** secrets.

## Decision

1. **Canonical programmatic entry**  
   **`POST /api/v1/trigger`** is the normative HTTP entry for starting a hosted agent run. As implemented, the handler parses a JSON object into **`TriggerBody`**, resolves **`thread_id`** (body and/or documented headers), builds **`TriggerContext`** (runtime config, observability settings, ids, optional tenant header), and invokes **`run_trigger_graph`** — see `helm/src/hosted_agents/app.py`, `helm/src/hosted_agents/agent_models.py`, `helm/src/hosted_agents/trigger_context.py`, and `helm/src/hosted_agents/trigger_graph.py`.

2. **Request shape (as implemented, not prescriptive beyond code)**  
   The JSON body is validated by **`TriggerBody`**: optional **`message`**, **`load_skill`**, **`tool`** / **`tool_arguments`**, **`thread_id`**, and **`ephemeral`**, with **`extra="forbid"`** on the model. The legacy **`subagent`** field is rejected before validation. Thread identity may also be supplied via headers as implemented in **`_resolve_thread_id`**. For the exact fields, defaults, and limits, treat **`helm/src/hosted_agents/agent_models.py`** and **`app.py`** as source of truth; OpenSpec changes under **`openspec/changes/slack-trigger/`** and **`openspec/changes/jira-bot/`** (e.g. **`jira-trigger`**) describe how external events must map into **`TriggerBody.message`** and related context.

3. **Inbound `*-trigger` bridges**  
   Slack and Jira trigger integrations **SHALL** verify the transport per their OpenSpec requirements, **SHALL NOT** treat trigger forwarding as managed RAG ingestion by default (no **`POST /v1/embed`** as part of the trigger step unless a future change explicitly requires it), and **SHALL** keep Helm/env configuration **documented as disjoint** from **`scrapers`** and from **`*-tools`** credential surfaces — see **`openspec/changes/slack-trigger/proposal.md`**, **`openspec/changes/slack-trigger/specs/slack-trigger/spec.md`**, **`openspec/changes/jira-bot/proposal.md`**, and **`openspec/changes/jira-bot/specs/jira-trigger/spec.md`**.

4. **Single pipeline entry**  
   Inbound bridges **SHALL** achieve the **same functional outcome** as **`POST /api/v1/trigger`** / **`run_trigger_graph`** (internal call or documented equivalent), per the OpenSpec language above. **`trigger_graph.py`** documents the graph as the pipeline for that launch path.

5. **Extensibility**  
   Future inbound triggers **SHOULD** normalize into the same internal contract (**`TriggerBody`** + **`TriggerContext`** / **`run_trigger_graph`**) so verification and transport stay at the edge and the LangGraph pipeline remains one place to evolve behavior.

## Consequences

- New triggers are specified and tested against **verification**, **payload mapping**, and **non-ingestion** expectations in OpenSpec, not by duplicating supervisor logic on side routes.
- Operators can reason about **three lanes**: **trigger in**, **tools out during a run**, and **scrapers** to RAG — with separate config keys as those changes require.
- Any evolution of the HTTP JSON contract requires updating **`TriggerBody`**, **`app.py`**, tests, and the relevant OpenSpec specs together; this ADR does not freeze field names beyond “follow implementation + specs.”
