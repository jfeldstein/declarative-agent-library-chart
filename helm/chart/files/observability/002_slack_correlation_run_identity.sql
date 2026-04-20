-- ADR 0016: persist neutral run identity on Slack message correlation for async feedback.
-- Mirror: helm/src/agent/migrations/002_slack_correlation_run_identity.sql
ALTER TABLE hosted_agents.slack_correlation
  ADD COLUMN IF NOT EXISTS run_identity JSONB;
