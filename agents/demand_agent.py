"""
agents/demand_agent.py
-----------------------
Forecasts demand using events, weather, and current inventory.
Generates demand forecast chart.

Hallucination prevention:
- At-risk combinations computed in Python by set intersection
- LLM receives exact event names, dates, multipliers, and SKUs
- Prompt asks LLM to use only the at_risk list provided
"""

from state import MarketState
from llm_config import get_llm
from tools.chart_tool import chart_demand_forecast
from tools.alert_tool import emit_alert, format_state_alerts, format_history_context
from tools.rag_tool import retrieve_context


def demand_agent(state: MarketState) -> MarketState:
    events    = state["city_events"]
    weather   = state["weather_data"]
    inventory = state["inventory_data"]

    # ── Rule-based: compute at-risk in Python ────────────────────
    low_skus      = {i["sku"] for i in inventory if i["status"] == "LOW_STOCK"}
    urgent_events = [e for e in events if e.get("demand_urgency") == "HIGH"]

    at_risk = []
    for event in urgent_events:
        overlap = set(event.get("high_demand_skus", [])) & low_skus
        if overlap:
            at_risk.append({
                "event":        event["name"],
                "days_away":    event["days_away"],
                "multiplier":   event["expected_footfall_multiplier"],
                "at_risk_skus": sorted(overlap),
            })

    # ── Alerts via emit_alert ─────────────────────────────────────
    alerts = [
        emit_alert(
            agent="demand",
            severity="HIGH",
            shop_id="ALL_SHOPS",
            message=(
                f"Demand surge risk: '{r['event']}' in {r['days_away']} days — "
                f"low stock on {r['at_risk_skus']} "
                f"(expected {r['multiplier']}x footfall)"
            ),
        )
        for r in at_risk
    ]

    # ── Chart ─────────────────────────────────────────────────────
    chart_demand = chart_demand_forecast(events, inventory)

    # ── Context injection ─────────────────────────────────────────
    upstream_context  = format_state_alerts(state["alerts"], exclude_agent="demand")
    prior_run_context = format_history_context()
    # RAG: retrieve demand patterns relevant to current events and weather
    event_names_str   = " ".join(e["name"] for e in urgent_events)
    rag_context       = retrieve_context(
        f"demand surge forecast {event_names_str} {weather.get('condition', '')} inventory reorder",
        k=3,
    )

    # ── LLM: forecast narrative ───────────────────────────────────
    llm = get_llm()
    prompt = f"""You are a demand forecasting analyst. Use ONLY the data below.
Do NOT invent events, SKUs, or dates not listed here.
{rag_context}
{upstream_context}
{prior_run_context}

UPCOMING EVENTS:
{[{'name': e['name'], 'days_away': e['days_away'], 'multiplier': e['expected_footfall_multiplier'], 'high_demand_skus': e['high_demand_skus']} for e in events]}

CURRENT WEATHER: {weather.get('condition')}, {weather.get('temperature_c')}°C
WEATHER DEMAND SIGNAL: {weather.get('demand_impact', 'none')}

AT-RISK COMBINATIONS (low stock + high demand event — computed from data):
{at_risk}

LOW STOCK SKUs (from current inventory): {sorted(low_skus)}

Tasks (reference only data above):
1. Top 3 SKUs to restock urgently — name exact SKUs from at_risk list and state which event drives each.
2. How many days do shops have before the highest-risk event? (use days_away from data)
3. One weather-driven demand insight using the weather signal provided.

Quote event names and SKU codes exactly as written. Do not suggest SKUs not in the data."""

    analysis = llm(prompt)

    return {
        **state,
        "demand_output": {
            "upcoming_events":    len(events),
            "urgent_events":      len(urgent_events),
            "at_risk":            at_risk,
            "low_stock_skus":     sorted(low_skus),
            "llm_analysis":       analysis,
            "charts": {
                "demand_forecast": chart_demand,
            },
        },
        "alerts": alerts,
    }
