"""
agents/customer_agent.py
-------------------------
Analyzes foot traffic, crowd events, and sentiment.
Generates foot traffic and sentiment charts.

Hallucination prevention:
- Sentiment counts computed in Python, not by LLM
- LLM receives exact computed counts, not raw data
- Prompt instructs: reference only the numbers provided
"""

from state import MarketState
from llm_config import get_llm
from tools.chart_tool import chart_foot_traffic, chart_sentiment
from tools.alert_tool import emit_alert, format_state_alerts, format_history_context


def customer_agent(state: MarketState) -> MarketState:
    camera = state["camera_data"]
    audio  = state["audio_data"]

    # ── Rule-based (source of truth) ─────────────────────────────
    traffic  = [e for e in camera if e["event_type"] == "FOOT_TRAFFIC"]
    surges   = [e for e in camera if e["event_type"] == "CROWD_SURGE"]
    dwell    = [e for e in camera if e["event_type"] == "DWELL_TIME_HIGH"]

    sentiments   = [a.get("sentiment") for a in audio if a.get("sentiment")]
    pos_count    = sentiments.count("POSITIVE")
    neu_count    = sentiments.count("NEUTRAL")
    neg_count    = sentiments.count("NEGATIVE")
    avg_footfall = (
        sum(e["person_count"] for e in traffic) / len(traffic)
        if traffic else 0
    )
    negative_shops = [
        {"shop": a["shop_id"], "sku": a["sku"], "issue": a["transcript"][:80]}
        for a in audio if a.get("sentiment") == "NEGATIVE"
    ]

    # ── Charts ────────────────────────────────────────────────────
    chart_traffic = chart_foot_traffic(camera)
    chart_sent    = chart_sentiment(audio)

    # ── Context injection ─────────────────────────────────────────
    upstream_context  = format_state_alerts(state["alerts"], exclude_agent="customer")
    prior_run_context = format_history_context()

    # ── LLM: natural language summary ────────────────────────────
    llm    = get_llm()
    prompt = f"""You are a customer experience analyst. Use ONLY the numbers and facts below.
Do NOT invent customer names, shop names, or events not listed here.
{upstream_context}
{prior_run_context}

FOOT TRAFFIC:
- Average: {avg_footfall:.0f} people per shop
- Crowd surges detected: {len(surges)} — shops: {[e['shop_id'] for e in surges]}
- High dwell-time events: {len(dwell)} — shops: {[e['shop_id'] for e in dwell]}

SENTIMENT (computed from {len(sentiments)} interactions):
- Positive: {pos_count}  Neutral: {neu_count}  Negative: {neg_count}
- Shops with negative interactions: {negative_shops}

Tasks (reference ONLY the numbers above):
1. Overall customer experience score: Good / Fair / Poor — justify in 1 sentence using exact counts.
2. List shops needing immediate attention and why.
3. One actionable recommendation based on the data."""

    analysis = llm(prompt)

    # ── Alerts via emit_alert ─────────────────────────────────────
    alerts = [
        emit_alert(
            agent="customer",
            severity="WARNING",
            shop_id=e["shop_id"],
            message=f"Crowd surge at {e['shop_id']}: {e['description']}",
        )
        for e in surges
    ]

    return {
        **state,
        "customer_output": {
            "avg_footfall":    round(avg_footfall, 1),
            "crowd_surges":    len(surges),
            "neg_sentiment":   neg_count,
            "pos_sentiment":   pos_count,
            "total_sentiment": len(sentiments),
            "llm_analysis":    analysis,
            "charts": {
                "foot_traffic": chart_traffic,
                "sentiment":    chart_sent,
            },
        },
        "alerts": alerts,
    }
