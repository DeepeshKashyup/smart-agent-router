# Smart Agent Router

> Cost-effective agentic AI with intelligent model routing — demonstrating up to 70% token cost reduction by routing queries to the right model based on complexity.

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Client     │────▶│  FastAPI Gateway  │────▶│  Input Guard    │
└─────────────┘     └──────────────────┘     └────────┬────────┘
                                                       │
                                              ┌────────▼────────┐
                                              │  Query Router    │
                                              │  (Flash ~$0.001) │
                                              └────────┬────────┘
                                                       │
                                    ┌──────────────────┼──────────────────┐
                                    │                  │                  │
                             ┌──────▼──────┐    ┌──────▼──────┐   ┌──────▼──────┐
                             │   SIMPLE    │    │  MODERATE   │   │   COMPLEX   │
                             │  Flash      │    │  Flash      │   │   Pro       │
                             │  ~$0.0003/K │    │  ~$0.0003/K │   │  ~$0.005/K  │
                             └──────┬──────┘    └──────┬──────┘   └──────┬──────┘
                                    │                  │                  │
                                    └──────────────────┼──────────────────┘
                                                       │
                                              ┌────────▼────────┐
                                              │  Output Guard   │
                                              └────────┬────────┘
                                                       │
                                              ┌────────▼────────┐
                                              │  Cost Tracker   │
                                              └─────────────────┘
```

## Features

- **Intelligent Routing** — Classifies query complexity (SIMPLE/MODERATE/COMPLEX) and routes to the cheapest adequate model
- **70% Cost Reduction** — Routes ~70% of typical queries to lightweight models at 1/16th the cost
- **Built-in Cost Tracking** — Real-time cost monitoring with savings dashboard at `/api/v1/costs`
- **Input/Output Guardrails** — Prompt injection detection, length limits, and output sanitization
- **Evaluation Suite** — 10 golden test cases with routing accuracy, latency, and cost metrics
- **RAG-Ready** — ChromaDB vector store with document ingestion pipeline
- **Production-Grade** — Structured logging, correlation IDs, async throughout, Docker support

## Tech Stack

| Component | Technology |
|-----------|-----------|
| API Framework | FastAPI |
| LLM Orchestration | LangChain + Vertex AI |
| Models | Gemini 1.5 Pro (large) + Gemini 1.5 Flash (small/router) |
| Vector Store | ChromaDB |
| Logging | structlog |
| Config | pydantic-settings + YAML |
| Testing | pytest + pytest-asyncio |

## Prerequisites

### Google Cloud SDK (gcloud)

This project uses Vertex AI (Gemini models), which requires the Google Cloud SDK and authenticated credentials.

**Install gcloud CLI:**

- **Windows:** Download and run the installer from https://cloud.google.com/sdk/docs/install
- **macOS:** `brew install --cask google-cloud-sdk`
- **Linux:** `curl https://sdk.cloud.google.com | bash`

**Authenticate:**

```bash
# Initialize gcloud and select your GCP project
gcloud init

# Set up Application Default Credentials (required for Vertex AI)
gcloud auth application-default login
```

This opens a browser for Google OAuth. After authenticating, your credentials are saved locally and used by the Vertex AI SDK.

**Verify:**

```bash
gcloud auth application-default print-access-token
```

If this prints a token, you're ready to go.

## Quick Start

### 1. Setup

```bash
# Clone and install
git clone https://github.com/yourusername/smart-agent-router.git
cd smart-agent-router
make setup

# Configure
cp .env.example .env
# Edit .env with your GCP project ID
```

### 2. (Optional) Ingest Documents

```bash
# Add .txt or .md files to data/raw/, then:
make ingest

# Or seed with sample data:
make seed
```

### 3. Run

```bash
make run
# Server starts at http://localhost:8000
```

## API Documentation

### Query Endpoint

```bash
# Let the router decide which model to use
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Python?"}'

# Force a specific model tier
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Design a fraud detection system", "force_model": "large"}'
```

**Response:**
```json
{
  "answer": "Python is a high-level programming language...",
  "model_used": "gemini-1.5-flash",
  "complexity": "SIMPLE",
  "confidence": 0.95,
  "tokens_used": 142,
  "estimated_cost_usd": 0.000053,
  "correlation_id": "a1b2c3d4"
}
```

### Cost Dashboard

```bash
# View cost summary
curl http://localhost:8000/api/v1/costs

# Reset counters
curl -X POST http://localhost:8000/api/v1/costs/reset
```

**Response:**
```json
{
  "total_requests": 100,
  "total_tokens": 45200,
  "total_cost_usd": 0.028,
  "routed_to_small": 72,
  "routed_to_large": 28,
  "cost_savings_pct": 71.3
}
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Evaluation

Run the evaluation suite against 10 golden test cases:

```bash
make eval
```

This measures:
- **Routing accuracy** — Did queries go to the correct model tier?
- **Latency** — Average response time per query
- **Cost savings** — Actual vs hypothetical (all-large) cost

## Project Structure

```
smart-agent-router/
├── app/                    # FastAPI application
│   ├── main.py             # Entrypoint with lifespan, CORS, health check
│   ├── api/routes.py       # /query, /costs endpoints
│   ├── core/               # Config (pydantic-settings) and logging (structlog)
│   └── middleware/          # Global error handling
├── src/                    # Core logic
│   ├── agents/agent.py     # QueryRouter + CostTracker
│   ├── chains/pipeline.py  # SmartRouterPipeline orchestration
│   ├── prompts/            # Prompt templates
│   ├── retrieval/          # Embeddings, vector store, chunking
│   ├── guardrails/         # Input/output validation
│   ├── tools/              # Custom tools (cost calculator)
│   └── utils/              # LLM client abstraction, helpers
├── eval/                   # Evaluation suite
├── tests/                  # pytest tests
├── configs/                # YAML config + prompt templates
├── docker/                 # Dockerfile + compose
├── scripts/                # Ingestion + seeding scripts
└── notebooks/              # Exploration + evaluation notebooks
```

## How It Works

1. **Query arrives** at `/api/v1/query`
2. **Input guard** validates for injection, length, blocked topics
3. **Router model** (Flash, ~50 tokens) classifies complexity as SIMPLE/MODERATE/COMPLEX
4. **Routing decision**: SIMPLE/MODERATE → Flash ($0.0003/1K), COMPLEX → Pro ($0.005/1K)
5. **Selected model** generates the response
6. **Output guard** sanitizes the response
7. **Cost tracker** logs tokens, cost, and model used
8. **Response** includes the answer + full cost metadata

The key insight: the router call costs <1% of the total, but saves 60-70% by avoiding the expensive model for simple queries.

## Future Improvements

- [ ] Semantic caching layer to skip LLM calls for repeated/similar queries
- [ ] A/B testing framework to compare routing strategies
- [ ] Multi-model support (OpenAI, Anthropic, Mistral) via provider abstraction
- [ ] Streaming responses for long-form generation
- [ ] Prometheus metrics export for production monitoring
- [ ] Fine-tuned router model on production query distribution
- [ ] Token budget policies with automatic fallback

## License

MIT