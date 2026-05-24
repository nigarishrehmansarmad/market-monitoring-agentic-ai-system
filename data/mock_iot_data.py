"""
mock_iot_data.py
----------------
Hardcoded + lightly randomized mock IoT sensor data for the
Agentic AI Local Market Monitoring System.

Covers all 4 data sources:
  1. IoT Sensors      — POS transactions, inventory stock levels
  2. Vision System    — Camera events (foot traffic, suspicious behavior)
  3. Audio Monitor    — Shopkeeper-customer negotiation transcripts
  4. External APIs    — Weather, city events, logistics/supply chain

Usage:
    from mock_iot_data import get_all_feeds
    feeds = get_all_feeds()

    # Or per-source:
    from mock_iot_data import (
        get_inventory_snapshot,
        get_pos_transactions,
        get_camera_events,
        get_audio_transcripts,
        get_weather_data,
        get_city_events,
        get_supply_chain_status,
    )
"""

import random
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────

SHOPS = ["SHOP_001", "SHOP_002", "SHOP_003", "SHOP_004", "SHOP_005"]
BASE_TIME = datetime(2026, 5, 23, 9, 0, 0)  # Market opens 9 AM

random.seed(42)  # Reproducible results


def _ts(offset_minutes: int) -> str:
    return (BASE_TIME + timedelta(minutes=offset_minutes)).isoformat()


# ─────────────────────────────────────────────
# 1. INVENTORY SENSOR DATA
# ─────────────────────────────────────────────

INVENTORY_CATALOG = [
    {"sku": "RICE_5KG",     "name": "Basmati Rice 5kg",    "unit": "bags",    "reorder_point": 20},
    {"sku": "OIL_1L",       "name": "Cooking Oil 1L",      "unit": "bottles", "reorder_point": 15},
    {"sku": "FLOUR_2KG",    "name": "Wheat Flour 2kg",     "unit": "packets", "reorder_point": 25},
    {"sku": "SUGAR_1KG",    "name": "Sugar 1kg",           "unit": "packets", "reorder_point": 30},
    {"sku": "MILK_1L",      "name": "Milk 1L",             "unit": "cartons", "reorder_point": 40},
    {"sku": "EGGS_12",      "name": "Eggs (dozen)",        "unit": "trays",   "reorder_point": 20},
    {"sku": "BREAD_400G",   "name": "Bread 400g",          "unit": "loaves",  "reorder_point": 15},
    {"sku": "TOMATO_1KG",   "name": "Tomatoes 1kg",        "unit": "kg",      "reorder_point": 10},
]

# Hardcoded stock levels per shop (some deliberately below reorder point to trigger alerts)
_STOCK_BASE = {
    "SHOP_001": {"RICE_5KG": 45, "OIL_1L": 8,  "FLOUR_2KG": 30, "SUGAR_1KG": 12,
                 "MILK_1L": 55, "EGGS_12": 18, "BREAD_400G": 22, "TOMATO_1KG": 6},
    "SHOP_002": {"RICE_5KG": 60, "OIL_1L": 20, "FLOUR_2KG": 5,  "SUGAR_1KG": 40,
                 "MILK_1L": 35, "EGGS_12": 25, "BREAD_400G": 10, "TOMATO_1KG": 14},
    "SHOP_003": {"RICE_5KG": 15, "OIL_1L": 30, "FLOUR_2KG": 28, "SUGAR_1KG": 50,
                 "MILK_1L": 10, "EGGS_12": 35, "BREAD_400G": 18, "TOMATO_1KG": 20},
    "SHOP_004": {"RICE_5KG": 80, "OIL_1L": 18, "FLOUR_2KG": 40, "SUGAR_1KG": 22,
                 "MILK_1L": 60, "EGGS_12": 12, "BREAD_400G": 30, "TOMATO_1KG": 8},
    "SHOP_005": {"RICE_5KG": 25, "OIL_1L": 45, "FLOUR_2KG": 15, "SUGAR_1KG": 35,
                 "MILK_1L": 28, "EGGS_12": 42, "BREAD_400G": 12, "TOMATO_1KG": 18},
}


