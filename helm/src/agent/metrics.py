"""Compatibility exports for Prometheus ``dalc_*`` metrics (implementation in observability plugin).

Traceability: [DALC-REQ-TOKEN-MET-001] [DALC-REQ-TOKEN-MET-002] [DALC-REQ-TOKEN-MET-003]
[DALC-REQ-TOKEN-MET-004] [DALC-REQ-TOKEN-MET-005] [DALC-REQ-TOKEN-MET-006]
[DALC-REQ-SLACK-TOOLS-006] [DALC-REQ-SLACK-TRIGGER-005] [DALC-REQ-JIRA-TRIGGER-005]
"""

from __future__ import annotations

from agent.observability.metric_semantics import BinaryResult, TriggerResult
from agent.observability.plugins.prometheus import (
    DALC_TOOL_CALLS_DURATION,
    DALC_TOOL_CALLS_TOTAL,
    DALC_TRIGGER_REQUESTS,
    observe_http_trigger,
    observe_llm_completion_metrics,
    observe_llm_time_to_first_token,
    observe_skill_load,
    observe_subagent,
    observe_tool_call,
    observe_trigger_http_payloads,
    observe_trigger_inbound,
    llm_metric_label_values,
    tagify_metric_label,
)

# Stable names referenced by Slack/Jira trigger tests (unified trigger counter).
SLACK_TRIGGER_INBOUND = DALC_TRIGGER_REQUESTS
JIRA_TRIGGER_INBOUND = DALC_TRIGGER_REQUESTS

__all__ = (
    "BinaryResult",
    "DALC_TOOL_CALLS_DURATION",
    "DALC_TOOL_CALLS_TOTAL",
    "DALC_TRIGGER_REQUESTS",
    "JIRA_TRIGGER_INBOUND",
    "SLACK_TRIGGER_INBOUND",
    "TriggerResult",
    "llm_metric_label_values",
    "observe_http_trigger",
    "observe_llm_completion_metrics",
    "observe_llm_time_to_first_token",
    "observe_skill_load",
    "observe_subagent",
    "observe_tool_call",
    "observe_trigger_http_payloads",
    "observe_trigger_inbound",
    "tagify_metric_label",
)
