"""
agents/security_agent.py
-------------------------
Detects threats and fraud. Most latency-critical agent.
Rule-based alerts fire before LLM call.
Generates security event severity chart.

Hallucination prevention:
- Alerts generated from rule-based code, never from LLM output
- LLM only correlates already-flagged events
- Prompt explicitly lists event IDs — LLM must reference them by ID
"""

from state import MarketState
from llm_config import get_llm
from tools.chart_tool import chart_security_events
from tools.alert_tool import emit_alert, format_state_alerts, format_history_context
from tools.rag_tool import retrieve_context


def security_agent(state: MarketState) -> MarketState:
    camera = state["camera_data"]
    pos    = state["pos_data"]

    # ── Rule-based: alerts before any LLM call ───────────────────
    critical = [e for e in camera if e["severity"] in ("CRITICAL", "HIGH")]
    all_sev  = list(camera)
    fraud    = [t for t in pos if t.get("anomaly_flag")]

    # ── Alerts via emit_alert (persisted to Redis) ────────────────
    alerts = [
        emit_alert(
            agent="security",
            severity=e["severity"],
            shop_id=e["shop_id"],
            message=f"[SECURITY] {e['event_type']} at {e['shop_id']}: {e['description']}",
        )
        for e in critical
    ]

    # ── Chart ─────────────────────────────────────────────────────
    chart_events = chart_security_events(all_sev)

    # ── Context injection ─────────────────────────────────────────
    upstream_context  = format_state_alerts(state["alerts"], exclude_agent="security")
    prior_run_context = format_history_context()
    # RAG: retrieve patterns relevant to the detected event types
    event_types_str   = " ".join({e["event_type"] for e in critical})
    rag_context       = retrieve_context(
        f"security threat {event_types_str} fraud detection market",
        k=2,
    )

    # ── LLM: pattern analysis on flagged events only ──────────────
    llm = get_llm()
    flagged_with_ids = [
        {**e, "ref_id": f"E{i+1:02d}"}
        for i, e in enumerate(critical)
    ]
    fraud_with_ids = [
        {**t, "ref_id": f"T{i+1:02d}"}
        for i, t in enumerate(fraud)
    ]

    prompt = f"""You are a security analyst. Analyze ONLY the events listed below by their ref_id.
Do NOT reference events, shops, or transactions not in this list.
{rag_context}
{upstream_context}
{prior_run_context}

CRITICAL/HIGH CAMERA EVENTS:
{[{'ref': e['ref_id'], 'shop': e['shop_id'], 'type': e['event_type'], 'desc': e['description']} for e in flagged_with_ids]}

SUSPICIOUS TRANSACTIONS:
{[{'ref': t['ref_id'], 'shop': t['shop_id'], 'sku': t['sku'], 'qty': t['quantity'], 'reason': t['anomaly_reason']} for t in fraud_with_ids]}

Tasks:
1. Do any events (cite ref_id) suggest coordinated fraud or organized threat? Yes/No + reason.
2. For each CRITICAL event (cite ref_id): one immediate recommended action.
3. Severity assessment: Isolated incidents or systemic pattern?

Be direct. Reference events by ref_id only."""

    analysis = llm(prompt)

    return {
        **state,
        "security_output": {
            "critical_count":  len(critical),
            "critical_events": critical,
            "fraud_txns":      fraud,
            "llm_analysis":    analysis,
            "charts": {
                "event_severity": chart_events,
            },
        },
        "alerts": alerts,
    }