def get_inventory_snapshot() -> list[dict]:
    """
    Returns current stock levels for all shops.
    Flags items below reorder point automatically.
    """
    snapshot = []
    reorder_map = {item["sku"]: item["reorder_point"] for item in INVENTORY_CATALOG}
    name_map = {item["sku"]: item["name"] for item in INVENTORY_CATALOG}

    for shop_id, stock in _STOCK_BASE.items():
        for sku, qty in stock.items():
            reorder_pt = reorder_map[sku]
            snapshot.append({
                "timestamp": _ts(0),
                "shop_id": shop_id,
                "sku": sku,
                "product_name": name_map[sku],
                "quantity_in_stock": qty,
                "reorder_point": reorder_pt,
                "status": "LOW_STOCK" if qty <= reorder_pt else "OK",
                "sales_velocity_per_hour": round(random.uniform(0.5, 3.5), 2),
            })
    return snapshot


# ─────────────────────────────────────────────
# 2. POS TRANSACTION DATA
# ─────────────────────────────────────────────

_POS_TRANSACTIONS = [
    # (shop_id, sku, qty, unit_price_pkr, offset_min, payment_method, anomaly_flag)
    ("SHOP_001", "RICE_5KG",   2, 850,  5,  "cash",   False),
    ("SHOP_001", "OIL_1L",     3, 320,  8,  "cash",   False),
    ("SHOP_001", "MILK_1L",    5, 180,  12, "card",   False),
    ("SHOP_001", "SUGAR_1KG",  10, 130, 15, "cash",   True),   # bulk buy — anomaly
    ("SHOP_002", "FLOUR_2KG",  4, 240,  7,  "cash",   False),
    ("SHOP_002", "EGGS_12",    2, 360,  20, "cash",   False),
    ("SHOP_002", "BREAD_400G", 6, 120,  25, "card",   False),
    ("SHOP_003", "RICE_5KG",   1, 860,  10, "cash",   False),
    ("SHOP_003", "TOMATO_1KG", 3, 95,   30, "cash",   False),
    ("SHOP_003", "OIL_1L",     8, 310,  35, "cash",   True),   # possible bulk/resale
    ("SHOP_004", "MILK_1L",    12, 175, 18, "card",   False),
    ("SHOP_004", "EGGS_12",    5, 355,  40, "cash",   False),
    ("SHOP_004", "SUGAR_1KG",  3, 140,  45, "cash",   False),
    ("SHOP_005", "FLOUR_2KG",  2, 245,  22, "cash",   False),
    ("SHOP_005", "BREAD_400G", 4, 125,  50, "cash",   False),
    ("SHOP_005", "RICE_5KG",   20, 820, 55, "cash",   True),   # price below market — anomaly
]


def get_pos_transactions() -> list[dict]:
    """Returns POS transaction log for the current session."""
    transactions = []
    for i, (shop, sku, qty, price, offset, method, anomaly) in enumerate(_POS_TRANSACTIONS):
        transactions.append({
            "transaction_id": f"TXN_{i+1:04d}",
            "timestamp": _ts(offset),
            "shop_id": shop,
            "sku": sku,
            "quantity": qty,
            "unit_price_pkr": price,
            "total_pkr": qty * price,
            "payment_method": method,
            "anomaly_flag": anomaly,
            "anomaly_reason": (
                "Unusually large quantity or below-market price" if anomaly else None
            ),
        })
    return transactions


# ─────────────────────────────────────────────
# 3. VISION / CAMERA EVENTS
# ─────────────────────────────────────────────

