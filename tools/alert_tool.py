"""
tools/alert_tool.py
-------------------
Standardized alert emission with Redis persistence and cross-run history.

emit_alert()              — create + persist an alert, return the alert dict
get_recent_alerts()       — retrieve prior-run alerts from Redis for LLM context
format_history_context()  — format Redis alerts as compact string for prompt injection
format_state_alerts()     — format within-run state alerts for downstream agents
"""

import json
from datetime import datetime

_redis_client = None
_redis_available = False

SEVERITY_RANK = {"CRITICAL": 4, "HIGH": 3, "WARNING": 2, "INFO": 1}


def _get_client():
    global _redis_client, _redis_available
    if _redis_client is not None:
        return _redis_client
    try:
        import redis, os
        from dotenv import load_dotenv
        load_dotenv()
        _redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True,
        )
        _redis_client.ping()
        _redis_available = True
    except Exception:
        _redis_available = False
    return _redis_client


def emit_alert(agent: str, severity: str, shop_id: str, message: str,
               metadata: dict | None = None) -> dict:
    """
    Create a structured alert, persist it to Redis (24h TTL), and return it.
    Return value is the dict that agents append to state["alerts"].
    """
    alert = {
        "agent":     agent,
        "severity":  severity,
        "shop_id":   shop_id,
        "message":   message,
        "timestamp": datetime.now().isoformat(),
        **(metadata or {}),
    }
    client = _get_client()
    if _redis_available and client:
        try:
            key = f"alerts:{shop_id}"
            client.lpush(key, json.dumps(alert))
            client.expire(key, 86400)
        except Exception:
            pass
    return alert


def get_recent_alerts(shop_id: str | None = None,
                      agent: str | None = None,
                      limit: int = 10) -> list[dict]:
    """
    Retrieve alerts from Redis for cross-run historical context.
    shop_id=None returns alerts across all shops (up to limit).
    """
    client = _get_client()
    alerts: list[dict] = []

    if _redis_available and client:
        try:
            if shop_id:
                raw = client.lrange(f"alerts:{shop_id}", 0, limit - 1)
                alerts = [json.loads(r) for r in raw]
            else:
                keys = client.keys("alerts:*")
                for k in keys[:10]:
                    raw = client.lrange(k, 0, 4)
                    alerts.extend(json.loads(r) for r in raw)
        except Exception:
            alerts = []

    if agent:
        alerts = [a for a in alerts if a.get("agent") == agent]

    return sorted(alerts, key=lambda a: a.get("timestamp", ""), reverse=True)[:limit]


def format_history_context(shop_id: str | None = None) -> str:
    """
    Format cross-run Redis alerts as a compact block for LLM prompt injection.
    Returns empty string if no prior alerts exist (first run or Redis down).
    """
    alerts = get_recent_alerts(shop_id=shop_id, limit=5)
    if not alerts:
        return ""
    lines = [
        f"- [{a['severity']}] {a['agent'].upper()} @ {a['shop_id']}: {a['message'][:110]}"
        for a in alerts
    ]
    return "PRIOR RUN ALERTS (historical context):\n" + "\n".join(lines)


def format_state_alerts(state_alerts: list[dict], exclude_agent: str = "") -> str:
    """
    Format within-run alerts accumulated in state["alerts"] for downstream agents.
    exclude_agent: skip alerts from the calling agent itself.
    Returns empty string if no upstream alerts yet.
    """
    prior = [a for a in state_alerts if a.get("agent") != exclude_agent]
    if not prior:
        return ""
    lines = [
        f"- [{a['severity']}] {a['agent'].upper()} @ {a['shop_id']}: {a['message'][:110]}"
        for a in prior[:8]
    ]
    return "ALERTS FROM UPSTREAM AGENTS (this run):\n" + "\n".join(lines)
