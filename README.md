# Agentic AI Local Market Monitoring System

A multi-agent smart city monitoring system that analyzes Karachi bazaar health in near real time using **LangGraph**, **Groq-hosted LLMs**, **RAG**, and a **Streamlit dashboard**.

The pipeline runs six specialized agents in sequence, accumulates alerts in shared state, and produces an executive summary for city administrators. A critical-event fast path generates an emergency briefing immediately.

---

## What this project does

- Monitors inventory, customer behavior, security events, supply chain status, pricing behavior, and demand risk.
- Uses deterministic mock data feeds (inventory, POS, camera, audio, weather, city events, supply chain).
- Emits structured alerts with severity (`CRITICAL`, `HIGH`, `WARNING`, `INFO`).
- Persists alert context in Redis when available (fallback: in-memory).
- Retrieves contextual market patterns via Qdrant + embeddings (fallback: keyword matching).
- Generates charts per agent under `./charts/`.
- Produces:
  - **Emergency briefing** (if critical conditions are detected)
  - **Executive summary** (always)

---

## Architecture overview

Pipeline graph (defined in `orchestrator.py`):

```text
orchestrator_node (load feeds, seed RAG)
    ↓
inventory_agent → customer_agent → security_agent
                                       ↓
                    CRITICAL? → emergency_synthesis
                                       ↓
                          supply_agent → pricing_agent → demand_agent
                                       ↓
                                  synthesis_node
                                       ↓
                                      END
```

- If any alert is `CRITICAL` after `security_agent`, the graph takes an emergency path.
- Both normal and emergency paths end in `synthesis_node` so a final report is always produced.

---

## Core design principles

1. **Rule-based truth first**
   - Counts, flags, and structured outputs are computed in Python.
   - LLMs provide narrative analysis only.

2. **Shared state accumulation**
   - State schema is in `state.py` (`MarketState`).
   - Alerts are appended using `Annotated[list[dict], operator.add]`.

3. **Graceful degradation**
   - Redis unavailable → in-memory fallback.
   - Qdrant/embeddings unavailable → keyword fallback.

4. **LLM singleton + response caching**
   - LLM initialization is centralized in `llm_config.py`.
   - Caching uses Redis if available, otherwise SQLite (`.llm_cache.db`).

---

## Repository structure

```text
.
├── agents/
│   ├── inventory_agent.py
│   ├── customer_agent.py
│   ├── security_agent.py
│   ├── supply_agent.py
│   ├── pricing_agent.py
│   └── demand_agent.py
├── data/
│   └── mock_iot_data.py
├── memory/
│   ├── redis_store.py
│   └── vector_store.py
├── tools/
│   ├── alert_tool.py
│   ├── rag_tool.py
│   └── chart_tool.py
├── charts/
├── dashboard.py
├── orchestrator.py
├── state.py
├── llm_config.py
└── requirements.txt
```

---

## Requirements

- Python 3.10+
- Groq API key (`GROQ_API_KEY`)

Optional (system works without these due to fallbacks):
- Redis
- Qdrant

---

## Installation

```bash
cd /home/runner/work/market-monitoring-agentic-ai-system/market-monitoring-agentic-ai-system
python -m venv .venv
source .venv/bin/activate   # On Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `.env` in the repository root:

```env
GROQ_API_KEY=your_groq_key_here
LLM_MODEL_ID=llama-3.3-70b-versatile
LLM_MAX_NEW_TOKENS=512
LLM_CACHE=true
REDIS_HOST=localhost
REDIS_PORT=6379
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

---

## Running the system

### 1) Streamlit dashboard (primary UI)

```bash
streamlit run dashboard.py
```

Features:
- Run pipeline from sidebar
- Switch model (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `meta-llama/llama-4-scout-17b-16e-instruct`)
- View overview metrics, per-agent outputs, and all alerts

### 2) CLI pipeline run

```bash
python orchestrator.py
```

Outputs printed in terminal:
- Emergency briefing (if any)
- Executive summary
- Full structured alert list

### 3) Inspect mock feeds

```bash
python data/mock_iot_data.py
```

---

## Agent responsibilities

- **Inventory agent**: low-stock and transaction anomaly analysis
- **Customer agent**: foot-traffic and sentiment analysis
- **Security agent**: critical event and suspicious transaction analysis
- **Supply agent**: delivery disruption and supplier reliability analysis
- **Pricing agent**: price manipulation/cartel signal analysis
- **Demand agent**: event/weather-driven demand risk analysis

Each agent:
- reads from shared state
- computes rule-based findings
- generates charts
- injects upstream + historical context into prompts
- emits alerts via `tools/alert_tool.py`
- writes agent output back into state

---

## RAG and memory behavior

### RAG (`tools/rag_tool.py`)

- Seeds baseline market knowledge at pipeline startup.
- Uses sentence-transformers + Qdrant for semantic retrieval.
- Falls back to keyword matching if vector pipeline is unavailable.

### Alerts/history (`tools/alert_tool.py`)

- `emit_alert()` creates and persists alerts.
- `format_state_alerts()` adds upstream same-run context.
- `format_history_context()` adds prior-run context from Redis.

---

## Chart outputs

Charts are generated under `./charts/`, including:

- `inventory_stock_levels.png`
- `inventory_sales_by_shop.png`
- `customer_foot_traffic.png`
- `customer_sentiment.png`
- `security_events.png`
- `supply_chain_status.png`
- `pricing_comparison.png`
- `demand_forecast.png`

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | *(required)* | Groq API key |
| `LLM_MODEL_ID` | `llama-3.3-70b-versatile` | Groq model used by all agents |
| `LLM_MAX_NEW_TOKENS` | `512` | Max output tokens per LLM call |
| `LLM_CACHE` | `true` | Enable/disable LLM response cache |
| `REDIS_HOST` | `localhost` | Redis hostname |
| `REDIS_PORT` | `6379` | Redis port |
| `QDRANT_HOST` | `localhost` | Qdrant hostname |
| `QDRANT_PORT` | `6333` | Qdrant port |

---

## Extending the system

To add a new agent:

1. Create `agents/my_agent.py` following existing agent pattern.
2. Add output key(s) to `MarketState` in `state.py`.
3. Register node and edges in `orchestrator.py`.
4. Add a corresponding dashboard view in `dashboard.py`.

To add permanent RAG knowledge:
- Add entries to `MARKET_KNOWLEDGE` in `tools/rag_tool.py`, or
- Call `index_text(...)` programmatically.

---

## Troubleshooting

- **`GROQ_API_KEY not set`**: add key to `.env`.
- **Redis connection errors**: system falls back automatically to in-memory storage.
- **Qdrant/embedding errors**: system falls back automatically to keyword retrieval.
- **Slow first run**: expected if models/cache are cold; subsequent repeated prompts are faster with cache.

---

## Notes

- Mock data is deterministic (`random.seed(42)`), useful for demos and reproducible behavior.
- Existing charts and `.llm_cache.db` are generated artifacts.
- No dedicated automated test suite is currently included in the repository.
