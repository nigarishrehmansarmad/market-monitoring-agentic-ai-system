"""
agents/pricing_agent.py
------------------------
Detects price manipulation and cartel signals from audio transcripts.
Generates price comparison chart.

Hallucination prevention:
- Manipulation flags set by rule-based code in mock data
- LLM receives exact price numbers (listed vs agreed) per transaction
- Prompt asks LLM to quote specific price figures from the data
"""

from state import MarketState
from llm_config import get_llm
from tools.chart_tool import chart_pricing
from tools.alert_tool import emit_alert, format_state_alerts, format_history_context


def pricing_agent(state: MarketState) -> MarketState:
    audio = state["audio_data"]

    # ── Rule-based ────────────────────────────────────────────────
    manipulated = [a for a in audio if a.get("price_manipulation_flag")]
    cartels     = [a for a in audio if a.get("cartel_signal")]
    normal      = [a for a in audio if not a.get("price_manipulation_flag")]

    # ── Alerts via emit_alert ─────────────────────────────────────
    alerts = [
        emit_alert(
            agent="pricing",
            severity="HIGH" if a.get("cartel_signal") else "WARNING",
            shop_id=a["shop_id"],
            message=(
                f"Pricing anomaly at {a['shop_id']} ({a['sku']}): "
                f"{a.get('cartel_signal', 'price manipulation detected')}"
            ),
        )
        for a in manipulated
    ]

    # ── Chart ─────────────────────────────────────────────────────
    chart_prices = chart_pricing(audio)

    # ── Context injection ─────────────────────────────────────────
    upstream_context  = format_state_alerts(state["alerts"], exclude_agent="pricing")
    prior_run_context = format_history_context()

    # ── LLM: pricing analysis ─────────────────────────────────────
    llm = get_llm()
    transcript_summary = [
        {
            "ref":           f"P{i+1:02d}",
            "shop":          a["shop_id"],
            "sku":           a["sku"],
            "listed_pkr":    a.get("listed_price_pkr"),
            "agreed_pkr":    a.get("agreed_price_pkr"),
            "discount_pct":  a.get("discount_pct"),
            "sentiment":     a.get("sentiment"),
            "flagged":       a.get("price_manipulation_flag", False),
            "cartel_signal": a.get("cartel_signal"),
        }
        for i, a in enumerate(audio)
    ]

    prompt = f"""You are a market pricing analyst. Use ONLY the transaction data below.
Do NOT invent prices, shops, or products not listed.
{upstream_context}
{prior_run_context}

PRICING TRANSACTIONS ({len(audio)} total, {len(manipulated)} flagged):
{transcript_summary}

Tasks:
1. Cartel risk: Do any shops show coordinated pricing? (cite ref_ids and exact prices from data)
2. Price hike: Which SKUs have agreed price ABOVE listed price? (quote exact figures from data)
3. Overall market pricing health: Competitive / Moderately distorted / Highly distorted — justify with numbers from data.

Always quote exact PKR values from the data. Do not estimate or round."""

    analysis = llm(prompt)

    return {
        **state,
        "pricing_output": {
            "total_transcripts":  len(audio),
            "manipulation_count": len(manipulated),
            "cartel_signals":     cartels,
            "normal_count":       len(normal),
            "llm_analysis":       analysis,
            "charts": {
                "price_comparison": chart_prices,
            },
        },
        "alerts": alerts,
    }
