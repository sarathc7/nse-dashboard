import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import anthropic
import json
import pytz

# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="Stocklens",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Dark theme CSS (Groww-inspired) ───────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: #0d0d0d !important;
    color: #f0f0f0 !important;
}
.stApp { background-color: #0d0d0d; }
.main .block-container {
    padding: 0 0.8rem 5rem;
    max-width: 480px;
    margin: auto;
}

/* Hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

/* Top nav bar */
.topbar {
    background: #0d0d0d;
    padding: 14px 4px 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 100;
    border-bottom: 1px solid #1e1e1e;
    margin-bottom: 12px;
}
.logo { font-size: 20px; font-weight: 700; color: #00d09c; letter-spacing: -0.5px; }
.logo span { color: #f0f0f0; }
.market-badge {
    font-size: 11px; font-weight: 600; padding: 3px 10px;
    border-radius: 20px; letter-spacing: 0.3px;
}
.market-open { background: #0a2e22; color: #00d09c; border: 1px solid #00d09c44; }
.market-closed { background: #2e1a1a; color: #ff6b6b; border: 1px solid #ff6b6b44; }

/* Hero card */
.hero-card {
    background: linear-gradient(135deg, #0a2e22 0%, #0d3d2d 100%);
    border: 1px solid #00d09c33;
    border-radius: 20px;
    padding: 22px 20px 18px;
    margin-bottom: 16px;
}
.hero-label { font-size: 12px; color: #00d09c99; font-weight: 500; margin-bottom: 4px; }
.hero-value { font-size: 32px; font-weight: 700; color: #f0f0f0; letter-spacing: -1px; }
.hero-pnl { font-size: 14px; font-weight: 600; margin-top: 4px; }
.hero-sub { font-size: 11px; color: #aaa; margin-top: 2px; }
.quick-btns { display: flex; gap: 8px; margin-top: 14px; }
.qbtn {
    flex: 1; background: #ffffff14; border: 1px solid #ffffff22;
    border-radius: 10px; padding: 8px 6px; text-align: center;
    font-size: 11px; font-weight: 500; color: #ccc; cursor: pointer;
}

/* Index scroll strip */
.index-strip { display: flex; gap: 8px; overflow-x: auto; padding: 4px 0 12px; margin-bottom: 4px; }
.index-strip::-webkit-scrollbar { display: none; }
.index-chip {
    min-width: 120px; background: #1a1a1a; border: 1px solid #2a2a2a;
    border-radius: 12px; padding: 10px 12px; flex-shrink: 0;
}
.chip-name { font-size: 11px; color: #888; font-weight: 500; }
.chip-val { font-size: 14px; font-weight: 600; color: #f0f0f0; margin: 2px 0; }
.chip-chg { font-size: 11px; font-weight: 600; }

/* Section header */
.sec-hdr {
    font-size: 13px; font-weight: 600; color: #888;
    text-transform: uppercase; letter-spacing: 0.6px;
    margin: 20px 0 10px;
}

/* Cards */
.card {
    background: #1a1a1a; border: 1px solid #2a2a2a;
    border-radius: 16px; padding: 16px; margin-bottom: 10px;
}

/* Stock row */
.stock-row {
    display: flex; align-items: center; gap: 12px;
    padding: 11px 0; border-bottom: 1px solid #1e1e1e;
}
.stock-row:last-child { border-bottom: none; }
.stock-avatar {
    width: 38px; height: 38px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 700; flex-shrink: 0;
}
.stock-name { font-size: 14px; font-weight: 600; color: #f0f0f0; }
.stock-sub  { font-size: 11px; color: #666; margin-top: 1px; }
.stock-right { margin-left: auto; text-align: right; }
.stock-price { font-size: 14px; font-weight: 600; color: #f0f0f0; }
.stock-chg  { font-size: 11px; font-weight: 600; margin-top: 2px; }

/* P&L bar */
.alloc-bar-bg { background: #2a2a2a; border-radius: 3px; height: 3px; margin-top: 6px; }
.alloc-bar    { height: 3px; border-radius: 3px; }

/* Pill badge */
.pill {
    display: inline-block; padding: 2px 8px; border-radius: 20px;
    font-size: 11px; font-weight: 600;
}
.pill-up   { background: #0a2e22; color: #00d09c; }
.pill-down { background: #2e1a1a; color: #ff6b6b; }
.pill-hold { background: #2a2200; color: #f5a623; }

/* Metric grid */
.mgrid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px; }
.mcard { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 14px; padding: 14px; }
.mcard-label { font-size: 11px; color: #666; font-weight: 500; margin-bottom: 4px; }
.mcard-val   { font-size: 18px; font-weight: 700; color: #f0f0f0; }
.mcard-sub   { font-size: 11px; margin-top: 2px; }

.up   { color: #00d09c; }
.down { color: #ff6b6b; }
.muted { color: #666; }

/* AI response box */
.ai-box {
    background: #0a2e22; border: 1px solid #00d09c33;
    border-radius: 14px; padding: 16px;
    font-size: 13px; line-height: 1.7; color: #e0e0e0;
}

/* Bottom nav */
.bottomnav {
    position: fixed; bottom: 0; left: 50%; transform: translateX(-50%);
    width: 100%; max-width: 480px;
    background: #111; border-top: 1px solid #222;
    display: flex; z-index: 200; padding: 6px 0 10px;
}
.bnav-item {
    flex: 1; text-align: center; padding: 6px 0;
    font-size: 10px; font-weight: 500; color: #555; cursor: pointer;
}
.bnav-item.active { color: #00d09c; }
.bnav-icon { font-size: 20px; display: block; margin-bottom: 2px; }

/* Tabs override */
div[data-testid="stTabs"] > div:first-child { display: none; }

/* Input styling */
input[type="text"], input[type="number"] {
    background: #1a1a1a !important; color: #f0f0f0 !important;
    border: 1px solid #2a2a2a !important; border-radius: 10px !important;
}
.stTextInput input, .stNumberInput input {
    background: #1a1a1a !important; color: #f0f0f0 !important;
}
.stSelectbox select { background: #1a1a1a !important; color: #f0f0f0 !important; }
.stButton button {
    background: #00d09c !important; color: #000 !important;
    font-weight: 600 !important; border-radius: 12px !important;
    border: none !important;
}
.stButton.secondary button {
    background: #1a1a1a !important; color: #f0f0f0 !important;
    border: 1px solid #2a2a2a !important;
}
div[data-testid="stForm"] {
    background: #1a1a1a; border: 1px solid #2a2a2a;
    border-radius: 16px; padding: 16px;
}
.stSpinner > div { border-top-color: #00d09c !important; }
div[data-testid="stMetric"] {
    background: #1a1a1a; border: 1px solid #2a2a2a;
    border-radius: 14px; padding: 12px 14px;
}
div[data-testid="stMetricValue"] { color: #f0f0f0 !important; font-size: 18px !important; }
div[data-testid="stMetricDelta"] svg { display: none; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #1a1a1a; }
::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }

/* Dataframe */
[data-testid="stDataFrame"] { background: #1a1a1a !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────
if "portfolio"       not in st.session_state: st.session_state.portfolio = []
if "ai_response"     not in st.session_state: st.session_state.ai_response = ""
if "active_tab"      not in st.session_state: st.session_state.active_tab = 0
if "anthropic_key"   not in st.session_state: st.session_state.anthropic_key = ""

# ── Market hours helper ────────────────────────────────────────
def market_status():
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    if now.weekday() < 5 and 9 <= now.hour < 16 and not (now.hour == 9 and now.minute < 15):
        return True, now.strftime("%I:%M %p IST")
    return False, now.strftime("%I:%M %p IST")

# ── Data helpers ───────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_price(ticker_ns):
    try:
        t    = yf.Ticker(ticker_ns)
        info = t.fast_info
        p    = round(info.last_price, 2)
        prev = round(info.previous_close, 2)
        chg  = round(p - prev, 2)
        pct  = round((chg / prev) * 100, 2)
        return p, chg, pct
    except Exception:
        return None, None, None

@st.cache_data(ttl=300)
def fetch_history(ticker_ns, period="1mo"):
    try:
        return yf.Ticker(ticker_ns).history(period=period)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_sparkline(ticker_ns):
    try:
        hist = yf.Ticker(ticker_ns).history(period="5d", interval="1h")
        return hist["Close"].tolist() if not hist.empty else []
    except Exception:
        return []

@st.cache_data(ttl=300)
def fetch_index(ticker):
    try:
        t    = yf.Ticker(ticker)
        info = t.fast_info
        p    = round(info.last_price, 2)
        prev = round(info.previous_close, 2)
        chg  = round(p - prev, 2)
        pct  = round((chg / prev) * 100, 2)
        return p, chg, pct
    except Exception:
        return None, None, None

@st.cache_data(ttl=300)
def fetch_stock_info(ticker_ns):
    try:
        t    = yf.Ticker(ticker_ns)
        info = t.info
        return {
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low":  info.get("fiftyTwoWeekLow"),
            "pe":       info.get("trailingPE"),
            "sector":   info.get("sector","—"),
            "mktcap":   info.get("marketCap"),
            "name":     info.get("longName", ticker_ns)
        }
    except Exception:
        return {}

@st.cache_data(ttl=600)
def fetch_top_movers():
    symbols = [
        "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS",
        "WIPRO.NS","AXISBANK.NS","SBIN.NS","MARUTI.NS","TATAMOTORS.NS",
        "SUNPHARMA.NS","DRREDDY.NS","BAJFINANCE.NS","LTIM.NS","HCLTECH.NS",
        "ADANIENT.NS","TITAN.NS","NESTLEIND.NS","POWERGRID.NS","NTPC.NS"
    ]
    rows = []
    for sym in symbols:
        p, chg, pct = fetch_price(sym)
        if p:
            rows.append({"symbol": sym.replace(".NS",""), "price": p, "chg": chg, "pct": pct})
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
    return df.nlargest(6,"pct"), df.nsmallest(6,"pct")

def portfolio_summary():
    rows = []
    invested = current = 0
    for h in st.session_state.portfolio:
        p, chg, pct = fetch_price(h["symbol"] + ".NS")
        if p is None:
            p, chg, pct = h["avg_price"], 0, 0
        inv    = h["qty"] * h["avg_price"]
        cur    = h["qty"] * p
        pnl    = cur - inv
        pnl_pct = (pnl / inv * 100) if inv else 0
        invested += inv
        current  += cur
        rows.append({"Symbol": h["symbol"], "Qty": h["qty"],
                     "Avg": h["avg_price"], "LTP": p,
                     "Invested": inv, "Current": cur,
                     "PnL": pnl, "PnL%": pnl_pct, "DayChg%": pct})
    return rows, invested, current, current - invested, ((current-invested)/invested*100) if invested else 0

def sparkline_fig(data, up=True):
    color = "#00d09c" if up else "#ff6b6b"
    fig = go.Figure(go.Scatter(y=data, mode="lines",
        line=dict(color=color, width=1.5),
        fill="tozeroy", fillcolor=color+"22"))
    fig.update_layout(margin=dict(t=0,b=0,l=0,r=0), height=40,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig

def avatar_colors(sym):
    palettes = [
        ("#0a2e22","#00d09c"),("  #1a1540","#a78bfa"),("#2e1a0a","#f5a623"),
        ("#1a0a2e","#c084fc"),("#0a1a2e","#60a5fa"),("#2e0a1a","#fb7185"),
    ]
    return palettes[sum(ord(c) for c in sym) % len(palettes)]

def ask_claude(question, rows, invested, current, pnl, pnl_pct):
    key = st.session_state.get("anthropic_key","")
    if not key:
        return "⚠️ Please enter your Anthropic API key in the ⚙️ sidebar."
    client = anthropic.Anthropic(api_key=key)
    system = f"""You are a sharp, concise NSE stock market analyst for the Stocklens app.
Portfolio: invested ₹{invested:,.0f}, current ₹{current:,.0f}, P&L ₹{pnl:,.0f} ({pnl_pct:.1f}%).
Holdings: {json.dumps(rows, default=str)}
Rules: Answer in 4-6 sentences max. Be specific. Use ₹ and % symbols. 
End every response with: "⚠️ Not financial advice — consult a SEBI-registered advisor."
"""
    msg = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=1000,
        system=system,
        messages=[{"role":"user","content":question}]
    )
    return msg.content[0].text

# ── Top bar ────────────────────────────────────────────────────
is_open, time_str = market_status()
badge_cls  = "market-open" if is_open else "market-closed"
badge_text = f"● OPEN · {time_str}" if is_open else f"● CLOSED · {time_str}"

st.markdown(f"""
<div class="topbar">
  <div class="logo">Stock<span>lens</span> 🔭</div>
  <span class="market-badge {badge_cls}">{badge_text}</span>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    key = st.text_input("Anthropic API key", type="password", placeholder="sk-ant-...")
    if key:
        st.session_state.anthropic_key = key
        st.success("Saved ✓")
    st.markdown("---")
    st.markdown("**Get a free key:**\n1. [console.anthropic.com](https://console.anthropic.com)\n2. Sign up → API Keys → Create")
    st.markdown("---")
    if st.button("🔄 Refresh data"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Data: Yahoo Finance (15-min delay)")

# ── Bottom nav ─────────────────────────────────────────────────
nav_labels = [("🏠","Home"),("💼","Portfolio"),("📊","Market"),("🤖","AI")]
nav_js = "".join([
    f'<div class="bnav-item {"active" if i==st.session_state.active_tab else ""}">'
    f'<span class="bnav-icon">{ic}</span>{lb}</div>'
    for i,(ic,lb) in enumerate(nav_labels)
])
st.markdown(f'<div class="bottomnav">{nav_js}</div>', unsafe_allow_html=True)

# Nav selector (workaround — radio hidden via CSS)
nav_choice = st.radio("nav", [lb for _,lb in nav_labels],
    horizontal=True, index=st.session_state.active_tab,
    label_visibility="collapsed")
st.session_state.active_tab = [lb for _,lb in nav_labels].index(nav_choice)

# ══════════════════════════════════════════════════════════════
# HOME TAB
# ══════════════════════════════════════════════════════════════
if st.session_state.active_tab == 0:
    ist  = pytz.timezone("Asia/Kolkata")
    hour = datetime.now(ist).hour
    greet = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")

    if st.session_state.portfolio:
        rows, invested, current, pnl, pnl_pct = portfolio_summary()
        pnl_color = "#00d09c" if pnl >= 0 else "#ff6b6b"
        sign      = "+" if pnl >= 0 else ""
        day_pnl   = sum(r["Current"] * r["DayChg%"] / 100 for r in rows)
        day_sign  = "+" if day_pnl >= 0 else ""

        st.markdown(f"""
        <div class="hero-card">
          <div class="hero-label">{greet}, Investor 👋 · Portfolio Value</div>
          <div class="hero-value">₹{current:,.0f}</div>
          <div class="hero-pnl" style="color:{pnl_color}">
            {sign}₹{pnl:,.0f} ({sign}{pnl_pct:.2f}%) overall &nbsp;·&nbsp;
            {day_sign}₹{abs(day_pnl):,.0f} today
          </div>
          <div class="hero-sub">Invested ₹{invested:,.0f} · {len(rows)} stocks</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="hero-card">
          <div class="hero-label">{greet}, Investor 👋</div>
          <div class="hero-value">₹0</div>
          <div class="hero-pnl muted">Add stocks in Portfolio tab to begin</div>
        </div>
        """, unsafe_allow_html=True)

    # Index strip
    st.markdown('<div class="sec-hdr">Indices</div>', unsafe_allow_html=True)
    indices = [("Nifty 50","^NSEI"),("Sensex","^BSESN"),
               ("Bank Nifty","^NSEBANK"),("Nifty IT","^CNXIT"),("Nifty Mid","^NSMIDCP")]
    chips = ""
    for name, ticker in indices:
        p, chg, pct = fetch_index(ticker)
        if p:
            cls  = "up" if pct >= 0 else "down"
            sign = "+" if pct >= 0 else ""
            chips += f"""
            <div class="index-chip">
              <div class="chip-name">{name}</div>
              <div class="chip-val">₹{p:,.2f}</div>
              <div class="chip-chg {cls}">{sign}{pct:.2f}%</div>
            </div>"""
    st.markdown(f'<div class="index-strip">{chips}</div>', unsafe_allow_html=True)

    # Top movers preview
    st.markdown('<div class="sec-hdr">Top movers today</div>', unsafe_allow_html=True)
    with st.spinner(""):
        gainers, losers = fetch_top_movers()

    if not gainers.empty:
        for _, r in gainers.head(3).iterrows():
            bg, fg = avatar_colors(r["symbol"])
            spark  = fetch_sparkline(r["symbol"]+".NS")
            c1, c2, c3 = st.columns([3,2,2])
            with c1:
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:6px 0;">
                  <div class="stock-avatar" style="background:{bg};color:{fg};">{r['symbol'][:3]}</div>
                  <div>
                    <div class="stock-name">{r['symbol']}</div>
                    <div class="stock-sub">₹{r['price']:,.2f}</div>
                  </div>
                </div>""", unsafe_allow_html=True)
            with c2:
                if spark:
                    st.plotly_chart(sparkline_fig(spark, True), use_container_width=True, config={"displayModeBar":False})
            with c3:
                st.markdown(f'<div style="text-align:right;padding-top:12px;"><span class="pill pill-up">+{r["pct"]:.2f}%</span></div>', unsafe_allow_html=True)

    if st.session_state.portfolio:
        st.markdown('<div class="sec-hdr">Holdings snapshot</div>', unsafe_allow_html=True)
        rows, invested, current, pnl, _ = portfolio_summary()
        for r in rows:
            bg, fg  = avatar_colors(r["Symbol"])
            alloc   = (r["Current"] / current * 100) if current else 0
            pnl_cls = "up" if r["PnL"] >= 0 else "down"
            sign    = "+" if r["PnL"] >= 0 else ""
            spark   = fetch_sparkline(r["Symbol"]+".NS")
            c1, c2, c3 = st.columns([3,2,2])
            with c1:
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:6px 0;">
                  <div class="stock-avatar" style="background:{bg};color:{fg};">{r['Symbol'][:3]}</div>
                  <div>
                    <div class="stock-name">{r['Symbol']}</div>
                    <div class="stock-sub">{r['Qty']} qty · {alloc:.1f}%</div>
                    <div class="alloc-bar-bg" style="width:70px;">
                      <div class="alloc-bar" style="width:{min(alloc,100):.0f}%;background:{'#00d09c' if r['PnL']>=0 else '#ff6b6b'};"></div>
                    </div>
                  </div>
                </div>""", unsafe_allow_html=True)
            with c2:
                if spark:
                    st.plotly_chart(sparkline_fig(spark, r["PnL"]>=0), use_container_width=True, config={"displayModeBar":False})
            with c3:
                st.markdown(f"""
                <div style="text-align:right;padding-top:8px;">
                  <div class="stock-price">₹{r['LTP']:,.2f}</div>
                  <div class="stock-chg {pnl_cls}">{sign}{r['PnL%']:.1f}%</div>
                </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# PORTFOLIO TAB
# ══════════════════════════════════════════════════════════════
elif st.session_state.active_tab == 1:

    if st.session_state.portfolio:
        rows, invested, current, pnl, pnl_pct = portfolio_summary()
        pnl_color = "#00d09c" if pnl >= 0 else "#ff6b6b"
        sign = "+" if pnl >= 0 else ""

        st.markdown(f"""
        <div class="mgrid">
          <div class="mcard"><div class="mcard-label">Current value</div>
            <div class="mcard-val">₹{current:,.0f}</div></div>
          <div class="mcard"><div class="mcard-label">Total P&L</div>
            <div class="mcard-val" style="color:{pnl_color}">{sign}₹{pnl:,.0f}</div>
            <div class="mcard-sub" style="color:{pnl_color}">{sign}{pnl_pct:.2f}%</div></div>
          <div class="mcard"><div class="mcard-label">Invested</div>
            <div class="mcard-val">₹{invested:,.0f}</div></div>
          <div class="mcard"><div class="mcard-label">Winners</div>
            <div class="mcard-val">{sum(1 for r in rows if r['PnL']>0)}/{len(rows)}</div></div>
        </div>
        """, unsafe_allow_html=True)

        # Allocation pie
        df_pie = pd.DataFrame(rows)
        fig_pie = go.Figure(go.Pie(
            labels=df_pie["Symbol"], values=df_pie["Current"],
            hole=0.55, textinfo="percent+label", textfont_size=11,
            marker=dict(colors=["#00d09c","#a78bfa","#f5a623","#60a5fa","#fb7185","#34d399"],
                        line=dict(color="#0d0d0d", width=2))))
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10,b=10,l=10,r=10), height=220,
            legend=dict(font=dict(color="#aaa", size=11), orientation="h", y=-0.1),
            showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar":False})

        st.markdown('<div class="sec-hdr">Holdings</div>', unsafe_allow_html=True)
        for i, (h, r) in enumerate(zip(st.session_state.portfolio, rows)):
            bg, fg   = avatar_colors(r["Symbol"])
            pnl_cls  = "up" if r["PnL"] >= 0 else "down"
            sign     = "+" if r["PnL"] >= 0 else ""
            day_cls  = "up" if r["DayChg%"] >= 0 else "down"
            day_sign = "+" if r["DayChg%"] >= 0 else ""

            with st.expander(f"{r['Symbol']}  ·  ₹{r['LTP']:,.2f}  ·  {sign}{r['PnL%']:.1f}%"):
                c1, c2 = st.columns(2)
                c1.markdown(f"**Qty:** {r['Qty']}")
                c1.markdown(f"**Avg price:** ₹{r['Avg']:,.2f}")
                c1.markdown(f"**Invested:** ₹{r['Invested']:,.0f}")
                c2.markdown(f"**Current:** ₹{r['Current']:,.0f}")
                c2.markdown(f"**P&L:** <span class='{pnl_cls}'>{sign}₹{r['PnL']:,.0f} ({sign}{r['PnL%']:.2f}%)</span>", unsafe_allow_html=True)
                c2.markdown(f"**Today:** <span class='{day_cls}'>{day_sign}{r['DayChg%']:.2f}%</span>", unsafe_allow_html=True)

                info = fetch_stock_info(r["Symbol"]+".NS")
                if info:
                    st.markdown("---")
                    c3, c4 = st.columns(2)
                    c3.markdown(f"**52W High:** ₹{info.get('52w_high','—')}")
                    c3.markdown(f"**52W Low:** ₹{info.get('52w_low','—')}")
                    c4.markdown(f"**P/E:** {round(info['pe'],1) if info.get('pe') else '—'}")
                    c4.markdown(f"**Sector:** {info.get('sector','—')}")

                period = st.radio("Chart", ["1wk","1mo","3mo","6mo","1y"],
                    horizontal=True, key=f"prd_{i}")
                hist = fetch_history(r["Symbol"]+".NS", period)
                if not hist.empty:
                    color = "#00d09c" if r["PnL"] >= 0 else "#ff6b6b"
                    fig = go.Figure(go.Scatter(
                        x=hist.index, y=hist["Close"], mode="lines",
                        line=dict(color=color, width=2),
                        fill="tozeroy", fillcolor=color+"22"))
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(t=4,b=4,l=0,r=0), height=160,
                        xaxis=dict(showgrid=False, color="#555"),
                        yaxis=dict(showgrid=True, gridcolor="#1e1e1e", color="#555"))
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

                if st.button(f"Remove {r['Symbol']}", key=f"del_{i}"):
                    st.session_state.portfolio.pop(i)
                    st.rerun()

    st.markdown('<div class="sec-hdr">Add holding</div>', unsafe_allow_html=True)
    with st.form("add_stock", clear_on_submit=True):
        sym = st.text_input("NSE Symbol", placeholder="e.g. TCS, RELIANCE, INFY").upper().strip()
        c1, c2 = st.columns(2)
        qty = c1.number_input("Quantity", min_value=1, step=1)
        avg = c2.number_input("Avg buy price ₹", min_value=0.01, step=0.01, format="%.2f")
        submitted = st.form_submit_button("➕ Add to Portfolio", use_container_width=True)
        if submitted:
            if sym and qty and avg:
                p, _, _ = fetch_price(sym+".NS")
                if p is None:
                    st.error(f"'{sym}' not found on NSE. Check ticker.")
                elif any(h["symbol"]==sym for h in st.session_state.portfolio):
                    st.warning(f"{sym} already in portfolio.")
                else:
                    st.session_state.portfolio.append({"symbol":sym,"qty":int(qty),"avg_price":float(avg)})
                    st.success(f"✓ {sym} added!")
                    st.rerun()
            else:
                st.warning("Fill in all fields.")

# ══════════════════════════════════════════════════════════════
# MARKET TAB
# ══════════════════════════════════════════════════════════════
elif st.session_state.active_tab == 2:

    # Indices
    st.markdown('<div class="sec-hdr">Indices</div>', unsafe_allow_html=True)
    indices = [("Nifty 50","^NSEI"),("Sensex","^BSESN"),
               ("Bank Nifty","^NSEBANK"),("Nifty IT","^CNXIT")]
    for name, ticker in indices:
        p, chg, pct = fetch_index(ticker)
        if p:
            cls  = "up" if pct >= 0 else "down"
            sign = "+" if pct >= 0 else ""
            spark = fetch_sparkline(ticker)
            c1, c2, c3 = st.columns([3,2,2])
            c1.markdown(f"""
            <div style="padding:8px 0;">
              <div class="stock-name">{name}</div>
              <div class="stock-sub">₹{p:,.2f}</div>
            </div>""", unsafe_allow_html=True)
            if spark and c2:
                with c2:
                    st.plotly_chart(sparkline_fig(spark, pct>=0),
                        use_container_width=True, config={"displayModeBar":False})
            c3.markdown(f"""
            <div style="text-align:right;padding-top:10px;">
              <span class="pill {'pill-up' if pct>=0 else 'pill-down'}">{sign}{pct:.2f}%</span><br>
              <span class="stock-sub {cls}">{sign}₹{chg:,.2f}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#1e1e1e;margin:4px 0;'>", unsafe_allow_html=True)

    # Gainers & Losers
    with st.spinner("Loading movers..."):
        gainers, losers = fetch_top_movers()

    st.markdown('<div class="sec-hdr">Top gainers</div>', unsafe_allow_html=True)
    if not gainers.empty:
        for _, r in gainers.iterrows():
            bg, fg = avatar_colors(r["symbol"])
            spark  = fetch_sparkline(r["symbol"]+".NS")
            c1, c2, c3 = st.columns([3,2,2])
            c1.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:6px 0;">
              <div class="stock-avatar" style="background:{bg};color:{fg};">{r['symbol'][:3]}</div>
              <div><div class="stock-name">{r['symbol']}</div>
              <div class="stock-sub">₹{r['price']:,.2f}</div></div>
            </div>""", unsafe_allow_html=True)
            if spark:
                with c2:
                    st.plotly_chart(sparkline_fig(spark,True),
                        use_container_width=True, config={"displayModeBar":False})
            c3.markdown(f'<div style="text-align:right;padding-top:10px;"><span class="pill pill-up">+{r["pct"]:.2f}%</span></div>',
                unsafe_allow_html=True)

    st.markdown('<div class="sec-hdr">Top losers</div>', unsafe_allow_html=True)
    if not losers.empty:
        for _, r in losers.iterrows():
            bg, fg = avatar_colors(r["symbol"])
            spark  = fetch_sparkline(r["symbol"]+".NS")
            c1, c2, c3 = st.columns([3,2,2])
            c1.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:6px 0;">
              <div class="stock-avatar" style="background:{bg};color:{fg};">{r['symbol'][:3]}</div>
              <div><div class="stock-name">{r['symbol']}</div>
              <div class="stock-sub">₹{r['price']:,.2f}</div></div>
            </div>""", unsafe_allow_html=True)
            if spark:
                with c2:
                    st.plotly_chart(sparkline_fig(spark,False),
                        use_container_width=True, config={"displayModeBar":False})
            c3.markdown(f'<div style="text-align:right;padding-top:10px;"><span class="pill pill-down">{r["pct"]:.2f}%</span></div>',
                unsafe_allow_html=True)

    # Stock lookup
    st.markdown('<div class="sec-hdr">Stock lookup</div>', unsafe_allow_html=True)
    lookup = st.text_input("Search NSE symbol", placeholder="e.g. RELIANCE, ZOMATO, IRCTC",
                           label_visibility="collapsed").upper().strip()
    if lookup:
        p, chg, pct = fetch_price(lookup+".NS")
        if p:
            info = fetch_stock_info(lookup+".NS")
            cls  = "up" if pct >= 0 else "down"
            sign = "+" if pct >= 0 else ""
            st.markdown(f"""
            <div class="card">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                  <div style="font-size:18px;font-weight:700;color:#f0f0f0;">{lookup}</div>
                  <div class="stock-sub">{info.get('name','')}</div>
                  <div class="stock-sub">{info.get('sector','')}</div>
                </div>
                <div style="text-align:right;">
                  <div style="font-size:22px;font-weight:700;color:#f0f0f0;">₹{p:,.2f}</div>
                  <span class="pill {'pill-up' if pct>=0 else 'pill-down'}">{sign}{pct:.2f}% · {sign}₹{chg:.2f}</span>
                </div>
              </div>
              <hr style="border-color:#2a2a2a;margin:12px 0;">
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:12px;color:#888;">
                <div>52W High: <span style="color:#f0f0f0;font-weight:600;">₹{info.get('52w_high','—')}</span></div>
                <div>52W Low: <span style="color:#f0f0f0;font-weight:600;">₹{info.get('52w_low','—')}</span></div>
                <div>P/E: <span style="color:#f0f0f0;font-weight:600;">{round(info['pe'],1) if info.get('pe') else '—'}</span></div>
                <div>Mkt Cap: <span style="color:#f0f0f0;font-weight:600;">{'₹'+str(round(info['mktcap']/1e9,0))+'Cr' if info.get('mktcap') else '—'}</span></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            period = st.radio("Period", ["1wk","1mo","3mo","6mo","1y"], horizontal=True, key="lookup_prd")
            hist = fetch_history(lookup+".NS", period)
            if not hist.empty:
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=hist.index, open=hist["Open"], high=hist["High"],
                    low=hist["Low"], close=hist["Close"],
                    increasing_line_color="#00d09c", decreasing_line_color="#ff6b6b",
                    increasing_fillcolor="#00d09c33", decreasing_fillcolor="#ff6b6b33"))
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(t=4,b=4,l=0,r=0), height=220,
                    xaxis=dict(showgrid=False, color="#555", rangeslider_visible=False),
                    yaxis=dict(showgrid=True, gridcolor="#1e1e1e", color="#555"))
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        else:
            st.error(f"Symbol '{lookup}' not found on NSE.")

# ══════════════════════════════════════════════════════════════
# AI INSIGHTS TAB
# ══════════════════════════════════════════════════════════════
elif st.session_state.active_tab == 3:

    if not st.session_state.get("anthropic_key"):
        st.markdown("""
        <div class="card" style="text-align:center;padding:24px;">
          <div style="font-size:32px;margin-bottom:8px;">🤖</div>
          <div style="font-weight:600;font-size:15px;color:#f0f0f0;margin-bottom:6px;">AI Analyst</div>
          <div style="font-size:13px;color:#888;">Enter your Anthropic API key in the ⚙️ sidebar to unlock AI-powered portfolio insights.</div>
        </div>
        """, unsafe_allow_html=True)
    elif not st.session_state.portfolio:
        st.info("Add holdings in the Portfolio tab first.")
    else:
        rows, invested, current, pnl, pnl_pct = portfolio_summary()

        st.markdown('<div class="sec-hdr">Quick questions</div>', unsafe_allow_html=True)
        quick_qs = [
            ("🔄","Should I rebalance my portfolio?"),
            ("⚠️","Which stock carries the most risk?"),
            ("📈","What's the Nifty 50 outlook this month?"),
            ("👀","2 NSE stocks to watch this week"),
            ("📊","Summarise my portfolio performance"),
            ("💡","What sector should I add exposure to?"),
        ]
        c1, c2 = st.columns(2)
        for i, (icon, q) in enumerate(quick_qs):
            col = c1 if i % 2 == 0 else c2
            if col.button(f"{icon} {q}", use_container_width=True, key=f"qq_{i}"):
                with st.spinner("Thinking..."):
                    st.session_state.ai_response = ask_claude(q, rows, invested, current, pnl, pnl_pct)

        st.markdown('<div class="sec-hdr">Ask anything</div>', unsafe_allow_html=True)
        custom_q = st.text_area("Your question", placeholder="e.g. My SUNPHARMA is down 12% — cut losses or average down?",
                                height=80, label_visibility="collapsed")
        if st.button("Ask AI analyst ↗", use_container_width=True):
            if custom_q.strip():
                with st.spinner("Thinking..."):
                    st.session_state.ai_response = ask_claude(custom_q, rows, invested, current, pnl, pnl_pct)

        if st.session_state.ai_response:
            st.markdown('<div class="sec-hdr">Response</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="ai-box">{st.session_state.ai_response}</div>',
                unsafe_allow_html=True)

st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
