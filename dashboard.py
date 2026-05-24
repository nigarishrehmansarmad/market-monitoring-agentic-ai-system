"""
dashboard.py — streamlit run dashboard.py
"""

import streamlit as st
import os
import random
import math
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Smart City Market Monitor",
    page_icon="🏙",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Dark theme CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Root palette */
  :root {
    --bg:        #0d1117;
    --card:      #161b27;
    --border:    #21262d;
    --accent:    #1f6feb;
    --accent2:   #388bfd;
    --green:     #3fb950;
    --red:       #f85149;
    --orange:    #d29922;
    --yellow:    #e3b341;
    --text:      #c9d1d9;
    --text-dim:  #8b949e;
    --text-head: #f0f6fc;
  }

  /* Force dark background everywhere */
  html, body, [data-testid="stApp"],
  [data-testid="stAppViewContainer"],
  [data-testid="stMain"],
  section.main, .block-container {
    background-color: var(--bg) !important;
    color: var(--text) !important;
  }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background-color: #0d1117 !important;
    border-right: 1px solid var(--border) !important;
  }
  [data-testid="stSidebar"] * { color: var(--text) !important; }

  /* Remove default padding */
  .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }

  /* Buttons */
  .stButton > button {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
  }
  .stButton > button:hover { background: var(--accent2) !important; }

  /* Selectbox / radio */
  .stSelectbox > div > div,
  .stRadio > div { background: var(--card) !important; border-color: var(--border) !important; }

  /* KPI card */
  .kpi-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px 18px;
    text-align: center;
  }
  .kpi-label { font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: .08em; margin-bottom: 4px; }
  .kpi-value { font-size: 2rem; font-weight: 700; color: var(--text-head); line-height: 1; }
  .kpi-delta { font-size: 0.72rem; margin-top: 4px; }
  .delta-up   { color: var(--green); }
  .delta-down { color: var(--red); }
  .delta-neu  { color: var(--text-dim); }

  /* Agent status card */
  .agent-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
    height: 100%;
  }
  .agent-card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }
  .agent-name { font-size: 0.92rem; font-weight: 600; color: var(--text-head); }
  .badge { font-size: 0.68rem; font-weight: 600; padding: 2px 8px; border-radius: 20px; }
  .badge-green  { background: rgba(63,185,80,.15); color: var(--green); border: 1px solid rgba(63,185,80,.3); }
  .badge-red    { background: rgba(248,81,73,.15);  color: var(--red);   border: 1px solid rgba(248,81,73,.3); }
  .badge-orange { background: rgba(210,153,34,.15); color: var(--orange);border: 1px solid rgba(210,153,34,.3); }
  .agent-meta   { font-size: 0.72rem; color: var(--text-dim); margin-bottom: 12px; }
  .agent-metric { font-size: 0.8rem; color: var(--text-dim); margin-bottom: 2px; }
  .agent-metric span { color: var(--text-head); font-weight: 600; }

  /* Section card wrapper */
  .section-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px 20px;
  }
  .section-title { font-size: 0.9rem; font-weight: 700; color: var(--text-head); text-transform: uppercase; letter-spacing: .06em; margin-bottom: 14px; }

  /* Event stream */
  .event-item {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 8px 0; border-bottom: 1px solid var(--border);
    font-size: 0.78rem;
  }
  .event-item:last-child { border-bottom: none; }
  .event-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 3px; }
  .dot-red    { background: var(--red); }
  .dot-orange { background: var(--orange); }
  .dot-yellow { background: var(--yellow); }
  .dot-green  { background: var(--green); }
  .dot-blue   { background: var(--accent2); }
  .event-time { color: var(--text-dim); white-space: nowrap; }
  .event-msg  { color: var(--text); }

  /* Alert summary */
  .alert-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 8px 0; border-bottom: 1px solid var(--border);
    font-size: 0.82rem;
  }
  .alert-row:last-child { border-bottom: none; }
  .alert-count { font-size: 1.3rem; font-weight: 700; }

  /* Insights table */
  .ins-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
  .ins-table th { color: var(--text-dim); font-weight: 600; text-transform: uppercase; font-size: 0.68rem;
                  letter-spacing: .08em; padding: 6px 10px; border-bottom: 1px solid var(--border); text-align: left; }
  .ins-table td { padding: 9px 10px; border-bottom: 1px solid rgba(33,38,45,.6); color: var(--text); vertical-align: middle; }
  .ins-table tr:last-child td { border-bottom: none; }
  .ins-table tr:hover td { background: rgba(255,255,255,.03); }

  /* Dividers */
  hr { border-color: var(--border) !important; }

  /* Plotly charts background fix */
  .js-plotly-plot .plotly, .plot-container { background: transparent !important; }

  /* Status topbar */
  .topbar {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 20px; padding-bottom: 14px; border-bottom: 1px solid var(--border);
  }
  .topbar-title { font-size: 1.4rem; font-weight: 700; color: var(--text-head); }
  .topbar-right { display: flex; align-items: center; gap: 16px; font-size: 0.78rem; color: var(--text-dim); }
  .status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: var(--green);
                box-shadow: 0 0 6px var(--green); margin-right: 5px; }

  /* Sidebar nav */
  .nav-section { font-size: 0.65rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: .12em;
                 padding: 12px 0 4px 0; font-weight: 700; }
  .nav-item { font-size: 0.83rem; padding: 6px 10px; border-radius: 6px; cursor: pointer;
              color: var(--text); margin-bottom: 2px; transition: background .15s; }
  .nav-item:hover, .nav-item.active { background: rgba(31,111,235,.15); color: var(--accent2); }

  /* Agent detail analysis box */
  .analysis-box {
    background: rgba(255,255,255,.03);
    border-left: 3px solid var(--accent);
    border-radius: 4px;
    padding: 12px 14px;
    font-size: 0.83rem;
    color: var(--text);
    line-height: 1.6;
    margin-bottom: 12px;
  }

  /* Hide Streamlit default elements */
  #MainMenu, footer { visibility: hidden; }
  [data-testid="stDecoration"] { display: none; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _sparkline_svg(values: list, color: str = "#388bfd", width: int = 80, height: int = 28) -> str:
    if not values or len(values) < 2:
        return ""
    mn, mx = min(values), max(values)
    rng = mx - mn or 1
    pts = []
    for i, v in enumerate(values):
        x = i / (len(values) - 1) * width
        y = height - (v - mn) / rng * height
        pts.append(f"{x:.1f},{y:.1f}")
    path = " ".join(pts)
    return (
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">'
        f'<polyline points="{path}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
        f'</svg>'
    )


def _severity_dot(severity: str) -> str:
    return {"CRITICAL": "dot-red", "HIGH": "dot-orange", "WARNING": "dot-yellow"}.get(severity, "dot-blue")


def _severity_color(severity: str) -> str:
    return {"CRITICAL": "#f85149", "HIGH": "#d29922", "WARNING": "#e3b341"}.get(severity, "#388bfd")


def _badge(text: str, kind: str = "green") -> str:
    return f'<span class="badge badge-{kind}">{text}</span>'


def _agent_badge(alerts: list, agent_key: str) -> tuple[str, str]:
    """Returns (badge_html, kind) based on agent's worst alert."""
    worst = None
    for a in alerts:
        if a.get("agent") == agent_key:
            s = a["severity"]
            if s == "CRITICAL":
                worst = "CRITICAL"
                break
            elif s == "HIGH" and worst != "CRITICAL":
                worst = "HIGH"
            elif s == "WARNING" and worst not in ("CRITICAL", "HIGH"):
                worst = "WARNING"
    if worst == "CRITICAL":
        return _badge("Critical", "red"), "red"
    elif worst == "HIGH":
        return _badge("Warning", "orange"), "orange"
    elif worst == "WARNING":
        return _badge("Caution", "orange"), "orange"
    return _badge("Healthy", "green"), "green"


def _random_sparkline(n: int = 12, base: int = 60, noise: int = 20) -> list:
    random.seed(42)
    return [base + random.randint(-noise, noise) for _ in range(n)]


def _agent_events(result: dict, key: str) -> int:
    out = result.get(f"{key}_output", {})
    fields = ["low_stock_count", "ok_stock_count", "crowd_surges", "critical_count",
              "disrupted_count", "manipulation_count", "forecast_count"]
    return sum(out.get(f, 0) for f in fields if isinstance(out.get(f), int))


# ── Sidebar ────────────────────────────────────────────────────────────────────
AGENT_PAGES = {
    "dashboard":  "Overview",
    "inventory":  "Inventory Agent",
    "customer":   "Customer Agent",
    "security":   "Security Agent",
    "supply":     "Supply Chain Agent",
    "pricing":    "Pricing Agent",
    "demand":     "Demand Agent",
    "alerts":     "All Alerts",
}

if "page" not in st.session_state:
    st.session_state.page = "dashboard"
if "pipeline_result" not in st.session_state:
    st.session_state.pipeline_result = None

with st.sidebar:
    st.markdown("""
    <div style="padding: 10px 0 18px 0;">
      <div style="font-size:1.05rem;font-weight:700;color:#f0f6fc;">🏙 Smart City</div>
      <div style="font-size:0.72rem;color:#8b949e;margin-top:2px;">Market Monitoring System</div>
    </div>
    """, unsafe_allow_html=True)

    model = st.selectbox(
        "LLM Model",
        ["llama-3.3-70b-versatile", "llama-3.1-8b-instant",
         "meta-llama/llama-4-scout-17b-16e-instruct"],
        index=0,
        label_visibility="collapsed",
        help="70B: best quality · 8B: fastest · Llama 4: balanced",
    )
    run_btn = st.button("▶  Run Pipeline", type="primary", use_container_width=True)

    st.markdown('<div class="nav-section">Overview</div>', unsafe_allow_html=True)
    for page_key, page_label in [("dashboard", "Dashboard"), ("alerts", "All Alerts")]:
        active = "active" if st.session_state.page == page_key else ""
        icon = {"dashboard": "⬡", "alerts": "🔔"}.get(page_key, "•")
        if st.button(f"{icon}  {page_label}", key=f"nav_{page_key}",
                     use_container_width=True,
                     type="secondary" if active else "secondary"):
            st.session_state.page = page_key

    st.markdown('<div class="nav-section">Agents</div>', unsafe_allow_html=True)
    agent_icons = {"inventory": "📦", "customer": "👥", "security": "🔒",
                   "supply": "🚚", "pricing": "💰", "demand": "📈"}
    for key, label in [("inventory", "Inventory"), ("customer", "Customer"),
                       ("security", "Security"), ("supply", "Supply Chain"),
                       ("pricing", "Pricing"), ("demand", "Demand")]:
        icon = agent_icons[key]
        if st.button(f"{icon}  {label}", key=f"nav_{key}",
                     use_container_width=True, type="secondary"):
            st.session_state.page = key

    st.divider()
    result = st.session_state.pipeline_result
    if result:
        alerts = result.get("alerts", [])
        n_crit = sum(1 for a in alerts if a["severity"] == "CRITICAL")
        st.markdown(f"""
        <div style="font-size:0.72rem;color:#8b949e;padding:4px 0;">
          <div style="margin-bottom:4px;">
            <span class="status-dot"></span>
            <span style="color:#3fb950;">System Online</span>
          </div>
          <div>{len(alerts)} alerts  ·  {n_crit} critical</div>
          <div style="margin-top:4px;">Last run: {datetime.now().strftime('%H:%M:%S')}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="font-size:0.72rem;color:#8b949e;">
          <div><span style="display:inline-block;width:8px;height:8px;border-radius:50%;
               background:#8b949e;margin-right:5px;"></span>No data</div>
          <div style="margin-top:4px;">Run pipeline to start</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top:12px;font-size:0.65rem;color:#484f58;padding-top:8px;border-top:1px solid #21262d;">
      Groq · LangGraph · Qdrant · Redis
    </div>
    """, unsafe_allow_html=True)


# ── Run pipeline ───────────────────────────────────────────────────────────────
if run_btn:
    os.environ["LLM_MODEL_ID"] = model
    with st.spinner(f"Running pipeline with **{model.split('/')[-1]}**…"):
        from orchestrator import run_pipeline
        st.session_state.pipeline_result = run_pipeline()
    st.session_state.page = "dashboard"
    st.rerun()

result = st.session_state.pipeline_result
page   = st.session_state.page


# ── Top bar ────────────────────────────────────────────────────────────────────
now_str = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
page_title = AGENT_PAGES.get(page, "Dashboard")
if result:
    sys_status = '<span class="status-dot"></span><span style="color:#3fb950;">System Online</span>'
else:
    sys_status = '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#8b949e;margin-right:5px;"></span><span>Awaiting run</span>'

st.markdown(f"""
<div class="topbar">
  <div class="topbar-title">{page_title}</div>
  <div class="topbar-right">
    <div>{sys_status}</div>
    <div>🕐 {now_str}</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: No data yet
# ═══════════════════════════════════════════════════════════════════════════════
if not result:
    st.markdown("""
    <div style="text-align:center;padding:80px 20px;">
      <div style="font-size:3rem;margin-bottom:16px;">🏙</div>
      <div style="font-size:1.3rem;font-weight:700;color:#f0f6fc;margin-bottom:8px;">Smart City Market Monitor</div>
      <div style="font-size:0.9rem;color:#8b949e;margin-bottom:24px;">
        Multi-agent AI system powered by Groq · LangGraph · Qdrant · Redis
      </div>
      <div style="font-size:0.82rem;color:#8b949e;">
        Click <strong style="color:#f0f6fc;">▶ Run Pipeline</strong> in the sidebar to begin analysis.
      </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Preview mock data feeds"):
        from data.mock_iot_data import get_all_feeds
        feeds = get_all_feeds()
        src = st.selectbox("Feed", list(feeds.keys()))
        st.json(feeds[src])
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# SHARED DATA (used by multiple pages)
# ═══════════════════════════════════════════════════════════════════════════════
alerts   = result.get("alerts", [])
critical = [a for a in alerts if a["severity"] == "CRITICAL"]
high     = [a for a in alerts if a["severity"] == "HIGH"]
warnings = [a for a in alerts if a["severity"] == "WARNING"]
emergency_report = result.get("emergency_report", "")
is_emergency     = bool(emergency_report)

AGENTS = ["inventory", "customer", "security", "supply", "pricing", "demand"]
AGENT_LABELS = {
    "inventory": "Inventory", "customer": "Customer", "security": "Security",
    "supply": "Supply Chain", "pricing": "Pricing", "demand": "Demand",
}


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD (overview)
# ═══════════════════════════════════════════════════════════════════════════════
if page == "dashboard":

    # Emergency banner
    if is_emergency:
        st.markdown(f"""
        <div style="background:rgba(248,81,73,.1);border:1px solid rgba(248,81,73,.4);
             border-radius:8px;padding:12px 16px;margin-bottom:18px;
             display:flex;align-items:center;gap:10px;">
          <span style="font-size:1.2rem;">🚨</span>
          <div>
            <div style="font-weight:700;color:#f85149;font-size:0.88rem;">EMERGENCY MODE ACTIVATED</div>
            <div style="font-size:0.78rem;color:#c9d1d9;margin-top:2px;">
              Critical alerts detected — supply, pricing, and demand analysis skipped. Immediate action required.
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── KPI cards ──────────────────────────────────────────────────────────────
    inv_out = result.get("inventory_output", {})
    sec_out = result.get("security_output", {})

    total_agents   = len(AGENTS)
    events_proc    = sum(_agent_events(result, k) for k in AGENTS)
    total_alerts   = len(alerts)
    health_pct     = max(0, 100 - len(critical) * 25 - len(high) * 8 - len(warnings) * 2)
    avg_resp       = "~600ms" if "70b" in model else "~150ms"

    k1, k2, k3, k4, k5 = st.columns(5)
    def kpi(col, label, value, delta_html=""):
        col.markdown(f"""
        <div class="kpi-card">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
          {f'<div class="kpi-delta">{delta_html}</div>' if delta_html else ""}
        </div>
        """, unsafe_allow_html=True)

    kpi(k1, "Total Agents", total_agents, '<span class="delta-neu">6 active</span>')
    kpi(k2, "Events Processed", events_proc,
        '<span class="delta-up">↑ pipeline complete</span>')
    kpi(k3, "Alerts", total_alerts,
        f'<span class="delta-{"down" if critical else "neu"}">{len(critical)} critical · {len(high)} high</span>')
    kpi(k4, "System Health", f"{health_pct}%",
        f'<span class="delta-{"up" if health_pct>=70 else "down"}">{"Nominal" if health_pct>=70 else "Degraded"}</span>')
    kpi(k5, "Resp. Time", avg_resp, '<span class="delta-neu">Groq API</span>')

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Agent status cards ─────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Agent Status Overview</div>', unsafe_allow_html=True)
    cols = st.columns(len(AGENTS))
    sparkline_colors = ["#388bfd", "#3fb950", "#f85149", "#d29922", "#a371f7", "#39d353"]

    for i, (key, col) in enumerate(zip(AGENTS, cols)):
        out = result.get(f"{key}_output", {})
        badge_html, badge_kind = _agent_badge(alerts, key)
        n_agent_alerts = sum(1 for a in alerts if a.get("agent") == key)

        # Key metric per agent
        metrics = {
            "inventory": ("Low stock",   out.get("low_stock_count", 0)),
            "customer":  ("Crowd surges", out.get("crowd_surges", 0)),
            "security":  ("Critical evts", out.get("critical_count", 0)),
            "supply":    ("Disruptions",  out.get("disrupted_count", 0)),
            "pricing":   ("Price flags",  out.get("manipulation_count", 0)),
            "demand":    ("At-risk SKUs",  len(out.get("at_risk", []))),
        }
        metric_label, metric_val = metrics[key]

        # Sparkline — simulated activity curve
        skipped = key in ("supply", "pricing", "demand") and is_emergency
        base = 40 if skipped else 65
        spark_vals = [base + int(15 * math.sin(j * 0.9 + i)) for j in range(12)]
        spark_svg  = _sparkline_svg(spark_vals, color=sparkline_colors[i])
        status_txt = "Skipped" if skipped else "Active"
        last_upd   = datetime.now().strftime("%H:%M:%S")

        col.markdown(f"""
        <div class="agent-card">
          <div class="agent-card-header">
            <div class="agent-name">{agent_icons[key]}  {AGENT_LABELS[key]}</div>
            {badge_html if not skipped else _badge("Skipped", "orange")}
          </div>
          <div class="agent-meta">Updated {last_upd} · {n_agent_alerts} alert(s)</div>
          <div class="agent-metric">{metric_label}: <span>{metric_val}</span></div>
          <div style="margin-top:10px;">{spark_svg}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Three-column row: Events | Performance | Alerts ────────────────────────
    ev_col, perf_col, alrt_col = st.columns([1, 1.6, 1])

    # Live Event Stream
    with ev_col:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Live Event Stream</div>', unsafe_allow_html=True)
        severity_order = {"CRITICAL": 0, "HIGH": 1, "WARNING": 2}
        sorted_alerts  = sorted(alerts, key=lambda x: severity_order.get(x["severity"], 3))

        events_html = ""
        base_time = datetime.now()
        for idx, a in enumerate(sorted_alerts[:10]):
            dot   = _severity_dot(a["severity"])
            t_str = (base_time - timedelta(seconds=idx * 23)).strftime("%H:%M")
            shop  = a.get("shop_id", "")
            msg   = a["message"][:55] + ("…" if len(a["message"]) > 55 else "")
            events_html += f"""
            <div class="event-item">
              <div class="event-dot {dot}"></div>
              <div>
                <div class="event-time">{t_str} · {a['agent'].upper()} [{shop}]</div>
                <div class="event-msg">{msg}</div>
              </div>
            </div>"""

        if not events_html:
            events_html = '<div style="color:#8b949e;font-size:0.8rem;">No events.</div>'

        st.markdown(events_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # System Performance chart
    with perf_col:
        import plotly.graph_objects as go
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">System Performance (simulated 24h)</div>',
                    unsafe_allow_html=True)

        hours = list(range(24))
        random.seed(7)
        inv_series  = [50 + random.randint(-12, 12) for _ in hours]
        cust_series = [40 + random.randint(-10, 18) for _ in hours]
        sec_series  = [30 + random.randint(-8,  22) for _ in hours]

        def _hex_fill(h: str, alpha: float = 0.06) -> str:
            r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
            return f"rgba({r},{g},{b},{alpha})"

        fig = go.Figure()
        for series, name, color in [
            (inv_series,  "Inventory",  "#388bfd"),
            (cust_series, "Customer",   "#3fb950"),
            (sec_series,  "Security",   "#f85149"),
        ]:
            fig.add_trace(go.Scatter(
                x=hours, y=series, name=name, mode="lines",
                line=dict(color=color, width=2),
                fill="tozeroy",
                fillcolor=_hex_fill(color),
            ))

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#8b949e", size=11),
            margin=dict(l=0, r=0, t=4, b=0),
            height=200,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                        font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
            xaxis=dict(gridcolor="#21262d", tickfont=dict(size=9),
                       tickvals=[0,6,12,18,23], ticktext=["00:00","06:00","12:00","18:00","23:00"]),
            yaxis=dict(gridcolor="#21262d", tickfont=dict(size=9)),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    # Alerts Summary
    with alrt_col:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Alerts Summary</div>', unsafe_allow_html=True)

        def alert_row(label, count, color):
            return f"""
            <div class="alert-row">
              <div style="display:flex;align-items:center;gap:8px;">
                <div style="width:10px;height:10px;border-radius:50%;background:{color};"></div>
                <span>{label}</span>
              </div>
              <div class="alert-count" style="color:{color};">{count}</div>
            </div>"""

        st.markdown(
            alert_row("Critical", len(critical), "#f85149") +
            alert_row("High",     len(high),     "#d29922") +
            alert_row("Warning",  len(warnings), "#e3b341") +
            alert_row("Total",    len(alerts),   "#8b949e"),
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        inv_out = result.get("inventory_output", {})
        sup_out = result.get("supply_output", {})
        pri_out = result.get("pricing_output", {})
        st.markdown(f"""
        <div style="font-size:0.75rem;color:#8b949e;border-top:1px solid #21262d;padding-top:10px;">
          <div style="margin-bottom:4px;">📦 Low stock: <strong style="color:#c9d1d9;">{inv_out.get('low_stock_count',0)}</strong></div>
          <div style="margin-bottom:4px;">🚚 Disruptions: <strong style="color:#c9d1d9;">{"N/A" if is_emergency else sup_out.get('disrupted_count',0)}</strong></div>
          <div>💰 Price flags: <strong style="color:#c9d1d9;">{"N/A" if is_emergency else pri_out.get('manipulation_count',0)}</strong></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Emergency briefing ─────────────────────────────────────────────────────
    if is_emergency:
        st.markdown('<div class="section-title">Emergency Briefing</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:rgba(248,81,73,.06);border:1px solid rgba(248,81,73,.3);
             border-radius:8px;padding:16px;font-size:0.83rem;line-height:1.7;color:#c9d1d9;
             margin-bottom:20px;">
          {emergency_report.replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)

    # ── Executive summary ──────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Executive Summary</div>', unsafe_allow_html=True)
    final_report = result.get("final_report", "No report generated.")
    st.markdown(f"""
    <div class="analysis-box" style="border-left-color:#3fb950;">
      {final_report.replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Agent Insights table ───────────────────────────────────────────────────
    st.markdown('<div class="section-title">Agent Insights</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-card">', unsafe_allow_html=True)

    top_activities = {
        "inventory": "Stock level analysis",
        "customer":  "Crowd & sentiment scan",
        "security":  "Threat detection",
        "supply":    "Delivery monitoring",
        "pricing":   "Price manipulation scan",
        "demand":    "Demand forecasting",
    }
    insights_html = """
    <table class="ins-table">
      <thead><tr>
        <th>Agent</th><th>Top Activity</th><th>Key Insight</th><th>Trend</th><th>Status</th>
      </tr></thead><tbody>"""

    for key in AGENTS:
        out    = result.get(f"{key}_output", {})
        label  = AGENT_LABELS[key]
        icon   = agent_icons[key]
        act    = top_activities[key]
        anlys  = out.get("llm_analysis", "")
        excerpt = (anlys[:80] + "…") if anlys and len(anlys) > 80 else (anlys or "—")
        skipped = key in ("supply", "pricing", "demand") and is_emergency

        badge_html, bk = _agent_badge(alerts, key)
        if skipped:
            badge_html = _badge("Skipped", "orange")

        svals = [40 + int(18 * math.sin(j * 0.8 + AGENTS.index(key))) for j in range(10)]
        spark = _sparkline_svg(svals, color=sparkline_colors[AGENTS.index(key)], width=60, height=20)

        insights_html += f"""
        <tr>
          <td><strong>{icon} {label}</strong></td>
          <td style="color:#8b949e;">{act}</td>
          <td>{excerpt}</td>
          <td>{spark}</td>
          <td>{badge_html}</td>
        </tr>"""

    insights_html += "</tbody></table>"
    st.markdown(insights_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ALL ALERTS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "alerts":
    if not alerts:
        st.info("No alerts in this run.")
    else:
        severity_order = {"CRITICAL": 0, "HIGH": 1, "WARNING": 2}
        sorted_alerts  = sorted(alerts, key=lambda x: severity_order.get(x["severity"], 3))

        # Summary row
        c1, c2, c3 = st.columns(3)
        c1.metric("Critical / High", f"{len(critical)} / {len(high)}")
        c2.metric("Warnings",        len(warnings))
        c3.metric("Total",           len(alerts))

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-card">', unsafe_allow_html=True)

        rows = ""
        for a in sorted_alerts:
            color = _severity_color(a["severity"])
            rows += f"""
            <div style="display:flex;align-items:flex-start;gap:12px;padding:10px 0;
                 border-bottom:1px solid #21262d;">
              <div style="width:10px;height:10px;border-radius:50%;background:{color};
                   flex-shrink:0;margin-top:4px;"></div>
              <div style="flex:1;">
                <div style="font-size:0.78rem;color:#8b949e;margin-bottom:2px;">
                  {a['severity']} · {a['agent'].upper()} · {a.get('shop_id','')}
                </div>
                <div style="font-size:0.85rem;color:#c9d1d9;">{a['message']}</div>
              </div>
            </div>"""

        st.markdown(rows, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT DETAIL PAGES
# ═══════════════════════════════════════════════════════════════════════════════
elif page in AGENTS:
    key = page
    out = result.get(f"{key}_output", {})

    skipped = key in ("supply", "pricing", "demand") and is_emergency
    if skipped:
        st.markdown(f"""
        <div style="background:rgba(210,153,34,.08);border:1px solid rgba(210,153,34,.3);
             border-radius:8px;padding:12px 16px;margin-bottom:16px;font-size:0.83rem;color:#d29922;">
          ⚠️  This agent was skipped on the emergency fast path. No data available for this run.
        </div>
        """, unsafe_allow_html=True)

    # Agent alerts
    agent_alerts = [a for a in alerts if a.get("agent") == key]
    badge_html, _ = _agent_badge(alerts, key)

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:18px;">
      <div style="font-size:1.8rem;">{agent_icons[key]}</div>
      <div>
        <div style="font-size:1.1rem;font-weight:700;color:#f0f6fc;">{AGENT_LABELS[key]} Agent</div>
        <div style="font-size:0.75rem;color:#8b949e;margin-top:2px;">
          {len(agent_alerts)} alert(s) this run
        </div>
      </div>
      <div style="margin-left:auto;">{badge_html}</div>
    </div>
    """, unsafe_allow_html=True)

    left, right = st.columns([1.4, 1])

    with left:
        # Analysis
        analysis = out.get("llm_analysis", "")
        st.markdown('<div class="section-card" style="margin-bottom:16px;">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">LLM Analysis</div>', unsafe_allow_html=True)
        if analysis:
            st.markdown(f'<div class="analysis-box">{analysis.replace(chr(10), "<br>")}</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#8b949e;font-size:0.83rem;">No analysis available.</div>',
                        unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Charts
        charts = out.get("charts", {})
        if charts:
            chart_paths = [p for p in charts.values() if p and os.path.exists(p)]
            if chart_paths:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">Charts</div>', unsafe_allow_html=True)
                c_cols = st.columns(min(len(chart_paths), 2))
                for ci, cp in enumerate(chart_paths):
                    with c_cols[ci % 2]:
                        st.image(cp, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

    with right:
        # Agent alerts
        st.markdown('<div class="section-card" style="margin-bottom:16px;">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Agent Alerts</div>', unsafe_allow_html=True)
        if agent_alerts:
            for a in sorted(agent_alerts, key=lambda x: {"CRITICAL":0,"HIGH":1,"WARNING":2}.get(x["severity"],3)):
                color = _severity_color(a["severity"])
                st.markdown(f"""
                <div style="display:flex;gap:8px;padding:7px 0;border-bottom:1px solid #21262d;font-size:0.8rem;">
                  <div style="width:8px;height:8px;border-radius:50%;background:{color};flex-shrink:0;margin-top:3px;"></div>
                  <div>
                    <div style="color:#8b949e;font-size:0.72rem;">{a['severity']} · {a.get('shop_id','')}</div>
                    <div style="color:#c9d1d9;">{a['message']}</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#8b949e;font-size:0.83rem;">No alerts for this agent.</div>',
                        unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Structured output (excluding charts + analysis)
        display_out = {k: v for k, v in out.items() if k not in ("charts", "llm_analysis")}
        if display_out:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Structured Output</div>', unsafe_allow_html=True)
            st.json(display_out)
            st.markdown('</div>', unsafe_allow_html=True)
