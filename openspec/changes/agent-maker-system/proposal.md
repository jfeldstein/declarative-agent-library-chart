## Why

We need a systematic way to create, validate, and deploy new agents while maintaining safety, composability, and observability. The current manual process for agent creation is error-prone and doesn't scale. An agent-maker system that listens to natural language requests, creates validated PRs, and integrates with our existing evaluation infrastructure will accelerate development while maintaining quality standards.

## What Changes

- Introduce **#agent-** prefix convention for bot-readable content across all channels
- Create **agent-maker bot** that listens to #agent-maker channel and automatically creates PRs for "I want an agent that..." requests
- Implement **subagent reference system** with validation, loop depth prevention, and request ID forwarding
- Establish **code-committed evals** with W&B integration and shadow rollouts
- Ensure **additive-only functionality** and composability requirements
- RBAC considerations explicitly out of scope for v1

## Capabilities

### New Capabilities

- `agent-prefix-convention`: Standard #agent- prefix for bot-readable content across all communication channels
- `agent-maker-bot`: Telegram bot that listens to #agent-maker channel, parses requests, and creates validated PRs
- `subagent-reference-system`: Validation, loop depth prevention, and request ID forwarding for agent composition
- `code-committed-evals`: Evaluation suites committed with code, synced to W&B, with versioned evaluations tied to releases
- `shadow-rollout-integration`: Safe testing of new agents alongside production systems
- `ci-delta-flagging`: CI integration that flags evaluation regressions

### Modified Capabilities

- `declarative-agent-library-chart`: Enhanced to support agent-maker generated configurations and subagent references
- `wandb-agent-traces`: Extended to include agent-maker metadata and evaluation results
- `runtime-langgraph-checkpoints`: Enhanced to support subagent request correlation

## Impact

- **Development Velocity**: Dramatically reduces time from idea to deployed agent
- **Quality**: Automated validation prevents common errors in agent composition
- **Observability**: Full traceability from user request to deployed agent
- **Safety**: Loop prevention and validation rules maintain system stability
- **Integration**: Seamless integration with existing W&B, CI/CD, and monitoring infrastructure
- **Backward Compatibility**: Additive-only changes ensure no breaking changes to existing agents