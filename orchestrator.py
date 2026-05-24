"""
orchestrator.py
---------------
LangGraph StateGraph — orchestrates all 6 agents then synthesizes a report.

Both paths always end at synthesis_node so the executive summary is always produced.

Normal flow:
  orchestrator_node  (loads mock data, seeds RAG)
       ↓
  inventory_agent → customer_agent → security_agent
                                          ↓
                         CRITICAL? → emergency_synthesis ─┐
                                          ↓ (no CRITICAL)  │
                    supply_agent → pricing_agent → demand_agent
                                          ↓                 │
                                    synthesis_node ←────────┘
                                          ↓
                                         END

Usage:
    from orchestrator import run_pipeline
    result = run_pipeline()
"""

from langgraph.graph import StateGraph, END
from state import MarketState
from data.mock_iot_data import get_all_feeds
from llm_config import get_llm

from agents.inventory_agent import inventory_agent
from agents.customer_agent  import customer_agent
from agents.security_agent  import security_agent
from agents.supply_agent    import supply_agent
from agents.pricing_agent   import pricing_agent
from agents.demand_agent    import demand_agent


# ── Node: load data + seed RAG knowledge base ──────────────────────

def orchestrator_node(_state: MarketState) -> MarketState:
    from tools.rag_tool import seed_market_knowledge
    seed_market_knowledge()   # idempotent — no-op after first call

    feeds = get_all_feeds()
    return {
        "inventory_data":    feeds["inventory"],
        "pos_data":          feeds["pos"],
        "camera_data":       feeds["camera"],
        "audio_data":        feeds["audio"],
        "weather_data":      feeds["weather"],
        "city_events":       feeds["city_events"],
        "supply_chain_data": feeds["supply_chain"],
    }


# ── Conditional router: after security ─────────────────────────────

def route_after_security(state: MarketState) -> str:
    """Route to emergency_synthesis on CRITICAL, else continue to supply."""
    if any(a["severity"] == "CRITICAL" for a in state["alerts"]):
        return "emergency_synthesis"
    return "supply"


# ── Node: emergency synthesis (CRITICAL fast path) ─────────────────

def emergency_synthesis_node(state: MarketState) -> MarketState:
    """
    Triggered by CRITICAL alerts. Writes a focused urgent briefing to
    emergency_report. synthesis_node always runs after to produce the
    full executive summary.
    """
    llm = get_llm()

    critical_alerts = [a for a in state["alerts"] if a["severity"] == "CRITICAL"]
    high_alerts     = [a for a in state["alerts"] if a["severity"] == "HIGH"]

    prompt = f"""URGENT SITUATION: Critical safety or security events detected in the market.

CRITICAL ALERTS ({len(critical_alerts)}):
{[{'agent': a['agent'].upper(), 'shop': a['shop_id'], 'message': a['message']} for a in critical_alerts]}

HIGH SEVERITY ALERTS ({len(high_alerts)}):
{[{'agent': a['agent'].upper(), 'shop': a['shop_id'], 'message': a['message'][:80]} for a in high_alerts]}

INVENTORY STATUS: {state['inventory_output'].get('low_stock_count', 'N/A')} low-stock items
CUSTOMER STATUS: {state['customer_output'].get('crowd_surges', 0)} crowd surges detected

Write a 2-paragraph URGENT briefing for city administrators and market security:

Paragraph 1: Describe the critical situation — which shops are affected, what the specific risk is,
and whether events suggest a coordinated incident. Be direct and factual.

Paragraph 2: List exactly 3 immediate actions required in the next 30 minutes, numbered.
Prioritize life safety above all else.

Be direct. Do not discuss non-critical issues or give background context."""

    report = llm(prompt)
    return {"emergency_report": f"[EMERGENCY — {len(critical_alerts)} CRITICAL ALERT(S)]\n\n{report}"}


# ── Node: full synthesis — always runs on both paths ───────────────

