"""
agents/supply_agent.py
-----------------------
Monitors deliveries, disruptions, and supplier reliability.
Generates supply chain status chart.

Hallucination prevention:
- Disruptions and reliability scores come from data, not LLM
- LLM receives structured dict per delivery — no ambiguous text
- Prompt asks for action recommendation from a fixed menu
"""

from state import MarketState
from llm_config import get_llm
from tools.chart_tool import chart_supply_status
from tools.alert_tool import emit_alert, format_state_alerts, format_history_context


def supply_agent(state: MarketState) -> MarketState:
    supply = state["supply_chain_data"]

    # ── Rule-based ────────────────────────────────────────────────
    disrupted       = [d for d in supply if d.get("disruption_flag")]
    on_time         = [d for d in supply if not d.get("disruption_flag")]
    low_reliability = [d for d in supply if
                       d.get("supplier_reliability_score", 1) < 0.8]

    # ── Alerts via emit_alert ─────────────────────────────────────
    alerts = [
        emit_alert(
            agent="supply",
            severity="WARNING",
            shop_id=d["shop_id"],
            message=(
                f"Supply disruption: {d['supplier']} → {d['shop_id']} "
                f"({d.get('disruption_reason', 'unknown')})"
            ),
        )
        for d in disrupted
    ]

    # ── Chart ─────────────────────────────────────────────────────
    chart_supply = chart_supply_status(supply)

    # ── Context injection ─────────────────────────────────────────
    upstream_context  = format_state_alerts(state["alerts"], exclude_agent="supply")
    prior_run_context = format_history_context()

    # ── LLM: recommendation per disruption ───────────────────────
    llm = get_llm()
    disrupted_structured = [
        {
            "ref":         f"D{i+1:02d}",
            "supplier":    d["supplier"],
            "shop":        d["shop_id"],
            "sku":         d["sku"],
            "reason":      d.get("disruption_reason", "unknown"),
            "reliability": d.get("supplier_reliability_score"),
            "alternative": d.get("alternative_supplier", "none listed"),
            "qty_ordered": d["quantity_ordered"],
        }
        for i, d in enumerate(disrupted)
    ]

    prompt = f"""You are a supply chain analyst. Analyze ONLY the disruptions listed below.
Do NOT invent suppliers, shops, or products not in this list.
{upstream_context}
{prior_run_context}

DISRUPTED DELIVERIES ({len(disrupted)} of {len(supply)} total):
{disrupted_structured}

LOW RELIABILITY SUPPLIERS (score < 0.8):
{[{'supplier': d['supplier'], 'score': d.get('supplier_reliability_score')} for d in low_reliability]}

For each disruption (cite ref_id):
1. Will it likely cause a stockout? (yes/no + reason from data)
2. Recommended action — choose ONE: [wait] [switch to alternative] [emergency order]
3. If alternative supplier listed, name it exactly as written.

Do not recommend actions beyond the three options listed. Max 2 sentences per item."""

    analysis = llm(prompt)

    return {
        **state,
        "supply_output": {
            "total":           len(supply),
            "disrupted_count": len(disrupted),
            "on_time_count":   len(on_time),
            "disrupted":       disrupted,
            "low_reliability": low_reliability,
            "llm_analysis":    analysis,
            "charts": {
                "supply_status": chart_supply,
            },
        },
        "alerts": alerts,
    }
