"""
memory/vector_store.py
-----------------------
Qdrant vector store — long-term semantic memory.
Runs fully locally using on-disk persistence (no Qdrant server needed).
One collection per agent domain.
Lazy initialization — connects only on first access, not at import time.

Collections:
    inventory_patterns    — historical stock and sales anomalies
    security_incidents    — fraud cases and threat response protocols
    pricing_history       — negotiation transcripts and market price trends
    supply_chain_events   — disruption history and resolution strategies
    customer_behavior     — foot traffic and sentiment patterns
    demand_forecasts      — seasonal and event-based demand patterns
"""

import os
import uuid
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

load_dotenv()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL_ID", "sentence-transformers/all-MiniLM-L6-v2")
DB_PATH         = "./qdrant_db"      # on-disk persistence folder
VECTOR_SIZE     = 384                # all-MiniLM-L6-v2 output dimension

COLLECTIONS = [
    "inventory_patterns",
    "security_incidents",
    "pricing_history",
    "supply_chain_events",
    "customer_behavior",
    "demand_forecasts",
]

_client    = None
_encoder   = None


def _get_client() -> QdrantClient:
    """Lazy init — creates on-disk Qdrant client on first call."""
    global _client
    if _client is None:
        os.makedirs(DB_PATH, exist_ok=True)
        _client = QdrantClient(path=DB_PATH)
        print(f"[vector_store] Qdrant initialized at {DB_PATH}")
    return _client


def _get_encoder() -> SentenceTransformer:
    """Lazy init — loads embedding model on first call."""
    global _encoder
    if _encoder is None:
        _encoder = SentenceTransformer(EMBEDDING_MODEL)
        print(f"[vector_store] Encoder loaded: {EMBEDDING_MODEL}")
    return _encoder


def _ensure_collection(name: str):
    """Create collection if it doesn't exist yet."""
    client = _get_client()
    existing = [c.name for c in client.get_collections().collections]
    if name not in existing:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        print(f"[vector_store] Created collection: {name}")


def store(collection_name: str, doc_id: str, text: str, metadata: dict = {}):
    """
    Store or update a document in a Qdrant collection.

    Args:
        collection_name: one of the COLLECTIONS list
        doc_id:          unique string ID for this document
        text:            the text to embed and store
        metadata:        any extra fields to attach as payload
    """
    _ensure_collection(collection_name)
    client  = _get_client()
    encoder = _get_encoder()

    vector  = encoder.encode(text).tolist()
    payload = {"text": text, "doc_id": doc_id, **metadata}

    # Use a deterministic integer ID derived from doc_id string
    point_id = abs(hash(doc_id)) % (2**63)

    client.upsert(
        collection_name=collection_name,
        points=[PointStruct(id=point_id, vector=vector, payload=payload)],
    )


def retrieve(collection_name: str, query: str, n_results: int = 3) -> list[str]:
    """
    Semantic search — returns top-k matching document texts.

    Returns empty list if collection is empty or doesn't exist yet.
    Agents handle this gracefully — they proceed with LLM reasoning only.
    """
    client = _get_client()
    existing = [c.name for c in client.get_collections().collections]
    if collection_name not in existing:
        return []

    info = client.get_collection(collection_name)
    if info.points_count == 0:
        return []

    encoder = _get_encoder()
    vector  = encoder.encode(query).tolist()

    results = client.search(
        collection_name=collection_name,
        query_vector=vector,
        limit=min(n_results, info.points_count),
    )

    return [hit.payload.get("text", "") for hit in results]