"""
agents/inventory_agent.py
--------------------------
Detects low stock and anomalous transactions.
Generates stock level and sales charts.

Hallucination prevention:
- LLM only sees pre-filtered, explicitly labelled data
- Prompt forbids invented numbers
- Rule-based counts are the source of truth; LLM adds language only
"""

from state import MarketState
from llm_config import get_llm
from tools.chart_tool import chart_stock_levels, chart_sales_velocity
from tools.alert_tool import emit_alert, format_history_context


def inventory_agent(state: MarketState) -> MarketState:
    inventory = state["inventory_data"]
    pos       = state["pos_data"]

    # ── Rule-based (source of truth) ─────────────────────────────
    low_stock = [i for i in inventory if i["status"] == "LOW_STOCK"]
    ok_stock  = [i for i in inventory if i["status"] == "OK"]
    anomalous = [t for t in pos if t.get("anomaly_flag")]

    # ── Charts (from real data only) ─────────────────────────────
    chart_stock = chart_stock_levels(inventory)
    chart_sales = chart_sales_velocity(pos)

    # ── Context injection ─────────────────────────────────────────
    # Prior-run alerts from Redis give the LLM historical memory
    prior_context = format_history_context()

    # ── LLM: natural language analysis ───────────────────────────
    llm    = get_llm()
    prompt = f"""You are an inventory monitoring agent. Analyze ONLY the data below.
Do NOT invent numbers, products, or shop names not present in the data.
{prior_context}

LOW STOCK ITEMS ({len(low_stock)} items):
{[{'shop': i['shop_id'], 'product': i['product_name'], 'qty': i['quantity_in_stock'], 'reorder_at': i['reorder_point'], 'velocity_per_hr': i['sales_velocity_per_hour']} for i in low_stock]}

ANOMALOUS TRANSACTIONS ({len(anomalous)} flagged):
{[{'shop': t['shop_id'], 'sku': t['sku'], 'qty': t['quantity'], 'price': t['unit_price_pkr'], 'reason': t['anomaly_reason']} for t in anomalous]}

Tasks (use ONLY data above):
1. For each low stock item: state recommended restock = reorder_point * 2. Use exact numbers from data.
2. For each anomalous transaction: classify as theft risk / bulk-resale / price dumping based on the reason field.
3. One sentence overall inventory health summary.

Format: numbered list. Max 2 sentences per item. Do not add items not in the data."""

    analysis = llm(prompt)

    # ── Alerts via emit_alert (persists to Redis + returns dict) ──
    alerts = [
        emit_alert(
            agent="inventory",
            severity="HIGH" if i["quantity_in_stock"] == 0 else "WARNING",
            shop_id=i["shop_id"],
            message=(
                f"Low stock: {i['product_name']} at {i['shop_id']} — "
                f"{i['quantity_in_stock']} units left "
                f"(reorder point: {i['reorder_point']})"
            ),
        )
        for i in low_stock
    ]

    return {
        **state,
        "inventory_output": {
            "low_stock_count":  len(low_stock),
            "ok_stock_count":   len(ok_stock),
            "low_stock_items":  low_stock,
            "anomalous_txns":   anomalous,
            "llm_analysis":     analysis,
            "charts": {
                "stock_levels":  chart_stock,
                "sales_by_shop": chart_sales,
            },
        },
        "alerts": alerts,
    }
