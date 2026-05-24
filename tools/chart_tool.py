"""
tools/chart_tool.py
--------------------
Shared charting utility for all agents.
Each agent calls the relevant function, gets back a saved .png path.
All charts use only the data explicitly passed in — no inference.

Output folder: ./charts/  (auto-created)
"""

import os
import matplotlib
matplotlib.use("Agg")   # non-interactive backend — no display needed
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

CHART_DIR = "./charts"
os.makedirs(CHART_DIR, exist_ok=True)

COLORS = {
    "ok":       "#4CAF50",
    "warning":  "#FF9800",
    "high":     "#F44336",
    "critical": "#B71C1C",
    "neutral":  "#90A4AE",
    "blue":     "#1976D2",
    "teal":     "#00796B",
    "purple":   "#7B1FA2",
}


def _save(fig, filename: str) -> str:
    path = os.path.join(CHART_DIR, filename)
    fig.savefig(path, bbox_inches="tight", dpi=120)
    plt.close(fig)
    return path


# ── Inventory: stock level bar chart ─────────────────────────────

def chart_stock_levels(inventory_data: list[dict]) -> str:
    """Bar chart of stock qty vs reorder point per SKU per shop."""
    if not inventory_data:
        return ""

    labels  = [f"{d['shop_id']}\n{d['sku']}" for d in inventory_data]
    qty     = [d["quantity_in_stock"] for d in inventory_data]
    reorder = [d["reorder_point"]     for d in inventory_data]
    colors  = [COLORS["high"] if d["status"] == "LOW_STOCK" else COLORS["ok"]
               for d in inventory_data]

    x   = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(max(10, len(labels) * 0.6), 5))

    bars = ax.bar(x, qty, color=colors, width=0.5, label="Stock qty")
    ax.plot(x, reorder, "o--", color=COLORS["warning"],
            linewidth=1.5, markersize=5, label="Reorder point")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7, rotation=45, ha="right")
    ax.set_ylabel("Units")
    ax.set_title("Stock levels vs reorder points", fontweight="bold")
    ax.legend()

    low_patch  = mpatches.Patch(color=COLORS["high"],   label="Low stock")
    ok_patch   = mpatches.Patch(color=COLORS["ok"],     label="OK")
    ax.legend(handles=[low_patch, ok_patch,
              mpatches.Patch(color=COLORS["warning"], label="Reorder point")])

    fig.tight_layout()
    return _save(fig, "inventory_stock_levels.png")


def chart_sales_velocity(pos_data: list[dict]) -> str:
    """Bar chart of total sales value per shop."""
    if not pos_data:
        return ""

    shop_totals: dict = {}
    for t in pos_data:
        shop_totals[t["shop_id"]] = shop_totals.get(t["shop_id"], 0) + t["total_pkr"]

    shops  = list(shop_totals.keys())
    totals = list(shop_totals.values())
    colors = [COLORS["blue"]] * len(shops)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(shops, totals, color=colors, width=0.5)
    ax.set_ylabel("Total sales (PKR)")
    ax.set_title("Sales value per shop (current session)", fontweight="bold")
    for i, v in enumerate(totals):
        ax.text(i, v + 50, f"Rs{v:,}", ha="center", fontsize=8)
    fig.tight_layout()
    return _save(fig, "inventory_sales_by_shop.png")


# ── Security: event severity breakdown ───────────────────────────

def chart_security_events(camera_data: list[dict]) -> str:
    """Stacked bar of event types per shop, colored by severity."""
    if not camera_data:
        return ""

    severity_order = ["INFO", "WARNING", "HIGH", "CRITICAL"]
    color_map = {
        "INFO":     COLORS["ok"],
        "WARNING":  COLORS["warning"],
        "HIGH":     COLORS["high"],
        "CRITICAL": COLORS["critical"],
    }

    shops = sorted({e["shop_id"] for e in camera_data})
    data  = {sev: [0] * len(shops) for sev in severity_order}

    for e in camera_data:
        si = shops.index(e["shop_id"])
        data[e["severity"]][si] += 1

    fig, ax = plt.subplots(figsize=(8, 4))
    bottom = np.zeros(len(shops))
    for sev in severity_order:
        vals = np.array(data[sev])
        ax.bar(shops, vals, bottom=bottom,
               color=color_map[sev], label=sev, width=0.5)
        bottom += vals

    ax.set_ylabel("Event count")
    ax.set_title("Security events by shop and severity", fontweight="bold")
    ax.legend(loc="upper right")
    fig.tight_layout()
    return _save(fig, "security_events.png")


# ── Customer: foot traffic + sentiment ───────────────────────────

def chart_foot_traffic(camera_data: list[dict]) -> str:
    """Bar chart of person count per shop from FOOT_TRAFFIC events."""
    traffic = [e for e in camera_data if e["event_type"] == "FOOT_TRAFFIC"]
    if not traffic:
        return ""

    shops  = [e["shop_id"]     for e in traffic]
    counts = [e["person_count"] for e in traffic]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(shops, counts, color=COLORS["teal"], width=0.5)
    ax.axhline(y=sum(counts)/len(counts), color=COLORS["warning"],
               linestyle="--", linewidth=1.5, label="Average")
    ax.set_ylabel("Person count")
    ax.set_title("Foot traffic per shop", fontweight="bold")
    ax.legend()
    fig.tight_layout()
    return _save(fig, "customer_foot_traffic.png")


