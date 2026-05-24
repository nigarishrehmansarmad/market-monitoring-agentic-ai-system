"""
memory/redis_store.py
----------------------
Redis working memory — real-time per-shop state.
Gracefully falls back to an in-memory dict if Redis isn't running.
No code changes needed either way.
"""

import json

_redis_client  = None
_fallback: dict = {}
REDIS_AVAILABLE = False


def _get_client():
    global _redis_client, REDIS_AVAILABLE
    if _redis_client is None:
        try:
            import redis, os
            from dotenv import load_dotenv
            load_dotenv()
            _redis_client   = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                decode_responses=True,
            )
            _redis_client.ping()
            REDIS_AVAILABLE = True
            print("[redis_store] Connected to Redis.")
        except Exception:
            REDIS_AVAILABLE = False
            print("[redis_store] Redis unavailable — using in-memory fallback.")
    return _redis_client


def set_state(shop_id: str, key: str, value: dict, ttl: int = 3600):
    full_key = f"{shop_id}:{key}"
    client   = _get_client()
    if REDIS_AVAILABLE and client:
        client.setex(full_key, ttl, json.dumps(value))
    else:
        _fallback[full_key] = value


def get_state(shop_id: str, key: str) -> dict | None:
    full_key = f"{shop_id}:{key}"
    client   = _get_client()
    if REDIS_AVAILABLE and client:
        raw = client.get(full_key)
        return json.loads(raw) if raw else None
    return _fallback.get(full_key)