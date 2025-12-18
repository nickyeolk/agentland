# AgentLand

Production-ready multi-agent customer support system with comprehensive observability, evaluation, and monitoring.

## Features

- **Multi-Agent System**: 5 specialized agents (Triage, Billing, Technical, Account, Escalation)
- **Custom State Machine**: Production-ready orchestration (LangGraph-compatible design)
- **Comprehensive Observability**: OpenTelemetry traces, Structlog JSON logs, Prometheus metrics
- **DeepEval Integration**: Industry-standard LLM evaluation with built-in metrics
- **FastAPI Backend**: Async API with automatic documentation
- **Production-Ready**: Error handling, retries, rate limiting, health checks

## Quick Start

### 1. Install Dependencies

```bash
make install-dev
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 3. Run the Server

```bash
make run
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

### 4. Test the API

Try these example API calls to see the multi-agent system in action:

#### Example 1: Billing Issue

```bash
curl -X POST "http://localhost:8000/tickets" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "C12345",
    "subject": "Issue with billing",
    "body": "I was charged twice this month",
    "email": "john.doe@example.com"
  }'
```

**Expected Response:**
- **Routing**: Triage agent routes to `billing_agent` with 92% confidence
- **Tools Used**: `database_query` (retrieves payment history), `email_sender` (sends confirmation)
- **Resolution**: Reviews payment history, explains charges are normal monthly subscriptions
- **Observability**: Full trace with correlation ID, token usage tracking, latency metrics

<details>
<summary>View sample JSON response</summary>

```json
{
  "ticket_id": "T-abc12345",
  "correlation_id": "CID-...",
  "routing": {
    "assigned_agent": "billing_agent",
    "urgency": "medium",
    "confidence_score": 0.92
  },
  "agent_interactions": [
    {
      "agent_name": "triage_agent",
      "action": "route",
      "reasoning": "Customer mentions billing-related terms"
    },
    {
      "agent_name": "billing_agent",
      "action": "resolve",
      "tool_calls": [
        {
          "tool": "database_query",
          "output": {
            "found": true,
            "payments": [
              {"payment_id": "PAY-001", "date": "2024-11-01", "amount": 49.99},
              {"payment_id": "PAY-002", "date": "2024-12-01", "amount": 49.99}
            ]
          }
        }
      ]
    }
  ],
  "resolution": {
    "status": "resolved",
    "response": "I've reviewed your payment history and found the following charges:\n- 2024-11-01: $49.99 (completed) - Pro subscription - November\n- 2024-12-01: $49.99 (completed) - Pro subscription - December\n\nThese appear to be your regular monthly subscription charges..."
  },
  "metadata": {
    "token_usage": {"triage": {"prompt": 662, "completion": 27}, "billing": {"prompt": 675, "completion": 132}},
    "latency_ms": {"triage": 110, "billing": 115}
  }
}
```
</details>

---

#### Example 2: Technical Support Issue

```bash
curl -X POST "http://localhost:8000/tickets" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "C12345",
    "subject": "API keeps returning 500 errors",
    "body": "Our production app is getting 500 errors from your API endpoint. This started happening 2 hours ago."
  }'
```

**Expected Response:**
- **Routing**: Routes to `technical_agent` with 88% confidence, marked as HIGH urgency
- **Tools Used**: `knowledge_base` (searches technical articles), `email_sender`
- **Resolution**: Provides troubleshooting steps based on KB articles
- **Performance**: ~225ms total latency (110ms triage + 115ms technical)

---

#### Example 3: Account Management

```bash
curl -X POST "http://localhost:8000/tickets" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "C67890",
    "subject": "Need to reset my password",
    "body": "I forgot my password and cannot access my account",
    "email": "jane.smith@example.com"
  }'
```

**Expected Response:**
- **Routing**: Routes to `account_agent` with 85% confidence
- **Tools Used**: `database_query` (retrieves account info), `email_sender` (sends reset link)
- **Resolution**: Sends secure password reset link to registered email
- **Security**: Verifies customer identity before sending sensitive links

---

#### Example 4: View Metrics

```bash
# Check Prometheus metrics
curl http://localhost:8000/metrics

# Check health status
curl http://localhost:8000/health
```

**Available Metrics:**
- `agent_invocation_count` - Agent usage statistics
- `agent_decision_latency_seconds` - Performance histograms
- `tool_call_count` - Tool usage tracking
- `llm_tokens_used` - Token consumption by agent
- `llm_api_cost_dollars` - Cost tracking per agent
- `tickets_processed_total` - Business metrics