def synthesis_node(state: MarketState) -> MarketState:
    """
    Produces the 3-paragraph executive summary. Always runs — on the
    emergency path the supply/pricing/demand outputs are empty, and the
    prompt acknowledges that those agents were skipped.
    """
    llm = get_llm()

    alerts   = state["alerts"]
    total    = len(alerts)
    critical = sum(1 for a in alerts if a["severity"] in ("CRITICAL", "HIGH"))
    warnings = total - critical

    inv = state["inventory_output"]
    sec = state["security_output"]
    sup = state["supply_output"]
    pri = state["pricing_output"]
    dem = state["demand_output"]

    emergency_mode = bool(state.get("emergency_report", ""))
    skipped_note   = " (skipped — emergency fast path activated)" if emergency_mode else ""

    at_risk_str = ", ".join(
        f"{r['event']} ({', '.join(r['at_risk_skus'])})"
        for r in dem.get("at_risk", [])
    ) or ("not assessed" if emergency_mode else "none")

    def _excerpt(text: str, max_chars: int = 220) -> str:
        if not text:
            return "Not assessed." if emergency_mode else "No analysis available."
        return text[:max_chars].rstrip() + ("..." if len(text) > max_chars else "")

    prompt = f"""You are a smart city market intelligence system.
Write a 3-paragraph executive summary for city administrators.
{f"NOTE: A CRITICAL security incident was detected. Supply, pricing, and demand analysis were skipped to prioritise the emergency response." if emergency_mode else ""}

QUANTITATIVE FINDINGS:
- Inventory: {inv.get('low_stock_count', 0)} low-stock items, {inv.get('ok_stock_count', 0)} OK
- Security: {sec.get('critical_count', 0)} critical/high camera events, {len(sec.get('fraud_txns', []))} suspicious transactions
- Supply chain: {sup.get('disrupted_count', 'not assessed') if emergency_mode else sup.get('disrupted_count', 0)} disrupted deliveries{skipped_note}
- Pricing: {pri.get('manipulation_count', 'not assessed') if emergency_mode else pri.get('manipulation_count', 0)} price manipulation flags{skipped_note}
- Demand risk: {at_risk_str}
- Alerts: {total} total ({critical} critical/high, {warnings} warnings)

AGENT ANALYSES:
- Inventory agent: {_excerpt(inv.get('llm_analysis', ''))}
- Security agent: {_excerpt(sec.get('llm_analysis', ''))}
- Supply agent: {_excerpt(sup.get('llm_analysis', ''))}
- Pricing agent: {_excerpt(pri.get('llm_analysis', ''))}
- Demand agent: {_excerpt(dem.get('llm_analysis', ''))}

Paragraph 1: Overall market health status (2-3 sentences).
Paragraph 2: Top 3 issues requiring immediate action today.
Paragraph 3: Recommendations for shop owners and city admin over the next 24 hours."""

    report = llm(prompt)
    return {"final_report": report}


# ── Build graph ────────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(MarketState)

    graph.add_node("orchestrator",        orchestrator_node)
    graph.add_node("inventory",           inventory_agent)
    graph.add_node("customer",            customer_agent)
    graph.add_node("security",            security_agent)
    graph.add_node("supply",              supply_agent)
    graph.add_node("pricing",             pricing_agent)
    graph.add_node("demand",              demand_agent)
    graph.add_node("synthesis",           synthesis_node)
    graph.add_node("emergency_synthesis", emergency_synthesis_node)

    graph.set_entry_point("orchestrator")
    graph.add_edge("orchestrator", "inventory")
    graph.add_edge("inventory",    "customer")
    graph.add_edge("customer",     "security")

    graph.add_conditional_edges(
        "security",
        route_after_security,
        {
            "emergency_synthesis": "emergency_synthesis",
            "supply":              "supply",
        },
    )

    # Both paths converge at synthesis
    graph.add_edge("emergency_synthesis", "synthesis")
    graph.add_edge("supply",              "pricing")
    graph.add_edge("pricing",             "demand")
    graph.add_edge("demand",              "synthesis")
    graph.add_edge("synthesis",           END)

    return graph.compile()


# ── Public entry point ─────────────────────────────────────────────

def run_pipeline() -> MarketState:
    print("[orchestrator] Initialising Groq client...")
    get_llm()

    app = build_graph()

    initial_state: MarketState = {
        "inventory_data":    [],
        "pos_data":          [],
        "camera_data":       [],
        "audio_data":        [],
        "weather_data":      {},
        "city_events":       [],
        "supply_chain_data": [],
        "inventory_output":  {},
        "customer_output":   {},
        "security_output":   {},
        "supply_output":     {},
        "pricing_output":    {},
        "demand_output":     {},
        "alerts":            [],
        "emergency_report":  "",
        "final_report":      "",
    }

    return app.invoke(initial_state)


if __name__ == "__main__":
    import json
    result = run_pipeline()

    if result.get("emergency_report"):
        print("\n" + "="*60)
        print("EMERGENCY BRIEFING")
        print("="*60)
        print(result["emergency_report"])

    print("\n" + "="*60)
    print("EXECUTIVE SUMMARY")
    print("="*60)
    print(result["final_report"])

    print("\n" + "="*60)
    print(f"ALERTS ({len(result['alerts'])} total)")
    print("="*60)
    print(json.dumps(result["alerts"], indent=2, default=str))
