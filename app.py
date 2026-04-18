import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import anthropic
import json
import pytz

st.set_page_config(
    page_title="Stocklens",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif !important;background:#0d0d0d !important;color:#f0f0f0 !important;}
.stApp{background:#0d0d0d;}
.main .block-container{padding:0 0.75rem 5rem;max-width:480px;margin:auto;}

/* Remove blank space */
.stApp>header{display:none !important;}
.stApp [data-testid="stAppViewContainer"]>section>div:first-child{padding-top:0 !important;}
.block-container{padding-top:0 !important;}
#MainMenu,footer,header{visibility:hidden;display:none;}
[data-testid="stToolbar"]{display:none;}
[data-testid="stDecoration"]{display:none;}
[data-testid="stStatusWidget"]{display:none;}

/* Topbar */
.topbar{background:#0d0d0d;padding:10px 2px 8px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1e1e1e;margin-bottom:10px;}
.logo-wrap{display:flex;align-items:center;gap:8px;}
.logo-text{font-size:19px;font-weight:700;letter-spacing:-0.5px;}
.logo-text .s1{color:#00d09c;} .logo-text .s2{color:#f0f0f0;}
.market-badge{font-size:11px;font-weight:600;padding:3px 10px;border-radius:20px;}
.market-open{background:#0a2e22;color:#00d09c;border:1px solid rgba(0,208,156,0.3);}
.market-closed{background:#2e1a1a;color:#ff6b6b;border:1px solid rgba(255,107,107,0.3);}

/* Hero */
.hero-card{background:linear-gradient(135deg,#0a2e22,#0d3d2d);border:1px solid rgba(0,208,156,0.2);border-radius:20px;padding:20px 18px 16px;margin-bottom:14px;}
.hero-label{font-size:11px;color:rgba(0,208,156,0.7);font-weight:500;margin-bottom:3px;}
.hero-value{font-size:30px;font-weight:700;color:#f0f0f0;letter-spacing:-1px;}
.hero-pnl{font-size:13px;font-weight:600;margin-top:3px;}
.hero-sub{font-size:11px;color:#aaa;margin-top:2px;}

/* Index strip */
.index-strip{display:flex;gap:8px;overflow-x:auto;padding:2px 0 10px;scrollbar-width:none;}
.index-strip::-webkit-scrollbar{display:none;}
.index-chip{min-width:110px;background:#1a1a1a;border:1px solid #2a2a2a;border-radius:12px;padding:9px 11px;flex-shrink:0;}
.chip-name{font-size:10px;color:#888;font-weight:500;}
.chip-val{font-size:13px;font-weight:600;color:#f0f0f0;margin:2px 0 1px;}
.chip-chg{font-size:10px;font-weight:600;}

/* Section header */
.sec-hdr{font-size:12px;font-weight:700;color:#666;text-transform:uppercase;letter-spacing:0.7px;margin:18px 0 8px;}

/* Filter pills */
.filter-row{display:flex;gap:6px;overflow-x:auto;padding:2px 0 8px;scrollbar-width:none;margin-bottom:4px;}
.filter-row::-webkit-scrollbar{display:none;}
.fpill{padding:5px 12px;border-radius:20px;font-size:12px;font-weight:600;background:#1a1a1a;border:1px solid #2a2a2a;color:#888;white-space:nowrap;}
.fpill.active{background:#0a2e22;border-color:#00d09c;color:#00d09c;}

/* Cards */
.card{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:16px;padding:14px;margin-bottom:10px;}

/* Stock rows */
.srow{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid #1e1e1e;}
.srow:last-child{border-bottom:none;}
.savatar{width:36px;height:36px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;flex-shrink:0;}
.sname{font-size:13px;font-weight:600;color:#f0f0f0;}
.ssub{font-size:10px;color:#666;margin-top:1px;}
.sprice{font-size:13px;font-weight:600;color:#f0f0f0;}
.schg{font-size:10px;font-weight:600;margin-top:2px;}

/* Pills */
.pill{display:inline-block;padding:2px 7px;border-radius:20px;font-size:10px;font-weight:700;}
.pill-up{background:#0a2e22;color:#00d09c;}
.pill-down{background:#2e1a1a;color:#ff6b6b;}

/* Metric grid */
.mgrid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px;}
.mcard{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:14px;padding:12px 14px;}
.mcard-label{font-size:10px;color:#555;font-weight:600;text-transform:uppercase;margin-bottom:3px;}
.mcard-val{font-size:18px;font-weight:700;color:#f0f0f0;}
.mcard-sub{font-size:10px;margin-top:2px;}

/* Recommendation card */
.rec-card{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:14px;padding:13px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:flex-start;}
.rec-tag{display:inline-block;padding:2px 8px;border-radius:6px;font-size:10px;font-weight:700;margin-bottom:4px;}
.rec-buy{background:#0a2e22;color:#00d09c;}
.rec-sell{background:#2e1a1a;color:#ff6b6b;}
.rec-hold{background:#2a1a00;color:#f5a623;}

/* Discover */
.disc-reason{font-size:10px;color:#00d09c;font-weight:600;margin-top:2px;}

/* AI */
.ai-box{background:#0a2e22;border:1px solid rgba(0,208,156,0.2);border-radius:14px;padding:14px;font-size:13px;line-height:1.7;color:#e0e0e0;}

/* Bottom nav */
.bnav{position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:100%;max-width:480px;background:#111;border-top:1px solid #222;display:flex;z-index:999;padding:4px 0 8px;}
.bnav-item{flex:1;text-align:center;padding:5px 0;font-size:9px;font-weight:600;color:#444;text-transform:uppercase;letter-spacing:0.3px;cursor:pointer;}
.bnav-item.on{color:#00d09c;}
.bnav-icon{font-size:18px;display:block;margin-bottom:1px;}

/* Hide all radio widgets (used only for state) */
.stRadio{display:none !important;}
div[data-testid="stHorizontalBlock"]{display:none !important;}

/* Inputs / buttons */
.stTextInput input,.stNumberInput input{background:#1a1a1a !important;color:#f0f0f0 !important;border:1px solid #2a2a2a !important;border-radius:10px !important;}
.stButton button{background:#00d09c !important;color:#000 !important;font-weight:700 !important;border-radius:12px !important;border:none !important;}
div[data-testid="stForm"]{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:16px;padding:14px;}
div[data-testid="stMetric"]{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:14px;padding:10px 14px;}
div[data-testid="stMetricValue"]{color:#f0f0f0 !important;}
::-webkit-scrollbar{width:3px;height:3px;}::-webkit-scrollbar-thumb{background:#333;border-radius:3px;}
.up{color:#00d09c;} .down{color:#ff6b6b;} .muted{color:#555;}
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────
defaults = {"portfolio":[],"ai_response":"","tab":0,"anthropic_key":"",
            "gl_filter":"Large Cap","disc_filter":"Bullish Movers",
            "aff_filter":"Under ₹100","rec_filter":"All"}
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k]=v

# ── Helpers ────────────────────────────────────────────────────
def market_status():
    ist=pytz.timezone("Asia/Kolkata"); now=datetime.now(ist)
    open_=(now.weekday()<5 and (now.hour>9 or (now.hour==9 and now.minute>=15)) and now.hour<16)
    return open_, now.strftime("%I:%M %p")

@st.cache_data(ttl=300)
def fetch_price(sym):
    try:
        t=yf.Ticker(sym); i=t.fast_info
        p=round(i.last_price,2); prev=round(i.previous_close,2)
        return p, round(p-prev,2), round((p-prev)/prev*100,2)
    except: return None,None,None

@st.cache_data(ttl=300)
def fetch_history(sym,period="1mo"):
    try: return yf.Ticker(sym).history(period=period)
    except: return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_sparkline(sym):
    try:
        h=yf.Ticker(sym).history(period="5d",interval="1h")
        return h["Close"].tolist() if not h.empty else []
    except: return []

@st.cache_data(ttl=600)
def fetch_info(sym):
    try:
        i=yf.Ticker(sym).info
        return {"52h":i.get("fiftyTwoWeekHigh"),"52l":i.get("fiftyTwoWeekLow"),
                "pe":i.get("trailingPE"),"sector":i.get("sector","—"),
                "mktcap":i.get("marketCap"),"name":i.get("longName",sym)}
    except: return {}

@st.cache_data(ttl=600)
def fetch_movers_by_cap(cap):
    syms={"Large Cap":["RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS","WIPRO.NS","AXISBANK.NS","SBIN.NS","BAJFINANCE.NS","HCLTECH.NS","LT.NS","KOTAKBANK.NS","BHARTIARTL.NS","ASIANPAINT.NS","MARUTI.NS"],
          "Mid Cap":["MPHASIS.NS","PERSISTENT.NS","LTIM.NS","COFORGE.NS","TATACOMM.NS","VOLTAS.NS","ALKEM.NS","TORNTPHARM.NS","SUNDARMFIN.NS","CDSL.NS","METROPOLIS.NS"],
          "Small Cap":["IRCTC.NS","ZOMATO.NS","NYKAA.NS","PAYTM.NS","EASEMYTRIP.NS","KAYNES.NS","IXIGO.NS","POLICYBZR.NS"]}.get(cap,[])
    rows=[]
    for s in syms:
        p,chg,pct=fetch_price(s)
        if p: rows.append({"symbol":s.replace(".NS",""),"price":p,"chg":chg,"pct":pct})
    df=pd.DataFrame(rows)
    if df.empty: return pd.DataFrame(),pd.DataFrame()
    return df.nlargest(5,"pct"),df.nsmallest(5,"pct")

@st.cache_data(ttl=600)
def fetch_discover(f):
    sets={"Bullish Movers":["RELIANCE.NS","TCS.NS","INFY.NS","LTIM.NS","HCLTECH.NS","BAJFINANCE.NS","TITAN.NS","ZOMATO.NS"],
          "Highest Returns":["IRCTC.NS","COFORGE.NS","PERSISTENT.NS","CDSL.NS","MPHASIS.NS","KAYNES.NS","DIXON.NS"],
          "Golden Cross":["HDFCBANK.NS","ICICIBANK.NS","KOTAKBANK.NS","SBIN.NS","AXISBANK.NS","INDUSINDBK.NS","FEDERALBNK.NS"],
          "Top Intraday":["RELIANCE.NS","TATAMOTORS.NS","WIPRO.NS","BPCL.NS","ONGC.NS","TATAPOWER.NS","HINDALCO.NS"],
          "52W Breakouts":["TITAN.NS","BHARTIARTL.NS","LT.NS","POWERGRID.NS","NTPC.NS","ADANIENT.NS"]}
    reasons={"Bullish Movers":"Strong upward momentum","Highest Returns":"Top YTD performer",
             "Golden Cross":"50MA crossed above 200MA","Top Intraday":"High volume & volatility","52W Breakouts":"Broke 52-week high"}
    rows=[]
    for s in sets.get(f,[]):
        p,chg,pct=fetch_price(s)
        if p: rows.append({"symbol":s.replace(".NS",""),"price":p,"pct":pct,"reason":reasons.get(f,"")})
    return rows

@st.cache_data(ttl=600)
def fetch_affordable(r):
    data={"Under ₹100":(0,100,["IRFC.NS","SAIL.NS","NHPC.NS","RVNL.NS","HUDCO.NS","BEL.NS","RECLTD.NS","YESBANK.NS"]),
          "₹100–500":(100,500,["ZOMATO.NS","NYKAA.NS","PAYTM.NS","BANKBARODA.NS","PNB.NS","GAIL.NS","IDEA.NS"]),
          "₹500–1000":(500,1000,["WIPRO.NS","HCLTECH.NS","SBIN.NS","AXISBANK.NS","DRREDDY.NS","CIPLA.NS","SUNPHARMA.NS"]),
          "₹1000–2000":(1000,2000,["INFY.NS","ICICIBANK.NS","HDFCBANK.NS","LT.NS","TITAN.NS","DMART.NS"]),
          "₹2000+":(2000,999999,["TCS.NS","RELIANCE.NS","MARUTI.NS","BAJFINANCE.NS","ASIANPAINT.NS","NESTLEIND.NS"])}
    lo,hi,syms=data.get(r,(0,100,[]))
    rows=[]
    for s in syms:
        p,chg,pct=fetch_price(s)
        if p and lo<=p<=hi: rows.append({"symbol":s.replace(".NS",""),"price":p,"pct":pct})
    return rows

RECS=[{"symbol":"TCS","action":"BUY","target":4200,"sl":3600,"reason":"Strong deal wins, margin expansion","confidence":82},
      {"symbol":"HDFCBANK","action":"BUY","target":1900,"sl":1580,"reason":"NIM improvement, robust credit growth","confidence":76},
      {"symbol":"SUNPHARMA","action":"HOLD","target":1380,"sl":1100,"reason":"US pipeline intact, watch FDA updates","confidence":61},
      {"symbol":"RELIANCE","action":"BUY","target":3100,"sl":2700,"reason":"Jio + retail growth, O2C steady","confidence":78},
      {"symbol":"ZOMATO","action":"HOLD","target":240,"sl":185,"reason":"Profitability improving, rich valuation","confidence":58},
      {"symbol":"PAYTM","action":"SELL","target":350,"sl":480,"reason":"RBI headwinds, monetisation unclear","confidence":70}]

def portfolio_summary():
    rows=[]; invested=current=0
    for h in st.session_state.portfolio:
        p,chg,pct=fetch_price(h["symbol"]+".NS")
        if p is None: p,chg,pct=h["avg_price"],0,0
        inv=h["qty"]*h["avg_price"]; cur=h["qty"]*p; pnl=cur-inv
        invested+=inv; current+=cur
        rows.append({"Symbol":h["symbol"],"Qty":h["qty"],"Avg":h["avg_price"],
                     "LTP":p,"Invested":inv,"Current":cur,"PnL":pnl,
                     "PnL%":(pnl/inv*100) if inv else 0,"DayChg%":pct})
    return rows,invested,current,current-invested,((current-invested)/invested*100) if invested else 0

def spark_fig(data,up=True):
    c="#00d09c" if up else "#ff6b6b"; f="rgba(0,208,156,0.12)" if up else "rgba(255,107,107,0.12)"
    fig=go.Figure(go.Scatter(y=data,mode="lines",line=dict(color=c,width=1.5),fill="tozeroy",fillcolor=f))
    fig.update_layout(margin=dict(t=0,b=0,l=0,r=0),height=38,
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),yaxis=dict(visible=False))
    return fig

def av(sym):
    p=[("#0a2e22","#00d09c"),("#1a1540","#a78bfa"),("#2e1a0a","#f5a623"),
       ("#1a0a2e","#c084fc"),("#0a1a2e","#60a5fa"),("#2e0a1a","#fb7185")]
    return p[sum(ord(c) for c in sym)%len(p)]

def ask_claude(q,rows,invested,current,pnl,pnl_pct):
    key=st.session_state.get("anthropic_key","")
    if not key: return "Please enter your Anthropic API key in the ⚙️ sidebar."
    client=anthropic.Anthropic(api_key=key)
    sys=f"""Sharp NSE analyst for Stocklens. Portfolio: invested ₹{invested:,.0f}, current ₹{current:,.0f}, P&L ₹{pnl:,.0f} ({pnl_pct:.1f}%). Holdings: {json.dumps(rows,default=str)}. 4-6 sentences, specific with ₹ and %. End: "⚠️ Not financial advice." """
    msg=client.messages.create(model="claude-sonnet-4-20250514",max_tokens=800,system=sys,messages=[{"role":"user","content":q}])
    return msg.content[0].text

# ── SVG LOGO ───────────────────────────────────────────────────
LOGO = """<svg width="34" height="34" viewBox="0 0 34 34" xmlns="http://www.w3.org/2000/svg">
  <rect width="34" height="34" rx="9" fill="#00d09c"/>
  <circle cx="14" cy="14" r="7" fill="none" stroke="white" stroke-width="2.5"/>
  <line x1="19.2" y1="19.2" x2="27" y2="27" stroke="white" stroke-width="2.6" stroke-linecap="round"/>
  <polyline points="9,14 12,10.5 15,15 18,11" fill="none" stroke="#065f46" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>"""

# ── TOP BAR ────────────────────────────────────────────────────
is_open,time_str=market_status()
bc="market-open" if is_open else "market-closed"
bt=f"● OPEN · {time_str}" if is_open else f"● CLOSED · {time_str}"
st.markdown(f'<div class="topbar"><div class="logo-wrap">{LOGO}<div class="logo-text"><span class="s1">Stock</span><span class="s2">lens</span></div></div><span class="market-badge {bc}">{bt}</span></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    key=st.text_input("Anthropic API key",type="password",placeholder="sk-ant-...")
    if key: st.session_state.anthropic_key=key; st.success("Saved ✓")
    st.markdown("---")
    if st.button("🔄 Refresh data"): st.cache_data.clear(); st.rerun()
    st.caption("Yahoo Finance · 15-min delay")

# ── BOTTOM NAV ─────────────────────────────────────────────────
nav_items=[("🏠","Home"),("💼","Portfolio"),("📊","Market"),("🤖","AI")]
bnav='<div class="bnav">'+''.join(
    f'<div class="bnav-item {"on" if i==st.session_state.tab else ""}" '
    f'onclick="document.querySelectorAll(\'[data-testid=stRadio] label\')[{i}].click()">'
    f'<span class="bnav-icon">{ic}</span>{lb}</div>'
    for i,(ic,lb) in enumerate(nav_items))+'</div>'
st.markdown(bnav,unsafe_allow_html=True)
nav=st.radio("nav",[lb for _,lb in nav_items],index=st.session_state.tab,horizontal=True,label_visibility="collapsed")
st.session_state.tab=[lb for _,lb in nav_items].index(nav)
tab=st.session_state.tab

# ══════════════════════════════════════════════════════════════
# HOME
# ══════════════════════════════════════════════════════════════
if tab==0:
    ist=pytz.timezone("Asia/Kolkata"); hour=datetime.now(ist).hour
    greet="Good morning" if hour<12 else ("Good afternoon" if hour<17 else "Good evening")

    if st.session_state.portfolio:
        rows,invested,current,pnl,pnl_pct=portfolio_summary()
        sign="+" if pnl>=0 else ""; pc="#00d09c" if pnl>=0 else "#ff6b6b"
        day_pnl=sum(r["Current"]*r["DayChg%"]/100 for r in rows); ds="+" if day_pnl>=0 else ""
        st.markdown(f'<div class="hero-card"><div class="hero-label">{greet}, Investor 👋 · Portfolio Value</div><div class="hero-value">₹{current:,.0f}</div><div class="hero-pnl" style="color:{pc}">{sign}₹{pnl:,.0f} ({sign}{pnl_pct:.2f}%) overall · {ds}₹{abs(day_pnl):,.0f} today</div><div class="hero-sub">Invested ₹{invested:,.0f} · {len(rows)} stocks</div></div>',unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="hero-card"><div class="hero-label">{greet}, Investor 👋</div><div class="hero-value">₹0.00</div><div class="hero-pnl muted">Add stocks in Portfolio tab to get started</div></div>',unsafe_allow_html=True)

    # Indices
    st.markdown('<div class="sec-hdr">Indices</div>',unsafe_allow_html=True)
    chips=""
    for name,ticker in [("Nifty 50","^NSEI"),("Sensex","^BSESN"),("Bank Nifty","^NSEBANK"),("Nifty IT","^CNXIT"),("Nifty Mid","^NSMIDCP")]:
        p,chg,pct=fetch_price(ticker)
        if p:
            cls="up" if pct>=0 else "down"; sign="+" if pct>=0 else ""
            chips+=f'<div class="index-chip"><div class="chip-name">{name}</div><div class="chip-val">₹{p:,.0f}</div><div class="chip-chg {cls}">{sign}{pct:.2f}%</div></div>'
    st.markdown(f'<div class="index-strip">{chips}</div>',unsafe_allow_html=True)

    # Gainers & Losers
    st.markdown('<div class="sec-hdr">Gainers &amp; Losers</div>',unsafe_allow_html=True)
    cap_opts=["Large Cap","Mid Cap","Small Cap"]
    fp="".join(f'<span class="fpill {"active" if st.session_state.gl_filter==o else ""}">{o}</span>' for o in cap_opts)
    st.markdown(f'<div class="filter-row">{fp}</div>',unsafe_allow_html=True)
    sel_cap=st.radio("cap_sel",cap_opts,index=cap_opts.index(st.session_state.gl_filter),horizontal=True,label_visibility="collapsed")
    if sel_cap!=st.session_state.gl_filter: st.session_state.gl_filter=sel_cap; st.rerun()
    with st.spinner(""):
        gainers,losers=fetch_movers_by_cap(sel_cap)
    c1,c2=st.columns(2)
    with c1:
        st.markdown('<div style="font-size:11px;font-weight:700;color:#00d09c;margin-bottom:5px;">▲ Top Gainers</div>',unsafe_allow_html=True)
        if not gainers.empty:
            for _,r in gainers.iterrows():
                bg,fg=av(r["symbol"])
                st.markdown(f'<div class="srow"><div class="savatar" style="background:{bg};color:{fg};">{r["symbol"][:3]}</div><div style="flex:1;min-width:0;"><div class="sname" style="font-size:11px;">{r["symbol"]}</div><div class="ssub">₹{r["price"]:,.1f}</div></div><span class="pill pill-up">+{r["pct"]:.1f}%</span></div>',unsafe_allow_html=True)
    with c2:
        st.markdown('<div style="font-size:11px;font-weight:700;color:#ff6b6b;margin-bottom:5px;">▼ Top Losers</div>',unsafe_allow_html=True)
        if not losers.empty:
            for _,r in losers.iterrows():
                bg,fg=av(r["symbol"])
                st.markdown(f'<div class="srow"><div class="savatar" style="background:{bg};color:{fg};">{r["symbol"][:3]}</div><div style="flex:1;min-width:0;"><div class="sname" style="font-size:11px;">{r["symbol"]}</div><div class="ssub">₹{r["price"]:,.1f}</div></div><span class="pill pill-down">{r["pct"]:.1f}%</span></div>',unsafe_allow_html=True)

    # Analyzed Recommendations
    st.markdown('<div class="sec-hdr">Analyzed Recommendations</div>',unsafe_allow_html=True)
    rec_opts=["All","BUY","HOLD","SELL"]
    rp="".join(f'<span class="fpill {"active" if st.session_state.rec_filter==o else ""}">{o}</span>' for o in rec_opts)
    st.markdown(f'<div class="filter-row">{rp}</div>',unsafe_allow_html=True)
    sel_rec=st.radio("rec_sel",rec_opts,index=rec_opts.index(st.session_state.rec_filter),horizontal=True,label_visibility="collapsed")
    if sel_rec!=st.session_state.rec_filter: st.session_state.rec_filter=sel_rec; st.rerun()
    for r in [x for x in RECS if sel_rec=="All" or x["action"]==sel_rec]:
        p,_,pct=fetch_price(r["symbol"]+".NS"); ltp=f"₹{p:,.2f}" if p else "—"
        tc={"BUY":"rec-buy","SELL":"rec-sell","HOLD":"rec-hold"}[r["action"]]
        cc="#00d09c" if r["confidence"]>=70 else ("#f5a623" if r["confidence"]>=55 else "#ff6b6b")
        bg,fg=av(r["symbol"])
        st.markdown(f'<div class="rec-card"><div style="display:flex;align-items:flex-start;gap:10px;flex:1;"><div class="savatar" style="background:{bg};color:{fg};flex-shrink:0;">{r["symbol"][:3]}</div><div><span class="rec-tag {tc}">{r["action"]}</span><div class="sname">{r["symbol"]} <span style="font-size:10px;color:#888;font-weight:400;">{ltp}</span></div><div style="font-size:11px;color:#666;margin-top:2px;">{r["reason"]}</div><div style="font-size:10px;color:#555;margin-top:3px;">Target ₹{r["target"]:,} · SL ₹{r["sl"]:,}</div></div></div><div style="text-align:right;flex-shrink:0;margin-left:8px;"><div style="font-size:16px;font-weight:700;color:{cc};">{r["confidence"]}%</div><div style="font-size:9px;color:#444;">confidence</div></div></div>',unsafe_allow_html=True)

    # Discover Stocks
    st.markdown('<div class="sec-hdr">Discover Stocks</div>',unsafe_allow_html=True)
    disc_opts=["Bullish Movers","Highest Returns","Golden Cross","Top Intraday","52W Breakouts"]
    dp="".join(f'<span class="fpill {"active" if st.session_state.disc_filter==o else ""}">{o}</span>' for o in disc_opts)
    st.markdown(f'<div class="filter-row">{dp}</div>',unsafe_allow_html=True)
    sel_disc=st.radio("disc_sel",disc_opts,index=disc_opts.index(st.session_state.disc_filter),horizontal=True,label_visibility="collapsed")
    if sel_disc!=st.session_state.disc_filter: st.session_state.disc_filter=sel_disc; st.rerun()
    for r in fetch_discover(sel_disc):
        bg,fg=av(r["symbol"]); sign="+" if r["pct"]>=0 else ""; cls="up" if r["pct"]>=0 else "down"
        spark=fetch_sparkline(r["symbol"]+".NS")
        c1,c2,c3=st.columns([3,2,2])
        with c1: st.markdown(f'<div style="display:flex;align-items:center;gap:9px;padding:5px 0;"><div class="savatar" style="background:{bg};color:{fg};">{r["symbol"][:3]}</div><div><div class="sname">{r["symbol"]}</div><div class="disc-reason">{r["reason"]}</div></div></div>',unsafe_allow_html=True)
        with c2:
            if spark: st.plotly_chart(spark_fig(spark,r["pct"]>=0),use_container_width=True,config={"displayModeBar":False})
        with c3: st.markdown(f'<div style="text-align:right;padding-top:8px;"><div class="sprice">₹{r["price"]:,.1f}</div><div class="schg {cls}">{sign}{r["pct"]:.2f}%</div></div>',unsafe_allow_html=True)

    # Affordable Stocks
    st.markdown('<div class="sec-hdr">Affordable Stocks</div>',unsafe_allow_html=True)
    aff_opts=["Under ₹100","₹100–500","₹500–1000","₹1000–2000","₹2000+"]
    ap="".join(f'<span class="fpill {"active" if st.session_state.aff_filter==o else ""}">{o}</span>' for o in aff_opts)
    st.markdown(f'<div class="filter-row">{ap}</div>',unsafe_allow_html=True)
    sel_aff=st.radio("aff_sel",aff_opts,index=aff_opts.index(st.session_state.aff_filter),horizontal=True,label_visibility="collapsed")
    if sel_aff!=st.session_state.aff_filter: st.session_state.aff_filter=sel_aff; st.rerun()
    aff=fetch_affordable(sel_aff)
    if aff:
        for r in aff:
            bg,fg=av(r["symbol"]); sign="+" if r["pct"]>=0 else ""; cls="up" if r["pct"]>=0 else "down"
            st.markdown(f'<div class="srow"><div class="savatar" style="background:{bg};color:{fg};">{r["symbol"][:3]}</div><div style="flex:1;"><div class="sname">{r["symbol"]}</div></div><div style="text-align:right;"><div class="sprice">₹{r["price"]:,.2f}</div><div class="schg {cls}">{sign}{r["pct"]:.2f}%</div></div></div>',unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:#555;font-size:13px;padding:8px 0;">Loading price data...</div>',unsafe_allow_html=True)

    st.markdown("<div style='height:70px'></div>",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# PORTFOLIO
# ══════════════════════════════════════════════════════════════
elif tab==1:
    if st.session_state.portfolio:
        rows,invested,current,pnl,pnl_pct=portfolio_summary()
        sign="+" if pnl>=0 else ""; pc="#00d09c" if pnl>=0 else "#ff6b6b"
        st.markdown(f'<div class="mgrid"><div class="mcard"><div class="mcard-label">Current Value</div><div class="mcard-val">₹{current:,.0f}</div></div><div class="mcard"><div class="mcard-label">Total P&amp;L</div><div class="mcard-val" style="color:{pc}">{sign}₹{pnl:,.0f}</div><div class="mcard-sub" style="color:{pc}">{sign}{pnl_pct:.2f}%</div></div><div class="mcard"><div class="mcard-label">Invested</div><div class="mcard-val">₹{invested:,.0f}</div></div><div class="mcard"><div class="mcard-label">Winners</div><div class="mcard-val">{sum(1 for r in rows if r["PnL"]>0)}/{len(rows)}</div></div></div>',unsafe_allow_html=True)
        df_pie=pd.DataFrame(rows)
        fig_pie=go.Figure(go.Pie(labels=df_pie["Symbol"],values=df_pie["Current"],hole=0.55,textinfo="percent+label",textfont_size=11,
            marker=dict(colors=["#00d09c","#a78bfa","#f5a623","#60a5fa","#fb7185","#34d399","#fbbf24"],line=dict(color="#0d0d0d",width=2))))
        fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",margin=dict(t=8,b=8,l=8,r=8),height=210,
            legend=dict(font=dict(color="#aaa",size=10),orientation="h",y=-0.1),showlegend=True)
        st.plotly_chart(fig_pie,use_container_width=True,config={"displayModeBar":False})
        st.markdown('<div class="sec-hdr">Holdings</div>',unsafe_allow_html=True)
        for i,(h,r) in enumerate(zip(st.session_state.portfolio,rows)):
            bg,fg=av(r["Symbol"]); pc2="up" if r["PnL"]>=0 else "down"; sign2="+" if r["PnL"]>=0 else ""
            alloc=(r["Current"]/current*100) if current else 0
            with st.expander(f"{r['Symbol']}  ·  ₹{r['LTP']:,.2f}  ·  {sign2}{r['PnL%']:.1f}%"):
                c1,c2=st.columns(2)
                c1.markdown(f"**Qty:** {r['Qty']}\n\n**Avg:** ₹{r['Avg']:,.2f}\n\n**Invested:** ₹{r['Invested']:,.0f}")
                c2.markdown(f"**Current:** ₹{r['Current']:,.0f}\n\n**P&L:** <span class='{pc2}'>{sign2}₹{r['PnL']:,.0f} ({sign2}{r['PnL%']:.1f}%)</span>\n\n**Alloc:** {alloc:.1f}%",unsafe_allow_html=True)
                info=fetch_info(r["Symbol"]+".NS")
                if info:
                    c3,c4=st.columns(2)
                    c3.markdown(f"**52W H:** ₹{info.get('52h','—')}\n\n**Sector:** {info.get('sector','—')}")
                    c4.markdown(f"**52W L:** ₹{info.get('52l','—')}\n\n**P/E:** {round(info['pe'],1) if info.get('pe') else '—'}")
                prd=st.radio("Period",["1wk","1mo","3mo","6mo","1y"],horizontal=True,key=f"prd_{i}")
                hist=fetch_history(r["Symbol"]+".NS",prd)
                if not hist.empty:
                    col="#00d09c" if r["PnL"]>=0 else "#ff6b6b"; fill="rgba(0,208,156,0.12)" if r["PnL"]>=0 else "rgba(255,107,107,0.12)"
                    fig=go.Figure(go.Scatter(x=hist.index,y=hist["Close"],mode="lines",line=dict(color=col,width=2),fill="tozeroy",fillcolor=fill))
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",margin=dict(t=4,b=4,l=0,r=0),height=150,
                        xaxis=dict(showgrid=False,color="#555"),yaxis=dict(showgrid=True,gridcolor="#1e1e1e",color="#555"))
                    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
                if st.button(f"Remove {r['Symbol']}",key=f"del_{i}"): st.session_state.portfolio.pop(i); st.rerun()
    st.markdown('<div class="sec-hdr">Add Holding</div>',unsafe_allow_html=True)
    with st.form("add_stock",clear_on_submit=True):
        sym=st.text_input("NSE Symbol",placeholder="e.g. TCS, RELIANCE").upper().strip()
        c1,c2=st.columns(2)
        qty=c1.number_input("Qty",min_value=1,step=1)
        avg=c2.number_input("Avg Price ₹",min_value=0.01,step=0.01,format="%.2f")
        if st.form_submit_button("➕ Add to Portfolio",use_container_width=True):
            if sym and qty and avg:
                p,_,_=fetch_price(sym+".NS")
                if p is None: st.error(f"'{sym}' not found on NSE.")
                elif any(h["symbol"]==sym for h in st.session_state.portfolio): st.warning(f"{sym} already added.")
                else: st.session_state.portfolio.append({"symbol":sym,"qty":int(qty),"avg_price":float(avg)}); st.success(f"✓ {sym} added!"); st.rerun()
            else: st.warning("Fill all fields.")
    st.markdown("<div style='height:70px'></div>",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# MARKET
# ══════════════════════════════════════════════════════════════
elif tab==2:
    st.markdown('<div class="sec-hdr">Indices</div>',unsafe_allow_html=True)
    for name,ticker in [("Nifty 50","^NSEI"),("Sensex","^BSESN"),("Bank Nifty","^NSEBANK"),("Nifty IT","^CNXIT")]:
        p,chg,pct=fetch_price(ticker)
        if p:
            cls="up" if pct>=0 else "down"; sign="+" if pct>=0 else ""; spark=fetch_sparkline(ticker)
            c1,c2,c3=st.columns([3,2,2])
            c1.markdown(f'<div style="padding:7px 0;"><div class="sname">{name}</div><div class="ssub">₹{p:,.2f}</div></div>',unsafe_allow_html=True)
            if spark:
                with c2: st.plotly_chart(spark_fig(spark,pct>=0),use_container_width=True,config={"displayModeBar":False})
            c3.markdown(f'<div style="text-align:right;padding-top:10px;"><span class="pill {"pill-up" if pct>=0 else "pill-down"}">{sign}{pct:.2f}%</span><br><span style="font-size:10px;color:#555;">{sign}₹{chg:,.2f}</span></div>',unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#1e1e1e;margin:2px 0;'>",unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">Gainers &amp; Losers</div>',unsafe_allow_html=True)
    cap_opts2=["Large Cap","Mid Cap","Small Cap"]
    sel2=st.radio("cap2",cap_opts2,horizontal=True,label_visibility="collapsed")
    gainers2,losers2=fetch_movers_by_cap(sel2)
    c1,c2=st.columns(2)
    for col,df,label,pcls in [(c1,gainers2,"▲ Gainers","pill-up"),(c2,losers2,"▼ Losers","pill-down")]:
        with col:
            color="#00d09c" if "Gain" in label else "#ff6b6b"
            st.markdown(f'<div style="font-size:11px;font-weight:700;color:{color};margin-bottom:5px;">{label}</div>',unsafe_allow_html=True)
            if not df.empty:
                for _,r in df.iterrows():
                    bg,fg=av(r["symbol"]); sign="+" if r["pct"]>=0 else ""
                    st.markdown(f'<div class="srow"><div class="savatar" style="background:{bg};color:{fg};width:30px;height:30px;font-size:9px;">{r["symbol"][:3]}</div><div style="flex:1;min-width:0;"><div style="font-size:11px;font-weight:600;color:#f0f0f0;">{r["symbol"]}</div><div class="ssub">₹{r["price"]:,.0f}</div></div><span class="pill {pcls}" style="font-size:9px;">{sign}{r["pct"]:.1f}%</span></div>',unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">Stock Lookup</div>',unsafe_allow_html=True)
    lookup=st.text_input("Symbol",placeholder="e.g. RELIANCE, ZOMATO",label_visibility="collapsed").upper().strip()
    if lookup:
        p,chg,pct=fetch_price(lookup+".NS")
        if p:
            info=fetch_info(lookup+".NS"); cls="up" if pct>=0 else "down"; sign="+" if pct>=0 else ""
            st.markdown(f'<div class="card"><div style="display:flex;justify-content:space-between;align-items:flex-start;"><div><div style="font-size:17px;font-weight:700;color:#f0f0f0;">{lookup}</div><div class="ssub">{info.get("name","")}</div><div class="ssub">{info.get("sector","")}</div></div><div style="text-align:right;"><div style="font-size:22px;font-weight:700;color:#f0f0f0;">₹{p:,.2f}</div><span class="pill {"pill-up" if pct>=0 else "pill-down"}">{sign}{pct:.2f}%</span></div></div><hr style="border-color:#2a2a2a;margin:10px 0;"><div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:11px;color:#666;"><div>52W High: <span style="color:#f0f0f0;font-weight:600;">₹{info.get("52h","—")}</span></div><div>52W Low: <span style="color:#f0f0f0;font-weight:600;">₹{info.get("52l","—")}</span></div><div>P/E: <span style="color:#f0f0f0;font-weight:600;">{round(info["pe"],1) if info.get("pe") else "—"}</span></div><div>Mkt Cap: <span style="color:#f0f0f0;font-weight:600;">{"₹"+str(round(info.get("mktcap",0)/1e7,0))+"Cr" if info.get("mktcap") else "—"}</span></div></div></div>',unsafe_allow_html=True)
            prd=st.radio("Period",["1wk","1mo","3mo","6mo","1y"],horizontal=True,key="mk_prd")
            hist=fetch_history(lookup+".NS",prd)
            if not hist.empty:
                fig=go.Figure(); fig.add_trace(go.Candlestick(x=hist.index,open=hist["Open"],high=hist["High"],low=hist["Low"],close=hist["Close"],increasing_line_color="#00d09c",decreasing_line_color="#ff6b6b",increasing_fillcolor="rgba(0,208,156,0.2)",decreasing_fillcolor="rgba(255,107,107,0.2)"))
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",margin=dict(t=4,b=4,l=0,r=0),height=200,xaxis=dict(showgrid=False,color="#555",rangeslider_visible=False),yaxis=dict(showgrid=True,gridcolor="#1e1e1e",color="#555"))
                st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        else: st.error(f"'{lookup}' not found on NSE.")
    st.markdown("<div style='height:70px'></div>",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# AI
# ══════════════════════════════════════════════════════════════
elif tab==3:
    if not st.session_state.get("anthropic_key"):
        st.markdown('<div class="card" style="text-align:center;padding:28px;"><div style="font-size:36px;margin-bottom:10px;">🤖</div><div style="font-weight:700;font-size:15px;color:#f0f0f0;margin-bottom:6px;">AI Analyst</div><div style="font-size:12px;color:#666;line-height:1.6;">Enter your Anthropic API key in the ⚙️ sidebar to unlock AI-powered portfolio insights.</div></div>',unsafe_allow_html=True)
    elif not st.session_state.portfolio:
        st.info("Add holdings in the Portfolio tab first.")
    else:
        rows,invested,current,pnl,pnl_pct=portfolio_summary()
        st.markdown('<div class="sec-hdr">Quick Questions</div>',unsafe_allow_html=True)
        c1,c2=st.columns(2)
        for i,(icon,q) in enumerate([("🔄","Rebalance needed?"),("⚠️","Highest risk stock?"),("📈","Nifty outlook?"),("👀","Stocks to watch?"),("📊","Portfolio summary"),("💡","Sector to add?")]):
            col=c1 if i%2==0 else c2
            if col.button(f"{icon} {q}",use_container_width=True,key=f"qq_{i}"):
                with st.spinner("Thinking..."): st.session_state.ai_response=ask_claude(q,rows,invested,current,pnl,pnl_pct)
        st.markdown('<div class="sec-hdr">Ask Anything</div>',unsafe_allow_html=True)
        q=st.text_area("Q",placeholder="e.g. My SUNPHARMA is down 12% — cut or hold?",height=75,label_visibility="collapsed")
        if st.button("Ask AI analyst ↗",use_container_width=True):
            if q.strip():
                with st.spinner("Thinking..."): st.session_state.ai_response=ask_claude(q,rows,invested,current,pnl,pnl_pct)
        if st.session_state.ai_response:
            st.markdown('<div class="sec-hdr">Response</div>',unsafe_allow_html=True)
            st.markdown(f'<div class="ai-box">{st.session_state.ai_response}</div>',unsafe_allow_html=True)
    st.markdown("<div style='height:70px'></div>",unsafe_allow_html=True)