## Development

### Run Tests

The project includes 40 comprehensive tests with 83% code coverage:

```bash
# All tests (40 tests: 21 unit + 10 integration + 9 evaluation)
make test

# Unit tests only (21 tests)
make test-unit

# Integration tests only (10 tests)
make test-integration

# Evaluation tests only (9 tests)
make test-evaluation
```

**Unit Tests (21 tests):**
- `tests/unit/test_agents/` - Agent behavior and routing logic (3 tests)
- `tests/unit/test_tools/` - Database, email, and payment tools (12 tests)
- `tests/unit/test_llm/` - LLM client and mock responses (6 tests)

**Integration Tests (10 tests):**
- `tests/integration/test_workflow.py` - End-to-end ticket processing (5 tests)
- `tests/integration/test_api.py` - API endpoint functionality (5 tests)

**Evaluation Tests (9 tests):**
- `tests/evaluation/` - Routing accuracy, tool usage, and performance benchmarks

**Test Results:**
```
====================== 40 passed, 153 warnings in 48.65s =======================
Code Coverage: 83%
```

### Run Evaluation

```bash
make evaluate
```

### Code Quality

```bash
# Lint code
make lint

# Format code
make format
```

## Project Structure

```
agentland/
├── config/           # Configuration and observability setup
├── src/              # Application source code
│   ├── api/          # FastAPI application
│   ├── agents/       # Agent implementations
│   ├── orchestration/# LangGraph state machine
│   ├── tools/        # Agent tools
│   ├── llm/          # LLM client wrapper
│   └── observability/# Tracing, logging, metrics
├── tests/            # Test suite
│   ├── unit/         # Unit tests
│   ├── integration/  # Integration tests
│   └── evaluation/   # DeepEval evaluation tests
├── scripts/          # Utility scripts
└── docs/             # Documentation
```

## Architecture

The system uses a multi-agent architecture with:

1. **Triage Agent**: Routes incoming tickets to appropriate specialists
2. **Specialist Agents**: Handle domain-specific issues (billing, technical, account)
3. **Escalation Agent**: Handles complex cases or escalates to humans
4. **LangGraph**: Coordinates agent interactions with state management
5. **Observability Layer**: Captures traces, logs, and metrics throughout

## Observability

### Traces (OpenTelemetry)
- Distributed tracing across all agent interactions
- Span attributes include agent decisions, tool calls, reasoning
- Correlation IDs for request tracking

### Logs (Structlog)
- JSON-formatted structured logs
- Automatic trace context injection
- Development-friendly console output

### Metrics (Prometheus)
- Agent invocation counts and latency
- Tool call duration and success rates
- LLM token usage and cost tracking
- Business metrics (tickets processed, resolution time)

## Evaluation

Comprehensive evaluation framework with custom metrics:

### Custom Metrics
- **RoutingAccuracyMetric**: Validates triage decisions (90% threshold)
  - Per-agent precision, recall, F1 scores
  - Detailed failure analysis
- **ToolUsageMetric**: Validates correct tool selection (80% threshold)
  - Checks expected tools were called
  - Identifies missing or unexpected tools
- **Performance Benchmarks**: Latency and cost tracking
  - P95 latency < 3 seconds
  - Average cost < $0.01 per ticket

### Run Evaluations
```bash
# Run all evaluations with comprehensive report
python scripts/run_evaluation.py

# Individual test suites
pytest tests/evaluation/test_routing_eval.py -v
pytest tests/evaluation/test_tool_usage_eval.py -v
pytest tests/evaluation/test_benchmark.py -v

# Or use make
make evaluate
```

Results include detailed routing accuracy, tool usage analysis, and performance metrics.

## Configuration

Key environment variables:

- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)
- `APP_ENV`: Environment (development/staging/production)
- `LOG_LEVEL`: Logging level (INFO/DEBUG/WARNING/ERROR)
- `USE_MOCK_TOOLS`: Use mock tools for testing (true/false)
- `OTEL_ENABLED`: Enable OpenTelemetry tracing (true/false)

See `.env.example` for all configuration options.

## License

MIT

## Status

✅ **Production Ready** - All phases complete!

- ✅ Phase 1: Foundation & Observability
- ✅ Phase 2: LLM Client & Tools
- ✅ Phase 3: Agents & Prompts
- ✅ Phase 4: Orchestration & Workflow
- ✅ Phase 5: Evaluation Framework
- ✅ Phase 6: Documentation & Polish