_CAMERA_EVENTS = [
    # (shop_id, event_type, severity, person_count, offset_min, description)
    ("SHOP_001", "FOOT_TRAFFIC",      "INFO",     12, 0,  "Normal morning crowd entering"),
    ("SHOP_001", "DWELL_TIME_HIGH",   "WARNING",  1,  10, "Customer lingering near cash register >5 min"),
    ("SHOP_002", "FOOT_TRAFFIC",      "INFO",     8,  5,  "Moderate traffic, queue forming at counter"),
    ("SHOP_002", "SUSPICIOUS_BEHAVIOR","HIGH",    1,  20, "Individual concealing item under clothing"),
    ("SHOP_003", "CROWD_SURGE",       "WARNING",  35, 15, "Unexpected crowd surge — possible event nearby"),
    ("SHOP_003", "FOOT_TRAFFIC",      "INFO",     15, 0,  "Normal traffic"),
    ("SHOP_004", "ALTERCATION",       "HIGH",     2,  30, "Physical confrontation detected between two individuals"),
    ("SHOP_004", "FOOT_TRAFFIC",      "INFO",     6,  0,  "Low morning traffic"),
    ("SHOP_005", "UNATTENDED_BAG",    "HIGH",     0,  25, "Unattended bag left near entrance for >3 min"),
    ("SHOP_005", "FOOT_TRAFFIC",      "INFO",     10, 0,  "Normal traffic"),
]


def get_camera_events() -> list[dict]:
    """Returns vision system events from security cameras."""
    events = []
    for i, (shop, event_type, severity, count, offset, desc) in enumerate(_CAMERA_EVENTS):
        events.append({
            "event_id": f"CAM_{i+1:04d}",
            "timestamp": _ts(offset),
            "shop_id": shop,
            "camera_id": f"CAM_{shop}_{i+1:02d}",
            "event_type": event_type,
            "severity": severity,
            "person_count": count,
            "description": desc,
            "action_required": severity in ("HIGH", "CRITICAL"),
        })
    return events


# ─────────────────────────────────────────────
# 4. AUDIO MONITOR — NEGOTIATION TRANSCRIPTS
# ─────────────────────────────────────────────

_AUDIO_TRANSCRIPTS = [
    {
        "shop_id": "SHOP_001",
        "offset_min": 8,
        "sku": "OIL_1L",
        "transcript": (
            "Customer: Bhai, oil ka kya rate hai? "
            "Shopkeeper: 320 rupay liter. "
            "Customer: 300 mein dedo, zyada le raha hoon. "
            "Shopkeeper: Theek hai, 310 final."
        ),
        "agreed_price_pkr": 310,
        "listed_price_pkr": 320,
        "discount_pct": 3.1,
        "sentiment": "POSITIVE",
        "price_manipulation_flag": False,
    },
    {
        "shop_id": "SHOP_002",
        "offset_min": 22,
        "sku": "RICE_5KG",
        "transcript": (
            "Customer: Rice kitne ka diya? "
            "Shopkeeper: 900 rupay. "
            "Customer: Kal 850 tha, aaj itna mehenga kyun? "
            "Shopkeeper: Supply kam hai, sab ne barhaya hai."
        ),
        "agreed_price_pkr": 900,
        "listed_price_pkr": 850,
        "discount_pct": -5.9,
        "sentiment": "NEGATIVE",
        "price_manipulation_flag": True,  # sudden unexplained price hike
    },
    {
        "shop_id": "SHOP_003",
        "offset_min": 35,
        "sku": "SUGAR_1KG",
        "transcript": (
            "Customer: Sugar ka rate? "
            "Shopkeeper: 140 rupay. "
            "Customer: Okay, 5 packet dena. "
            "Shopkeeper: Ji zaroor."
        ),
        "agreed_price_pkr": 140,
        "listed_price_pkr": 140,
        "discount_pct": 0.0,
        "sentiment": "NEUTRAL",
        "price_manipulation_flag": False,
    },
    {
        "shop_id": "SHOP_004",
        "offset_min": 42,
        "sku": "FLOUR_2KG",
        "transcript": (
            "Customer: Aata kab aayega stock mein? Kal se nahi hai. "
            "Shopkeeper: Supplier ne bataya parson tak delivery aayegi. "
            "Customer: Parson tak kaise guzara karein? "
            "Shopkeeper: Sorry, hamare paas bhi nahi hai abhi."
        ),
        "agreed_price_pkr": None,
        "listed_price_pkr": 240,
        "discount_pct": None,
        "sentiment": "NEGATIVE",
        "price_manipulation_flag": False,
        "supply_signal": "STOCKOUT_REPORTED",  # supply chain signal
    },
    {
        "shop_id": "SHOP_005",
        "offset_min": 50,
        "sku": "TOMATO_1KG",
        "transcript": (
            "Customer: Tamatar kitne ke hain? "
            "Shopkeeper: 95 rupay kilo. "
            "Customer: Market mein sab ne 95 rakha hai aaj. "
            "Shopkeeper: Haan, aaj sab ka same rate hai."
        ),
        "agreed_price_pkr": 95,
        "listed_price_pkr": 95,
        "discount_pct": 0.0,
        "sentiment": "NEUTRAL",
        "price_manipulation_flag": True,  # coordinated same price across shops — cartel signal
        "cartel_signal": "UNIFORM_PRICING_ACROSS_SHOPS",
    },
]