def chart_sentiment(audio_data: list[dict]) -> str:
    """Pie chart of sentiment distribution across all shops."""
    sentiments = [a.get("sentiment") for a in audio_data if a.get("sentiment")]
    if not sentiments:
        return ""

    labels = ["POSITIVE", "NEUTRAL", "NEGATIVE"]
    counts = [sentiments.count(l) for l in labels]
    colors = [COLORS["ok"], COLORS["neutral"], COLORS["high"]]
    # Filter out zero-count segments
    filtered = [(l, c, col) for l, c, col in zip(labels, counts, colors) if c > 0]
    if not filtered:
        return ""
    labels_f, counts_f, colors_f = zip(*filtered)

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(counts_f, labels=labels_f, colors=colors_f,
           autopct="%1.0f%%", startangle=90)
    ax.set_title("Customer sentiment distribution", fontweight="bold")
    fig.tight_layout()
    return _save(fig, "customer_sentiment.png")


# ── Supply chain: delivery status ────────────────────────────────

def chart_supply_status(supply_data: list[dict]) -> str:
    """Horizontal bar showing each delivery and its status."""
    if not supply_data:
        return ""

    labels   = [f"{d['supplier'][:20]}\n→ {d['shop_id']}" for d in supply_data]
    colors   = [COLORS["high"] if d["disruption_flag"] else COLORS["ok"]
                for d in supply_data]
    scores   = [d.get("supplier_reliability_score", 0) for d in supply_data]

    fig, ax = plt.subplots(figsize=(8, max(4, len(labels) * 0.8)))
    y = np.arange(len(labels))
    ax.barh(y, scores, color=colors, height=0.5)
    ax.set_xlim(0, 1.1)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Supplier reliability score")
    ax.set_title("Supply chain status", fontweight="bold")
    ax.axvline(x=0.8, color=COLORS["warning"], linestyle="--",
               linewidth=1.5, label="Min acceptable (0.8)")
    ax.legend()

    for i, (score, d) in enumerate(zip(scores, supply_data)):
        status = "DELAYED" if d["disruption_flag"] else "ON TIME"
        ax.text(score + 0.02, i, status, va="center", fontsize=8)

    fig.tight_layout()
    return _save(fig, "supply_chain_status.png")


# ── Pricing: price vs listed per transcript ───────────────────────

def chart_pricing(audio_data: list[dict]) -> str:
    """Bar chart comparing agreed price vs listed price per transaction."""
    valid = [a for a in audio_data
             if a.get("agreed_price_pkr") and a.get("listed_price_pkr")]
    if not valid:
        return ""

    labels  = [f"{a['shop_id']}\n{a['sku']}" for a in valid]
    listed  = [a["listed_price_pkr"]  for a in valid]
    agreed  = [a["agreed_price_pkr"]  for a in valid]
    colors  = [COLORS["high"] if a.get("price_manipulation_flag")
               else COLORS["teal"] for a in valid]

    x   = np.arange(len(labels))
    w   = 0.35
    fig, ax = plt.subplots(figsize=(max(7, len(labels) * 1.2), 5))
    ax.bar(x - w/2, listed, w, label="Listed price", color=COLORS["neutral"])
    ax.bar(x + w/2, agreed, w, label="Agreed price", color=colors)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8, rotation=30, ha="right")
    ax.set_ylabel("Price (PKR)")
    ax.set_title("Listed vs negotiated prices", fontweight="bold")

    flag_patch = mpatches.Patch(color=COLORS["high"],  label="Flagged")
    ok_patch   = mpatches.Patch(color=COLORS["teal"],  label="Normal")
    ax.legend(handles=[
        mpatches.Patch(color=COLORS["neutral"], label="Listed"),
        ok_patch, flag_patch
    ])
    fig.tight_layout()
    return _save(fig, "pricing_comparison.png")


# ── Demand: event demand multiplier ──────────────────────────────

def chart_demand_forecast(city_events: list[dict],
                          inventory_data: list[dict]) -> str:
    """Bar chart of expected footfall multiplier per upcoming event."""
    if not city_events:
        return ""

    low_skus = {i["sku"] for i in inventory_data if i["status"] == "LOW_STOCK"}

    names       = [e["name"][:25]                      for e in city_events]
    multipliers = [e["expected_footfall_multiplier"]   for e in city_events]
    days_away   = [e["days_away"]                      for e in city_events]
    # Red if any high-demand SKU for this event is already low stock
    colors = [
        COLORS["high"] if set(e.get("high_demand_skus", [])) & low_skus
        else COLORS["teal"]
        for e in city_events
    ]

    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(len(names))
    bars = ax.bar(x, multipliers, color=colors, width=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(
        [f"{n}\n(in {d}d)" for n, d in zip(names, days_away)],
        fontsize=8
    )
    ax.set_ylabel("Expected footfall multiplier")
    ax.set_title("Upcoming events — demand impact", fontweight="bold")
    ax.axhline(y=1.0, color=COLORS["neutral"], linestyle="--",
               linewidth=1, label="Baseline (1.0x)")

    risk_patch = mpatches.Patch(color=COLORS["high"], label="Has low-stock SKUs")
    ok_patch   = mpatches.Patch(color=COLORS["teal"], label="Stock OK")
    ax.legend(handles=[risk_patch, ok_patch,
              mpatches.Patch(color=COLORS["neutral"], label="Baseline")])
    fig.tight_layout()
    return _save(fig, "demand_forecast.png")