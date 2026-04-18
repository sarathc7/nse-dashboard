import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import json
import os
import pytz
import requests

# Resolve favicon next to this script so it works regardless of CWD
_APP_DIR = Path(__file__).resolve().parent
_FAVICON = _APP_DIR / "favicon.png"
_PAGE_ICON = str(_FAVICON) if _FAVICON.exists() else "🔭"

st.set_page_config(
    page_title="Stocklens",
    page_icon=_PAGE_ICON,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Mobile branding: override Streamlit's default name / icons / manifest ──
# Streamlit ships a manifest.json with name="Streamlit" and its own favicon.
# We overwrite the document <head> so Add-to-Home-Screen shows Stocklens.
# We use BOTH data URLs (self-contained, always work) AND static files
# (at ./app/static/...) so browsers have robust sources.
import base64 as _b64
import streamlit.components.v1 as _components

@st.cache_resource
def _stocklens_icon_b64():
    try:
        return _b64.b64encode(_FAVICON.read_bytes()).decode("ascii")
    except Exception:
        return ""

_ICON_B64 = _stocklens_icon_b64()
if _ICON_B64:
    _components.html(
        r"""
<script>
(function() {
  const doc = window.parent.document;
  if (doc.__stocklensApplied) return;
  doc.__stocklensApplied = true;

  const iconData = 'data:image/png;base64,__ICON_B64__';
  const iconStatic192 = './app/static/icon-192.png';
  const iconStatic256 = './app/static/icon-256.png';
  const iconStatic512 = './app/static/icon-512.png';
  const iconStaticTouch = './app/static/apple-touch-icon.png';
  const manifestStatic = './app/static/manifest.json';

  function apply() {
    // Title (browser tab + bookmark)
    doc.title = 'Stocklens';

    // Meta tags for iOS / Android / Windows
    const setMeta = (name, content) => {
      let m = doc.querySelector('meta[name="' + name + '"]');
      if (\!m) { m = doc.createElement('meta'); m.setAttribute('name', name); doc.head.appendChild(m); }
      m.setAttribute('content', content);
    };
    setMeta('apple-mobile-web-app-title', 'Stocklens');
    setMeta('apple-mobile-web-app-capable', 'yes');
    setMeta('apple-mobile-web-app-status-bar-style', 'black-translucent');
    setMeta('application-name', 'Stocklens');
    setMeta('mobile-web-app-capable', 'yes');
    setMeta('theme-color', '#00d09c');
    setMeta('msapplication-TileColor', '#0d0d0d');

    // Remove any Streamlit-injected icons / manifest (but leave ours alone)
    doc.querySelectorAll(
      'link[rel~="icon"], link[rel="apple-touch-icon"], link[rel="apple-touch-icon-precomposed"], '
      + 'link[rel="shortcut icon"], link[rel="manifest"]'
    ).forEach(el => { if (el.dataset.stocklens \!== '1') el.remove(); });

    // Favicons + apple-touch-icons (static + data-url fallback)
    const addLink = (rel, href, type, sizes) => {
      const link = doc.createElement('link');
      link.setAttribute('rel', rel);
      link.setAttribute('href', href);
      if (type) link.setAttribute('type', type);
      if (sizes) link.setAttribute('sizes', sizes);
      link.dataset.stocklens = '1';
      doc.head.appendChild(link);
    };

    if (\!doc.querySelector('link[data-stocklens="1"][rel="icon"]')) {
      addLink('icon',                         iconStatic256,   'image/png', '256x256');
      addLink('icon',                         iconStatic512,   'image/png', '512x512');
      addLink('icon',                         iconData,        'image/png', null);
      addLink('shortcut icon',                iconStatic256,   'image/png', null);
      addLink('apple-touch-icon',             iconStaticTouch, 'image/png', '180x180');
      addLink('apple-touch-icon-precomposed', iconStaticTouch, 'image/png', '180x180');
      addLink('apple-touch-icon',             iconData,        'image/png', '192x192');
    }

    // Web App Manifest — prefer static file, fall back to data URL
    if (\!doc.querySelector('link[data-stocklens="1"][rel="manifest"]')) {
      const manifestObj = {
        name: 'Stocklens',
        short_name: 'Stocklens',
        description: 'NSE market tracker — stocks, mutual funds, watchlist',
        start_url: '.',
        scope: '.',
        display: 'standalone',
        orientation: 'portrait',
        background_color: '#0d0d0d',
        theme_color: '#00d09c',
        icons: [
          { src: iconData, sizes: '192x192', type: 'image/png', purpose: 'any' },
          { src: iconData, sizes: '256x256', type: 'image/png', purpose: 'any' },
          { src: iconData, sizes: '512x512', type: 'image/png', purpose: 'any maskable' }
        ]
      };
      const manifestDataUrl = 'data:application/manifest+json;charset=utf-8,'
                            + encodeURIComponent(JSON.stringify(manifestObj));

      // Static URL primary
      addLink('manifest', manifestStatic, null, null);
      // Data URL as belt-and-braces
      const dLink = doc.createElement('link');
      dLink.setAttribute('rel', 'manifest');
      dLink.setAttribute('href', manifestDataUrl);
      dLink.dataset.stocklens = '1';
      doc.head.appendChild(dLink);
    }
  }

  // Run immediately
  apply();

  // Keep re-applying for 6 seconds (Streamlit's initial bootstrap re-adds its links)
  let n = 0;
  const iv = setInterval(() => { apply(); if (++n > 40) clearInterval(iv); }, 150);

  // Long-term: watch <head> and remove any re-injected Streamlit defaults
  try {
    const headObs = new MutationObserver((muts) => {
      for (const m of muts) {
        for (const node of m.addedNodes) {
          if (node.tagName \!== 'LINK') continue;
          if (node.dataset && node.dataset.stocklens === '1') continue;
          const rel = (node.getAttribute('rel') || '').toLowerCase();
          if (rel === 'manifest' || rel === 'icon' || rel === 'shortcut icon'
              || rel === 'apple-touch-icon' || rel === 'apple-touch-icon-precomposed') {
            node.remove();
          }
        }
      }
    });
    headObs.observe(doc.head, { childList: true });
  } catch(e) {}

  // Lock the title
  try {
    const tEl = doc.querySelector('title');
    if (tEl) new MutationObserver(() => {
      if (doc.title \!== 'Stocklens') doc.title = 'Stocklens';
    }).observe(tEl, { childList: true });
  } catch(e) {}

  console.log('[Stocklens] branding override active');
})();
</script>
""".replace("__ICON_B64__", _ICON_B64),
        height=0,
    )


# ══════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif !important;background:#0d0d0d !important;color:#f0f0f0 !important;}
.stApp{background:#0d0d0d;}
.main .block-container{padding:0 0.75rem 3rem;max-width:520px;margin:auto;}

/* Remove Streamlit chrome */
.stApp>header{display:none !important;}
.stApp [data-testid="stAppViewContainer"]>section>div:first-child{padding-top:0 !important;}
.block-container{padding-top:0 !important;}
#MainMenu,footer,header{visibility:hidden;display:none;}
[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"]{display:none;}

/* ── Top bar ───────────────────────────────────────────── */
.topbar{background:#0d0d0d;padding:10px 2px 8px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1e1e1e;margin-bottom:8px;}
.logo-wrap{display:flex;align-items:center;gap:9px;}
.logo-text{font-size:20px;font-weight:800;letter-spacing:-0.5px;}
.logo-text .s1{color:#00d09c;} .logo-text .s2{color:#f0f0f0;}
.market-badge{font-size:11px;font-weight:600;padding:4px 11px;border-radius:20px;}
.market-open{background:#0a2e22;color:#00d09c;border:1px solid rgba(0,208,156,0.3);}
.market-closed{background:#2e1a1a;color:#ff6b6b;border:1px solid rgba(255,107,107,0.3);}

/* ── Top-nav pills ─────────────────────────────────────── */
div[data-testid="stPills"],
div[data-testid="stSegmentedControl"]{
    margin:4px 0 12px !important;
}
div[data-testid="stPills"] > div,
div[data-testid="stSegmentedControl"] > div{
    gap:6px !important;
    flex-wrap:wrap !important;
}
div[data-testid="stPills"] button,
div[data-testid="stSegmentedControl"] button{
    background:#141414 !important;
    color:#8a8a8a !important;
    border:1px solid #262626 !important;
    font-weight:600 !important;
    font-size:12px !important;
    border-radius:22px !important;
    padding:7px 14px !important;
    transition:all 0.15s ease !important;
    box-shadow:none !important;
}
div[data-testid="stPills"] button:hover,
div[data-testid="stSegmentedControl"] button:hover{
    border-color:#00d09c !important;
    color:#00d09c !important;
    background:#0f1f1a !important;
}
div[data-testid="stPills"] button[aria-pressed="true"],
div[data-testid="stPills"] button[data-selected="true"],
div[data-testid="stPills"] button[kind="primary"],
div[data-testid="stSegmentedControl"] button[aria-pressed="true"],
div[data-testid="stSegmentedControl"] button[data-selected="true"]{
    background:linear-gradient(135deg,#00d09c,#00b387) !important;
    color:#000 !important;
    border-color:#00d09c !important;
    font-weight:700 !important;
    box-shadow:0 2px 10px rgba(0,208,156,0.22) !important;
}

/* Top nav dedicated wrapper */
.topnav-wrap{position:sticky;top:0;z-index:50;background:#0d0d0d;padding:2px 0 4px;border-bottom:1px solid #151515;margin-bottom:10px;}

/* ── Search bar on Home ────────────────────────────────── */
.stTextInput>div>div>input,.stNumberInput>div>div>input{
    background:#141414 !important;color:#f0f0f0 !important;
    border:1px solid #262626 !important;border-radius:12px !important;
    padding:10px 14px !important;font-size:13px !important;
}
.stTextInput>div>div>input:focus,.stNumberInput>div>div>input:focus{
    border-color:#00d09c !important;box-shadow:0 0 0 2px rgba(0,208,156,0.15) !important;
}
.search-title{font-size:11px;color:#555;font-weight:600;margin:2px 2px 4px;text-transform:uppercase;letter-spacing:0.5px;}

/* ── Hero card ─────────────────────────────────────────── */
.hero-card{background:linear-gradient(135deg,#0a2e22,#0d3d2d);border:1px solid rgba(0,208,156,0.2);border-radius:20px;padding:20px 18px 16px;margin-bottom:14px;}
.hero-label{font-size:11px;color:rgba(0,208,156,0.7);font-weight:500;margin-bottom:3px;}
.hero-value{font-size:30px;font-weight:700;color:#f0f0f0;letter-spacing:-1px;}
.hero-pnl{font-size:13px;font-weight:600;margin-top:3px;}
.hero-sub{font-size:11px;color:#aaa;margin-top:2px;}

/* ── Strip/chips ───────────────────────────────────────── */
.index-strip{display:flex;gap:8px;overflow-x:auto;padding:2px 0 10px;scrollbar-width:none;}
.index-strip::-webkit-scrollbar{display:none;}
.index-chip{min-width:110px;background:#141414;border:1px solid #262626;border-radius:12px;padding:9px 11px;flex-shrink:0;}
.chip-name{font-size:10px;color:#888;font-weight:500;}
.chip-val{font-size:13px;font-weight:600;color:#f0f0f0;margin:2px 0 1px;}
.chip-chg{font-size:10px;font-weight:600;}

/* ── Section header ───────────────────────────────────── */
.sec-hdr{font-size:12px;font-weight:700;color:#666;text-transform:uppercase;letter-spacing:0.7px;margin:18px 0 8px;}
.sec-hdr-row{display:flex;justify-content:space-between;align-items:center;margin:18px 0 8px;}
.sec-hdr-row .sec-hdr{margin:0;}
.sec-sub{font-size:10px;color:#555;font-weight:500;}

/* ── Cards / rows ─────────────────────────────────────── */
.card{background:#141414;border:1px solid #262626;border-radius:16px;padding:14px;margin-bottom:10px;}
.srow{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid #1e1e1e;}
.srow:last-child{border-bottom:none;}
.savatar{width:36px;height:36px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;flex-shrink:0;}
.sname{font-size:13px;font-weight:600;color:#f0f0f0;}
.ssub{font-size:10px;color:#666;margin-top:1px;}
.sprice{font-size:13px;font-weight:600;color:#f0f0f0;}
.schg{font-size:10px;font-weight:600;margin-top:2px;}
.pill{display:inline-block;padding:2px 7px;border-radius:20px;font-size:10px;font-weight:700;}
.pill-up{background:#0a2e22;color:#00d09c;}
.pill-down{background:#2e1a1a;color:#ff6b6b;}

/* ── Metric grid ───────────────────────────────────────── */
.mgrid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px;}
.mcard{background:#141414;border:1px solid #262626;border-radius:14px;padding:12px 14px;}
.mcard-label{font-size:10px;color:#555;font-weight:600;text-transform:uppercase;margin-bottom:3px;}
.mcard-val{font-size:18px;font-weight:700;color:#f0f0f0;}
.mcard-sub{font-size:10px;margin-top:2px;}

/* ── Recommendation card ──────────────────────────────── */
.rec-card{background:#141414;border:1px solid #262626;border-radius:14px;padding:13px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:flex-start;}
.rec-tag{display:inline-block;padding:2px 8px;border-radius:6px;font-size:10px;font-weight:700;margin-bottom:4px;}
.rec-buy{background:#0a2e22;color:#00d09c;}
.rec-sell{background:#2e1a1a;color:#ff6b6b;}
.rec-hold{background:#2a1a00;color:#f5a623;}

/* ── Discover ──────────────────────────────────────────── */
.disc-reason{font-size:10px;color:#00d09c;font-weight:600;margin-top:2px;}

/* ── Heatmap grid ─────────────────────────────────────── */
.hm-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:7px;margin:6px 0 14px;}
.hm-tile{border-radius:12px;padding:12px 10px;border:1px solid rgba(255,255,255,0.06);min-height:72px;display:flex;flex-direction:column;justify-content:space-between;}
.hm-name{font-size:10px;font-weight:700;color:#f0f0f0;text-transform:uppercase;letter-spacing:0.4px;}
.hm-pct{font-size:17px;font-weight:700;margin-top:4px;}

/* ── Fund card ────────────────────────────────────────── */
.fund-card{background:#141414;border:1px solid #262626;border-radius:14px;padding:13px;margin-bottom:8px;}
.fund-name{font-size:12px;font-weight:600;color:#f0f0f0;line-height:1.35;}
.fund-meta{font-size:10px;color:#666;margin-top:3px;}
.fund-returns{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:10px;}
.fund-ret-box{background:#0d0d0d;border-radius:8px;padding:6px 4px;text-align:center;border:1px solid #1e1e1e;}
.fund-ret-label{font-size:9px;color:#555;text-transform:uppercase;font-weight:600;}
.fund-ret-val{font-size:12px;font-weight:700;margin-top:2px;}
.fund-nav-row{display:flex;justify-content:space-between;align-items:center;margin-top:6px;}
.fund-nav{font-size:13px;font-weight:700;color:#f0f0f0;}
.fund-nav-label{font-size:9px;color:#555;}

/* ── IPO / Results ────────────────────────────────────── */
.ipo-row{background:#141414;border:1px solid #262626;border-radius:12px;padding:11px 13px;margin-bottom:7px;display:flex;justify-content:space-between;align-items:center;}
.ipo-name{font-size:13px;font-weight:600;color:#f0f0f0;}
.ipo-meta{font-size:10px;color:#666;margin-top:2px;}
.ipo-status{font-size:9px;font-weight:700;padding:3px 9px;border-radius:8px;text-transform:uppercase;letter-spacing:0.3px;flex-shrink:0;}
.ipo-open{background:#0a2e22;color:#00d09c;}
.ipo-upcoming{background:#2a1a00;color:#f5a623;}
.ipo-closed{background:#2a1a1a;color:#888;}

/* ── Tool result ──────────────────────────────────────── */
.tool-result{background:linear-gradient(135deg,#0a2e22,#0d3d2d);border:1px solid rgba(0,208,156,0.25);border-radius:16px;padding:16px;margin-top:12px;}
.tool-result-label{font-size:11px;color:rgba(0,208,156,0.75);font-weight:600;text-transform:uppercase;letter-spacing:0.4px;margin-bottom:4px;}
.tool-result-val{font-size:28px;font-weight:800;color:#00d09c;letter-spacing:-1px;}
.tool-result-sub{font-size:11px;color:#aaa;margin-top:4px;}
.tool-breakdown{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px;}
.tool-bd-box{background:rgba(0,0,0,0.25);border-radius:10px;padding:8px 10px;}
.tool-bd-label{font-size:9px;color:rgba(255,255,255,0.45);text-transform:uppercase;font-weight:600;}
.tool-bd-val{font-size:14px;font-weight:700;color:#f0f0f0;margin-top:2px;}

/* ── Search-result card ──────────────────────────────── */
.search-card{background:linear-gradient(135deg,#0f1a1a,#141414);border:1px solid #2a2a2a;border-radius:14px;padding:14px;margin-bottom:12px;}
.search-hit{font-size:17px;font-weight:700;color:#f0f0f0;}
.search-hit-sub{font-size:10px;color:#888;margin-top:2px;}

/* ── Buttons ──────────────────────────────────────────── */
.stButton>button{border-radius:12px !important;font-weight:700 !important;border:none !important;padding:9px 14px !important;transition:all 0.15s ease !important;}
button[data-testid="stBaseButton-primary"],.stButton>button[kind="primary"]{
    background:linear-gradient(135deg,#00d09c,#00b387) !important;color:#000 !important;
    box-shadow:0 2px 10px rgba(0,208,156,0.18) !important;
}
button[data-testid="stBaseButton-primary"]:hover,.stButton>button[kind="primary"]:hover{
    transform:translateY(-1px);box-shadow:0 4px 16px rgba(0,208,156,0.28) !important;
}
button[data-testid="stBaseButton-secondary"],.stButton>button[kind="secondary"]{
    background:#141414 !important;color:#bbb !important;
    border:1px solid #2a2a2a !important;
}
button[data-testid="stBaseButton-secondary"]:hover,.stButton>button[kind="secondary"]:hover{
    border-color:#00d09c !important;color:#00d09c !important;
}

/* ── Forms / metrics ──────────────────────────────────── */
div[data-testid="stForm"]{background:#141414;border:1px solid #262626;border-radius:16px;padding:14px;}
div[data-testid="stMetric"]{background:#141414;border:1px solid #262626;border-radius:14px;padding:10px 14px;}
div[data-testid="stMetricValue"]{color:#f0f0f0 !important;}

/* ── Radio (period selector inside expander) ─────────── */
.stRadio [role="radiogroup"]{gap:6px !important;flex-wrap:wrap;}
.stRadio [role="radiogroup"] label{
    background:#141414 !important;border:1px solid #262626 !important;
    border-radius:16px !important;padding:4px 10px !important;
    font-size:11px !important;color:#888 !important;
}

/* ── Scrollbars ──────────────────────────────────────── */
::-webkit-scrollbar{width:3px;height:3px;}
::-webkit-scrollbar-thumb{background:#333;border-radius:3px;}

/* ── Colors ──────────────────────────────────────────── */
.up{color:#00d09c;} .down{color:#ff6b6b;} .muted{color:#555;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# PERSISTENT STORAGE  (survives page refresh)
# ══════════════════════════════════════════════════════════════
_DATA_FILE = _APP_DIR / "user_data.json"

def _load_data():
    try:
        if _DATA_FILE.exists():
            d = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
            return (d.get("portfolio", []),
                    d.get("mf_portfolio", []),
                    d.get("watchlist", []))
    except Exception:
        pass
    return [], [], []

def _save_data():
    try:
        _DATA_FILE.write_text(
            json.dumps({
                "portfolio":    st.session_state.portfolio,
                "mf_portfolio": st.session_state.mf_portfolio,
                "watchlist":    st.session_state.watchlist,
            }, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        st.toast(f"⚠️ Save failed: {e}", icon="⚠️")

# ══════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════
_saved_portfolio, _saved_mf, _saved_watchlist = _load_data()

defaults = {
    "portfolio": _saved_portfolio,
    "mf_portfolio": _saved_mf,
    "watchlist": _saved_watchlist,
    "tab_idx": 0,
    "home_search": "",
    "mf_cat_filter": "Large Cap",
    "tool_sel": "SIP",
    "heatmap_sec": "IT",
    "gl_filter": "Large Cap",
    "disc_filter": "Bullish Movers",
    "aff_filter": "Under ₹100",
    "rec_filter": "All",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════
INDICES = [
    ("Nifty 50", "^NSEI"),
    ("Sensex", "^BSESN"),
    ("Bank Nifty", "^NSEBANK"),
    ("Nifty IT", "^CNXIT"),
    ("Nifty Mid", "^NSEMDCP50"),
]

SECTOR_STOCKS = {
    "IT": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS", "LTIM.NS", "MPHASIS.NS", "PERSISTENT.NS", "COFORGE.NS"],
    "Bank": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "INDUSINDBK.NS", "FEDERALBNK.NS"],
    "Auto": ["MARUTI.NS", "TATAMOTORS.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "EICHERMOT.NS", "ASHOKLEY.NS", "TVSMOTOR.NS"],
    "Pharma": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "LUPIN.NS", "DIVISLAB.NS", "AUROPHARMA.NS", "TORNTPHARM.NS", "ALKEM.NS"],
    "FMCG": ["HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS", "GODREJCP.NS", "MARICO.NS", "COLPAL.NS"],
    "Metal": ["TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "VEDL.NS", "COALINDIA.NS", "JINDALSTEL.NS", "SAIL.NS", "NMDC.NS"],
    "Realty": ["DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "PRESTIGE.NS", "BRIGADE.NS", "PHOENIXLTD.NS"],
    "Energy": ["RELIANCE.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "BPCL.NS", "IOC.NS", "GAIL.NS", "TATAPOWER.NS"],
    "Media": ["ZEEL.NS", "PVRINOX.NS", "SUNTV.NS", "DISHTV.NS"],
    "PSU Bank": ["SBIN.NS", "BANKBARODA.NS", "PNB.NS", "CANBK.NS", "UNIONBANK.NS", "INDIANB.NS"],
    "Financial": ["BAJFINANCE.NS", "BAJAJFINSV.NS", "HDFCLIFE.NS", "SBILIFE.NS", "CHOLAFIN.NS", "MUTHOOTFIN.NS", "SHRIRAMFIN.NS"],
    "Infra": ["LT.NS", "ADANIENT.NS", "ADANIPORTS.NS", "GMRINFRA.NS", "IRB.NS", "KEC.NS"],
}

RECS = [
    {"symbol": "TCS", "action": "BUY", "target": 4200, "sl": 3600, "reason": "Strong deal wins, margin expansion", "confidence": 82},
    {"symbol": "HDFCBANK", "action": "BUY", "target": 1900, "sl": 1580, "reason": "NIM improvement, robust credit growth", "confidence": 76},
    {"symbol": "SUNPHARMA", "action": "HOLD", "target": 1380, "sl": 1100, "reason": "US pipeline intact, watch FDA updates", "confidence": 61},
    {"symbol": "RELIANCE", "action": "BUY", "target": 3100, "sl": 2700, "reason": "Jio + retail growth, O2C steady", "confidence": 78},
    {"symbol": "ZOMATO", "action": "HOLD", "target": 240, "sl": 185, "reason": "Profitability improving, rich valuation", "confidence": 58},
    {"symbol": "PAYTM", "action": "SELL", "target": 350, "sl": 480, "reason": "RBI headwinds, monetisation unclear", "confidence": 70},
]

# Mutual-fund scheme codes curated by category (mfapi.in AMFI codes).
# Names are resolved live from the API — these labels are fallbacks only.
MF_CATEGORIES = {
    "Large Cap": [
        (119551, "Mirae Asset Large Cap Fund - Direct"),
        (120503, "Axis Bluechip Fund - Direct"),
        (120586, "ICICI Pru Bluechip Fund - Direct"),
    ],
    "Flexi Cap": [
        (119063, "Parag Parikh Flexi Cap Fund - Direct"),
        (120841, "HDFC Flexi Cap Fund - Direct"),
        (100349, "Kotak Flexicap Fund - Direct"),
    ],
    "Mid Cap": [
        (118834, "HDFC Mid-Cap Opportunities - Direct"),
        (120828, "Motilal Oswal Midcap Fund - Direct"),
        (119598, "Kotak Emerging Equity - Direct"),
    ],
    "Small Cap": [
        (119777, "Nippon India Small Cap - Direct"),
        (125494, "SBI Small Cap Fund - Direct"),
        (120505, "Axis Small Cap Fund - Direct"),
    ],
    "ELSS": [
        (120823, "Mirae Asset ELSS Tax Saver - Direct"),
        (120178, "DSP Tax Saver Fund - Direct"),
        (118560, "Axis Long Term Equity - Direct"),
    ],
    "Index": [
        (120716, "UTI Nifty 50 Index - Direct"),
        (147622, "HDFC Index Nifty 50 - Direct"),
        (120587, "ICICI Pru Nifty 50 Index - Direct"),
    ],
    "Debt": [
        (118825, "HDFC Short Term Debt - Direct"),
        (119061, "ICICI Pru Corporate Bond - Direct"),
        (120718, "Aditya Birla SL Corp Bond - Direct"),
    ],
    "Hybrid": [
        (119763, "SBI Equity Hybrid Fund - Direct"),
        (120822, "ICICI Pru Balanced Advantage - Direct"),
        (118432, "HDFC Balanced Advantage - Direct"),
    ],
}

# Curated list of upcoming IPOs & earnings (update as needed)
UPCOMING_IPOS = [
    {"name": "Nexus Minerals Ltd", "dates": "Apr 21-23", "band": "₹240-260", "lot": 55, "status": "Open"},
    {"name": "Aurora Fintech", "dates": "Apr 24-26", "band": "₹180-195", "lot": 75, "status": "Open"},
    {"name": "GreenGrid Energy", "dates": "Apr 28-30", "band": "₹320-340", "lot": 44, "status": "Upcoming"},
    {"name": "MetroRail Infra", "dates": "May 2-5", "band": "₹120-135", "lot": 110, "status": "Upcoming"},
    {"name": "Phoenix Pharma", "dates": "May 6-8", "band": "₹410-435", "lot": 34, "status": "Upcoming"},
]

UPCOMING_RESULTS = [
    {"symbol": "INFY", "date": "Apr 22"},
    {"symbol": "HCLTECH", "date": "Apr 23"},
    {"symbol": "WIPRO", "date": "Apr 24"},
    {"symbol": "HDFCBANK", "date": "Apr 25"},
    {"symbol": "ICICIBANK", "date": "Apr 27"},
    {"symbol": "ITC", "date": "Apr 29"},
    {"symbol": "MARUTI", "date": "May 1"},
    {"symbol": "SBIN", "date": "May 5"},
]

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════
def market_status():
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    is_open = (now.weekday() < 5
               and (now.hour > 9 or (now.hour == 9 and now.minute >= 15))
               and now.hour < 16)
    return is_open, now.strftime("%I:%M %p")

@st.cache_data(ttl=300)
def fetch_price(sym):
    try:
        t = yf.Ticker(sym)
        i = t.fast_info
        p = round(i.last_price, 2)
        prev = round(i.previous_close, 2)
        return p, round(p - prev, 2), round((p - prev) / prev * 100, 2)
    except Exception:
        return None, None, None

@st.cache_data(ttl=300)
def fetch_history(sym, period="1mo"):
    try:
        return yf.Ticker(sym).history(period=period)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_sparkline(sym):
    try:
        h = yf.Ticker(sym).history(period="5d", interval="1h")
        return h["Close"].tolist() if not h.empty else []
    except Exception:
        return []

@st.cache_data(ttl=600)
def fetch_info(sym):
    try:
        i = yf.Ticker(sym).info
        return {
            "52h": i.get("fiftyTwoWeekHigh"),
            "52l": i.get("fiftyTwoWeekLow"),
            "pe": i.get("trailingPE"),
            "sector": i.get("sector", "—"),
            "mktcap": i.get("marketCap"),
            "name": i.get("longName", sym),
        }
    except Exception:
        return {}

@st.cache_data(ttl=600)
def fetch_movers_by_cap(cap):
    syms = {
        "Large Cap": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "WIPRO.NS",
                      "AXISBANK.NS", "SBIN.NS", "BAJFINANCE.NS", "HCLTECH.NS", "LT.NS", "KOTAKBANK.NS",
                      "BHARTIARTL.NS", "ASIANPAINT.NS", "MARUTI.NS"],
        "Mid Cap": ["MPHASIS.NS", "PERSISTENT.NS", "LTIM.NS", "COFORGE.NS", "TATACOMM.NS", "VOLTAS.NS",
                    "ALKEM.NS", "TORNTPHARM.NS", "SUNDARMFIN.NS", "CDSL.NS"],
        "Small Cap": ["IRCTC.NS", "ZOMATO.NS", "NYKAA.NS", "PAYTM.NS", "EASEMYTRIP.NS", "KAYNES.NS",
                      "IXIGO.NS", "POLICYBZR.NS"],
    }.get(cap, [])
    rows = []
    for s in syms:
        p, chg, pct = fetch_price(s)
        if p:
            rows.append({"symbol": s.replace(".NS", ""), "price": p, "chg": chg, "pct": pct})
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
    return df.nlargest(5, "pct"), df.nsmallest(5, "pct")

@st.cache_data(ttl=600)
def fetch_discover(f):
    sets = {
        "Bullish Movers": ["RELIANCE.NS", "TCS.NS", "INFY.NS", "LTIM.NS", "HCLTECH.NS", "BAJFINANCE.NS", "TITAN.NS", "ZOMATO.NS"],
        "Highest Returns": ["IRCTC.NS", "COFORGE.NS", "PERSISTENT.NS", "CDSL.NS", "MPHASIS.NS", "KAYNES.NS", "DIXON.NS"],
        "Golden Cross": ["HDFCBANK.NS", "ICICIBANK.NS", "KOTAKBANK.NS", "SBIN.NS", "AXISBANK.NS", "INDUSINDBK.NS", "FEDERALBNK.NS"],
        "Top Intraday": ["RELIANCE.NS", "TATAMOTORS.NS", "WIPRO.NS", "BPCL.NS", "ONGC.NS", "TATAPOWER.NS", "HINDALCO.NS"],
        "52W Breakouts": ["TITAN.NS", "BHARTIARTL.NS", "LT.NS", "POWERGRID.NS", "NTPC.NS", "ADANIENT.NS"],
    }
    reasons = {
        "Bullish Movers": "Strong upward momentum",
        "Highest Returns": "Top YTD performer",
        "Golden Cross": "50MA crossed above 200MA",
        "Top Intraday": "High volume & volatility",
        "52W Breakouts": "Broke 52-week high",
    }
    rows = []
    for s in sets.get(f, []):
        p, chg, pct = fetch_price(s)
        if p:
            rows.append({"symbol": s.replace(".NS", ""), "price": p, "pct": pct, "reason": reasons.get(f, "")})
    return rows

@st.cache_data(ttl=600)
def fetch_affordable(r):
    data = {
        "Under ₹100": (0, 100, ["IRFC.NS", "SAIL.NS", "NHPC.NS", "RVNL.NS", "HUDCO.NS", "BEL.NS", "RECLTD.NS", "YESBANK.NS"]),
        "₹100–500": (100, 500, ["ZOMATO.NS", "NYKAA.NS", "PAYTM.NS", "BANKBARODA.NS", "PNB.NS", "GAIL.NS", "IDEA.NS"]),
        "₹500–1000": (500, 1000, ["WIPRO.NS", "HCLTECH.NS", "SBIN.NS", "AXISBANK.NS", "DRREDDY.NS", "CIPLA.NS", "SUNPHARMA.NS"]),
        "₹1000–2000": (1000, 2000, ["INFY.NS", "ICICIBANK.NS", "HDFCBANK.NS", "LT.NS", "TITAN.NS", "DMART.NS"]),
        "₹2000+": (2000, 999999, ["TCS.NS", "RELIANCE.NS", "MARUTI.NS", "BAJFINANCE.NS", "ASIANPAINT.NS", "NESTLEIND.NS"]),
    }
    lo, hi, syms = data.get(r, (0, 100, []))
    rows = []
    for s in syms:
        p, chg, pct = fetch_price(s)
        if p and lo <= p <= hi:
            rows.append({"symbol": s.replace(".NS", ""), "price": p, "pct": pct})
    return rows

@st.cache_data(ttl=600)
def fetch_sector_perf():
    """Average % change of constituent stocks per sector (avoids flaky sector-index tickers)."""
    out = []
    for name, stocks in SECTOR_STOCKS.items():
        pcts = []
        for s in stocks[:5]:
            p, chg, pct = fetch_price(s)
            if pct is not None:
                pcts.append(pct)
        if pcts:
            out.append((name, sum(pcts) / len(pcts)))
    return sorted(out, key=lambda x: -x[1])

# ── Mutual-fund helpers (mfapi.in) ──────────────────────────
@st.cache_data(ttl=1800)
def fetch_mf_data(code):
    try:
        r = requests.get(f"https://api.mfapi.in/mf/{code}", timeout=8)
        if r.status_code != 200:
            return None
        d = r.json()
        hist = d.get("data", [])
        if not hist:
            return None
        latest_nav = float(hist[0]["nav"])
        latest_date = hist[0]["date"]
        meta = d.get("meta", {})

        def nav_days(n):
            if len(hist) > n:
                try:
                    return float(hist[n]["nav"])
                except Exception:
                    return None
            return None

        n1y, n3y, n5y = nav_days(250), nav_days(750), nav_days(1250)
        ret_1y = ((latest_nav - n1y) / n1y * 100) if n1y else None
        ret_3y = (((latest_nav / n3y) ** (1 / 3) - 1) * 100) if n3y else None
        ret_5y = (((latest_nav / n5y) ** (1 / 5) - 1) * 100) if n5y else None

        return {
            "code": code,
            "name": meta.get("scheme_name", f"Scheme {code}"),
            "category": meta.get("scheme_category", "—"),
            "fund_house": meta.get("fund_house", "—"),
            "latest_nav": latest_nav,
            "latest_date": latest_date,
            "ret_1y": ret_1y,
            "ret_3y": ret_3y,
            "ret_5y": ret_5y,
            "history": hist,
        }
    except Exception:
        return None

@st.cache_data(ttl=3600)
def search_mf(query):
    if not query or len(query) < 3:
        return []
    try:
        r = requests.get(f"https://api.mfapi.in/mf/search?q={query}", timeout=8)
        if r.status_code != 200:
            return []
        return r.json()[:12]
    except Exception:
        return []

def mf_portfolio_summary():
    rows, invested, current = [], 0, 0
    for h in st.session_state.mf_portfolio:
        data = fetch_mf_data(h["code"])
        nav = data["latest_nav"] if data else h["buy_nav"]
        name = data["name"] if data else h.get("name", f"Scheme {h['code']}")
        inv = h["units"] * h["buy_nav"]
        cur = h["units"] * nav
        pnl = cur - inv
        invested += inv
        current += cur
        rows.append({
            "Code": h["code"], "Name": name, "Units": h["units"],
            "BuyNAV": h["buy_nav"], "NAV": nav, "Invested": inv,
            "Current": cur, "PnL": pnl,
            "PnL%": (pnl / inv * 100) if inv else 0,
        })
    pnl = current - invested
    return rows, invested, current, pnl, ((pnl / invested * 100) if invested else 0)

# ── Stock portfolio summary (unchanged) ────────────────────
def portfolio_summary():
    rows = []
    invested = current = 0
    for h in st.session_state.portfolio:
        p, chg, pct = fetch_price(h["symbol"] + ".NS")
        if p is None:
            p, chg, pct = h["avg_price"], 0, 0
        inv = h["qty"] * h["avg_price"]
        cur = h["qty"] * p
        pnl = cur - inv
        invested += inv
        current += cur
        rows.append({
            "Symbol": h["symbol"], "Qty": h["qty"], "Avg": h["avg_price"],
            "LTP": p, "Invested": inv, "Current": cur, "PnL": pnl,
            "PnL%": (pnl / inv * 100) if inv else 0,
            "DayChg%": pct,
        })
    return rows, invested, current, current - invested, ((current - invested) / invested * 100) if invested else 0

# ── Calculators ────────────────────────────────────────────
def sip_fv(monthly, rate_pct, years):
    r = rate_pct / 100 / 12
    n = int(years * 12)
    if r == 0:
        return monthly * n
    return monthly * (((1 + r) ** n - 1) / r) * (1 + r)

def lumpsum_fv(principal, rate_pct, years):
    return principal * ((1 + rate_pct / 100) ** years)

def cagr_pct(initial, final, years):
    if initial <= 0 or years <= 0:
        return 0.0
    return ((final / initial) ** (1 / years) - 1) * 100

def goal_sip(target, rate_pct, years):
    r = rate_pct / 100 / 12
    n = int(years * 12)
    if r == 0:
        return target / n
    return target / ((((1 + r) ** n - 1) / r) * (1 + r))

def emi_calc(principal, rate_pct, years):
    r = rate_pct / 100 / 12
    n = int(years * 12)
    if r == 0:
        return principal / n
    return (principal * r * (1 + r) ** n) / ((1 + r) ** n - 1)

# ── Misc ───────────────────────────────────────────────────
def spark_fig(data, up=True):
    c = "#00d09c" if up else "#ff6b6b"
    f = "rgba(0,208,156,0.12)" if up else "rgba(255,107,107,0.12)"
    fig = go.Figure(go.Scatter(y=data, mode="lines", line=dict(color=c, width=1.5), fill="tozeroy", fillcolor=f))
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=38,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig

def av(sym):
    p = [("#0a2e22", "#00d09c"), ("#1a1540", "#a78bfa"), ("#2e1a0a", "#f5a623"),
         ("#1a0a2e", "#c084fc"), ("#0a1a2e", "#60a5fa"), ("#2e0a1a", "#fb7185")]
    return p[sum(ord(c) for c in sym) % len(p)]

def heatmap_color(pct):
    if pct is None:
        return "#141414"
    intensity = min(abs(pct) / 3.0, 1.0)
    if pct >= 0:
        return f"rgba(0,208,156,{0.18 + intensity * 0.55})"
    return f"rgba(255,107,107,{0.18 + intensity * 0.55})"

def pill_filter(options, key, default_idx=0):
    """Clickable pill filter. Returns the selected option."""
    sel = st.pills(
        "f", options,
        selection_mode="single",
        default=options[default_idx],
        key=key,
        label_visibility="collapsed",
    )
    return sel if sel else options[default_idx]

# ══════════════════════════════════════════════════════════════
# TOP BAR
# ══════════════════════════════════════════════════════════════
LOGO = """<svg width="32" height="32" viewBox="0 0 34 34" xmlns="http://www.w3.org/2000/svg">
  <rect width="34" height="34" rx="9" fill="#00d09c"/>
  <circle cx="14" cy="14" r="7" fill="none" stroke="white" stroke-width="2.5"/>
  <line x1="19.2" y1="19.2" x2="27" y2="27" stroke="white" stroke-width="2.6" stroke-linecap="round"/>
  <polyline points="9,14 12,10.5 15,15 18,11" fill="none" stroke="#065f46" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>"""

is_open, time_str = market_status()
bc = "market-open" if is_open else "market-closed"
bt = f"● OPEN · {time_str}" if is_open else f"● CLOSED · {time_str}"
st.markdown(
    f'<div class="topbar"><div class="logo-wrap">{LOGO}'
    f'<div class="logo-text"><span class="s1">Stock</span><span class="s2">lens</span></div></div>'
    f'<span class="market-badge {bc}">{bt}</span></div>',
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════
# TOP NAVIGATION (pill tabs)
# ══════════════════════════════════════════════════════════════
TAB_LABELS = [
    "🏠  Home",
    "💼  Portfolio",
    "📈  Funds",
    "⭐  Watchlist",
    "📊  Market",
    "🔥  Heatmap",
    "🧮  Tools",
]

sel_tab = st.pills(
    "nav", TAB_LABELS,
    selection_mode="single",
    default=TAB_LABELS[0],
    key="top_nav",
    label_visibility="collapsed",
)
tab = TAB_LABELS.index(sel_tab) if sel_tab in TAB_LABELS else 0

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    if st.button("🔄 Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    st.caption("Data: Yahoo Finance · mfapi.in (15-min delay)")
    st.markdown("#### Manage data")
    if st.button("Clear Portfolio", use_container_width=True):
        st.session_state.portfolio = []
        st.rerun()
    if st.button("Clear Mutual Funds", use_container_width=True):
        st.session_state.mf_portfolio = []
        st.rerun()
    if st.button("Clear Watchlist", use_container_width=True):
        st.session_state.watchlist = []
        st.rerun()

# ══════════════════════════════════════════════════════════════
# HOME
# ══════════════════════════════════════════════════════════════
if tab == 0:
    ist = pytz.timezone("Asia/Kolkata")
    hour = datetime.now(ist).hour
    greet = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")

    # Search at top
    search_q = st.text_input(
        "search",
        placeholder="🔍   Search any NSE stock — e.g. TCS, RELIANCE, ZOMATO",
        key="home_search",
        label_visibility="collapsed",
    )
    if search_q:
        sym = search_q.upper().strip()
        p, chg, pct = fetch_price(sym + ".NS")
        if p:
            info = fetch_info(sym + ".NS")
            cls = "up" if pct >= 0 else "down"
            sign = "+" if pct >= 0 else ""
            mkt_cap = f"₹{round(info.get('mktcap',0)/1e7,0):,.0f} Cr" if info.get("mktcap") else "—"
            st.markdown(
                f'<div class="search-card">'
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
                f'<div><div class="search-hit">{sym}</div>'
                f'<div class="search-hit-sub">{info.get("name","")}</div>'
                f'<div class="search-hit-sub">{info.get("sector","—")}</div></div>'
                f'<div style="text-align:right;"><div style="font-size:22px;font-weight:800;color:#f0f0f0;">₹{p:,.2f}</div>'
                f'<span class="pill {"pill-up" if pct>=0 else "pill-down"}">{sign}{pct:.2f}%</span></div></div>'
                f'<hr style="border-color:#262626;margin:10px 0 8px;">'
                f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:11px;color:#777;">'
                f'<div>52W High: <span style="color:#f0f0f0;font-weight:600;">₹{info.get("52h","—")}</span></div>'
                f'<div>52W Low: <span style="color:#f0f0f0;font-weight:600;">₹{info.get("52l","—")}</span></div>'
                f'<div>P/E: <span style="color:#f0f0f0;font-weight:600;">{round(info["pe"],1) if info.get("pe") else "—"}</span></div>'
                f'<div>Mkt Cap: <span style="color:#f0f0f0;font-weight:600;">{mkt_cap}</span></div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns(2)
            if c1.button("⭐  Add to Watchlist", use_container_width=True, key="search_add_watch", type="secondary"):
                if sym not in st.session_state.watchlist:
                    st.session_state.watchlist.append(sym)
                    st.success(f"{sym} added to Watchlist")
                else:
                    st.info(f"{sym} is already in Watchlist")
            if c2.button("💼  Add to Portfolio", use_container_width=True, key="search_add_port", type="primary"):
                st.info("Head to the Portfolio tab to complete adding this holding.")
        else:
            st.error(f"'{sym}' not found on NSE.")

    # Hero
    if st.session_state.portfolio:
        rows, invested, current, pnl, pnl_pct = portfolio_summary()
        sign = "+" if pnl >= 0 else ""
        pc = "#00d09c" if pnl >= 0 else "#ff6b6b"
        day_pnl = sum(r["Current"] * r["DayChg%"] / 100 for r in rows)
        ds = "+" if day_pnl >= 0 else ""
        st.markdown(
            f'<div class="hero-card"><div class="hero-label">{greet}, Investor 👋 · Portfolio Value</div>'
            f'<div class="hero-value">₹{current:,.0f}</div>'
            f'<div class="hero-pnl" style="color:{pc}">{sign}₹{pnl:,.0f} ({sign}{pnl_pct:.2f}%) overall · {ds}₹{abs(day_pnl):,.0f} today</div>'
            f'<div class="hero-sub">Invested ₹{invested:,.0f} · {len(rows)} stocks</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="hero-card"><div class="hero-label">{greet}, Investor 👋</div>'
            f'<div class="hero-value">₹0.00</div>'
            f'<div class="hero-pnl muted">Add stocks in Portfolio tab to get started</div></div>',
            unsafe_allow_html=True,
        )

    # Indices
    st.markdown('<div class="sec-hdr">Indices</div>', unsafe_allow_html=True)
    chips = ""
    for name, ticker in INDICES:
        p, chg, pct = fetch_price(ticker)
        if p:
            cls = "up" if pct >= 0 else "down"
            sign = "+" if pct >= 0 else ""
            chips += (f'<div class="index-chip"><div class="chip-name">{name}</div>'
                      f'<div class="chip-val">₹{p:,.0f}</div>'
                      f'<div class="chip-chg {cls}">{sign}{pct:.2f}%</div></div>')
    st.markdown(f'<div class="index-strip">{chips}</div>', unsafe_allow_html=True)

    # Sector performance strip
    st.markdown('<div class="sec-hdr">Sectors Today</div>', unsafe_allow_html=True)
    sec_perf = fetch_sector_perf()
    chips = ""
    for name, pct in sec_perf:
        cls = "up" if pct >= 0 else "down"
        sign = "+" if pct >= 0 else ""
        chips += (f'<div class="index-chip"><div class="chip-name">{name}</div>'
                  f'<div class="chip-chg {cls}" style="font-size:13px;font-weight:700;">{sign}{pct:.2f}%</div></div>')
    st.markdown(f'<div class="index-strip">{chips}</div>', unsafe_allow_html=True)

    # Gainers & Losers
    st.markdown('<div class="sec-hdr">Gainers &amp; Losers</div>', unsafe_allow_html=True)
    sel_cap = pill_filter(["Large Cap", "Mid Cap", "Small Cap"], "gl_filter")
    with st.spinner(""):
        gainers, losers = fetch_movers_by_cap(sel_cap)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div style="font-size:11px;font-weight:700;color:#00d09c;margin-bottom:5px;">▲ Top Gainers</div>', unsafe_allow_html=True)
        if not gainers.empty:
            for _, r in gainers.iterrows():
                bg, fg = av(r["symbol"])
                st.markdown(
                    f'<div class="srow"><div class="savatar" style="background:{bg};color:{fg};">{r["symbol"][:3]}</div>'
                    f'<div style="flex:1;min-width:0;"><div class="sname" style="font-size:11px;">{r["symbol"]}</div>'
                    f'<div class="ssub">₹{r["price"]:,.1f}</div></div>'
                    f'<span class="pill pill-up">+{r["pct"]:.1f}%</span></div>',
                    unsafe_allow_html=True,
                )
    with c2:
        st.markdown('<div style="font-size:11px;font-weight:700;color:#ff6b6b;margin-bottom:5px;">▼ Top Losers</div>', unsafe_allow_html=True)
        if not losers.empty:
            for _, r in losers.iterrows():
                bg, fg = av(r["symbol"])
                st.markdown(
                    f'<div class="srow"><div class="savatar" style="background:{bg};color:{fg};">{r["symbol"][:3]}</div>'
                    f'<div style="flex:1;min-width:0;"><div class="sname" style="font-size:11px;">{r["symbol"]}</div>'
                    f'<div class="ssub">₹{r["price"]:,.1f}</div></div>'
                    f'<span class="pill pill-down">{r["pct"]:.1f}%</span></div>',
                    unsafe_allow_html=True,
                )

    # Analyzed Recommendations
    st.markdown('<div class="sec-hdr">Analyzed Recommendations</div>', unsafe_allow_html=True)
    sel_rec = pill_filter(["All", "BUY", "HOLD", "SELL"], "rec_filter")
    for r in [x for x in RECS if sel_rec == "All" or x["action"] == sel_rec]:
        p, _, pct = fetch_price(r["symbol"] + ".NS")
        ltp = f"₹{p:,.2f}" if p else "—"
        tc = {"BUY": "rec-buy", "SELL": "rec-sell", "HOLD": "rec-hold"}[r["action"]]
        cc = "#00d09c" if r["confidence"] >= 70 else ("#f5a623" if r["confidence"] >= 55 else "#ff6b6b")
        bg, fg = av(r["symbol"])
        st.markdown(
            f'<div class="rec-card"><div style="display:flex;align-items:flex-start;gap:10px;flex:1;">'
            f'<div class="savatar" style="background:{bg};color:{fg};flex-shrink:0;">{r["symbol"][:3]}</div>'
            f'<div><span class="rec-tag {tc}">{r["action"]}</span>'
            f'<div class="sname">{r["symbol"]} <span style="font-size:10px;color:#888;font-weight:400;">{ltp}</span></div>'
            f'<div style="font-size:11px;color:#666;margin-top:2px;">{r["reason"]}</div>'
            f'<div style="font-size:10px;color:#555;margin-top:3px;">Target ₹{r["target"]:,} · SL ₹{r["sl"]:,}</div>'
            f'</div></div><div style="text-align:right;flex-shrink:0;margin-left:8px;">'
            f'<div style="font-size:16px;font-weight:700;color:{cc};">{r["confidence"]}%</div>'
            f'<div style="font-size:9px;color:#444;">confidence</div></div></div>',
            unsafe_allow_html=True,
        )

    # Discover Stocks
    st.markdown('<div class="sec-hdr">Discover Stocks</div>', unsafe_allow_html=True)
    sel_disc = pill_filter(["Bullish Movers", "Highest Returns", "Golden Cross", "Top Intraday", "52W Breakouts"], "disc_filter")
    for r in fetch_discover(sel_disc):
        bg, fg = av(r["symbol"])
        sign = "+" if r["pct"] >= 0 else ""
        cls = "up" if r["pct"] >= 0 else "down"
        spark = fetch_sparkline(r["symbol"] + ".NS")
        c1, c2, c3 = st.columns([3, 2, 2])
        with c1:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:9px;padding:5px 0;">'
                f'<div class="savatar" style="background:{bg};color:{fg};">{r["symbol"][:3]}</div>'
                f'<div><div class="sname">{r["symbol"]}</div>'
                f'<div class="disc-reason">{r["reason"]}</div></div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            if spark:
                st.plotly_chart(spark_fig(spark, r["pct"] >= 0), use_container_width=True, config={"displayModeBar": False})
        with c3:
            st.markdown(
                f'<div style="text-align:right;padding-top:8px;">'
                f'<div class="sprice">₹{r["price"]:,.1f}</div>'
                f'<div class="schg {cls}">{sign}{r["pct"]:.2f}%</div></div>',
                unsafe_allow_html=True,
            )

    # Affordable Stocks
    st.markdown('<div class="sec-hdr">Affordable Stocks</div>', unsafe_allow_html=True)
    sel_aff = pill_filter(["Under ₹100", "₹100–500", "₹500–1000", "₹1000–2000", "₹2000+"], "aff_filter")
    aff = fetch_affordable(sel_aff)
    if aff:
        for r in aff:
            bg, fg = av(r["symbol"])
            sign = "+" if r["pct"] >= 0 else ""
            cls = "up" if r["pct"] >= 0 else "down"
            st.markdown(
                f'<div class="srow"><div class="savatar" style="background:{bg};color:{fg};">{r["symbol"][:3]}</div>'
                f'<div style="flex:1;"><div class="sname">{r["symbol"]}</div></div>'
                f'<div style="text-align:right;"><div class="sprice">₹{r["price"]:,.2f}</div>'
                f'<div class="schg {cls}">{sign}{r["pct"]:.2f}%</div></div></div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown('<div style="color:#555;font-size:13px;padding:8px 0;">Loading price data...</div>', unsafe_allow_html=True)

    # Upcoming IPOs
    st.markdown(
        '<div class="sec-hdr-row"><div class="sec-hdr">Upcoming IPOs</div>'
        '<div class="sec-sub">curated</div></div>',
        unsafe_allow_html=True,
    )
    for ipo in UPCOMING_IPOS:
        status_cls = {"Open": "ipo-open", "Upcoming": "ipo-upcoming", "Closed": "ipo-closed"}.get(ipo["status"], "ipo-upcoming")
        st.markdown(
            f'<div class="ipo-row"><div><div class="ipo-name">{ipo["name"]}</div>'
            f'<div class="ipo-meta">{ipo["dates"]} · Band {ipo["band"]} · Lot {ipo["lot"]}</div></div>'
            f'<span class="ipo-status {status_cls}">{ipo["status"]}</span></div>',
            unsafe_allow_html=True,
        )

    # Results calendar
    st.markdown('<div class="sec-hdr">Results Calendar</div>', unsafe_allow_html=True)
    for rs in UPCOMING_RESULTS:
        bg, fg = av(rs["symbol"])
        p, chg, pct = fetch_price(rs["symbol"] + ".NS")
        ltp = f"₹{p:,.2f}" if p else "—"
        st.markdown(
            f'<div class="srow"><div class="savatar" style="background:{bg};color:{fg};">{rs["symbol"][:3]}</div>'
            f'<div style="flex:1;"><div class="sname">{rs["symbol"]}</div>'
            f'<div class="ssub">Earnings · {rs["date"]}</div></div>'
            f'<div style="text-align:right;"><div class="sprice">{ltp}</div></div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# PORTFOLIO (Stocks)
# ══════════════════════════════════════════════════════════════
elif tab == 1:
    if st.session_state.portfolio:
        rows, invested, current, pnl, pnl_pct = portfolio_summary()
        sign = "+" if pnl >= 0 else ""
        pc = "#00d09c" if pnl >= 0 else "#ff6b6b"
        st.markdown(
            f'<div class="mgrid"><div class="mcard"><div class="mcard-label">Current Value</div>'
            f'<div class="mcard-val">₹{current:,.0f}</div></div>'
            f'<div class="mcard"><div class="mcard-label">Total P&amp;L</div>'
            f'<div class="mcard-val" style="color:{pc}">{sign}₹{pnl:,.0f}</div>'
            f'<div class="mcard-sub" style="color:{pc}">{sign}{pnl_pct:.2f}%</div></div>'
            f'<div class="mcard"><div class="mcard-label">Invested</div>'
            f'<div class="mcard-val">₹{invested:,.0f}</div></div>'
            f'<div class="mcard"><div class="mcard-label">Winners</div>'
            f'<div class="mcard-val">{sum(1 for r in rows if r["PnL"]>0)}/{len(rows)}</div></div></div>',
            unsafe_allow_html=True,
        )
        df_pie = pd.DataFrame(rows)
        fig_pie = go.Figure(go.Pie(
            labels=df_pie["Symbol"], values=df_pie["Current"], hole=0.55,
            textinfo="percent+label", textfont_size=11,
            marker=dict(colors=["#00d09c", "#a78bfa", "#f5a623", "#60a5fa", "#fb7185", "#34d399", "#fbbf24"],
                        line=dict(color="#0d0d0d", width=2)),
        ))
        fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              margin=dict(t=8, b=8, l=8, r=8), height=220,
                              legend=dict(font=dict(color="#aaa", size=10), orientation="h", y=-0.1),
                              showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

        st.markdown('<div class="sec-hdr">Holdings</div>', unsafe_allow_html=True)
        for i, (h, r) in enumerate(zip(st.session_state.portfolio, rows)):
            bg, fg = av(r["Symbol"])
            pc2 = "up" if r["PnL"] >= 0 else "down"
            sign2 = "+" if r["PnL"] >= 0 else ""
            alloc = (r["Current"] / current * 100) if current else 0
            with st.expander(f"{r['Symbol']}  ·  ₹{r['LTP']:,.2f}  ·  {sign2}{r['PnL%']:.1f}%"):
                c1, c2 = st.columns(2)
                c1.markdown(f"**Qty:** {r['Qty']}\n\n**Avg:** ₹{r['Avg']:,.2f}\n\n**Invested:** ₹{r['Invested']:,.0f}")
                c2.markdown(
                    f"**Current:** ₹{r['Current']:,.0f}\n\n"
                    f"**P&L:** <span class='{pc2}'>{sign2}₹{r['PnL']:,.0f} ({sign2}{r['PnL%']:.1f}%)</span>\n\n"
                    f"**Alloc:** {alloc:.1f}%",
                    unsafe_allow_html=True,
                )
                info = fetch_info(r["Symbol"] + ".NS")
                if info:
                    c3, c4 = st.columns(2)
                    c3.markdown(f"**52W H:** ₹{info.get('52h','—')}\n\n**Sector:** {info.get('sector','—')}")
                    c4.markdown(f"**52W L:** ₹{info.get('52l','—')}\n\n**P/E:** {round(info['pe'],1) if info.get('pe') else '—'}")
                prd = st.pills("period", ["1wk", "1mo", "3mo", "6mo", "1y"],
                               selection_mode="single", default="1mo",
                               key=f"prd_{i}", label_visibility="collapsed")
                prd = prd or "1mo"
                hist = fetch_history(r["Symbol"] + ".NS", prd)
                if not hist.empty:
                    col = "#00d09c" if r["PnL"] >= 0 else "#ff6b6b"
                    fill = "rgba(0,208,156,0.12)" if r["PnL"] >= 0 else "rgba(255,107,107,0.12)"
                    fig = go.Figure(go.Scatter(x=hist.index, y=hist["Close"], mode="lines",
                                               line=dict(color=col, width=2), fill="tozeroy", fillcolor=fill))
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                      margin=dict(t=4, b=4, l=0, r=0), height=150,
                                      xaxis=dict(showgrid=False, color="#555"),
                                      yaxis=dict(showgrid=True, gridcolor="#1e1e1e", color="#555"))
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                if st.button(f"Remove {r['Symbol']}", key=f"del_{i}", type="secondary"):
                    st.session_state.portfolio.pop(i)
                    _save_data()
                    st.rerun()

    st.markdown('<div class="sec-hdr">Add Holding</div>', unsafe_allow_html=True)
    with st.form("add_stock", clear_on_submit=True):
        sym = st.text_input("NSE Symbol", placeholder="e.g. TCS, RELIANCE").upper().strip()
        c1, c2 = st.columns(2)
        qty = c1.number_input("Qty", min_value=1, step=1)
        avg = c2.number_input("Avg Price ₹", min_value=0.01, step=0.01, format="%.2f")
        if st.form_submit_button("➕ Add to Portfolio", use_container_width=True, type="primary"):
            if sym and qty and avg:
                p, _, _ = fetch_price(sym + ".NS")
                if p is None:
                    st.error(f"'{sym}' not found on NSE.")
                elif any(h["symbol"] == sym for h in st.session_state.portfolio):
                    st.warning(f"{sym} already added.")
                else:
                    st.session_state.portfolio.append({"symbol": sym, "qty": int(qty), "avg_price": float(avg)})
                    _save_data()
                    st.success(f"✓ {sym} added\!")
                    st.rerun()
            else:
                st.warning("Fill all fields.")
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# MUTUAL FUNDS
# ══════════════════════════════════════════════════════════════
elif tab == 2:
    if st.session_state.mf_portfolio:
        rows, invested, current, pnl, pnl_pct = mf_portfolio_summary()
        sign = "+" if pnl >= 0 else ""
        pc = "#00d09c" if pnl >= 0 else "#ff6b6b"
        st.markdown(
            f'<div class="hero-card"><div class="hero-label">Mutual Funds · Portfolio Value</div>'
            f'<div class="hero-value">₹{current:,.0f}</div>'
            f'<div class="hero-pnl" style="color:{pc}">{sign}₹{pnl:,.0f} ({sign}{pnl_pct:.2f}%) overall</div>'
            f'<div class="hero-sub">Invested ₹{invested:,.0f} · {len(rows)} funds</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="mgrid"><div class="mcard"><div class="mcard-label">Invested</div>'
            f'<div class="mcard-val">₹{invested:,.0f}</div></div>'
            f'<div class="mcard"><div class="mcard-label">Current</div>'
            f'<div class="mcard-val">₹{current:,.0f}</div></div>'
            f'<div class="mcard"><div class="mcard-label">P&amp;L</div>'
            f'<div class="mcard-val" style="color:{pc}">{sign}₹{pnl:,.0f}</div>'
            f'<div class="mcard-sub" style="color:{pc}">{sign}{pnl_pct:.2f}%</div></div>'
            f'<div class="mcard"><div class="mcard-label">Winners</div>'
            f'<div class="mcard-val">{sum(1 for r in rows if r["PnL"]>0)}/{len(rows)}</div></div></div>',
            unsafe_allow_html=True,
        )
        df_pie = pd.DataFrame(rows)
        fig_pie = go.Figure(go.Pie(
            labels=[n[:22] + ("…" if len(n) > 22 else "") for n in df_pie["Name"]],
            values=df_pie["Current"], hole=0.55,
            textinfo="percent", textfont_size=11,
            marker=dict(colors=["#00d09c", "#a78bfa", "#f5a623", "#60a5fa", "#fb7185", "#34d399", "#fbbf24"],
                        line=dict(color="#0d0d0d", width=2)),
        ))
        fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              margin=dict(t=8, b=8, l=8, r=8), height=240,
                              legend=dict(font=dict(color="#aaa", size=9), orientation="h", y=-0.25),
                              showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

        st.markdown('<div class="sec-hdr">My Funds</div>', unsafe_allow_html=True)
        for i, r in enumerate(rows):
            pc2 = "up" if r["PnL"] >= 0 else "down"
            s2 = "+" if r["PnL"] >= 0 else ""
            short = r["Name"][:38] + ("…" if len(r["Name"]) > 38 else "")
            with st.expander(f"{short}  ·  {s2}{r['PnL%']:.1f}%"):
                c1, c2 = st.columns(2)
                c1.markdown(f"**Code:** {r['Code']}\n\n**Units:** {r['Units']:.3f}\n\n**Buy NAV:** ₹{r['BuyNAV']:.4f}")
                c2.markdown(
                    f"**Current NAV:** ₹{r['NAV']:.4f}\n\n"
                    f"**Invested:** ₹{r['Invested']:,.0f}\n\n"
                    f"**Current:** ₹{r['Current']:,.0f}"
                )
                st.markdown(
                    f"**P&L:** <span class='{pc2}'>{s2}₹{r['PnL']:,.0f} ({s2}{r['PnL%']:.1f}%)</span>",
                    unsafe_allow_html=True,
                )
                data = fetch_mf_data(r["Code"])
                if data and data.get("history"):
                    hist = data["history"][:500]
                    dates = [datetime.strptime(h["date"], "%d-%m-%Y") for h in hist]
                    navs = [float(h["nav"]) for h in hist]
                    col = "#00d09c" if r["PnL"] >= 0 else "#ff6b6b"
                    fill = "rgba(0,208,156,0.12)" if r["PnL"] >= 0 else "rgba(255,107,107,0.12)"
                    fig = go.Figure(go.Scatter(x=dates[::-1], y=navs[::-1], mode="lines",
                                               line=dict(color=col, width=2), fill="tozeroy", fillcolor=fill))
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                      margin=dict(t=4, b=4, l=0, r=0), height=160,
                                      xaxis=dict(showgrid=False, color="#555"),
                                      yaxis=dict(showgrid=True, gridcolor="#1e1e1e", color="#555"))
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                if st.button("Remove fund", key=f"mf_del_{i}", type="secondary"):
                    st.session_state.mf_portfolio.pop(i)
                    _save_data()
                    st.rerun()

    # Add fund form
    st.markdown('<div class="sec-hdr">Add Fund</div>', unsafe_allow_html=True)
    with st.form("add_mf", clear_on_submit=True):
        st.caption("Find scheme codes at api.mfapi.in or use search below")
        code = st.number_input("AMFI Scheme Code", min_value=100000, max_value=999999, step=1, value=100000)
        c1, c2 = st.columns(2)
        units = c1.number_input("Units", min_value=0.001, step=0.001, format="%.3f")
        buy_nav = c2.number_input("Buy NAV ₹", min_value=0.01, step=0.01, format="%.4f")
        if st.form_submit_button("➕ Add Fund", use_container_width=True, type="primary"):
            if code and units > 0 and buy_nav > 0:
                data = fetch_mf_data(int(code))
                if not data:
                    st.error(f"Scheme code {code} not found on mfapi.in")
                elif any(h["code"] == int(code) for h in st.session_state.mf_portfolio):
                    st.warning("Already added")
                else:
                    st.session_state.mf_portfolio.append({
                        "code": int(code),
                        "name": data["name"],
                        "units": float(units),
                        "buy_nav": float(buy_nav),
                    })
                    _save_data()
                    st.success(f"✓ {data['name'][:40]} added")
                    st.rerun()

    # Search MF
    st.markdown('<div class="sec-hdr">Search Schemes</div>', unsafe_allow_html=True)
    mf_q = st.text_input("search_mf", placeholder="🔍   Search by name (e.g. Parag Parikh, HDFC Mid-Cap)",
                         key="mf_search", label_visibility="collapsed")
    if mf_q and len(mf_q) >= 3:
        results = search_mf(mf_q.strip())
        if results:
            for s in results:
                st.markdown(
                    f'<div class="fund-card"><div class="fund-name">{s.get("schemeName","")[:60]}</div>'
                    f'<div class="fund-meta">Code: {s.get("schemeCode","")}</div></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No matches. Try a longer query.")

    # Discover by category
    st.markdown('<div class="sec-hdr">Discover Funds</div>', unsafe_allow_html=True)
    cats = list(MF_CATEGORIES.keys())
    sel_cat = pill_filter(cats, "mf_cat_filter", default_idx=0)
    for code, fallback in MF_CATEGORIES.get(sel_cat, []):
        data = fetch_mf_data(code)
        if data:
            name = data["name"]
            nav = data["latest_nav"]
            nav_date = data["latest_date"]
            r1 = data["ret_1y"]
            r3 = data["ret_3y"]
            r5 = data["ret_5y"]
        else:
            name = fallback
            nav = nav_date = None
            r1 = r3 = r5 = None

        def _fmt(v):
            if v is None:
                return ("—", "muted")
            return (f"{'+' if v>=0 else ''}{v:.1f}%", "up" if v >= 0 else "down")

        r1f, r1c = _fmt(r1)
        r3f, r3c = _fmt(r3)
        r5f, r5c = _fmt(r5)
        nav_txt = f"₹{nav:.4f}" if nav else "—"
        nav_date_txt = nav_date or ""
        st.markdown(
            f'<div class="fund-card"><div class="fund-name">{name[:70]}</div>'
            f'<div class="fund-meta">Code: {code}</div>'
            f'<div class="fund-nav-row"><div><div class="fund-nav-label">NAV {nav_date_txt}</div>'
            f'<div class="fund-nav">{nav_txt}</div></div></div>'
            f'<div class="fund-returns">'
            f'<div class="fund-ret-box"><div class="fund-ret-label">1Y</div><div class="fund-ret-val {r1c}">{r1f}</div></div>'
            f'<div class="fund-ret-box"><div class="fund-ret-label">3Y CAGR</div><div class="fund-ret-val {r3c}">{r3f}</div></div>'
            f'<div class="fund-ret-box"><div class="fund-ret-label">5Y CAGR</div><div class="fund-ret-val {r5c}">{r5f}</div></div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# WATCHLIST
# ══════════════════════════════════════════════════════════════
elif tab == 3:
    st.markdown('<div class="sec-hdr">Add to Watchlist</div>', unsafe_allow_html=True)
    with st.form("add_watch", clear_on_submit=True):
        wsym = st.text_input("NSE Symbol", placeholder="e.g. RELIANCE, ZOMATO").upper().strip()
        if st.form_submit_button("⭐ Add Symbol", use_container_width=True, type="primary"):
            if wsym:
                p, _, _ = fetch_price(wsym + ".NS")
                if p is None:
                    st.error(f"'{wsym}' not found on NSE.")
                elif wsym in st.session_state.watchlist:
                    st.warning(f"{wsym} already in watchlist")
                else:
                    st.session_state.watchlist.append(wsym)
                    _save_data()
                    st.success(f"✓ {wsym} added")
                    st.rerun()
            else:
                st.warning("Enter a symbol.")

    if st.session_state.watchlist:
        st.markdown('<div class="sec-hdr">My Watchlist</div>', unsafe_allow_html=True)
        for i, sym in enumerate(st.session_state.watchlist):
            p, chg, pct = fetch_price(sym + ".NS")
            info = fetch_info(sym + ".NS")
            spark = fetch_sparkline(sym + ".NS")
            if p is None:
                continue
            bg, fg = av(sym)
            cls = "up" if pct >= 0 else "down"
            sign = "+" if pct >= 0 else ""
            with st.expander(f"{sym}  ·  ₹{p:,.2f}  ·  {sign}{pct:.2f}%"):
                c1, c2, c3 = st.columns([3, 2, 2])
                with c1:
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:10px;">'
                        f'<div class="savatar" style="background:{bg};color:{fg};">{sym[:3]}</div>'
                        f'<div><div class="sname">{sym}</div>'
                        f'<div class="ssub">{info.get("sector","—")}</div></div></div>',
                        unsafe_allow_html=True,
                    )
                with c2:
                    if spark:
                        st.plotly_chart(spark_fig(spark, pct >= 0), use_container_width=True, config={"displayModeBar": False})
                with c3:
                    st.markdown(
                        f'<div style="text-align:right;">'
                        f'<div class="sprice">₹{p:,.2f}</div>'
                        f'<div class="schg {cls}">{sign}{pct:.2f}%</div></div>',
                        unsafe_allow_html=True,
                    )
                if info:
                    d1, d2 = st.columns(2)
                    d1.markdown(f"**52W High:** ₹{info.get('52h','—')}\n\n**P/E:** {round(info['pe'],1) if info.get('pe') else '—'}")
                    d2.markdown(
                        f"**52W Low:** ₹{info.get('52l','—')}\n\n"
                        f"**Mkt Cap:** {'₹'+str(round(info.get('mktcap',0)/1e7,0))+' Cr' if info.get('mktcap') else '—'}"
                    )
                prd = st.pills("w_period", ["1wk", "1mo", "3mo", "6mo", "1y"],
                               selection_mode="single", default="1mo",
                               key=f"w_prd_{i}", label_visibility="collapsed")
                prd = prd or "1mo"
                hist = fetch_history(sym + ".NS", prd)
                if not hist.empty:
                    col = "#00d09c" if pct >= 0 else "#ff6b6b"
                    fill = "rgba(0,208,156,0.12)" if pct >= 0 else "rgba(255,107,107,0.12)"
                    fig = go.Figure(go.Scatter(x=hist.index, y=hist["Close"], mode="lines",
                                               line=dict(color=col, width=2), fill="tozeroy", fillcolor=fill))
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                      margin=dict(t=4, b=4, l=0, r=0), height=150,
                                      xaxis=dict(showgrid=False, color="#555"),
                                      yaxis=dict(showgrid=True, gridcolor="#1e1e1e", color="#555"))
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                if st.button("Remove", key=f"w_del_{i}", type="secondary"):
                    st.session_state.watchlist.pop(i)
                    _save_data()
                    st.rerun()
    else:
        st.markdown(
            '<div class="card" style="text-align:center;padding:28px;">'
            '<div style="font-size:36px;margin-bottom:10px;">⭐</div>'
            '<div style="font-weight:700;font-size:15px;color:#f0f0f0;margin-bottom:6px;">Your watchlist is empty</div>'
            '<div style="font-size:12px;color:#666;">Add symbols above to monitor them without adding to portfolio.</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# MARKET
# ══════════════════════════════════════════════════════════════
elif tab == 4:
    st.markdown('<div class="sec-hdr">Indices</div>', unsafe_allow_html=True)
    for name, ticker in [("Nifty 50", "^NSEI"), ("Sensex", "^BSESN"), ("Bank Nifty", "^NSEBANK"), ("Nifty IT", "^CNXIT")]:
        p, chg, pct = fetch_price(ticker)
        if p:
            sign = "+" if pct >= 0 else ""
            spark = fetch_sparkline(ticker)
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.markdown(
                f'<div style="padding:7px 0;"><div class="sname">{name}</div>'
                f'<div class="ssub">₹{p:,.2f}</div></div>',
                unsafe_allow_html=True,
            )
            if spark:
                with c2:
                    st.plotly_chart(spark_fig(spark, pct >= 0), use_container_width=True, config={"displayModeBar": False})
            c3.markdown(
                f'<div style="text-align:right;padding-top:10px;">'
                f'<span class="pill {"pill-up" if pct>=0 else "pill-down"}">{sign}{pct:.2f}%</span><br>'
                f'<span style="font-size:10px;color:#555;">{sign}₹{chg:,.2f}</span></div>',
                unsafe_allow_html=True,
            )
        st.markdown("<hr style='border-color:#1e1e1e;margin:2px 0;'>", unsafe_allow_html=True)

    st.markdown('<div class="sec-hdr">Gainers &amp; Losers</div>', unsafe_allow_html=True)
    sel2 = pill_filter(["Large Cap", "Mid Cap", "Small Cap"], "mk_cap_filter")
    gainers2, losers2 = fetch_movers_by_cap(sel2)
    c1, c2 = st.columns(2)
    for col, df, label, pcls in [(c1, gainers2, "▲ Gainers", "pill-up"), (c2, losers2, "▼ Losers", "pill-down")]:
        with col:
            color = "#00d09c" if "Gain" in label else "#ff6b6b"
            st.markdown(
                f'<div style="font-size:11px;font-weight:700;color:{color};margin-bottom:5px;">{label}</div>',
                unsafe_allow_html=True,
            )
            if not df.empty:
                for _, r in df.iterrows():
                    bg, fg = av(r["symbol"])
                    sign = "+" if r["pct"] >= 0 else ""
                    st.markdown(
                        f'<div class="srow"><div class="savatar" style="background:{bg};color:{fg};width:30px;height:30px;font-size:9px;">{r["symbol"][:3]}</div>'
                        f'<div style="flex:1;min-width:0;"><div style="font-size:11px;font-weight:600;color:#f0f0f0;">{r["symbol"]}</div>'
                        f'<div class="ssub">₹{r["price"]:,.0f}</div></div>'
                        f'<span class="pill {pcls}" style="font-size:9px;">{sign}{r["pct"]:.1f}%</span></div>',
                        unsafe_allow_html=True,
                    )

    st.markdown('<div class="sec-hdr">Stock Lookup</div>', unsafe_allow_html=True)
    lookup = st.text_input("Symbol", placeholder="e.g. RELIANCE, ZOMATO", label_visibility="collapsed").upper().strip()
    if lookup:
        p, chg, pct = fetch_price(lookup + ".NS")
        if p:
            info = fetch_info(lookup + ".NS")
            sign = "+" if pct >= 0 else ""
            st.markdown(
                f'<div class="card"><div style="display:flex;justify-content:space-between;align-items:flex-start;">'
                f'<div><div style="font-size:17px;font-weight:700;color:#f0f0f0;">{lookup}</div>'
                f'<div class="ssub">{info.get("name","")}</div>'
                f'<div class="ssub">{info.get("sector","")}</div></div>'
                f'<div style="text-align:right;"><div style="font-size:22px;font-weight:700;color:#f0f0f0;">₹{p:,.2f}</div>'
                f'<span class="pill {"pill-up" if pct>=0 else "pill-down"}">{sign}{pct:.2f}%</span></div></div>'
                f'<hr style="border-color:#2a2a2a;margin:10px 0;">'
                f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:11px;color:#666;">'
                f'<div>52W High: <span style="color:#f0f0f0;font-weight:600;">₹{info.get("52h","—")}</span></div>'
                f'<div>52W Low: <span style="color:#f0f0f0;font-weight:600;">₹{info.get("52l","—")}</span></div>'
                f'<div>P/E: <span style="color:#f0f0f0;font-weight:600;">{round(info["pe"],1) if info.get("pe") else "—"}</span></div>'
                f'<div>Mkt Cap: <span style="color:#f0f0f0;font-weight:600;">{"₹"+str(round(info.get("mktcap",0)/1e7,0))+"Cr" if info.get("mktcap") else "—"}</span></div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
            prd = st.pills("m_period", ["1wk", "1mo", "3mo", "6mo", "1y"],
                           selection_mode="single", default="1mo",
                           key="mk_prd", label_visibility="collapsed")
            prd = prd or "1mo"
            hist = fetch_history(lookup + ".NS", prd)
            if not hist.empty:
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=hist.index, open=hist["Open"], high=hist["High"], low=hist["Low"], close=hist["Close"],
                    increasing_line_color="#00d09c", decreasing_line_color="#ff6b6b",
                    increasing_fillcolor="rgba(0,208,156,0.2)", decreasing_fillcolor="rgba(255,107,107,0.2)",
                ))
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                  margin=dict(t=4, b=4, l=0, r=0), height=220,
                                  xaxis=dict(showgrid=False, color="#555", rangeslider_visible=False),
                                  yaxis=dict(showgrid=True, gridcolor="#1e1e1e", color="#555"))
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.error(f"'{lookup}' not found on NSE.")

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# HEATMAP
# ══════════════════════════════════════════════════════════════
elif tab == 5:
    st.markdown(
        '<div class="sec-hdr-row"><div class="sec-hdr">Sector Heatmap</div>'
        '<div class="sec-sub">Today\'s performance</div></div>',
        unsafe_allow_html=True,
    )
    perf = fetch_sector_perf()
    tiles = '<div class="hm-grid">'
    for name, pct in perf:
        bg = heatmap_color(pct)
        cls = "up" if pct >= 0 else "down"
        sign = "+" if pct >= 0 else ""
        tiles += (f'<div class="hm-tile" style="background:{bg};">'
                  f'<div class="hm-name">{name}</div>'
                  f'<div class="hm-pct {cls}">{sign}{pct:.2f}%</div></div>')
    tiles += '</div>'
    st.markdown(tiles, unsafe_allow_html=True)

    st.markdown('<div class="sec-hdr">Explore Sector</div>', unsafe_allow_html=True)
    sector_names = list(SECTOR_STOCKS.keys())
    sel_sec = pill_filter(sector_names, "heatmap_sec", default_idx=0)

    stocks = SECTOR_STOCKS.get(sel_sec, [])
    rows = []
    for s in stocks:
        p, chg, pct = fetch_price(s)
        if p is not None:
            rows.append({"symbol": s.replace(".NS", ""), "price": p, "pct": pct})
    if rows:
        rows.sort(key=lambda x: -x["pct"])
        st.markdown(
            f'<div style="font-size:11px;color:#888;margin-bottom:6px;">'
            f'{len(rows)} stocks · sorted by day change</div>',
            unsafe_allow_html=True,
        )
        for r in rows:
            bg, fg = av(r["symbol"])
            cls = "pill-up" if r["pct"] >= 0 else "pill-down"
            sign = "+" if r["pct"] >= 0 else ""
            st.markdown(
                f'<div class="srow"><div class="savatar" style="background:{bg};color:{fg};">{r["symbol"][:3]}</div>'
                f'<div style="flex:1;"><div class="sname">{r["symbol"]}</div>'
                f'<div class="ssub">₹{r["price"]:,.2f}</div></div>'
                f'<span class="pill {cls}">{sign}{r["pct"]:.2f}%</span></div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("Loading sector data…")

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# TOOLS
# ══════════════════════════════════════════════════════════════
elif tab == 6:
    st.markdown('<div class="sec-hdr">Calculator</div>', unsafe_allow_html=True)
    tool = pill_filter(["SIP", "Lumpsum", "Goal", "CAGR", "EMI"], "tool_sel", default_idx=0)

    if tool == "SIP":
        st.markdown("**Project your SIP returns**")
        c1, c2 = st.columns(2)
        monthly = c1.number_input("Monthly SIP ₹", min_value=500, step=500, value=10000)
        years = c2.number_input("Period (years)", min_value=1, max_value=40, step=1, value=10)
        rate = st.slider("Expected Return (%)", 4.0, 25.0, 12.0, 0.5)
        fv = sip_fv(monthly, rate, years)
        invested = monthly * years * 12
        gains = fv - invested
        st.markdown(
            f'<div class="tool-result">'
            f'<div class="tool-result-label">Maturity Value</div>'
            f'<div class="tool-result-val">₹{fv:,.0f}</div>'
            f'<div class="tool-result-sub">in {years} years at {rate:.1f}% p.a.</div>'
            f'<div class="tool-breakdown">'
            f'<div class="tool-bd-box"><div class="tool-bd-label">Invested</div><div class="tool-bd-val">₹{invested:,.0f}</div></div>'
            f'<div class="tool-bd-box"><div class="tool-bd-label">Est. Gains</div><div class="tool-bd-val up">₹{gains:,.0f}</div></div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    elif tool == "Lumpsum":
        st.markdown("**Project your one-time investment**")
        c1, c2 = st.columns(2)
        principal = c1.number_input("Lumpsum ₹", min_value=1000, step=1000, value=100000)
        years = c2.number_input("Period (years)", min_value=1, max_value=40, step=1, value=10)
        rate = st.slider("Expected Return (%)", 4.0, 25.0, 12.0, 0.5)
        fv = lumpsum_fv(principal, rate, years)
        gains = fv - principal
        st.markdown(
            f'<div class="tool-result">'
            f'<div class="tool-result-label">Maturity Value</div>'
            f'<div class="tool-result-val">₹{fv:,.0f}</div>'
            f'<div class="tool-result-sub">in {years} years at {rate:.1f}% p.a.</div>'
            f'<div class="tool-breakdown">'
            f'<div class="tool-bd-box"><div class="tool-bd-label">Invested</div><div class="tool-bd-val">₹{principal:,.0f}</div></div>'
            f'<div class="tool-bd-box"><div class="tool-bd-label">Est. Gains</div><div class="tool-bd-val up">₹{gains:,.0f}</div></div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    elif tool == "Goal":
        st.markdown("**Plan SIP for a future goal**")
        c1, c2 = st.columns(2)
        target = c1.number_input("Target amount ₹", min_value=10000, step=10000, value=5000000)
        years = c2.number_input("Years to goal", min_value=1, max_value=40, step=1, value=15)
        rate = st.slider("Expected Return (%)", 4.0, 25.0, 12.0, 0.5)
        monthly = goal_sip(target, rate, years)
        invested = monthly * years * 12
        st.markdown(
            f'<div class="tool-result">'
            f'<div class="tool-result-label">Required Monthly SIP</div>'
            f'<div class="tool-result-val">₹{monthly:,.0f}</div>'
            f'<div class="tool-result-sub">to reach ₹{target:,.0f} in {years} years at {rate:.1f}% p.a.</div>'
            f'<div class="tool-breakdown">'
            f'<div class="tool-bd-box"><div class="tool-bd-label">Total Invested</div><div class="tool-bd-val">₹{invested:,.0f}</div></div>'
            f'<div class="tool-bd-box"><div class="tool-bd-label">Target</div><div class="tool-bd-val up">₹{target:,.0f}</div></div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    elif tool == "CAGR":
        st.markdown("**Calculate annualised return (CAGR)**")
        c1, c2 = st.columns(2)
        start_v = c1.number_input("Initial value ₹", min_value=1.0, step=100.0, value=100000.0)
        end_v = c2.number_input("Final value ₹", min_value=1.0, step=100.0, value=180000.0)
        years = st.number_input("Years", min_value=0.5, max_value=40.0, step=0.5, value=5.0)
        cg = cagr_pct(start_v, end_v, years)
        total_pct = (end_v / start_v - 1) * 100
        st.markdown(
            f'<div class="tool-result">'
            f'<div class="tool-result-label">CAGR</div>'
            f'<div class="tool-result-val">{cg:.2f}%</div>'
            f'<div class="tool-result-sub">over {years:g} years</div>'
            f'<div class="tool-breakdown">'
            f'<div class="tool-bd-box"><div class="tool-bd-label">Total Return</div><div class="tool-bd-val up">{total_pct:.1f}%</div></div>'
            f'<div class="tool-bd-box"><div class="tool-bd-label">Absolute Gain</div><div class="tool-bd-val">₹{end_v-start_v:,.0f}</div></div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    elif tool == "EMI":
        st.markdown("**Calculate loan EMI**")
        c1, c2 = st.columns(2)
        loan = c1.number_input("Loan amount ₹", min_value=10000, step=10000, value=2500000)
        years = c2.number_input("Tenure (years)", min_value=1, max_value=30, step=1, value=20)
        rate = st.slider("Interest Rate (%)", 5.0, 20.0, 8.5, 0.1)
        emi = emi_calc(loan, rate, years)
        total = emi * years * 12
        interest = total - loan
        st.markdown(
            f'<div class="tool-result">'
            f'<div class="tool-result-label">Monthly EMI</div>'
            f'<div class="tool-result-val">₹{emi:,.0f}</div>'
            f'<div class="tool-result-sub">{years}-year loan at {rate:.2f}% p.a.</div>'
            f'<div class="tool-breakdown">'
            f'<div class="tool-bd-box"><div class="tool-bd-label">Total Payable</div><div class="tool-bd-val">₹{total:,.0f}</div></div>'
            f'<div class="tool-bd-box"><div class="tool-bd-label">Total Interest</div><div class="tool-bd-val down">₹{interest:,.0f}</div></div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="sec-hdr">Good to know</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="card" style="font-size:12px;color:#999;line-height:1.6;">'
        '• SIP & Lumpsum assume constant returns — real markets are volatile.<br>'
        '• Equity MF long-term (5Y+) can average ~12% historically, but is not guaranteed.<br>'
        '• Factor in 4–6% inflation when planning future goals.<br>'
        '• For tax planning, remember LTCG on equity above ₹1.25L at 12.5% (FY25+).'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
