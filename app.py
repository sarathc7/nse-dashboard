import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import anthropic
import json
import os

st.set_page_config(
    page_title="NSE Portfolio Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .main .block-container { padding: 1rem 1rem 2rem; max-width: 480px; margin: auto; }
    .metric-card { background: #f8f9fa; border-radius: 12px; padding: 14px; margin-bottom: 8px; }
    .up { color: #1D9E75; font-weight: 500; }
    .down { color: #E24B4A; font-weight: 500; }
    .section-title { font-size: 12px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin: 16px 0 8px; }
    div[data-testid="stTab"] button { font-size: 13px; padding: 6px 10px; }
    .stAlert { font-size: 13px; }
    .ai-response { background: #f0faf5; border-left: 3px solid #1D9E75; padding: 12px; border-radius: 8px; font-size: 14px; line-height: 1.6; }
    footer { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []   # list of {symbol, qty, avg_price}
if "ai_response" not in st.session_state:
    st.session_state.ai_response = ""
if "prices_cache" not in st.session_state:
    st.session_state.prices_cache = {}

# ── Helpers ────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_price(ticker_ns):
    """Fetch current price + day change for a .NS ticker."""
    try:
        t = yf.Ticker(ticker_ns)
        info = t.fast_info
        price = info.last_price
        prev  = info.previous_close
        chg   = price - prev
        pct   = (chg / prev) * 100
        return round(price, 2), round(chg, 2), round(pct, 2)
    except Exception:
        return None, None, None

@st.cache_data(ttl=300)
def fetch_history(ticker_ns, period="1mo"):
    try:
        t = yf.Ticker(ticker_ns)
        return t.history(period=period)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_index(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        price = info.last_price
        prev  = info.previous_close
        chg   = price - prev
        pct   = (chg / prev) * 100
        return round(price, 2), round(chg, 2), round(pct, 2)
    except Exception:
        return None, None, None

@st.cache_data(ttl=600)
def fetch_top_movers():
    """Sample Nifty 50 stocks for top gainers/losers."""
    symbols = [
        "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS",
        "WIPRO.NS","AXISBANK.NS","SBIN.NS","MARUTI.NS","TATAMOTORS.NS",
        "SUNPHARMA.NS","DRREDDY.NS","BAJFINANCE.NS","LTIM.NS","HCLTECH.NS"
    ]
    rows = []
    for sym in symbols:
        p, chg, pct = fetch_price(sym)
        if p:
            rows.append({"symbol": sym.replace(".NS",""), "price": p, "change": chg, "pct": pct})
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
    gainers = df.nlargest(5, "pct")
    losers  = df.nsmallest(5, "pct")
    return gainers, losers

def portfolio_summary():
    """Compute portfolio totals from session state."""
    invested = 0
    current  = 0
    rows = []
    for h in st.session_state.portfolio:
        sym = h["symbol"] + ".NS"
        p, chg, pct = fetch_price(sym)
        if p is None:
            p = h["avg_price"]
            chg, pct = 0, 0
        inv = h["qty"] * h["avg_price"]
        cur = h["qty"] * p
        pnl = cur - inv
        pnl_pct = (pnl / inv * 100) if inv else 0
        invested += inv
        current  += cur
        rows.append({
            "Symbol": h["symbol"],
            "Qty": h["qty"],
            "Avg Price": h["avg_price"],
            "LTP": p,
            "Invested": inv,
            "Current": cur,
            "P&L": pnl,
            "P&L %": pnl_pct,
            "Day Chg %": pct
        })
    total_pnl = current - invested
    total_pct = (total_pnl / invested * 100) if invested else 0
    return rows, invested, current, total_pnl, total_pct

def ask_claude(question, portfolio_rows, invested, current, total_pnl, total_pct):
    api_key = st.session_state.get("anthropic_key", "")
    if not api_key:
        return "Please enter your Anthropic API key in the sidebar to use AI insights."
    portfolio_str = json.dumps(portfolio_rows, default=str, indent=2)
    client = anthropic.Anthropic(api_key=api_key)
    system = f"""You are a concise NSE stock market analyst assistant.
User portfolio summary:
- Invested: ₹{invested:,.0f}
- Current value: ₹{current:,.0f}
- Total P&L: ₹{total_pnl:,.0f} ({total_pct:.1f}%)
Holdings: {portfolio_str}

Give practical, brief answers in 4-6 sentences. Be specific about the stocks.
Always end with: "This is not financial advice — consult a SEBI-registered advisor."
"""
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=system,
        messages=[{"role": "user", "content": question}]
    )
    return msg.content[0].text

# ── Header ─────────────────────────────────────────────────────
st.markdown("## 📈 NSE Dashboard")
st.caption(f"Last refreshed: {datetime.now().strftime('%d %b %Y, %I:%M %p IST')}")

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    api_key = st.text_input("Anthropic API key (for AI insights)", type="password",
                            placeholder="sk-ant-...")
    if api_key:
        st.session_state.anthropic_key = api_key
        st.success("API key saved")
    st.markdown("---")
    st.markdown("**How to get a free API key:**")
    st.markdown("1. Go to [console.anthropic.com](https://console.anthropic.com)\n2. Sign up → API Keys → Create Key\n3. Paste it above")
    st.markdown("---")
    if st.button("🔄 Clear cache & refresh"):
        st.cache_data.clear()
        st.rerun()

# ── Tabs ───────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Portfolio", "Market", "AI Insights"])

# ══════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════
with tab1:
    if not st.session_state.portfolio:
        st.info("👋 Add your holdings in the **Portfolio** tab to see your overview.")
    else:
        rows, invested, current, total_pnl, total_pct = portfolio_summary()

        c1, c2 = st.columns(2)
        with c1:
            st.metric("Portfolio Value", f"₹{current:,.0f}")
            st.metric("Invested", f"₹{invested:,.0f}")
        with c2:
            st.metric("Total P&L", f"₹{total_pnl:,.0f}",
                      delta=f"{total_pct:.1f}%",
                      delta_color="normal")
            winners = sum(1 for r in rows if r["P&L"] > 0)
            st.metric("Winners / Total", f"{winners} / {len(rows)}")

        st.markdown('<div class="section-title">Sector-wise allocation</div>', unsafe_allow_html=True)
        df = pd.DataFrame(rows)
        fig_pie = px.pie(df, values="Current", names="Symbol",
                         color_discrete_sequence=px.colors.qualitative.Pastel,
                         hole=0.45)
        fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=240,
                              showlegend=True,
                              legend=dict(font_size=11, orientation="h", y=-0.15))
        fig_pie.update_traces(textinfo="percent+label", textfont_size=11)
        st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown('<div class="section-title">Holdings snapshot</div>', unsafe_allow_html=True)
        df_show = df[["Symbol","Qty","LTP","P&L","P&L %","Day Chg %"]].copy()
        df_show["P&L"]     = df_show["P&L"].map(lambda x: f"{'+'if x>=0 else ''}₹{x:,.0f}")
        df_show["P&L %"]   = df_show["P&L %"].map(lambda x: f"{'+'if x>=0 else ''}{x:.1f}%")
        df_show["Day Chg %"] = df_show["Day Chg %"].map(lambda x: f"{'+'if x>=0 else ''}{x:.1f}%")
        df_show["LTP"]     = df_show["LTP"].map(lambda x: f"₹{x:,.2f}")
        st.dataframe(df_show, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
# TAB 2 — PORTFOLIO
# ══════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-title">Add a holding</div>', unsafe_allow_html=True)
    with st.form("add_holding", clear_on_submit=True):
        c1, c2, c3 = st.columns([2,1,1.5])
        with c1:
            sym = st.text_input("NSE Symbol", placeholder="e.g. TCS").upper().strip()
        with c2:
            qty = st.number_input("Qty", min_value=1, step=1)
        with c3:
            avg = st.number_input("Avg Price ₹", min_value=0.01, step=0.01, format="%.2f")
        submitted = st.form_submit_button("➕ Add", use_container_width=True)
        if submitted:
            if sym and qty and avg:
                # Quick validate
                test_p, _, _ = fetch_price(sym + ".NS")
                if test_p is None:
                    st.error(f"Could not find '{sym}.NS' on NSE. Check the symbol.")
                else:
                    existing = [h for h in st.session_state.portfolio if h["symbol"] == sym]
                    if existing:
                        st.warning(f"{sym} already in portfolio. Remove it first to update.")
                    else:
                        st.session_state.portfolio.append({"symbol": sym, "qty": int(qty), "avg_price": float(avg)})
                        st.success(f"Added {sym}")
                        st.rerun()
            else:
                st.warning("Fill in all fields.")

    if st.session_state.portfolio:
        st.markdown('<div class="section-title">Your holdings</div>', unsafe_allow_html=True)
        rows, invested, current, total_pnl, total_pct = portfolio_summary()
        for i, (h, r) in enumerate(zip(st.session_state.portfolio, rows)):
            with st.container():
                c1, c2, c3 = st.columns([3, 2, 1])
                with c1:
                    st.markdown(f"**{r['Symbol']}**  \n{r['Qty']} qty · avg ₹{r['Avg Price']:,.2f}")
                with c2:
                    color = "up" if r["P&L"] >= 0 else "down"
                    sign  = "+" if r["P&L"] >= 0 else ""
                    st.markdown(f"₹{r['LTP']:,.2f}  \n<span class='{color}'>{sign}₹{r['P&L']:,.0f} ({sign}{r['P&L %']:.1f}%)</span>",
                                unsafe_allow_html=True)
                with c3:
                    if st.button("🗑", key=f"del_{i}"):
                        st.session_state.portfolio.pop(i)
                        st.rerun()
                st.markdown("---")

        st.markdown('<div class="section-title">Price history (select stock)</div>', unsafe_allow_html=True)
        syms = [h["symbol"] for h in st.session_state.portfolio]
        sel  = st.selectbox("Stock", syms, label_visibility="collapsed")
        period = st.radio("Period", ["1mo","3mo","6mo","1y"], horizontal=True, index=1)
        hist = fetch_history(sel + ".NS", period=period)
        if not hist.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"],
                                     mode="lines", line=dict(color="#1D9E75", width=2),
                                     fill="tozeroy", fillcolor="rgba(29,158,117,0.08)"))
            fig.update_layout(margin=dict(t=10,b=10,l=0,r=0), height=200,
                              xaxis=dict(showgrid=False),
                              yaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
                              plot_bgcolor="white", paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No holdings yet. Add your first stock above!")

# ══════════════════════════════════════════════════════════════
# TAB 3 — MARKET
# ══════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-title">Indices</div>', unsafe_allow_html=True)
    indices = {
        "Nifty 50":   "^NSEI",
        "Sensex":     "^BSESN",
        "Bank Nifty": "^NSEBANK",
        "Nifty IT":   "^CNXIT",
    }
    c1, c2 = st.columns(2)
    for i, (name, ticker) in enumerate(indices.items()):
        p, chg, pct = fetch_index(ticker)
        col = c1 if i % 2 == 0 else c2
        if p:
            sign  = "+" if pct >= 0 else ""
            color = "#1D9E75" if pct >= 0 else "#E24B4A"
            col.metric(name, f"{p:,.2f}", delta=f"{sign}{pct:.2f}%")
        else:
            col.metric(name, "—")

    st.markdown('<div class="section-title">Top gainers & losers (Nifty sample)</div>', unsafe_allow_html=True)
    with st.spinner("Fetching movers..."):
        gainers, losers = fetch_top_movers()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**📈 Gainers**")
        if not gainers.empty:
            for _, row in gainers.iterrows():
                st.markdown(f"`{row['symbol']}` — <span class='up'>+{row['pct']:.1f}%</span>  \n₹{row['price']:,.2f}",
                            unsafe_allow_html=True)
                st.markdown("")
    with c2:
        st.markdown("**📉 Losers**")
        if not losers.empty:
            for _, row in losers.iterrows():
                st.markdown(f"`{row['symbol']}` — <span class='down'>{row['pct']:.1f}%</span>  \n₹{row['price']:,.2f}",
                            unsafe_allow_html=True)
                st.markdown("")

    st.markdown('<div class="section-title">Stock lookup</div>', unsafe_allow_html=True)
    lookup = st.text_input("Enter NSE symbol", placeholder="e.g. RELIANCE").upper().strip()
    if lookup:
        p, chg, pct = fetch_price(lookup + ".NS")
        if p:
            sign = "+" if pct >= 0 else ""
            color = "up" if pct >= 0 else "down"
            st.markdown(f"**{lookup}** — ₹{p:,.2f}  \n<span class='{color}'>{sign}₹{chg:.2f} ({sign}{pct:.2f}%) today</span>",
                        unsafe_allow_html=True)
            hist = fetch_history(lookup + ".NS", "3mo")
            if not hist.empty:
                fig = go.Figure(go.Candlestick(
                    x=hist.index, open=hist["Open"], high=hist["High"],
                    low=hist["Low"], close=hist["Close"],
                    increasing_line_color="#1D9E75", decreasing_line_color="#E24B4A"))
                fig.update_layout(margin=dict(t=10,b=10,l=0,r=0), height=220,
                                  xaxis_rangeslider_visible=False,
                                  plot_bgcolor="white", paper_bgcolor="white")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"Symbol '{lookup}.NS' not found. Check the NSE ticker.")

# ══════════════════════════════════════════════════════════════
# TAB 4 — AI INSIGHTS
# ══════════════════════════════════════════════════════════════
with tab4:
    if not st.session_state.get("anthropic_key"):
        st.warning("Enter your Anthropic API key in the ⚙️ sidebar to unlock AI insights.")
    elif not st.session_state.portfolio:
        st.info("Add holdings in the **Portfolio** tab first so the AI can analyse them.")
    else:
        rows, invested, current, total_pnl, total_pct = portfolio_summary()

        st.markdown('<div class="section-title">Quick questions</div>', unsafe_allow_html=True)
        quick_qs = [
            "Should I rebalance my portfolio?",
            "Which of my stocks has the highest risk?",
            "What is the Nifty 50 outlook for next month?",
            "Give me 2 NSE stocks to watch this week.",
            "Summarise my portfolio performance.",
        ]
        cols = st.columns(2)
        for i, q in enumerate(quick_qs):
            if cols[i % 2].button(q, use_container_width=True):
                with st.spinner("Thinking..."):
                    st.session_state.ai_response = ask_claude(q, rows, invested, current, total_pnl, total_pct)

        st.markdown('<div class="section-title">Ask anything</div>', unsafe_allow_html=True)
        custom_q = st.text_area("Your question", placeholder="e.g. My Sun Pharma is down 10% — should I average down or cut losses?", height=80)
        if st.button("Ask AI analyst ↗", use_container_width=True):
            if custom_q.strip():
                with st.spinner("Thinking..."):
                    st.session_state.ai_response = ask_claude(custom_q, rows, invested, current, total_pnl, total_pct)

        if st.session_state.ai_response:
            st.markdown('<div class="section-title">AI response</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="ai-response">{st.session_state.ai_response}</div>', unsafe_allow_html=True)

st.markdown("---")
st.caption("Data via Yahoo Finance (15-min delay). Not financial advice.")
