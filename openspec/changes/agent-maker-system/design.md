## Context

The current agent development process requires manual creation of Helm charts, configuration files, and evaluation suites. This leads to inconsistencies, security risks from improper agent composition, and slow iteration cycles. The agent-maker system automates this process while enforcing safety constraints and maintaining full observability.

## Goals / Non-Goals

**Goals:**

- Natural language requests in #agent-maker channel SHALL automatically create validated PRs
- All agent content SHALL use #agent- prefix convention for bot readability
- Subagent references SHALL be validated for existence, loop prevention, and proper request forwarding
- Evaluation suites SHALL be committed with code and automatically synced to W&B
- Shadow rollouts SHALL be integrated for safe testing
- CI SHALL flag evaluation regressions automatically
- Functionality SHALL be additive-only with no breaking changes

**Non-Goals:**

- RBAC implementation (explicitly out of scope for v1)
- Full natural language understanding beyond "I want an agent that..." patterns
- Automatic deployment approval (PRs require human review)
- Complex multi-agent orchestration beyond subagent references

## Decisions

1. **#agent- Prefix Convention**
   - **Decision**: All bot-readable content SHALL use #agent- prefix (e.g., #agent-config, #agent-eval, #agent-description)
   - **Rationale**: Clear machine-readable boundary, prevents false positives in non-agent channels
   - **Alternatives**: Custom parser without prefixes (higher false positive rate)

2. **Agent-Maker Bot Architecture**
   - **Decision**: Telegram bot listening to #agent-maker channel, parsing "I want an agent that..." patterns, creating PRs with validated templates
   - **Rationale**: Leverages existing communication patterns, minimal friction for developers
   - **Alternatives**: Web interface (higher barrier to entry), email-based (slower feedback)

3. **Subagent Reference Validation**
   - **Decision**: Three-level validation: existence check, loop depth prevention (max 3 levels), request ID correlation
   - **Rationale**: Prevents infinite loops, ensures proper observability, maintains system stability
   - **Alternatives**: No validation (dangerous), manual validation (slow)

4. **Code-Committed Evals**
   - **Decision**: Evaluation suites committed alongside agent code, automatically synced to W&B, versioned with releases
   - **Rationale**: Ensures evaluations evolve with code, provides historical comparison baseline
   - **Alternatives**: External eval store (version drift risk), manual sync (error-prone)

5. **Shadow Rollout Integration**
   - **Decision**: New agents run in shadow mode alongside production, tagged appropriately in W&B
   - **Rationale**: Safe testing without production impact, real-world performance data
   - **Alternatives**: Staging-only testing (less realistic), no testing (dangerous)

6. **Additive-Only Functionality**
   - **Decision**: All changes MUST be additive, no refactoring of existing agent interfaces
   - **Rationale**: Maintains backward compatibility, reduces migration burden
   - **Alternatives**: Breaking changes (high migration cost)

## System Architecture

### High-Level Architecture

```
Telegram #agent-maker Channel
         ↓
   Agent-Maker Bot (Python)
         ↓
   Request Parser & Validator
         ↓
  Template Engine + PR Creator
         ↓
GitHub PR (with validation checks)
         ↓
   CI/CD Pipeline (automated)
         ↓
  Production Deployment (manual)
```

### Data Flow

1. **User Request**: "I want an agent that can analyze customer feedback and route to appropriate teams #agent-customer-feedback"
2. **Bot Processing**: Parse intent, validate against existing agents, check for conflicts
3. **PR Creation**: Generate Helm chart, configuration, evaluation suite, documentation
4. **Validation**: Automated checks for subagent references, loop prevention, security
5. **CI Integration**: Run evaluations, sync to W&B, flag regressions
6. **Deployment**: Manual review and approval, shadow rollout, production promotion

### API Contracts

**Agent-Maker Bot API:**
- Input: Natural language message with #agent- prefix
- Output: GitHub PR with generated files
- Validation: Subagent existence, loop depth, naming conflicts

**Subagent Reference API:**
- Format: `subagent: <agent-name>@<version>`
- Validation: Max depth 3, circular reference prevention
- Correlation: Request ID forwarding through call chain

**W&B Integration API:**
- Evaluation sync: Automatic push of committed eval results
- Version tagging: `agent_version`, `eval_version`, `git_sha`
- Shadow tagging: `rollout_arm: shadow|primary`

### Validation Rules

1. **Naming Convention**: Must match `[a-z0-9-]+` pattern
2. **Subagent Validation**: Referenced agents must exist, max depth 3
3. **Loop Prevention**: No circular references detected
4. **Request ID**: Unique correlation ID generated and forwarded
5. **Security**: No external API calls without explicit approval
6. **Resource Limits**: CPU/memory constraints enforced

### Safety Mechanisms

- **Automatic Timeouts**: All agent operations have configurable timeouts
- **Circuit Breakers**: Failure rate monitoring and automatic isolation
- **Resource Quotas**: Hard limits on CPU, memory, API calls
- **Audit Logging**: Full traceability from user request to agent execution
- **Rollback Protocol**: Automatic rollback on evaluation regression

### Integration with Existing CI/CD

- **Pre-commit Hooks**: Validation of agent configurations
- **CI Pipeline**: Automated testing of generated agents
- **W&B Sync**: Evaluation results automatically uploaded
- **Release Automation**: Versioned evaluations tied to releases
- **Monitoring Integration**: Health checks and performance metrics

### Implementation Roadmap

**Phase 1 (Foundation):**
- #agent- prefix convention established
- Basic agent-maker bot skeleton
- Template system for simple agents
- Basic validation rules

**Phase 2 (Validation):**
- Subagent reference validation
- Loop prevention mechanisms
- Request ID correlation
- Basic CI integration

**Phase 3 (Evaluation):**
- Code-committed eval system
- W&B integration
- Shadow rollout capability
- Regression flagging

**Phase 4 (Optimization):**
- Performance optimizations
- Advanced template varieties
- Enhanced natural language parsing
- Self-improvement mechanisms

## Risks / Trade-offs

- **[Risk] Natural language ambiguity** → **Mitigation**: Structured templates with validation, human review required
- **[Risk] Subagent dependency management** → **Mitigation**: Strict versioning, dependency resolution
- **[Risk] Evaluation quality** → **Mitigation**: Comprehensive test suites, peer review process
- **[Risk] Performance overhead** → **Mitigation**: Efficient validation algorithms, caching
- **[Trade-off] Flexibility vs Safety** → Choose safety with option to override for advanced users

## Migration Plan

1. **Phase 1**: Deploy agent-maker bot in monitoring-only mode
2. **Phase 2**: Enable PR creation for simple agents
3. **Phase 3**: Gradually expand to more complex agent types
4. **Phase 4**: Full integration with existing CI/CD pipeline
5. **Rollback**: Disable bot, manual agent creation process remains available

## Open Questions

- **Template Customization**: How much customization should be allowed in generated agents?
- **Evaluation Standards**: What constitutes a "passing" evaluation suite?
- **Natural Language Scope**: How complex can the "I want an agent that..." patterns be?
- **Versioning Strategy**: How to handle agent version dependencies?
- **Approval Process**: What should the PR review process look like?