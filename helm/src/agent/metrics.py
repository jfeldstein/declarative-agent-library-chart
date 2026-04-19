"""Compatibility exports for Prometheus ``dalc_*`` metrics (implementation in observability plugin).

Traceability: [DALC-REQ-TOKEN-MET-001] [DALC-REQ-TOKEN-MET-002] [DALC-REQ-TOKEN-MET-003]
[DALC-REQ-TOKEN-MET-004] [DALC-REQ-TOKEN-MET-005] [DALC-REQ-TOKEN-MET-006]
[DALC-REQ-SLACK-TOOLS-006] [DALC-REQ-SLACK-TRIGGER-005] [DALC-REQ-JIRA-TRIGGER-005]
"""

from __future__ import annotations

from agent.observability.metric_semantics import BinaryResult, TriggerResult
from agent.observability.plugins.prometheus import (
    DALC_TRIGGER_REQUESTS,
    observe_http_trigger,
    observe_jira_trigger_inbound,
    observe_llm_completion_metrics,
    observe_llm_time_to_first_token,
    observe_mcp_tool,
    observe_skill_load,
    observe_slack_tool_api,
    observe_slack_trigger_inbound,
    observe_subagent,
    observe_trigger_http_payloads,
    llm_metric_label_values,
    tagify_metric_label,
)

# Stable names referenced by Slack/Jira trigger tests (unified trigger counter).
SLACK_TRIGGER_INBOUND = DALC_TRIGGER_REQUESTS
JIRA_TRIGGER_INBOUND = DALC_TRIGGER_REQUESTS

__all__ = (
    "BinaryResult",
    "DALC_TRIGGER_REQUESTS",
    "JIRA_TRIGGER_INBOUND",
    "SLACK_TRIGGER_INBOUND",
    "TriggerResult",
    "llm_metric_label_values",
    "observe_http_trigger",
    "observe_jira_trigger_inbound",
    "observe_llm_completion_metrics",
    "observe_llm_time_to_first_token",
    "observe_mcp_tool",
    "observe_skill_load",
    "observe_slack_tool_api",
    "observe_slack_trigger_inbound",
    "observe_subagent",
    "observe_trigger_http_payloads",
    "tagify_metric_label",
)