def get_audio_transcripts() -> list[dict]:
    """Returns audio monitor transcripts with pricing and sentiment analysis."""
    transcripts = []
    for i, item in enumerate(_AUDIO_TRANSCRIPTS):
        transcripts.append({
            "audio_id": f"AUD_{i+1:04d}",
            "timestamp": _ts(item["offset_min"]),
            **item,
        })
    return transcripts


# ─────────────────────────────────────────────
# 5. WEATHER DATA
# ─────────────────────────────────────────────

def get_weather_data() -> dict:
    """Returns current weather snapshot for the city."""
    return {
        "timestamp": _ts(0),
        "city": "Karachi",
        "temperature_c": 34,
        "humidity_pct": 72,
        "condition": "Partly Cloudy",
        "wind_speed_kmh": 18,
        "rain_probability_pct": 15,
        "heat_index_c": 40,
        "forecast_24h": [
            {"hour": "12:00", "temp_c": 37, "condition": "Sunny",        "rain_pct": 5},
            {"hour": "15:00", "temp_c": 38, "condition": "Hot",          "rain_pct": 8},
            {"hour": "18:00", "temp_c": 35, "condition": "Partly Cloudy","rain_pct": 20},
            {"hour": "21:00", "temp_c": 31, "condition": "Clear",        "rain_pct": 10},
        ],
        "demand_impact": "HIGH_TEMP: Expect increased demand for cold drinks, ice, dairy",
    }


# ─────────────────────────────────────────────
# 6. CITY EVENTS
# ─────────────────────────────────────────────

def get_city_events() -> list[dict]:
    """Returns upcoming city events that may affect market demand."""
    return [
        {
            "event_id": "EVT_001",
            "name": "Eid ul-Adha Preparation Week",
            "type": "RELIGIOUS_FESTIVAL",
            "start_date": "2026-06-04",
            "end_date": "2026-06-08",
            "days_away": 12,
            "expected_footfall_multiplier": 2.5,
            "high_demand_skus": ["RICE_5KG", "OIL_1L", "SUGAR_1KG", "FLOUR_2KG"],
            "demand_urgency": "HIGH",
        },
        {
            "event_id": "EVT_002",
            "name": "Local School Exams End — Summer Break Starts",
            "type": "SEASONAL",
            "start_date": "2026-05-30",
            "end_date": "2026-07-31",
            "days_away": 7,
            "expected_footfall_multiplier": 1.3,
            "high_demand_skus": ["MILK_1L", "BREAD_400G", "EGGS_12"],
            "demand_urgency": "MEDIUM",
        },
        {
            "event_id": "EVT_003",
            "name": "Friday Bazaar — Weekly Market Day",
            "type": "WEEKLY_RECURRING",
            "start_date": "2026-05-29",
            "end_date": "2026-05-29",
            "days_away": 6,
            "expected_footfall_multiplier": 1.8,
            "high_demand_skus": ["TOMATO_1KG", "RICE_5KG", "OIL_1L"],
            "demand_urgency": "MEDIUM",
        },
    ]


