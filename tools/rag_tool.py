"""
tools/rag_tool.py
-----------------
RAG context retrieval using Qdrant (in-memory) + sentence-transformers.

Graceful degradation:
  - Tries local Qdrant server first (QDRANT_HOST env var), falls back to in-memory.
  - If sentence-transformers unavailable, falls back to token-overlap keyword search.

Public API:
  seed_market_knowledge()      — pre-load baseline patterns at pipeline startup (idempotent)
  index_text(text, metadata)   — add a finding/document to the knowledge base
  retrieve_context(query, k=3) — return top-k relevant snippets as a formatted string
"""

import os
from functools import lru_cache

# ── Baseline market knowledge ─────────────────────────────────────────────────

MARKET_KNOWLEDGE = [
    {
        "text": (
            "Price manipulation: sudden hikes above 10% on staples (rice, oil, flour, sugar) "
            "especially when multiple shops raise on the same day, indicate coordinated pricing."
        ),
        "type": "pricing_pattern",
    },
    {
        "text": (
            "Cartel detection: exact uniform pricing across 3+ shops for a perishable (tomatoes, milk) "
            "after a supply disruption is a strong cartel signal. Cross-reference with audio transcripts."
        ),
        "type": "pricing_pattern",
    },
    {
        "text": (
            "Security escalation: UNATTENDED_BAG near entrances combined with SUSPICIOUS_BEHAVIOR "
            "in the same 30-minute window indicates a coordinated threat — escalate immediately."
        ),
        "type": "security_pattern",
    },
    {
        "text": (
            "Shoplifting pattern: DWELL_TIME_HIGH events at cash register area followed by "
            "FOOT_TRAFFIC spikes at exit — high correlation with theft incidents."
        ),
        "type": "security_pattern",
    },
    {
        "text": (
            "Eid festival demand: Pakistani markets need 2.0–2.5x normal inventory for rice, oil, "
            "flour, and sugar at least 2 weeks before Eid ul-Adha or Eid ul-Fitr."
        ),
        "type": "demand_pattern",
    },
    {
        "text": (
            "Inventory reorder urgency: when a LOW_STOCK flag and a HIGH-urgency demand event "
            "within 14 days co-occur for the same SKU, emergency restocking overrides normal reorder cycles."
        ),
        "type": "inventory_pattern",
    },
    {
        "text": (
            "Supply chain risk: suppliers with reliability score below 0.75 historically cause "
            "stockouts within 3 days for high-velocity SKUs. Switch to alternatives when reliability drops."
        ),
        "type": "supply_pattern",
    },
    {
        "text": (
            "Customer panic buying: crowd surges above 30 persons at single-shop markets often precede "
            "panic buying — monitor for inventory depletion of staples within 2 hours of the surge."
        ),
        "type": "customer_pattern",
    },
    {
        "text": (
            "Heat weather effect: temperatures above 35°C in Karachi reliably increase demand for "
            "cold drinks, ice, dairy products, and fresh vegetables by 20–40%."
        ),
        "type": "demand_pattern",
    },
    {
        "text": (
            "Friday Bazaar effect: weekly bazaar days inflate foot traffic 1.5–2x. Shops near "
            "the bazaar perimeter see the highest surge in the first 2 hours of opening."
        ),
        "type": "demand_pattern",
    },
]

# ── Module state ──────────────────────────────────────────────────────────────

_qdrant_client = None
_qdrant_ready  = False
_collection    = "market_knowledge"
_doc_counter   = 0
_seeded        = False
_docs_fallback: list[dict] = []   # keyword-search fallback store


# ── Lazy loaders ──────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_embedder():
    """Load sentence-transformers once. Returns None if unavailable."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        return model
    except Exception as e:
        print(f"[rag_tool] sentence-transformers unavailable ({e}) — using keyword search.")
        return None


def _get_qdrant():
    global _qdrant_client, _qdrant_ready
    if _qdrant_client is not None:
        return _qdrant_client

    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams

        # Try configured server first, fall back to fast in-memory mode
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", 6333))
        try:
            client = QdrantClient(host, port=port, timeout=2)
            client.get_collections()
            print(f"[rag_tool] Connected to Qdrant server at {host}:{port}.")
        except Exception:
            client = QdrantClient(":memory:")
            print("[rag_tool] Using Qdrant in-memory mode.")

        # Create collection if it doesn't exist
        existing = {c.name for c in client.get_collections().collections}
        if _collection not in existing:
            client.create_collection(
                _collection,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

        _qdrant_client = client
        _qdrant_ready  = True
    except Exception as e:
        print(f"[rag_tool] Qdrant unavailable ({e}) — using keyword fallback.")
        _qdrant_ready = False

    return _qdrant_client


def _embed(text: str) -> list[float] | None:
    embedder = _load_embedder()
    if embedder is None:
        return None
    try:
        return embedder.encode(text, show_progress_bar=False).tolist()
    except Exception:
        return None


# ── Public API ────────────────────────────────────────────────────────────────

def seed_market_knowledge() -> None:
    """
    Pre-load baseline market knowledge into the vector store.
    Idempotent — safe to call multiple times; only seeds once per process.
    Call this at pipeline startup via run_pipeline().
    """
    global _seeded
    if _seeded:
        return
    _seeded = True
    for doc in MARKET_KNOWLEDGE:
        index_text(doc["text"], {"type": doc["type"], "source": "baseline"})


def index_text(text: str, metadata: dict | None = None) -> None:
    """
    Add a document to the knowledge base (Qdrant or keyword fallback).
    Agents call this after a run to persist their findings for future runs.
    """
    global _doc_counter
    _docs_fallback.append({"text": text, "metadata": metadata or {}})

    client = _get_qdrant()
    if client is None:
        return

    vec = _embed(text)
    if vec is None:
        return

    try:
        from qdrant_client.models import PointStruct
        client.upsert(
            collection_name=_collection,
            points=[PointStruct(
                id=_doc_counter,
                vector=vec,
                payload={"text": text, **(metadata or {})},
            )],
        )
        _doc_counter += 1
    except Exception:
        pass


def retrieve_context(query: str, k: int = 3) -> str:
    """
    Retrieve the top-k most relevant knowledge snippets for a query.
    Returns a formatted string ready for LLM prompt injection.
    Returns empty string if nothing relevant found.
    """
    client = _get_qdrant()
    if client is not None:
        vec = _embed(query)
        if vec is not None:
            try:
                results = client.search(
                    collection_name=_collection,
                    query_vector=vec,
                    limit=k,
                    score_threshold=0.25,
                )
                if results:
                    snippets = [r.payload.get("text", "") for r in results]
                    return "RELEVANT MARKET KNOWLEDGE:\n" + "\n".join(f"- {s}" for s in snippets)
            except Exception:
                pass

    # Keyword overlap fallback
    if not _docs_fallback:
        return ""
    query_tokens = set(query.lower().split())
    scored = [
        (len(query_tokens & set(doc["text"].lower().split())), doc["text"])
        for doc in _docs_fallback
    ]
    scored = [(s, t) for s, t in scored if s > 0]
    scored.sort(reverse=True)
    if not scored:
        return ""
    snippets = [t for _, t in scored[:k]]
    return "RELEVANT MARKET KNOWLEDGE:\n" + "\n".join(f"- {s}" for s in snippets)
