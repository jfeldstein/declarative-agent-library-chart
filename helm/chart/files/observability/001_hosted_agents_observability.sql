-- Application observability tables (correlation, feedback, side-effects, span summaries).
-- Schema is namespaced for shared Postgres clusters. LangGraph checkpoint tables are
-- created separately by langgraph-checkpoint-postgres via PostgresSaver.setup().

CREATE SCHEMA IF NOT EXISTS hosted_agents;

CREATE TABLE IF NOT EXISTS hosted_agents.slack_correlation (
  channel_id TEXT NOT NULL,
  message_ts TEXT NOT NULL,
  tool_call_id TEXT NOT NULL,
  run_id TEXT NOT NULL,
  thread_id TEXT NOT NULL,
  checkpoint_id TEXT,
  tool_name TEXT NOT NULL,
  wandb_run_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (channel_id, message_ts)
);

CREATE INDEX IF NOT EXISTS ix_slack_correlation_run
  ON hosted_agents.slack_correlation (run_id);

CREATE INDEX IF NOT EXISTS ix_slack_correlation_thread
  ON hosted_agents.slack_correlation (thread_id);

CREATE TABLE IF NOT EXISTS hosted_agents.human_feedback (
  id BIGSERIAL PRIMARY KEY,
  dedupe_key TEXT,
  registry_id TEXT NOT NULL,
  schema_version TEXT NOT NULL,
  label_id TEXT NOT NULL,
  tool_call_id TEXT NOT NULL,
  checkpoint_id TEXT,
  run_id TEXT NOT NULL,
  thread_id TEXT NOT NULL,
  feedback_source TEXT NOT NULL,
  agent_id TEXT,
  created_at TIMESTAMPTZ NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_human_feedback_dedupe
  ON hosted_agents.human_feedback (dedupe_key)
  WHERE dedupe_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_human_feedback_run
  ON hosted_agents.human_feedback (run_id);

CREATE INDEX IF NOT EXISTS ix_human_feedback_tool_call
  ON hosted_agents.human_feedback (tool_call_id);

CREATE INDEX IF NOT EXISTS ix_human_feedback_created
  ON hosted_agents.human_feedback (created_at DESC);

CREATE TABLE IF NOT EXISTS hosted_agents.orphan_reaction (
  id BIGSERIAL PRIMARY KEY,
  channel_id TEXT NOT NULL,
  message_ts TEXT NOT NULL,
  reason TEXT NOT NULL,
  raw_event_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_orphan_channel_ts
  ON hosted_agents.orphan_reaction (channel_id, message_ts);

CREATE TABLE IF NOT EXISTS hosted_agents.side_effect_checkpoint (
  id BIGSERIAL PRIMARY KEY,
  checkpoint_id TEXT NOT NULL UNIQUE,
  run_id TEXT NOT NULL,
  thread_id TEXT NOT NULL,
  tool_call_id TEXT NOT NULL,
  tool_name TEXT NOT NULL,
  external_ref JSONB NOT NULL DEFAULT '{}',
  created_at DOUBLE PRECISION NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_side_effect_thread
  ON hosted_agents.side_effect_checkpoint (thread_id);

CREATE INDEX IF NOT EXISTS ix_side_effect_run
  ON hosted_agents.side_effect_checkpoint (run_id);

CREATE INDEX IF NOT EXISTS ix_side_effect_tool_call
  ON hosted_agents.side_effect_checkpoint (tool_call_id);

CREATE TABLE IF NOT EXISTS hosted_agents.tool_span_summary (
  id BIGSERIAL PRIMARY KEY,
  tool_call_id TEXT NOT NULL,
  run_id TEXT NOT NULL,
  thread_id TEXT NOT NULL,
  tool_name TEXT NOT NULL,
  duration_ms INTEGER NOT NULL,
  outcome TEXT NOT NULL,
  args_hash TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_span_run
  ON hosted_agents.tool_span_summary (run_id);

CREATE INDEX IF NOT EXISTS ix_span_tool_call
  ON hosted_agents.tool_span_summary (tool_call_id);

CREATE INDEX IF NOT EXISTS ix_span_created
  ON hosted_agents.tool_span_summary (created_at DESC);
