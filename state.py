"""
state.py
--------
Shared LangGraph state schema.
Every agent reads from and writes to this TypedDict.
operator.add on alerts means each agent's new alerts 
are appended to the list rather than overwriting it.
"""

from typing import TypedDict, Annotated
import operator


class MarketState(TypedDict):
    # ── Raw feeds (loaded by orchestrator_node) ───────────────────
    inventory_data:    list[dict]
    pos_data:          list[dict]
    camera_data:       list[dict]
    audio_data:        list[dict]
    weather_data:      dict
    city_events:       list[dict]
    supply_chain_data: list[dict]

    # ── Agent outputs ─────────────────────────────────────────────
    inventory_output:  dict
    customer_output:   dict
    security_output:   dict
    supply_output:     dict
    pricing_output:    dict
    demand_output:     dict

    # ── Alerts: appended by every agent, never overwritten ────────
    alerts: Annotated[list[dict], operator.add]

    # ── Final synthesis output ────────────────────────────────────
    emergency_report: str   # populated only on CRITICAL fast path
    final_report:     str   # executive summary — always populated