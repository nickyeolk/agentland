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

```bash
curl -X POST "http://localhost:8000/tickets" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "C12345",
    "subject": "Issue with billing",
    "body": "I was charged twice this month"
  }'
```

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