# ─────────────────────────────────────────────
# 7. SUPPLY CHAIN STATUS
# ─────────────────────────────────────────────

def get_supply_chain_status() -> list[dict]:
    """Returns current delivery and supplier status."""
    return [
        {
            "delivery_id": "DEL_001",
            "supplier": "Karachi Wholesale Grains Co.",
            "shop_id": "SHOP_001",
            "sku": "RICE_5KG",
            "expected_delivery": _ts(180),   # 3 hours from now
            "status": "ON_TIME",
            "quantity_ordered": 100,
            "disruption_flag": False,
            "supplier_reliability_score": 0.92,
        },
        {
            "delivery_id": "DEL_002",
            "supplier": "Pak Edible Oils Ltd.",
            "shop_id": "SHOP_002",
            "sku": "OIL_1L",
            "expected_delivery": _ts(360),   # 6 hours from now
            "status": "DELAYED",
            "quantity_ordered": 50,
            "disruption_flag": True,
            "disruption_reason": "Traffic congestion on Superhighway — estimated 2hr delay",
            "supplier_reliability_score": 0.78,
        },
        {
            "delivery_id": "DEL_003",
            "supplier": "Punjab Flour Mills",
            "shop_id": "SHOP_002",
            "sku": "FLOUR_2KG",
            "expected_delivery": _ts(2880),  # 2 days from now
            "status": "DELAYED",
            "quantity_ordered": 80,
            "disruption_flag": True,
            "disruption_reason": "Mill strike — production halted, rescheduled to day after tomorrow",
            "supplier_reliability_score": 0.65,
            "alternative_supplier": "Sindh Flour Distributors (available same day)",
        },
        {
            "delivery_id": "DEL_004",
            "supplier": "City Dairy Farm",
            "shop_id": "SHOP_003",
            "sku": "MILK_1L",
            "expected_delivery": _ts(60),
            "status": "ON_TIME",
            "quantity_ordered": 120,
            "disruption_flag": False,
            "supplier_reliability_score": 0.95,
        },
        {
            "delivery_id": "DEL_005",
            "supplier": "Fresh Veggie Traders",
            "shop_id": "SHOP_004",
            "sku": "TOMATO_1KG",
            "expected_delivery": _ts(90),
            "status": "ON_TIME",
            "quantity_ordered": 40,
            "disruption_flag": False,
            "supplier_reliability_score": 0.88,
        },
    ]


# ─────────────────────────────────────────────
# UNIFIED FEED
# ─────────────────────────────────────────────

def get_all_feeds() -> dict:
    """
    Returns all data feeds in a single dict.
    This is what the LangGraph ingestion node should call.
    """
    return {
        "inventory":     get_inventory_snapshot(),
        "pos":           get_pos_transactions(),
        "camera":        get_camera_events(),
        "audio":         get_audio_transcripts(),
        "weather":       get_weather_data(),
        "city_events":   get_city_events(),
        "supply_chain":  get_supply_chain_status(),
    }


# ─────────────────────────────────────────────
# Quick test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import json
    feeds = get_all_feeds()
    for feed_name, data in feeds.items():
        print(f"\n{'='*50}")
        print(f"  {feed_name.upper()}")
        print(f"{'='*50}")
        print(json.dumps(data, indent=2, default=str))