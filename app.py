# AI TRADE INTELLIGENCE V13.0
# Unified dashboard with trade confirmation engine: TradingView chart, technical analysis, news,
# rule-based AI scoring, multi-timeframe trends, options OI/PCR/Max Pain,
# strategy payoff planner, scanner, S/R, risk calculator, manual alerts, FII/DII.
# Run: python -m streamlit run app.py

import streamlit as st
import hmac
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from ai_engine import evaluate_signal
from options_analytics import parse_chain, max_pain, add_greeks
from index_options_intelligence import analyze_option_context
from dashboard_intelligence import (SECTOR_SYMBOLS, BREADTH_SYMBOLS, fetch_change, add_alert, list_alerts, remove_alert, check_alerts, save_trade, load_trades, clear_trades)
from ml_backtest_engine import run_ml_backtest
from patterns_engine import (detect_candlestick_patterns, detect_chart_setups, pattern_history, breakout_context, classify_market_regime, optimize_ema_strategy, rank_opportunities)
from market_intelligence_v12 import volume_intelligence, market_structure, supply_demand_zones, sector_rotation
from market_intelligence_v13 import regime_intelligence, index_confluence, rank_intraday_opportunities
from news_intelligence_v19 import fetch_all_news, fetch_forex_factory_calendar, FOREX_FACTORY_NEWS
from news_impact_engine_v20 import analyze_news_frame
from market_intelligence_v21 import enrich_news, fetch_cross_asset_snapshot, correlation_matrix
from central_ai_brain_v35 import TOOL_CATALOG, analyze_market as analyze_central_market, rank_symbols as rank_central_symbols, correlation_matrix as central_correlation_matrix

st.set_page_config(page_title="AI Trade Intelligence V22", page_icon="📈", layout="wide")

st.markdown("""
<style>
:root{--ati-bg:#080d18;--ati-panel:#111a2b;--ati-border:#26364e;--ati-muted:#9aabc2;--ati-accent:#38bdf8}
.block-container{padding-top:1.1rem;padding-bottom:2.4rem;max-width:1600px}
[data-testid="stMetric"]{background:linear-gradient(145deg,#142238,#0d1728);padding:16px 18px;border-radius:14px;border:1px solid var(--ati-border);box-shadow:0 8px 24px rgba(0,0,0,.16)}
[data-testid="stMetricLabel"]{color:#a9bad0}
[data-testid="stMetricValue"]{font-weight:700;letter-spacing:-.03em}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0b1424,#080d18);border-right:1px solid #1d2b40}
section[data-testid="stSidebar"] [data-testid="stRadio"] label{padding:5px 2px}
.small-note{color:var(--ati-muted);font-size:.85rem}
.ati-hero{padding:26px 28px;border-radius:18px;background:radial-gradient(circle at 85% 10%,rgba(14,165,233,.22),transparent 32%),linear-gradient(120deg,#14243b,#0b1322);border:1px solid #2b4563;margin-bottom:18px}
.ati-hero h1{font-size:2rem;line-height:1.15;margin:0 0 8px 0}
.ati-hero p{color:#b6c7dc;margin:0}
.ati-section{font-size:1.12rem;font-weight:700;margin:12px 0 8px 0}
.ati-tile{background:linear-gradient(150deg,#142238,#0d1728);border:1px solid #26364e;border-radius:14px;padding:16px;height:100%;}
.ati-tile h4{margin:0 0 6px 0;font-size:1rem}
.ati-tile p{margin:0;color:#9aabc2;font-size:.86rem}
div.stButton>button{border-radius:10px;border:1px solid #34506f;font-weight:600}
.ati-terminal-card{background:linear-gradient(145deg,#142238,#0d1728);border:1px solid #26364e;border-radius:14px;padding:14px 16px}
@media(max-width:768px){.block-container{padding-left:.7rem;padding-right:.7rem;padding-top:.5rem}.ati-hero{padding:18px 16px}.ati-hero h1{font-size:1.45rem}[data-testid="stMetric"]{padding:10px 11px}}
hr{border-color:#24344a}
/* V43 responsive terminal shell */
[data-testid="stAppViewContainer"]{background:#080d18}
[data-testid="stHeader"]{background:rgba(8,13,24,.88)}
[data-testid="stSidebar"]{min-width:245px}
[data-testid="stPlotlyChart"]{width:100%;overflow:hidden}
[data-testid="stDataFrame"], [data-testid="stTable"]{max-width:100%;overflow-x:auto}
@media(max-width:900px){
  [data-testid="stSidebar"]{min-width:0}
  [data-testid="stMetricValue"]{font-size:1.15rem}
  [data-testid="stMetricLabel"]{font-size:.78rem}
  .ati-tile{padding:12px;min-height:100px}
  .ati-terminal-card{padding:11px}
  div[data-testid="stHorizontalBlock"]{gap:.55rem}
}
@media(max-width:600px){
  .block-container{padding-left:.55rem!important;padding-right:.55rem!important}
  .ati-hero h1{font-size:1.28rem}
  .ati-hero p{font-size:.83rem}
  [data-testid="stMetric"]{padding:8px!important}
  [data-testid="stMetricValue"]{font-size:1rem}
  [data-testid="stTabs"] button{font-size:.78rem;padding:.35rem .45rem}
  div.stButton>button{min-height:2.65rem;white-space:normal}
}
.login-shell{max-width:470px;margin:8vh auto;padding:30px;border:1px solid #2b4563;border-radius:20px;background:linear-gradient(145deg,#142238,#0b1322);box-shadow:0 24px 70px rgba(0,0,0,.35)}
.login-shell h1{font-size:1.8rem;margin-bottom:5px}.login-shell p{color:#a9bad0}
</style>
""", unsafe_allow_html=True)

# ---------------- V43 ACCOUNT LOGIN ----------------
def _secret_value(key, default=""):
    try:
        return str(st.secrets.get(key, default))
    except Exception:
        return default

LOGIN_USER = _secret_value("APP_LOGIN_USERNAME", "")
LOGIN_PASSWORD = _secret_value("APP_LOGIN_PASSWORD", "")
LOGIN_ENABLED = bool(LOGIN_USER and LOGIN_PASSWORD)
if LOGIN_ENABLED and not st.session_state.get("ati_authenticated", False):
    st.markdown("<div class='login-shell'><h1>📈 AI Trade Intelligence</h1><p>Secure access · V43 Professional Trading Terminal</p></div>", unsafe_allow_html=True)
    with st.form("ati_login_form"):
        username = st.text_input("Account ID", autocomplete="username")
        password = st.text_input("Password", type="password", autocomplete="current-password")
        submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
    if submitted:
        if hmac.compare_digest(username, LOGIN_USER) and hmac.compare_digest(password, LOGIN_PASSWORD):
            st.session_state["ati_authenticated"] = True
            st.rerun()
        else:
            st.error("Invalid account ID or password.")
    st.caption("Account credentials are read from server-side Streamlit secrets and are never embedded in the application source.")
    st.stop()
elif not LOGIN_ENABLED:
    st.sidebar.info("Login is not configured. Add APP_LOGIN_USERNAME and APP_LOGIN_PASSWORD to Streamlit secrets before public deployment.")

# ---------------- DATA ----------------
@st.cache_data(ttl=180)
def load_data(symbol, period, interval):
    try:
        df=yf.download(symbol,period=period,interval=interval,auto_adjust=True,progress=False,threads=False)
        if df is None or df.empty: return pd.DataFrame()
        if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
        df=df.rename(columns=str.title)
        cols=["Open","High","Low","Close","Volume"]
        if not all(c in df.columns for c in cols): return pd.DataFrame()
        return df[cols].dropna()
    except Exception: return pd.DataFrame()

def add_indicators(df):
    x=df.copy(); c=x.Close
    x["EMA20"]=c.ewm(span=20,adjust=False).mean()
    x["EMA50"]=c.ewm(span=50,adjust=False).mean()
    x["EMA200"]=c.ewm(span=200,adjust=False).mean()
    delta=c.diff(); gain=delta.clip(lower=0).ewm(alpha=1/14,adjust=False).mean()
    loss=(-delta.clip(upper=0)).ewm(alpha=1/14,adjust=False).mean()
    x["RSI"]=100-100/(1+gain/loss.replace(0,np.nan))
    x["MACD"]=c.ewm(span=12,adjust=False).mean()-c.ewm(span=26,adjust=False).mean()
    x["MACD_Signal"]=x.MACD.ewm(span=9,adjust=False).mean()
    tr=pd.concat([x.High-x.Low,(x.High-c.shift()).abs(),(x.Low-c.shift()).abs()],axis=1).max(axis=1)
    x["ATR"]=tr.ewm(alpha=1/14,adjust=False).mean()
    x["Volume_Avg20"]=x.Volume.rolling(20).mean()
    return x

def score_trend(df):
    if len(df)<30: return 0,["Insufficient candles"]
    r=df.iloc[-1]; score=0; reasons=[]
    checks=[
        (r.Close>r.EMA20,"Price above EMA20","Price below EMA20"),
        (r.EMA20>r.EMA50,"EMA20 above EMA50","EMA20 below EMA50"),
        (r.Close>r.EMA200,"Price above EMA200","Price below EMA200"),
        (r.MACD>r.MACD_Signal,"MACD bullish","MACD bearish")]
    for ok,pos,neg in checks:
        score += 1 if ok else -1; reasons.append(pos if ok else neg)
    if pd.notna(r.RSI):
        if 50<=r.RSI<=70: score+=1; reasons.append("RSI momentum positive")
        elif r.RSI<45: score-=1; reasons.append("RSI momentum weak")
        elif r.RSI>75: reasons.append("RSI elevated; avoid chasing")
    return score,reasons

@st.cache_data(ttl=300)
def get_news(query):
    try:
        res=requests.get("https://news.google.com/rss/search",
          params={"q":query,"hl":"en-IN","gl":"IN","ceid":"IN:en"},
          headers={"User-Agent":"Mozilla/5.0"},timeout=10)
        root=ET.fromstring(res.content); rows=[]
        for it in root.findall(".//item")[:20]:
            rows.append({"Headline":it.findtext("title",""),"Published":it.findtext("pubDate",""),
                         "Link":it.findtext("link","")})
        return pd.DataFrame(rows)
    except Exception: return pd.DataFrame(columns=["Headline","Published","Link"])

def sentiment(news):
    if news.empty: return 0,"Unavailable"
    pos=["beats","growth","profit","surge","gain","strong","upgrade","record","bullish","rally","approval"]
    neg=["fall","loss","weak","fraud","drop","crash","downgrade","bearish","decline","miss","investigation"]
    s=0
    for h in news.Headline.astype(str).str.lower():
        s+=sum(w in h for w in pos)-sum(w in h for w in neg)
    s=int(np.clip(s,-5,5))
    return s,"Positive" if s>0 else "Negative" if s<0 else "Neutral / mixed"

def price_chart(df,title):
    fig = make_subplots(
    rows=4,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.04,
    row_heights=[0.50, 0.17, 0.17, 0.16],
    subplot_titles=(
        "Price & Technical Indicators",
        "Volume",
        "RSI (14)",
        "MACD"
    )
)
    fig.add_trace(go.Candlestick(x=df.index,open=df.Open,high=df.High,low=df.Low,close=df.Close,name="Price"),row=1,col=1)
    for col in ["EMA20","EMA50","EMA200"]:
        fig.add_trace(go.Scatter(x=df.index,y=df[col],name=col),row=1,col=1)
    fig.add_trace(go.Bar(x=df.index,y=df.Volume,name="Volume"),row=2,col=1)
    if "RSI" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df.RSI,name="RSI (14)"),row=3,col=1)
        fig.add_hline(y=70,line_dash="dot",line_color="gray",row=3,col=1)
        fig.add_hline(y=30,line_dash="dot",line_color="gray",row=3,col=1)
    if "MACD" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df.MACD,name="MACD"),row=4,col=1)
    if "MACD_Signal" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df.MACD_Signal,name="MACD Signal"),row=4,col=1)
    fig.update_layout(title=title,height=750,template="plotly_dark",xaxis_rangeslider_visible=False,legend_orientation="h")
    return fig

def find_col(df, candidates):
    norm={str(c).lower().replace(" ","").replace("_","").replace("-",""):c for c in df.columns}
    for candidate in candidates:
        key=candidate.lower().replace(" ","").replace("_","").replace("-","")
        if key in norm: return norm[key]
    return None

def parse_options(file):
    df=pd.read_csv(file)
    strike=find_col(df,["strike","strikeprice"])
    ce=find_col(df,["CE_OI","Call_OI","CallOpenInterest"])
    pe=find_col(df,["PE_OI","Put_OI","PutOpenInterest"])
    cchange=find_col(df,["CE_change_OI","CE_OI_change","CallChangeOI"])
    pchange=find_col(df,["PE_change_OI","PE_OI_change","PutChangeOI"])
    for c in [strike,ce,pe,cchange,pchange]:
        if c: df[c]=pd.to_numeric(df[c],errors="coerce")
    return df,strike,ce,pe,cchange,pchange


# ---------------- UPSTOX ANALYTICS TOKEN HELPERS ----------------
def upstox_headers():
    token = st.secrets.get("UPSTOX_ACCESS_TOKEN", "")
    if not token:
        return None
    return {"Authorization": f"Bearer {token}", "Accept": "application/json",
            "Content-Type": "application/json"}

@st.cache_data(ttl=5)
def upstox_full_quote(instrument_key, token):
    try:
        response = requests.get(
            "https://api.upstox.com/v2/market-quote/quotes",
            params={"instrument_key": instrument_key},
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=15
        )
        if response.status_code != 200:
            return {"error": f"Upstox returned HTTP {response.status_code}: {response.text[:400]}"}
        return response.json()
    except Exception as exc:
        return {"error": str(exc)}

@st.cache_data(ttl=300)
def upstox_historical(instrument_key, interval, to_date, from_date, token):
    try:
        url = f"https://api.upstox.com/v2/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"
        response = requests.get(url, headers={"Authorization": f"Bearer {token}",
                                              "Accept": "application/json"}, timeout=20)
        if response.status_code != 200:
            return {"error": f"Upstox returned HTTP {response.status_code}: {response.text[:400]}"}
        return response.json()
    except Exception as exc:
        return {"error": str(exc)}

# ---------------- SIDEBAR ----------------
st.sidebar.title("📈 AI Trade Intelligence")
st.sidebar.caption("V28 | Options Intelligence")
pages=[
"Command Center Dashboard","V22 Trading Signal Intelligence","V21 Advanced Market Intelligence","Multi-Source News & Forex Factory","Trading Terminal","AI Prediction Engine","AI Market Intelligence","Index & Options Signal Desk","AI Multi-Timeframe Scanner","Smart Money & Market Structure","AI Trade Confirmation Engine","Multi-Timeframe Analysis","Global Market News",
"Options & OI Analytics","Options Strategy Planner","Stock Scanner","Support & Resistance",
"Risk & Position Planner","Price Alerts","FII/DII Activity","TradingView Chart",
"Market Overview","Professional Market Dashboard","Market Breadth & Sector Strength","Market Alerts","Portfolio & Trade Journal","ML Prediction & Backtesting","AI Patterns & Opportunity Lab","V12 Market Intelligence","V13 AI Market Command Centre","V14 Live Feed Monitor","V15 Live Options Intelligence","V16 AI Options Strategy Engine","V17 Intraday Signal Engine","V18 Opportunity Scanner","V28 Options Intelligence","V29 Strategy Generator","V30 Trade Confirmation","V31 AI Trading Assistant","V32 Chart Pattern & Smart Entry","V33 Multi-Asset AI Scanner","V34 Portfolio & Watchlist Intelligence","V35 Central AI Brain – 25 Tools","V36 Live Operations & Institutional Monitor","V37 Ultimate Platform & Paper Trading","V38 Professional Trading Terminal","V39 Paper Execution Simulator","V40 Advanced Backtesting Lab","V41 Performance Analytics","Central AI Command Centre","AI Market & Option Chain Assistant","V42 AI Decision & Broker Hub","V43 Live Market Intelligence","Upstox Live Data"
]
def navigate_to(target):
    st.session_state["Navigation"] = target

if "Navigation" not in st.session_state:
    st.session_state["Navigation"] = "Command Center Dashboard"
page=st.sidebar.radio("Navigation",pages,key="Navigation")
if LOGIN_ENABLED and st.session_state.get("ati_authenticated", False):
    st.sidebar.caption("🔒 Signed in")
    if st.sidebar.button("Log out", use_container_width=True, key="ati_logout"):
        st.session_state["ati_authenticated"] = False
        st.rerun()
st.sidebar.divider()
symbol=st.sidebar.text_input("Yahoo Finance symbol","RELIANCE.NS").strip().upper()
period=st.sidebar.selectbox("History",["1mo","3mo","6mo","1y","2y","5y"],index=2)
interval=st.sidebar.selectbox("Interval",["5m","15m","30m","1h","1d","1wk"],index=4)
st.sidebar.caption("Examples: RELIANCE.NS, TCS.NS, SBIN.NS, INFY.NS, ^NSEI")

with st.spinner("Loading price data..."):
    raw=load_data(symbol,period,interval)
data=add_indicators(raw) if not raw.empty else pd.DataFrame()

# ---------------- PAGES ----------------
if page=="Command Center Dashboard":
    st.markdown("""
    <div class="ati-hero">
      <h1>📈 AI Trade Intelligence</h1>
      <p>Market brief · Options intelligence · Technical charts · Multi-source news · Trading assistant · Learning centre</p>
    </div>
    """, unsafe_allow_html=True)
    # Prominent one-click entry to the shared Central AI Brain from the main command centre.
    brain_col, brain_info = st.columns([1.15, 3.2])
    with brain_col:
        if st.button("🧠 Open Central AI Brain →", type="primary", use_container_width=True, key="command_center_brain_shortcut"):
            navigate_to("V35 Central AI Brain – 25 Tools")
            st.rerun()
    with brain_info:
        st.markdown("**CENTRAL AI BRAIN · 25 SPECIALIST TOOLS**")
        st.caption(f"Launch the unified analysis workspace for **{symbol}** using the currently selected market history. The Brain is evidence-based and review-only; it does not place orders automatically.")
    if st.button("📡 Open V43 Live Market Intelligence →", use_container_width=True, key="command_center_v43_shortcut"):
        navigate_to("V43 Live Market Intelligence"); st.rerun()
    head1, head2, head3 = st.columns([3,2,1])
    with head1:
        st.markdown(f"**Workspace:** `{symbol}` &nbsp; · &nbsp; **Interval:** `{interval}` &nbsp; · &nbsp; **History:** `{period}`")
    with head2:
        st.caption("Data source: Yahoo Finance for this chart; other modules use their configured providers.")
    with head3:
        if st.button("↻ Refresh", type="primary", use_container_width=True, key="demo_style_refresh"):
            st.cache_data.clear(); st.rerun()

    brief_tab, chain_tab, chart_tab, news_tab, ask_tab, learn_tab = st.tabs([
        "📋 Brief", "📊 Option Chain", "📈 Chart", "📰 News", "💬 Ask", "🎓 Learn"
    ])

    with brief_tab:
        st.markdown('<div class="ati-section">Market pulse</div>', unsafe_allow_html=True)
        try:
            pulse = fetch_change({"NIFTY 50":"^NSEI", "BANK NIFTY":"^NSEBANK", "SENSEX":"^BSESN", "S&P 500":"^GSPC"})
        except Exception:
            pulse = pd.DataFrame()
        if pulse is not None and not pulse.empty:
            metric_cols = st.columns(min(4, len(pulse)))
            for i, (_, row) in enumerate(pulse.head(4).iterrows()):
                metric_cols[i].metric(str(row.get("Name", "Market")), f"{row.get('Last', 0):,.2f}", f"{row.get('Day %', 0):+.2f}%")
        else:
            st.info("Market pulse is unavailable from the current feed. No sample values are substituted.")

        st.markdown('<div class="ati-section">Selected instrument snapshot</div>', unsafe_allow_html=True)
        if not data.empty:
            last=data.iloc[-1]
            prev=data.iloc[-2] if len(data)>1 else last
            change=((float(last.Close)/float(prev.Close))-1)*100 if float(prev.Close) else 0
            a,b,c,d,e=st.columns(5)
            a.metric("Last price",f"₹{last.Close:,.2f}",f"{change:+.2f}%")
            b.metric("RSI (14)",f"{last.RSI:.1f}" if pd.notna(last.RSI) else "—")
            c.metric("EMA 20",f"{last.EMA20:,.2f}" if pd.notna(last.EMA20) else "—")
            d.metric("EMA 50",f"{last.EMA50:,.2f}" if pd.notna(last.EMA50) else "—")
            e.metric("EMA 200",f"{last.EMA200:,.2f}" if pd.notna(last.EMA200) else "—")
            score,reasons=score_trend(data)
            bias="Bullish" if score>=2 else "Bearish" if score<=-2 else "Neutral / mixed"
            st.markdown(f"**Technical bias:** `{bias}` · Score `{score:+d}` (rule-based, not a probability)")
            with st.expander("Why this technical bias?"):
                for reason in reasons: st.write("• "+reason)
        else:
            st.warning("No OHLCV history returned for this symbol/interval. Change the symbol or interval in the sidebar.")

        st.markdown('<div class="ati-section">Quick access</div>', unsafe_allow_html=True)
        quick = [
            ("🧠 Central AI Brain","Central AI Command Centre"),
            ("📊 Performance Analytics","V41 Performance Analytics"),
            ("⚡ AI Trade Assistant","AI Market & Option Chain Assistant"),
            ("⚡ Trading Terminal","Trading Terminal"),("🧠 V22 Signal Intelligence","V22 Trading Signal Intelligence"),
            ("🧭 V21 Market Intelligence","V21 Advanced Market Intelligence"),("🛡️ Risk Planner","Risk & Position Planner")]
        qcols=st.columns(5)
        for col,(label,target) in zip(qcols,quick):
            with col:
                st.markdown(f'<div class="ati-tile"><h4>{label}</h4><p>Open the existing platform module.</p></div>',unsafe_allow_html=True)
                st.button("Open module →",key="demoquick_"+target,use_container_width=True,on_click=navigate_to,args=(target,))

    with chain_tab:
        st.subheader("Options and derivatives workspace")
        st.caption("The demo's option-chain figures are generated samples. This dashboard deliberately does not reproduce them. Open the existing live/analytics modules for provider-backed data.")
        opts=[("Index & Options Signal Desk","Index & Options Signal Desk"),("Options & OI Analytics","Options & OI Analytics"),("V15 Live Options Intelligence","V15 Live Options Intelligence"),("Options Strategy Planner","Options Strategy Planner")]
        for label,target in opts:
            if st.button("Open "+label+" →",key="demochain_"+target,use_container_width=True): navigate_to(target); st.rerun()
        st.info("PCR, Max Pain, OI, Greeks and option-chain availability depend on the selected instrument, expiry and connected data provider.")

    with chart_tab:
        st.subheader("Price chart and technical indicators")
        st.caption(f"{symbol} · {interval} · {period}. Chart uses the currently selected sidebar settings.")
        if not data.empty:
            st.plotly_chart(price_chart(data.tail(220),f"{symbol} · Candles, EMA, volume, RSI and MACD"),use_container_width=True)
        else:
            st.warning("Chart unavailable because no market candles were returned.")
        if st.button("Open full Trading Terminal →",key="demo_chart_terminal"):
            navigate_to("Trading Terminal"); st.rerun()

    with news_tab:
        st.subheader("Multi-source market news")
        st.caption("News feeds are separate from Yahoo Finance price history. Headlines and sentiment are informational and should be checked against the original article.")
        try:
            ndf, nstatus=fetch_all_news()
            if not ndf.empty:
                enriched=enrich_news(ndf)
                show=[c for c in ["Headline","Source","Published (UTC)","Sentiment","Priority","Potential sectors","Link"] if c in enriched.columns]
                st.dataframe(enriched[show].head(15),use_container_width=True,hide_index=True,
                    column_config={"Link":st.column_config.LinkColumn("Article",display_text="Open")})
                st.caption(f"{len(enriched)} headlines received. Feed coverage may vary by publisher and time.")
            else:
                st.info("No publisher headlines were returned at this time. Open the dedicated news module for source diagnostics and Forex Factory calendar.")
        except Exception as exc:
            st.warning(f"News is temporarily unavailable: {exc}")
        if st.button("Open News & Forex Factory →",key="demo_news_full"):
            navigate_to("Multi-Source News & Forex Factory"); st.rerun()

    with ask_tab:
        st.subheader("Ask the trading assistant")
        st.caption("This quick explainer uses available chart indicators and transparent rules. It is not a connected general-purpose AI chat model.")
        question=st.selectbox("Choose a question",["What is the current technical bias?","Explain RSI","What does EMA alignment show?","How should I think about risk?"] ,key="demo_ask_question")
        if st.button("Explain",key="demo_ask_submit"):
            if question.startswith("What is the current"):
                if data.empty: st.info("No market candles are available to assess the current technical bias.")
                else:
                    sc,why=score_trend(data); st.write(f"Rule-based technical score: **{sc:+d}**. Bias: **{'Bullish' if sc>=2 else 'Bearish' if sc<=-2 else 'Neutral / mixed'}**.")
                    for reason in why: st.write("• "+reason)
            elif question=="Explain RSI":
                st.write("RSI measures recent upward versus downward price movement on a 0–100 scale. Common reference zones are 70 and 30; neither is a standalone buy or sell signal.")
                if not data.empty and pd.notna(data.RSI.iloc[-1]): st.metric("Latest RSI",f"{data.RSI.iloc[-1]:.1f}")
            elif question.startswith("What does EMA"):
                st.write("EMA gives more weight to recent prices. Shorter EMAs above longer EMAs can indicate upward trend alignment; price whipsaws and sideways markets can create false signals.")
            else:
                st.write("Define the maximum acceptable loss before entry, calculate position size from stop distance, account for fees/slippage, and avoid risking money you cannot afford to lose.")
        if st.button("Open AI Prediction Engine →",key="demo_ask_ai"):
            navigate_to("AI Prediction Engine"); st.rerun()

    with learn_tab:
        st.subheader("Trading concepts")
        concepts={
            "Option chain":"An option chain lists calls and puts by strike and expiry. Compare OI, change in OI, volume, IV and bid/ask spread; verify the exchange/broker timestamp.",
            "PCR and Max Pain":"PCR compares put open interest with call open interest. Max Pain estimates the strike with the greatest aggregate option-buyer payout loss at expiry. Both are context, not reliable standalone forecasts.",
            "RSI, EMA and VWAP":"RSI describes momentum; EMA smooths price; VWAP is the volume-weighted average price. Combine indicators with price structure and risk controls.",
            "Risk management":"Position size should be based on capital at risk and the distance to the invalidation/stop level. Include brokerage, taxes, slippage, gaps and liquidity.",
            "News and event risk":"Check the original publisher, timestamp, event calendar and affected assets. Headlines can be incomplete or misleading when read without context."
        }
        for title,body in concepts.items():
            with st.expander(title): st.write(body)
        if st.button("Open full AI Patterns & Opportunity Lab →",key="demo_learn_full"):
            navigate_to("AI Patterns & Opportunity Lab"); st.rerun()

    st.markdown('<div class="ati-section">All existing platform modules</div>', unsafe_allow_html=True)
    st.caption("The six-tab layout is a new front-end organisation only. Existing specialist pages, engines, broker integrations and historical modules remain in the sidebar.")
    groups={
        "Market intelligence":["V22 Trading Signal Intelligence","V21 Advanced Market Intelligence","Multi-Source News & Forex Factory","Global Market News","Market Overview","Professional Market Dashboard","Market Breadth & Sector Strength","FII/DII Activity"],
        "Trading & analysis":["Trading Terminal","TradingView Chart","AI Prediction Engine","AI Market Intelligence","AI Trade Confirmation Engine","Multi-Timeframe Analysis","AI Multi-Timeframe Scanner","Smart Money & Market Structure"],
        "Options & opportunities":["Index & Options Signal Desk","Options & OI Analytics","Options Strategy Planner","V15 Live Options Intelligence","V16 AI Options Strategy Engine","V17 Intraday Signal Engine","V18 Opportunity Scanner","Stock Scanner","AI Patterns & Opportunity Lab"],
        "Risk & portfolio":["Risk & Position Planner","Price Alerts","Market Alerts","Portfolio & Trade Journal","ML Prediction & Backtesting","Support & Resistance","Upstox Live Data","V14 Live Feed Monitor"]}
    for group,items in groups.items():
        with st.expander(group,expanded=False):
            cols=st.columns(3)
            for i,item in enumerate(items):
                if item in pages:
                    cols[i%3].button(item,key="demodir_"+item,use_container_width=True,on_click=navigate_to,args=(item,))
    st.caption("Market data may be delayed or unavailable. Signal scores and headline classifications are decision-support heuristics, not guaranteed forecasts or automatic trade instructions.")

if page=="V21 Advanced Market Intelligence":
    st.title("🧠 V21 Advanced Market Intelligence")
    st.caption("Multi-publisher news intelligence, transparent headline sentiment and priority, sector mapping, breaking-headline detection, and cross-asset context.")
    refresh = st.button("Refresh V21 intelligence", key="v21_refresh")
    if refresh:
        st.cache_data.clear()
    with st.spinner("Collecting India and international publisher feeds..."):
        news_v21, status_v21 = fetch_all_news()
    intel = enrich_news(news_v21)
    if intel.empty:
        st.warning("No publisher headlines are available right now. Check source status on the Multi-Source News page and try again.")
    else:
        a,b,c,d = st.columns(4)
        a.metric("Headlines", len(intel))
        b.metric("High priority", int((intel["Priority"] == "High").sum()))
        c.metric("Positive wording", int((intel["Sentiment"] == "Positive").sum()))
        d.metric("Negative wording", int((intel["Sentiment"] == "Negative").sum()))
        # Detect new high-priority headlines against the prior refresh in this browser session.
        current = set(intel.loc[intel["Priority"] == "High", "Link"].dropna().astype(str))
        previous = st.session_state.get("v21_seen_high_priority", None)
        if previous is not None:
            new_links = current - previous
            if new_links:
                st.warning(f"🔔 {len(new_links)} new high-priority headline(s) since the previous V21 refresh.")
                st.dataframe(intel[intel["Link"].astype(str).isin(new_links)][["Headline","Source","Priority score","Sentiment","Link"]], use_container_width=True, hide_index=True,
                    column_config={"Link": st.column_config.LinkColumn("Original article", display_text="Open")})
            else:
                st.success("No new high-priority headlines since the previous V21 refresh.")
        else:
            st.info("Breaking-headline comparison starts after the next refresh in this browser session.")
        st.session_state["v21_seen_high_priority"] = current
        t1,t2,t3,t4 = st.tabs(["News intelligence", "Sector intelligence", "Global market snapshot", "Correlation & methodology"])
        with t1:
            st.subheader("Ranked news and sentiment")
            st.caption("Priority is a rules-based attention score using headline terms, source weighting and publication freshness. Sentiment is headline wording only; it does not measure the full article or market reaction.")
            priorities = ["All", "High", "Medium", "Low"]
            selected = st.selectbox("Priority filter", priorities, key="v21_priority_filter")
            view = intel if selected == "All" else intel[intel["Priority"] == selected]
            cols = [x for x in ["Headline","Source","Published (UTC)","Sentiment","Priority score","Priority","Potential sectors","Impact Topic","Link"] if x in view.columns]
            st.dataframe(view[cols], use_container_width=True, hide_index=True,
                column_config={"Link": st.column_config.LinkColumn("Original article", display_text="Open source")})
        with t2:
            st.subheader("Sector intelligence")
            sector_rows=[]
            for sector in ["Banking","IT","Pharma","Auto","FMCG","Energy","Metals"]:
                subset=intel[intel["Potential sectors"].str.contains(sector, case=False, na=False)]
                sector_rows.append({"Sector":sector,"Related headlines":len(subset),"High priority":int((subset["Priority"]=="High").sum()) if not subset.empty else 0,
                                    "Tone": "Positive" if int((subset["Sentiment"]=="Positive").sum())>int((subset["Sentiment"]=="Negative").sum()) else "Negative" if int((subset["Sentiment"]=="Negative").sum())>int((subset["Sentiment"]=="Positive").sum()) else "Mixed / unclear"})
            st.dataframe(pd.DataFrame(sector_rows), use_container_width=True, hide_index=True)
            st.caption("Sector mapping is based on matched words and named entities; verify each original article before inferring sector impact.")
        with t3:
            st.subheader("Global and Indian cross-asset snapshot")
            st.caption("Secondary price feed: Yahoo Finance. This is separate from the multi-publisher news feeds and may be delayed, incomplete or unavailable.")
            if st.button("Load cross-asset prices", key="v21_prices"):
                st.session_state["v21_cross_asset"] = fetch_cross_asset_snapshot()
            snap = st.session_state.get("v21_cross_asset", pd.DataFrame())
            if snap is None or snap.empty:
                st.info("Press Load cross-asset prices to retrieve the latest available daily observations.")
            else:
                st.dataframe(snap, use_container_width=True, hide_index=True,
                    column_config={"Daily change %":st.column_config.NumberColumn("Daily change %",format="%.2f%%")})
        with t4:
            st.subheader("Cross-asset correlations")
            st.caption("Correlation uses daily percentage returns over the selected lookback. Correlation is not causation and can change sharply during market stress.")
            lookback = st.selectbox("Lookback", ["3mo","6mo","1y"], index=1, key="v21_corr_period")
            if st.button("Calculate correlation matrix", key="v21_corr"):
                st.session_state["v21_corr_matrix"] = correlation_matrix(lookback)
            corr = st.session_state.get("v21_corr_matrix", pd.DataFrame())
            if corr is not None and not corr.empty:
                st.dataframe(corr, use_container_width=True)
            else:
                st.info("Select a lookback and calculate the matrix. Symbols without sufficient data are omitted.")
    st.markdown("---")
    st.subheader("Unified intelligence coverage")
    st.write("V21 combines headline attention and sentiment with sector mapping and a separate cross-asset price context. Existing V17 technical scans and V15/V16 Upstox options modules remain separate panels; V21 does not fabricate a combined probability when those inputs are missing.")
    st.warning("Research support only — not a calibrated AI forecast, investment recommendation, or automatic order system. Verify source articles, timestamps, exchange data and risk before trading.")

if page=="Multi-Source News & Forex Factory":
    st.title("Multi-Source Market News & Forex Factory")
    st.caption("News headlines are aggregated from multiple India and international publishers. Forex Factory is used for its economic calendar and its curated News page is linked separately.")
    if st.button("Refresh all news sources", key="v19_refresh_news"):
        st.cache_data.clear()
    with st.spinner("Checking news publishers and economic calendar..."):
        news_df, source_status = fetch_all_news()
        ff_calendar, ff_error = fetch_forex_factory_calendar()
    impact_df = analyze_news_frame(news_df)
    a,b,c = st.columns(3)
    a.metric("Headlines loaded", len(news_df))
    b.metric("Publishers checked", len(source_status))
    c.metric("Sources responding", int(source_status["Status"].str.startswith("OK").sum()) if not source_status.empty else 0)
    tab_india, tab_global, tab_official, tab_impact, tab_fx, tab_status = st.tabs(["🇮🇳 India", "🌍 International", "🏛️ Official policy", "🧭 Potential market impact", "💱 Forex Factory calendar", "Source status"])
    def render_news(frame):
        if frame.empty:
            st.info("No headlines were returned by these feeds. Try refreshing later; publishers may change or temporarily block RSS access.")
            return
        for _, item in frame.iterrows():
            st.markdown(f"**[{item['Headline']}]({item['Link']})**")
            meta = f"{item['Source']} · {item['Published (UTC)'] or 'Publication time not supplied'}"
            st.caption(meta)
            if item["Summary"]:
                st.write(item["Summary"])
            st.divider()
    with tab_india:
        render_news(news_df[news_df.Category == "India"] if not news_df.empty else news_df)
    with tab_global:
        render_news(news_df[news_df.Category == "International"] if not news_df.empty else news_df)
    with tab_official:
        render_news(news_df[news_df.Category == "Official"] if not news_df.empty else news_df)
    with tab_impact:
        st.subheader("Potential Market Impact — explainable headline analysis")
        st.caption("V20 uses transparent keyword rules to tag possible topics and affected assets. This is a heuristic, not a trained AI model, forecast, or buy/sell signal.")
        if impact_df.empty:
            st.info("No headlines available to analyse. Refresh the feeds and try again.")
        else:
            topics = ["All topics"] + sorted(impact_df["Impact Topic"].dropna().unique().tolist())
            chosen_topic = st.selectbox("Filter by impact topic", topics, key="v20_impact_topic")
            view = impact_df if chosen_topic == "All topics" else impact_df[impact_df["Impact Topic"] == chosen_topic]
            show_cols = [c for c in ["Headline", "Source", "Category", "Published (UTC)", "Impact Topic", "Potentially Affected Assets", "Heuristic Bias", "Confidence", "Link"] if c in view.columns]
            st.dataframe(view[show_cols], use_container_width=True, hide_index=True,
                         column_config={"Link": st.column_config.LinkColumn("Original article", display_text="Open source")})
            with st.expander("How to interpret the impact tags"):
                st.markdown("- **Potentially affected assets** are examples to investigate, not guaranteed movers.\n- **Heuristic bias** describes the topic's typical transmission channel; actual direction depends on expectations and the full article.\n- **Confidence** reflects keyword-match strength only, not the probability of a market move.\n- Always open the original source and verify the event before making a decision.")
    with tab_fx:
        st.markdown(f"**Forex Factory curated News:** [{FOREX_FACTORY_NEWS}]({FOREX_FACTORY_NEWS})")
        st.caption("Forex Factory's curated News product is a separate web page; this integration does not pretend that its news stories are an RSS feed. Its public XML calendar is shown below when reachable.")
        if ff_error:
            st.warning("Forex Factory calendar unavailable: " + ff_error)
        elif ff_calendar.empty:
            st.info("The Forex Factory calendar feed returned no parseable events. Open the Forex Factory calendar directly if needed.")
        else:
            st.dataframe(ff_calendar, use_container_width=True, hide_index=True)
        st.markdown("[Open Forex Factory economic calendar](https://www.forexfactory.com/calendar)")
    with tab_status:
        st.dataframe(source_status, use_container_width=True, hide_index=True)
        st.caption("Feeds are best-effort public RSS/XML endpoints. A source can be temporarily unavailable, change its feed URL, or restrict automated access.")
    st.warning("Headlines are source material, not trading signals. Verify important events with the original publisher. RSS terms vary; this dashboard displays headlines, links and brief feed summaries for personal use.")

elif page=="Trading Terminal":
    st.title("Trading Terminal")
    st.caption("TradingView-inspired chart, technical indicators and market snapshot.")
    if data.empty: st.error("No price data. Check symbol, internet connection or interval.")
    else:
        r=data.iloc[-1]; prev=data.iloc[-2] if len(data)>1 else r
        pct=(r.Close/prev.Close-1)*100 if prev.Close else 0
        a,b,c,d,e=st.columns(5)
        a.metric("Last price",f"{r.Close:,.2f}",f"{pct:+.2f}%")
        b.metric("RSI",f"{r.RSI:.1f}" if pd.notna(r.RSI) else "—")
        c.metric("MACD",f"{r.MACD:.2f}")
        d.metric("ATR",f"{r.ATR:.2f}" if pd.notna(r.ATR) else "—")
        e.metric("Volume",f"{r.Volume:,.0f}")
        st.plotly_chart(price_chart(data,f"{symbol} | Candles, EMA & Volume"),use_container_width=True)
        with st.expander("Indicator data table"):
            st.dataframe(data[["Open","High","Low","Close","Volume","EMA20","EMA50","EMA200","RSI","MACD","ATR"]].tail(30),use_container_width=True)
    st.info("Yahoo Finance data can be delayed or unavailable. Use your broker for execution prices.")

elif page=="AI Prediction Engine":
    st.title("🧠 AI-Assisted Market Signal")
    st.caption("Transparent technical decision support with explainable indicators; this is not a trained ML forecast.")
    if data.empty:
        st.warning("Price data unavailable. Check the symbol and interval.")
    else:
        result = evaluate_signal(raw)
        if not result.get("ready"):
            st.warning(result.get("message", "Insufficient data."))
        else:
            news = get_news(symbol.replace(".NS", "").replace(".BO", "") + " stock India")
            ns, nlabel = sentiment(news)
            pcr = None
            option_file = st.file_uploader("Optional option-chain CSV for PCR context", type=["csv"], key="aiopt_v2")
            if option_file:
                try:
                    od, strike_col, ce_col, pe_col, _, _ = parse_options(option_file)
                    if ce_col and pe_col:
                        call_oi = pd.to_numeric(od[ce_col], errors="coerce").fillna(0).sum()
                        put_oi = pd.to_numeric(od[pe_col], errors="coerce").fillna(0).sum()
                        pcr = put_oi / call_oi if call_oi else None
                except Exception as exc:
                    st.warning(f"Could not read option-chain CSV: {exc}")
            color_icon = "🟢" if result["bias"] == "BULLISH" else "🔴" if result["bias"] == "BEARISH" else "🟡"
            st.markdown(f"<div class='card'><h2>{color_icon} {result['bias']} BIAS</h2><h3>Technical score: {result['score']:+d} · Heuristic confidence: {result['confidence']}%</h3></div>", unsafe_allow_html=True)
            a,b,c,d = st.columns(4)
            a.metric("Last close", f"₹{result['close']:,.2f}")
            b.metric("RSI (14)", f"{result['rsi']:.1f}" if np.isfinite(result['rsi']) else "—")
            c.metric("ADX (14)", f"{result['adx']:.1f}" if np.isfinite(result['adx']) else "—")
            d.metric("Relative volume", f"{result['relative_volume']:.2f}x" if np.isfinite(result['relative_volume']) else "—")
            st.subheader("Why this signal?")
            for reason in result["reasons"]: st.write("• " + reason)
            st.subheader("Context checks")
            x,y = st.columns(2)
            x.metric("Headline tone", nlabel, f"{ns:+d}")
            y.metric("Option PCR", f"{pcr:.2f}" if pcr is not None else "Not supplied")
            if result["levels"]:
                lv = result["levels"]
                st.subheader("Illustrative ATR-based levels")
                p,q,r,t = st.columns(4)
                p.metric("Reference entry", f"₹{lv['entry']:,.2f}")
                q.metric("Stop (1.5 ATR)", f"₹{lv['stop']:,.2f}")
                r.metric("Target 1 (2 ATR)", f"₹{lv['target_1']:,.2f}")
                t.metric("Target 2 (3 ATR)", f"₹{lv['target_2']:,.2f}")
            else:
                st.info("No directional trade levels: the technical score is neutral or ATR is unavailable.")
            st.subheader("Related headlines")
            if news.empty: st.info("News unavailable.")
            else:
                for _, item in news.head(8).iterrows(): st.markdown(f"- [{item.Headline}]({item.Link})")
            st.warning(result["warning"] + " News tone and PCR are shown as context and are not included in the technical score.")

elif page=="AI Market Intelligence":
    st.title("AI Market Intelligence | Breakout & Market Structure")
    st.caption("Rule-based analysis of the selected symbol and interval. This is decision support, not an ML prediction.")
    from market_intelligence import analyze_market_structure
    lookback = st.slider("Range lookback candles", 10, 100, 20, key="mi_lookback")
    if data.empty:
        st.warning("Price data unavailable. Check the symbol, interval and internet connection.")
    else:
        result = analyze_market_structure(data, lookback)
        if not result.get("ready"):
            st.info(result.get("message", "Analysis unavailable."))
        else:
            a,b,c,d = st.columns(4)
            a.metric("Market bias", result["bias"])
            b.metric("Range status", result["breakout"])
            c.metric("Support", f"₹{result['support']:,.2f}")
            d.metric("Resistance", f"₹{result['resistance']:,.2f}")
            e,f,g = st.columns(3)
            e.metric("RSI", f"{result['rsi']:.1f}" if np.isfinite(result["rsi"]) else "—")
            f.metric("ADX", f"{result['adx']:.1f}" if np.isfinite(result["adx"]) else "—")
            g.metric("Relative volume", f"{result['relative_volume']:.2f}x" if np.isfinite(result["relative_volume"]) else "—")
            chart_data = data.tail(lookback + 30)
            fig = go.Figure(go.Candlestick(x=chart_data.index, open=chart_data.Open, high=chart_data.High, low=chart_data.Low, close=chart_data.Close, name="Price"))
            fig.add_hline(y=result["support"], line_dash="dash", annotation_text="Lookback support")
            fig.add_hline(y=result["resistance"], line_dash="dash", annotation_text="Lookback resistance")
            fig.update_layout(template="plotly_dark", height=520, xaxis_rangeslider_visible=False, title=f"{symbol} | Market structure")
            st.plotly_chart(fig, use_container_width=True)
            st.subheader("Confluence checks")
            for reason in result["reasons"]:
                st.write("• " + reason)
            if result["levels"]:
                st.subheader("Reference levels")
                st.json({k: round(v, 2) for k, v in result["levels"].items()})
            st.warning(result["warning"])
            st.caption("Support/resistance use the previous lookback candles, excluding the current candle. A breakout label is based on the latest close, not an intrabar trigger.")

elif page=="AI Multi-Timeframe Scanner":
    st.title("AI Multi-Timeframe Scanner & Risk Sizer")
    st.caption("Compares rule-based technical context across daily and hourly candles. No orders are placed.")
    from multi_timeframe_engine import analyze_alignment, calculate_cash_risk
    scan_symbols = st.text_area("Symbols (comma separated)", "^NSEI,^NSEBANK,RELIANCE.NS,ICICIBANK.NS,SBIN.NS,TCS.NS")
    symbols = list(dict.fromkeys(x.strip().upper() for x in scan_symbols.split(",") if x.strip()))[:12]
    if st.button("Run multi-timeframe scan", type="primary"):
        scan_rows = []
        with st.spinner("Fetching daily and hourly candles..."):
            for ticker in symbols:
                daily = load_data(ticker, "1y", "1d")
                hourly = load_data(ticker, "60d", "1h")
                result = analyze_alignment({"1D": daily, "1H": hourly})
                if result["ready"]:
                    daily_result = result["timeframes"].get("1D", {})
                    hourly_result = result["timeframes"].get("1H", {})
                    scan_rows.append({"Symbol": ticker, "Alignment": result["overall"],
                                      "Daily": daily_result.get("bias", "Unavailable"),
                                      "Hourly": hourly_result.get("bias", "Unavailable"),
                                      "Daily RSI": round(daily_result.get("rsi", np.nan), 1) if daily_result.get("ready") else "—",
                                      "Daily score": daily_result.get("score", "—")})
                else:
                    scan_rows.append({"Symbol": ticker, "Alignment": "Unavailable", "Daily": "—", "Hourly": "—", "Daily RSI": "—", "Daily score": "—"})
        st.session_state["ati_v6_scan_rows"] = scan_rows
    if st.session_state.get("ati_v6_scan_rows"):
        scan_df = pd.DataFrame(st.session_state["ati_v6_scan_rows"])
        st.dataframe(scan_df, use_container_width=True, hide_index=True)
        st.download_button("Download scan CSV", scan_df.to_csv(index=False), "multi_timeframe_scan.csv", "text/csv")
    st.divider()
    st.subheader("Cash-equity position risk calculator")
    c1, c2, c3, c4 = st.columns(4)
    entry_input = c1.number_input("Entry price", min_value=0.01, value=100.0, step=1.0)
    stop_input = c2.number_input("Stop-loss price", min_value=0.01, value=98.0, step=1.0)
    capital_input = c3.number_input("Available capital (₹)", min_value=1.0, value=100000.0, step=5000.0)
    risk_input = c4.number_input("Risk per trade (%)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
    try:
        sizing = calculate_cash_risk(entry_input, stop_input, capital_input, risk_input)
        a, b, c = st.columns(3)
        a.metric("Suggested cash quantity", f"{sizing['quantity']:,} shares")
        b.metric("Risk budget", f"₹{sizing['risk_budget']:,.2f}")
        c.metric("Estimated loss at stop", f"₹{sizing['estimated_max_loss_before_costs']:,.2f}")
        st.caption(f"Estimated position value: ₹{sizing['estimated_position_value']:,.2f}. Fees, taxes, slippage, gaps and liquidity are excluded. Quantity is for cash-equity units only, not option lots or leveraged products.")
    except ValueError as exc:
        st.error(str(exc))
    st.warning("Scanner data comes from Yahoo Finance and may be delayed, incomplete or unavailable. Confirm symbols, timestamps and live prices with your broker. This tool does not generate guaranteed predictions or place trades.")

elif page=="Smart Money & Market Structure":
    st.title("Smart Money & Market Structure")
    st.caption("OHLCV-derived heuristics: liquidity sweeps, order-block candidates, fair-value gaps and approximate volume profile.")
    from smart_money_engine import (detect_liquidity_sweeps, detect_fair_value_gaps,
                                    detect_order_blocks, calculate_volume_profile,
                                    summarize_structure)
    if data.empty or len(data) < 35:
        st.warning("Not enough price history for this analysis. Choose a symbol and a longer history in the sidebar.")
    else:
        try:
            structure = summarize_structure(data)
            sweep = structure["sweep"]
            a, b, c, dcol = st.columns(4)
            a.metric("Latest candle", "Buy-side sweep" if sweep["high_sweep"] else "Sell-side sweep" if sweep["low_sweep"] else "No sweep")
            b.metric("FVG candidates", structure["fvg_count"])
            c.metric("Order-block candidates", structure["order_block_count"])
            dcol.metric("Volume POC (approx.)", f"₹{structure['poc_price']:,.2f}")
            st.subheader("Liquidity sweep context")
            st.write(sweep["interpretation"])
            if sweep["reference_high"] is not None:
                st.write(f"Prior rolling high: {sweep['reference_high']:.2f} · Prior rolling low: {sweep['reference_low']:.2f}")
            gaps = detect_fair_value_gaps(data)
            blocks = detect_order_blocks(data)
            left, right = st.columns(2)
            with left:
                st.subheader("Fair Value Gap candidates")
                if gaps.empty: st.info("No three-candle gap candidates in the selected history.")
                else: st.dataframe(gaps, use_container_width=True, hide_index=True)
            with right:
                st.subheader("Order-block candidates")
                if blocks.empty: st.info("No order-block candidates found by this heuristic.")
                else: st.dataframe(blocks, use_container_width=True, hide_index=True)
            st.subheader("Approximate volume profile")
            profile = calculate_volume_profile(data)
            fig = go.Figure(go.Bar(x=profile["Volume"], y=profile["Price"], orientation="h", name="Estimated volume"))
            fig.update_layout(template="plotly_dark", height=520, xaxis_title="Volume assigned to typical price", yaxis_title="Price", title=f"{symbol} | Approximate volume-at-price")
            st.plotly_chart(fig, use_container_width=True)
            st.download_button("Download volume profile CSV", profile.to_csv(index=False), "volume_profile.csv", "text/csv")
            st.warning(structure["warning"])
        except (ValueError, KeyError, TypeError) as exc:
            st.error(f"Could not calculate market structure: {exc}")

elif page=="AI Trade Confirmation Engine":
    st.title("AI Trade Confirmation Engine")
    st.caption("Rule-based confluence across timeframes and OHLCV market-structure clues. Analysis only; no orders are placed.")
    from trade_confirmation_engine import evaluate_trade_confluence, build_atr_trade_plan
    tf_options = st.multiselect("Timeframes to combine", ["1D", "1H", "15m"], default=["1D", "1H"])
    if st.button("Evaluate trade confluence", type="primary"):
        frames = {}
        fetch_specs = {"1D": ("1y", "1d"), "1H": ("60d", "1h"), "15m": ("30d", "15m")}
        with st.spinner("Fetching selected timeframe candles and evaluating confluence..."):
            for tf in tf_options:
                per, inter = fetch_specs[tf]
                frames[tf] = load_data(symbol, per, inter)
            try:
                result = evaluate_trade_confluence(frames)
                st.session_state["ati_v8_confirmation"] = result
            except (ValueError, KeyError, TypeError) as exc:
                st.session_state.pop("ati_v8_confirmation", None)
                st.error(str(exc))
    result = st.session_state.get("ati_v8_confirmation")
    if result:
        a, b, c, d = st.columns(4)
        a.metric("Setup assessment", result["bias"])
        b.metric("Setup rank", result["rank"])
        c.metric("Bullish points", result["long_score"])
        d.metric("Bearish points", result["short_score"])
        st.subheader("Timeframe readings")
        tf_rows = []
        for tf, reading in result["timeframes"].items():
            tf_rows.append({"Timeframe": tf, "Bias": reading.get("bias", "Unavailable"),
                            "Score": reading.get("score", "—"), "RSI": reading.get("rsi", "—")})
        st.dataframe(pd.DataFrame(tf_rows), use_container_width=True, hide_index=True)
        st.subheader("Confluence evidence")
        for reason in result["reasons"]:
            st.write("• " + reason)
        st.write("Latest liquidity sweep:", result["sweep"]["interpretation"])
        if result.get("latest_fvg"):
            st.write("Latest FVG candidate:", result["latest_fvg"])
        if result.get("latest_order_block"):
            st.write("Latest order-block candidate:", result["latest_order_block"])
        st.divider()
        st.subheader("ATR-based reference risk plan")
        ctx = result["context"]
        direction = "LONG" if result["long_score"] > result["short_score"] else "SHORT"
        p1, p2, p3 = st.columns(3)
        entry = p1.number_input("Entry reference", min_value=0.01, value=float(ctx["close"]), step=0.05)
        risk_budget = p2.number_input("Risk budget (₹)", min_value=1.0, value=1000.0, step=100.0)
        direction = p3.selectbox("Plan direction", [direction, "LONG" if direction == "SHORT" else "SHORT"])
        try:
            plan = build_atr_trade_plan(entry, ctx["atr"], direction, risk_budget)
            x1, x2, x3, x4 = st.columns(4)
            x1.metric("Stop reference", f"₹{plan['stop_loss']:,.2f}")
            x2.metric("Target reference", f"₹{plan['target']:,.2f}")
            x3.metric("Cash-equity quantity", f"{plan['quantity']:,}")
            x4.metric("Estimated risk", f"₹{plan['estimated_risk_before_costs']:,.2f}")
            st.caption(f"ATR: ₹{ctx['atr']:.2f} · Estimated position value: ₹{plan['estimated_position_value']:,.2f}. Quantity is for cash-equity shares only, not F&O lots; costs, slippage, gaps and liquidity are excluded.")
        except ValueError as exc:
            st.error(str(exc))
        st.warning(result["warning"])
    st.info("The engine requires at least 35 valid candles per selected timeframe. If an interval is unavailable from the data provider, deselect it and rerun.")

elif page=="Multi-Timeframe Analysis":
    st.title("Multi-Timeframe Trend Alignment")
    rows=[]
    for label,per,inter in [("1D","1y","1d"),("1W","5y","1wk"),("1H","60d","1h")]:
        dd=load_data(symbol,per,inter)
        if not dd.empty and len(dd)>30:
            di=add_indicators(dd); sc,_=score_trend(di); rr=di.iloc[-1]
            rows.append({"Timeframe":label,"Close":round(float(rr.Close),2),"RSI":round(float(rr.RSI),1),"Score":sc,
                         "Trend":"Bullish" if sc>=2 else "Bearish" if sc<=-2 else "Sideways"})
        else: rows.append({"Timeframe":label,"Close":"—","RSI":"—","Score":"—","Trend":"Unavailable"})
    st.dataframe(pd.DataFrame(rows),use_container_width=True)
    st.caption("Availability of intraday history depends on Yahoo Finance symbol and interval support.")

elif page=="Global Market News":
    st.title("Global Market News & Sentiment")
    query=st.text_input("Search news",symbol.replace(".NS","")+" stock market India")
    if st.button("Refresh news"): get_news.clear()
    news=get_news(query); sc,label=sentiment(news)
    st.metric("Simple headline tone",label,f"{sc:+d}")
    if news.empty: st.info("No headlines returned.")
    else:
        for _,r in news.iterrows(): st.markdown(f"**{r.Headline}**  \n{r.Published} · [Open source]({r.Link})")

elif page=="Index & Options Signal Desk":
    st.title("NIFTY / BANKNIFTY Index & Options Signal Desk")
    st.caption("OI-based context from a user-uploaded option-chain CSV. This page does not fetch or invent live option-chain quotes.")
    underlying = st.selectbox("Underlying", ["NIFTY 50", "BANKNIFTY", "FINNIFTY", "SENSEX"])
    spot = st.number_input("Current underlying spot (₹)", min_value=0.01, value=25000.0, step=50.0, key="oi_desk_spot")
    chain_file = st.file_uploader("Upload option-chain CSV for one expiry", type=["csv"], key="oi_desk_csv")
    if chain_file is not None:
        try:
            result = analyze_option_context(pd.read_csv(chain_file), float(spot))
            st.subheader(f"{underlying} · {result['bias']}")
            a,b,c,d = st.columns(4)
            a.metric("PCR", f"{result['pcr']:.3f}" if np.isfinite(result['pcr']) else "—")
            b.metric("ATM strike", f"{result['atm_strike']:,.0f}")
            c.metric("Put OI wall", f"{result['put_wall']:,.0f}" if np.isfinite(result['put_wall']) else "—")
            d.metric("Call OI wall", f"{result['call_wall']:,.0f}" if np.isfinite(result['call_wall']) else "—")
            e,f = st.columns(2)
            e.metric("Total Call OI", f"{result['call_oi_total']:,.0f}")
            f.metric("Total Put OI", f"{result['put_oi_total']:,.0f}")
            g,h = st.columns(2)
            g.metric("Estimated Max Pain", f"{result['max_pain']:,.0f}")
            h.metric("Spot vs ATM", f"{result['spot']-result['atm_strike']:+,.2f}")
            st.subheader("OI interpretation")
            for note in result["notes"]: st.write("• " + note)
            if result["call_oi_change"] is not None or result["put_oi_change"] is not None:
                x,y = st.columns(2)
                x.metric("Net Call OI change", f"{result['call_oi_change']:+,.0f}" if result['call_oi_change'] is not None else "Not supplied")
                y.metric("Net Put OI change", f"{result['put_oi_change']:+,.0f}" if result['put_oi_change'] is not None else "Not supplied")
            chain = result["chain"]; cols = result["columns"]
            oi_fig = go.Figure()
            oi_fig.add_bar(x=chain[cols["strike"]], y=chain[cols["ce_oi"]], name="Call OI")
            oi_fig.add_bar(x=chain[cols["strike"]], y=chain[cols["pe_oi"]], name="Put OI")
            oi_fig.add_vline(x=float(spot), line_dash="dash", annotation_text="Spot")
            oi_fig.update_layout(barmode="group", template="plotly_dark", title="Open Interest by strike", xaxis_title="Strike", yaxis_title="Open interest")
            st.plotly_chart(oi_fig, use_container_width=True)
            pain_fig = go.Figure(go.Scatter(x=result["curve"]["Settlement"], y=result["curve"]["Estimated payout"], mode="lines+markers"))
            pain_fig.add_vline(x=result["max_pain"], line_dash="dash", annotation_text="Estimated Max Pain")
            pain_fig.update_layout(template="plotly_dark", title="Estimated expiry payout curve", xaxis_title="Settlement price", yaxis_title="OI-weighted intrinsic payout")
            st.plotly_chart(pain_fig, use_container_width=True)
            st.warning(result["warning"])
            st.download_button("Download normalized option chain", chain.to_csv(index=False).encode("utf-8"), "normalized_option_chain.csv", "text/csv")
        except Exception as exc:
            st.error(f"Unable to analyze this option chain: {exc}")
    else:
        st.info("Upload a CSV containing Strike, CE_OI and PE_OI. Optional columns: CE_change_OI and PE_change_OI. Select the matching expiry and enter a current spot price from your broker.")

elif page=="Options & OI Analytics":
    st.title("Advanced Options Chain Intelligence")
    st.caption("Analyze a broker/provider CSV. This page does not claim live option-chain access.")
    f=st.file_uploader("Upload option-chain CSV", type=["csv"], key="optfull_v2")
    if f:
        try:
            od, cols = parse_chain(pd.read_csv(f))
            strike, ce, pe = cols["strike"], cols["ce_oi"], cols["pe_oi"]
            co=float(od[ce].fillna(0).sum()); po=float(od[pe].fillna(0).sum())
            pcr=po/co if co else np.nan
            mp, pain_curve=max_pain(od,strike,ce,pe)
            a,b,c,d=st.columns(4)
            a.metric("Total Call OI",f"{co:,.0f}"); b.metric("Total Put OI",f"{po:,.0f}")
            c.metric("Put-Call Ratio",f"{pcr:.3f}" if np.isfinite(pcr) else "—")
            d.metric("Estimated Max Pain",f"{mp:,.2f}")
            if cols["ce_change"] and cols["pe_change"]:
                call_change=float(od[cols["ce_change"]].sum()); put_change=float(od[cols["pe_change"]].sum())
                x,y=st.columns(2); x.metric("Call OI change",f"{call_change:+,.0f}"); y.metric("Put OI change",f"{put_change:+,.0f}")
                st.caption("OI change is interpreted exactly as supplied in the CSV; confirm whether provider values are net changes or raw figures.")
            chart=go.Figure()
            chart.add_bar(x=od[strike],y=od[ce],name="Call OI")
            chart.add_bar(x=od[strike],y=od[pe],name="Put OI")
            chart.update_layout(barmode="group",template="plotly_dark",title="Open Interest by Strike",xaxis_title="Strike",yaxis_title="Open interest")
            st.plotly_chart(chart,use_container_width=True)
            pc=go.Figure(go.Scatter(x=pain_curve["Settlement"],y=pain_curve["Estimated payout"],mode="lines+markers",name="Payout"))
            pc.add_vline(x=mp,line_dash="dash",annotation_text="Estimated Max Pain")
            pc.update_layout(template="plotly_dark",title="Estimated Expiry Payout by Settlement",xaxis_title="Settlement price",yaxis_title="OI-weighted intrinsic payout (not actual market P&L)")
            st.plotly_chart(pc,use_container_width=True)
            st.subheader("Optional Black–Scholes Greeks")
            if cols["ce_iv"] or cols["pe_iv"]:
                spot_default=float(data.Close.iloc[-1]) if not data.empty else float(od[strike].median())
                g1,g2,g3=st.columns(3)
                spot_in=g1.number_input("Underlying spot (₹)",min_value=0.01,value=spot_default,key="greek_spot")
                expiry_days=g2.number_input("Days to expiry",min_value=0.1,value=7.0,step=1.0,key="greek_days")
                rate=g3.number_input("Risk-free rate (%)",min_value=0.0,max_value=30.0,value=6.5,step=0.25,key="greek_rate")
                with_greeks=add_greeks(od,cols,float(spot_in),float(expiry_days),float(rate))
                st.dataframe(with_greeks,use_container_width=True)
                st.caption("Greeks are theoretical European Black–Scholes estimates. IV must be entered in percent (e.g. 18.5), and dividends, early exercise, volatility skew and market microstructure are not modeled.")
            else:
                st.info("To calculate Greeks, include CE_IV and/or PE_IV columns. IV should be expressed as a percentage.")
            st.subheader("Option-chain data")
            st.dataframe(od,use_container_width=True)
            st.download_button("Download analyzed option chain CSV",od.to_csv(index=False).encode("utf-8"),"option_chain_analysis.csv","text/csv")
        except Exception as ex:
            st.error(f"Could not process option-chain CSV: {ex}")
    else:
        st.info("Required columns: Strike, CE_OI, PE_OI. Optional: CE_change_OI, PE_change_OI, CE_LTP, PE_LTP, CE_IV, PE_IV. Values must correspond to the same underlying and expiry.")

elif page=="Options Strategy Planner":
    st.title("Options Strategy Planner")
    st.caption("Simplified expiry payoff calculator. Enter premiums manually from your broker.")
    strategy=st.selectbox("Strategy",["Bull Call Spread","Bear Put Spread","Long Call","Long Put"])
    spot=st.number_input("Current underlying price",min_value=.01,value=25000.0,step=100.0)
    k1=st.number_input("Primary strike",min_value=.01,value=spot,step=100.0)
    p1=st.number_input("Primary option premium",min_value=0.0,value=200.0,step=5.0)
    k2=st.number_input("Secondary strike (spread)",min_value=.01,value=spot+500,step=100.0)
    p2=st.number_input("Secondary option premium (spread)",min_value=0.0,value=100.0,step=5.0)
    lot=st.number_input("Lot size / quantity",min_value=1,value=25,step=1)
    low=max(0,spot*.8); high=spot*1.2
    prices=np.linspace(low,high,101)
    if strategy=="Bull Call Spread":
        pnl=(np.maximum(prices-k1,0)-p1-np.maximum(prices-k2,0)+p2)*lot
        debit=(p1-p2)*lot
    elif strategy=="Bear Put Spread":
        pnl=(np.maximum(k1-prices,0)-p1-np.maximum(k2-prices,0)+p2)*lot
        debit=(p1-p2)*lot
    elif strategy=="Long Call":
        pnl=(np.maximum(prices-k1,0)-p1)*lot; debit=p1*lot
    else:
        pnl=(np.maximum(k1-prices,0)-p1)*lot; debit=p1*lot
    fig=go.Figure(); fig.add_trace(go.Scatter(x=prices,y=pnl,mode="lines",name="Expiry P&L",fill="tozeroy"))
    fig.add_hline(y=0,line_dash="dash"); fig.add_vline(x=spot,line_dash="dot",annotation_text="Current price")
    fig.update_layout(title=f"{strategy} — estimated expiry payoff",xaxis_title="Underlying at expiry",yaxis_title="P&L (₹)",template="plotly_dark",height=480)
    st.plotly_chart(fig,use_container_width=True)
    a,b=st.columns(2); a.metric("Net debit / premium paid",f"₹{debit:,.2f}"); b.metric("Best P&L in displayed range",f"₹{np.max(pnl):,.2f}")
    st.caption("Simplified payoff only; excludes brokerage, taxes, slippage, margin, exercise/assignment and contract-specific rules. Verify leg direction and expiry with your broker.")

elif page=="Stock Scanner":
    st.title("Indian Stock Scanner")
    default=["RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","INFY.NS","ITC.NS","LT.NS","BHARTIARTL.NS","AXISBANK.NS"]
    symbols=st.text_area("Symbols (comma separated)",", ".join(default)).split(",")
    if st.button("Run scanner"):
        results=[]; progress=st.progress(0); symbols=[s.strip().upper() for s in symbols if s.strip()]
        for i,s in enumerate(symbols):
            dd=load_data(s,"6mo","1d")
            if not dd.empty and len(dd)>30:
                di=add_indicators(dd); sc,_=score_trend(di); rr=di.iloc[-1]
                results.append({"Symbol":s,"Price":round(float(rr.Close),2),"RSI":round(float(rr.RSI),1),"Score":sc,
                                "Bias":"Bullish" if sc>=2 else "Bearish" if sc<=-2 else "Neutral"})
            progress.progress((i+1)/max(len(symbols),1))
        if results: st.dataframe(pd.DataFrame(results).sort_values("Score",ascending=False),use_container_width=True)
        else: st.warning("No scanner data returned.")

elif page=="Support & Resistance":
    st.title("Support & Resistance")
    if data.empty: st.warning("Price data unavailable.")
    else:
        n=st.slider("Lookback candles",20,min(200,len(data)),min(60,len(data)))
        recent=data.tail(n); support=float(recent.Low.min()); resistance=float(recent.High.max())
        pivot=(support+resistance+float(recent.Close.iloc[-1]))/3
        a,b,c=st.columns(3); a.metric("Support",f"{support:,.2f}"); b.metric("Pivot",f"{pivot:,.2f}"); c.metric("Resistance",f"{resistance:,.2f}")
        fig=go.Figure(go.Candlestick(x=recent.index,open=recent.Open,high=recent.High,low=recent.Low,close=recent.Close))
        for val,name in [(support,"Support"),(pivot,"Pivot"),(resistance,"Resistance")]: fig.add_hline(y=val,annotation_text=name)
        fig.update_layout(template="plotly_dark",height=550,xaxis_rangeslider_visible=False)
        st.plotly_chart(fig,use_container_width=True)
        st.caption("Levels are lookback extremes and a simple pivot estimate, not guaranteed turning points.")

elif page=="Risk & Position Planner":
    st.title("Risk, Reward & Position Size Calculator")
    a,b=st.columns(2)
    with a:
        capital=st.number_input("Trading capital (₹)",min_value=1000.0,value=100000.0,step=5000.0)
        riskpct=st.number_input("Risk per trade (%)",min_value=.1,max_value=5.0,value=1.0,step=.1)
        entry=st.number_input("Entry price",min_value=.01,value=float(data.Close.iloc[-1]) if not data.empty else 100.0)
    with b:
        stop=st.number_input("Stop-loss price",min_value=0.0,value=entry*.98)
        target=st.number_input("Target price",min_value=0.0,value=entry*1.04)
    risk=capital*riskpct/100; per=abs(entry-stop); qty=int(risk/per) if per else 0
    rr=abs(target-entry)/per if per else 0
    x,y,z=st.columns(3); x.metric("Planned risk",f"₹{risk:,.2f}"); y.metric("Indicative quantity",f"{qty:,}"); z.metric("Reward / Risk",f"1 : {rr:.2f}")
    st.caption("Excludes brokerage, taxes, slippage, lot size, margin and gap risk.")

elif page=="Price Alerts":
    st.title("Manual Price Alerts")
    st.caption("Alerts are checked when this page reruns; this app does not run a background monitor.")
    if "alerts_v10" not in st.session_state: st.session_state.alerts_v10=[]
    with st.form("alert_form"):
        alert_symbol=st.text_input("Symbol",symbol)
        condition=st.selectbox("Condition",["Price above","Price below"])
        level=st.number_input("Alert price",min_value=.01,value=float(data.Close.iloc[-1]) if not data.empty else 100.0)
        submitted=st.form_submit_button("Add alert")
        if submitted: st.session_state.alerts_v10.append({"symbol":alert_symbol.strip().upper(),"condition":condition,"level":float(level)})
    if st.button("Check alerts now"):
        for al in st.session_state.alerts_v10:
            ad=load_data(al["symbol"],"5d","1d")
            if not ad.empty:
                current=float(ad.Close.iloc[-1])
                hit=current>=al["level"] if al["condition"]=="Price above" else current<=al["level"]
                if hit: st.success(f"TRIGGERED: {al['symbol']} at {current:.2f} — {al['condition']} {al['level']:.2f}")
                else: st.info(f"{al['symbol']}: current {current:.2f}; condition not met.")
            else: st.warning(f"Could not fetch {al['symbol']}.")
    if st.session_state.alerts_v10:
        st.dataframe(pd.DataFrame(st.session_state.alerts_v10),use_container_width=True)
        if st.button("Clear all alerts"): st.session_state.alerts_v10=[]; st.rerun()
    else: st.info("No alerts added yet.")

elif page=="FII/DII Activity":
    st.title("FII / DII Activity Tracker")
    st.write("Upload official exchange or trusted-provider data. No institutional flow values are fabricated.")
    f=st.file_uploader("FII/DII CSV",type=["csv"],key="fiidii")
    if f:
        fd=pd.read_csv(f); st.dataframe(fd,use_container_width=True)
        nums=fd.select_dtypes(include=np.number)
        if not nums.empty:
            st.subheader("Numeric data overview")
            st.dataframe(nums.describe().T,use_container_width=True)
        st.caption("Confirm date, units, cash/derivatives segment and buy/sell column definitions.")

elif page == "TradingView Chart":

    import requests
    import pandas as pd
    import plotly.graph_objects as go

    from plotly.subplots import make_subplots
    from urllib.parse import quote
    from datetime import datetime, timedelta

    st.title("🚀 AI Trade Intelligence - Advanced Chart")

    st.caption(
        "Powered by Upstox Market Data | "
        "Professional Candlestick Trading Terminal"
    )

    # --------------------------------
    # UPSTOX CONNECTION
    # --------------------------------

    token = st.secrets.get("UPSTOX_ACCESS_TOKEN", "")

    if not token:
        st.error("Upstox access token not found.")
        st.stop()

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # --------------------------------
    # CHART SETTINGS
    # --------------------------------

    col1, col2 = st.columns(2)

    with col1:

        instrument_key = st.selectbox(
            "Select Instrument",
            [
                "NSE_INDEX|Nifty 50",
                "NSE_INDEX|Nifty Bank",
                "NSE_INDEX|India VIX"
            ]
        )

    with col2:

        timeframe = st.selectbox(
            "Timeframe",
            [
                "1m",
                "5m",
                "15m",
                "30m",
                "1h",
                "1D"
            ],
            index=1
        )

    show_ema = st.checkbox(
        "Show EMA 20 and EMA 50",
        value=True
    )

    # --------------------------------
    # FETCH UPSTOX CANDLES
    # --------------------------------

    if st.button("Fetch Market Chart", type="primary"):

        try:

            encoded_key = quote(
                instrument_key,
                safe=""
            )

            if timeframe == "1D":

                to_date = datetime.now().date()

                from_date = (
                    to_date - timedelta(days=90)
                )

                url = (
                    "https://api.upstox.com/v3/"
                    f"historical-candle/{encoded_key}/"
                    f"days/1/{to_date}/{from_date}"
                )

            else:

                if timeframe == "1h":

                    unit = "hours"
                    interval = "1"

                else:

                    unit = "minutes"
                    interval = timeframe.replace("m", "")

                url = (
                    "https://api.upstox.com/v3/"
                    "historical-candle/intraday/"
                    f"{encoded_key}/{unit}/{interval}"
                )

            response = requests.get(
                url,
                headers=headers,
                timeout=20
            )

            if response.status_code != 200:

                st.error(
                    f"Upstox API Error: "
                    f"{response.status_code}"
                )

                st.code(response.text)

                st.stop()

            result = response.json()

            candles = result.get(
                "data", {}
            ).get("candles", [])

            if not candles:

                st.warning(
                    "No candle data available for this instrument."
                )

                st.stop()

            # --------------------------------
            # DATAFRAME
            # --------------------------------

            df = pd.DataFrame(
                candles,
                columns=[
                    "Timestamp",
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Volume",
                    "OI"
                ]
            )

            df["Timestamp"] = pd.to_datetime(
                df["Timestamp"]
            )

            df = df.sort_values(
                "Timestamp"
            ).reset_index(drop=True)

            numeric_columns = [
                "Open",
                "High",
                "Low",
                "Close",
                "Volume"
            ]

            df[numeric_columns] = df[
                numeric_columns
            ].apply(pd.to_numeric)

            # --------------------------------
            # TECHNICAL INDICATORS
            # --------------------------------

            df["EMA20"] = df["Close"].ewm(
                span=20,
                adjust=False
            ).mean()

            df["EMA50"] = df["Close"].ewm(
                span=50,
                adjust=False
            ).mean()

            # --------------------------------
            # MARKET INFORMATION
            # --------------------------------

            latest = df.iloc[-1]

            st.subheader(
                f"{instrument_key} Market Overview"
            )

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Latest Close",
                f"{latest['Close']:,.2f}"
            )

            c2.metric(
                "Open",
                f"{latest['Open']:,.2f}"
            )

            c3.metric(
                "Day High",
                f"{latest['High']:,.2f}"
            )

            c4.metric(
                "Day Low",
                f"{latest['Low']:,.2f}"
            )

            # --------------------------------
            # ADVANCED CANDLESTICK CHART
            # --------------------------------

            fig = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.04,
                row_heights=[0.75, 0.25]
            )

            fig.add_trace(

                go.Candlestick(
                    x=df["Timestamp"],
                    open=df["Open"],
                    high=df["High"],
                    low=df["Low"],
                    close=df["Close"],
                    name="Price"
                ),

                row=1,
                col=1
            )

            # EMA INDICATORS

            if show_ema:

                fig.add_trace(

                    go.Scatter(
                        x=df["Timestamp"],
                        y=df["EMA20"],
                        name="EMA 20",
                        line=dict(
                            color="#00D9FF",
                            width=1.5
                        )
                    ),

                    row=1,
                    col=1
                )

                fig.add_trace(

                    go.Scatter(
                        x=df["Timestamp"],
                        y=df["EMA50"],
                        name="EMA 50",
                        line=dict(
                            color="#FFA500",
                            width=1.5
                        )
                    ),

                    row=1,
                    col=1
                )
            # ======================================
        # RSI CHART
        # ======================================
        #  if show_rsi:

            fig.add_trace(
                go.Scatter(
                    x=df["Timestamp"],
                    y=df["RSI"],
                    name="RSI 14",
                    line=dict(width=2)
                ),
                row=3,
                col=1
            )

            fig.add_hline(
                y=70,
                line_dash="dash",
                row=3,
                col=1
            )

            fig.add_hline(
                y=30,
                line_dash="dash",
                row=3,
                col=1
            )

        # ======================================
        # MACD CHART
        # ======================================
        #  if show_macd:

            fig.add_trace(
                go.Scatter(
                    x=df["Timestamp"],
                    y=df["MACD"],
                    name="MACD",
                ),
                row=4,
                col=1
            )

            fig.add_trace(
                go.Scatter(
                    x=df["Timestamp"],
                    y=df["MACD_Signal"],
                    name="MACD Signal",
                ),
                row=4,
                col=1
            )

            fig.add_trace(
                go.Bar(
                    x=df["Timestamp"],
                    y=df["MACD_Histogram"],
                    name="MACD Histogram",
                ),
                row=4,
                col=1
            )
            # VOLUME

            fig.add_trace(

                go.Bar(
                    x=df["Timestamp"],
                    y=df["Volume"],
                    name="Volume",
                    marker_color="#2962FF"
                ),

                row=2,
                col=1
            )

            # CHART DESIGN

            fig.update_layout(

                template="plotly_dark",

                height=750,

                title=(
                    f"{instrument_key} | {timeframe} "
                    "Advanced Candlestick Chart"
                ),

                xaxis_rangeslider_visible=False,

                hovermode="x unified",

                legend=dict(
                    orientation="h",
                    y=1.02,
                    x=0
                ),

                margin=dict(
                    l=10,
                    r=10,
                    t=70,
                    b=10
                )
            )

            fig.update_yaxes(
                title_text="Price",
                row=1,
                col=1
            )

            fig.update_yaxes(
                title_text="Volume",
                row=2,
                col=1
            )

            st.plotly_chart(
    fig,
    use_container_width=True,
    config={
        "responsive": True,
        "displayModeBar": True,
        "scrollZoom": True
    }
)

            # --------------------------------
            # CANDLE DATA
            # --------------------------------

            with st.expander(
                "View Raw Market Data"
            ):

                st.dataframe(
                    df.tail(50),
                    use_container_width=True
                )

            st.success(
                "Upstox market chart loaded successfully."
            )

        except Exception as e:

            st.error(
                f"Chart loading error: {e}"
            )

elif page == "Market Overview":

    st.title("Market Overview")

    # ==========================================
    # LIVE UPSTOX MARKET FEED
    # ==========================================

    from live_market_feed import (
        start_live_feed,
        get_market_data
    )

    st.subheader("🔴 Live Market Intelligence")

    if st.button("Start Live Market Feed"):
        result = start_live_feed()
        st.info(result)

    market = get_market_data()

    if market:

        st.success("Connected to Live Market Feed")

        st.caption(
            f"Last update: {market.get('last_update', 'Waiting...')}"
        )

        def get_index_price(symbol):

            data = market.get(symbol, {})

            ltpc = (
                data.get("fullFeed", {})
                .get("indexFF", {})
                .get("ltpc", {})
            )

            ltp = ltpc.get("ltp")
            cp = ltpc.get("cp")

            if ltp is not None and cp is not None and cp != 0:

                change = ((ltp - cp) / cp) * 100

                return ltp, change

            return None, None

        nifty, nifty_change = get_index_price(
            "NSE_INDEX|Nifty 50"
        )

        bank, bank_change = get_index_price(
            "NSE_INDEX|Nifty Bank"
        )

        vix, vix_change = get_index_price(
            "NSE_INDEX|India VIX"
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "NIFTY 50",
                f"{nifty:,.2f}" if nifty is not None else "Waiting",
                f"{nifty_change:+.2f}%" if nifty_change is not None else None
            )

        with col2:

            st.metric(
                "BANK NIFTY",
                f"{bank:,.2f}" if bank is not None else "Waiting",
                f"{bank_change:+.2f}%" if bank_change is not None else None
            )

        with col3:

            st.metric(
                "INDIA VIX",
                f"{vix:,.2f}" if vix is not None else "Waiting",
                f"{vix_change:+.2f}%" if vix_change is not None else None
            )

        with st.expander("View Raw Live Market Data"):

            st.json(market)

    else:

        st.info("Waiting for live market data.")

    # ==========================================
    # INDIAN & GLOBAL MARKET OVERVIEW
    # EXISTING SECTION - PRESERVED
    # ==========================================

    st.title("Indian & Global Market Overview")

    st.caption(
        "Indicative snapshots from Yahoo Finance. Quotes may be delayed."
    )

    market_symbols = {

        "NIFTY 50": "^NSEI",
        "SENSEX": "^BSESN",
        "BANK NIFTY": "^NSEBANK",
        "NIFTY IT": "^CNXIT",
        "S&P 500": "^GSPC",
        "NASDAQ": "^IXIC",
        "DOW JONES": "^DJI",
        "GOLD": "GC=F",
        "CRUDE OIL": "CL=F",
        "USD/INR": "INR=X"

    }

    rows = []

    with st.spinner("Fetching market snapshots..."):

        for name, ticker in market_symbols.items():

            q = load_data(ticker, "5d", "1d")

            if not q.empty:

                latest = float(q.Close.iloc[-1])

                previous = (
                    float(q.Close.iloc[-2])
                    if len(q) > 1
                    else latest
                )

                change = (
                    (latest / previous - 1) * 100
                    if previous
                    else 0
                )

                rows.append({

                    "Market": name,
                    "Last": round(latest, 2),
                    "Change %": round(change, 2),

                    "Direction": (
                        "▲" if change > 0
                        else "▼" if change < 0
                        else "—"
                    )

                })

            else:

                rows.append({

                    "Market": name,
                    "Last": "Unavailable",
                    "Change %": "—",
                    "Direction": "—"

                })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True
    )

    st.info(
        "This is a convenience snapshot, not an exchange-grade live feed. "
        "Verify prices with your broker."
    )
    # ==========================================

    # HISTORICAL MARKET CHARTS
    # ==========================================

    st.divider()

    st.subheader("📊 Historical Market Analysis")

    from historical_market_data import get_historical_data
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    col1, col2 = st.columns(2)

    with col1:
        selected_market = st.selectbox(
            "Select Market",
            ["NIFTY 50", "BANK NIFTY"]
        )

    with col2:
        selected_timeframe = st.selectbox(
            "Select Timeframe",
            ["Daily", "30 Minutes", "15 Minutes", "5 Minutes", "1 Minute"]
        )

    market_keys = {
        "NIFTY 50": "NSE_INDEX|Nifty 50",
        "BANK NIFTY": "NSE_INDEX|Nifty Bank"
    }

    timeframes = {
        "Daily": ("days", "1"),
        "30 Minutes": ("minutes", "30"),
        "15 Minutes": ("minutes", "15"),
        "5 Minutes": ("minutes", "5"),
        "1 Minute": ("minutes", "1")
    }
    st.markdown("### Technical Indicators")

    indicator_col1, indicator_col2, indicator_col3 = st.columns(3)

    with indicator_col1:
        show_ema = st.checkbox("EMA 20 & 50", value=True)
        show_rsi = st.checkbox("RSI (14)", value=True)

    with indicator_col2:
        show_macd = st.checkbox("MACD", value=True)
        show_vwap = st.checkbox("VWAP", value=False)

    with indicator_col3:
        show_bollinger = st.checkbox("Bollinger Bands", value=True)

    if st.button("Load Historical Chart"):

        unit, interval = timeframes[selected_timeframe]

        with st.spinner("Loading historical market data..."):

            df = get_historical_data(
                instrument_key=market_keys[selected_market],
                unit=unit,
                interval=interval,
                days=30
            )

        if df is not None and not df.empty:
            # ======================================
            # TECHNICAL INDICATOR CALCULATIONS
            # ======================================

            from ta.trend import EMAIndicator, MACD
            from ta.momentum import RSIIndicator
            from ta.volatility import BollingerBands

            df["EMA_20"] = EMAIndicator(
                close=df["Close"], window=20
            ).ema_indicator()

            df["EMA_50"] = EMAIndicator(
                close=df["Close"], window=50
            ).ema_indicator()

            df["RSI"] = RSIIndicator(
                close=df["Close"], window=14
            ).rsi()

            macd_indicator = MACD(close=df["Close"])

            df["MACD"] = macd_indicator.macd()
            df["MACD_Signal"] = macd_indicator.macd_signal()
            df["MACD_Histogram"] = macd_indicator.macd_diff()

            bb = BollingerBands(close=df["Close"], window=20)

            df["BB_Upper"] = bb.bollinger_hband()
            df["BB_Lower"] = bb.bollinger_lband()

            # VWAP calculation, reset each trading day
            typical_price = (
                df["High"] + df["Low"] + df["Close"]
            ) / 3

            daily_group = df["Timestamp"].dt.date

            cumulative_volume = df["Volume"].groupby(
                daily_group
            ).cumsum()

            cumulative_value = (
                typical_price * df["Volume"]
            ).groupby(daily_group).cumsum()

            df["VWAP"] = (
                cumulative_value / cumulative_volume.replace(0, float("nan"))
            )

            st.success("Historical data loaded successfully!")

            fig = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                row_heights=[0.75, 0.25]
            )

            fig.add_trace(
                go.Candlestick(
                    x=df["Timestamp"],
                    open=df["Open"],
                    high=df["High"],
                    low=df["Low"],
                    close=df["Close"],
                    name="Price"
                ),
                row=1,
                col=1
            )
            # ======================================
            # DISPLAY TECHNICAL INDICATORS
            # ======================================

            if show_ema:

                fig.add_trace(
                    go.Scatter(
                        x=df["Timestamp"],
                        y=df["EMA_20"],
                        name="EMA 20",
                        line=dict(width=2)
                    ),
                    row=1, col=1
                )

                fig.add_trace(
                    go.Scatter(
                        x=df["Timestamp"],
                        y=df["EMA_50"],
                        name="EMA 50",
                        line=dict(width=2)
                    ),
                    row=1, col=1
                )

            if show_vwap:

                fig.add_trace(
                    go.Scatter(
                        x=df["Timestamp"],
                        y=df["VWAP"],
                        name="VWAP",
                        line=dict(width=2)
                    ),
                    row=1, col=1
                )

            if show_bollinger:

                fig.add_trace(
                    go.Scatter(
                        x=df["Timestamp"],
                        y=df["BB_Upper"],
                        name="Bollinger Upper",
                        line=dict(dash="dot")
                    ),
                    row=1, col=1
                )

                fig.add_trace(
                    go.Scatter(
                        x=df["Timestamp"],
                        y=df["BB_Lower"],
                        name="Bollinger Lower",
                        line=dict(dash="dot")
                    ),
                    row=1, col=1
                )

            fig.add_trace(
                go.Bar(
                    x=df["Timestamp"],
                    y=df["Volume"],
                    name="Volume"
                ),
                row=2,
                col=1
            )

            fig.update_layout(
                title=f"{selected_market} Historical Chart",
                height=900,
                xaxis_rangeslider_visible=False,
                template="plotly_dark"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            st.subheader("Historical OHLC Data")

            st.dataframe(
                df.tail(20),
                use_container_width=True,
                hide_index=True
            )

        else:

            st.warning(
                "Historical data unavailable. Please check your Upstox connection."
            )

elif page=="Professional Market Dashboard":
    st.title("Professional Market Dashboard")
    st.caption("A consolidated market pulse using Yahoo Finance daily data. Quotes may be delayed; verify with your broker.")
    with st.spinner("Loading index and sector snapshots..."):
        idx = fetch_change({"NIFTY 50":"^NSEI", "NIFTY Bank":"^NSEBANK", "NIFTY IT":"^CNXIT", "S&P 500":"^GSPC", "NASDAQ":"^IXIC", "Gold":"GC=F", "USD/INR":"INR=X"})
        sectors = fetch_change(SECTOR_SYMBOLS)
    if not idx.empty:
        cols=st.columns(min(4,len(idx)))
        for i,(_,row) in enumerate(idx.iterrows()):
            cols[i%len(cols)].metric(row["Name"], f"{row['Last']:,.2f}", f"{row['Day %']:+.2f}%")
        st.subheader("Market snapshot")
        st.dataframe(idx.rename(columns={"Day %":"Day Change %"}).style.format({"Last":"{:,.2f}","Day Change %":"{:+.2f}%","5D %":"{:+.2f}%"}),use_container_width=True,hide_index=True)
    else: st.warning("Index snapshot unavailable. Check internet connectivity or try again later.")
    st.subheader("Sector leaders and laggards")
    if not sectors.empty:
        sectors=sectors.sort_values("5D %",ascending=False)
        st.dataframe(sectors.style.format({"Last":"{:,.2f}","Day %":"{:+.2f}%","5D %":"{:+.2f}%"}),use_container_width=True,hide_index=True)
        fig=go.Figure(go.Bar(x=sectors["5D %"],y=sectors["Name"],orientation="h")); fig.update_layout(template="plotly_dark",title="Sector performance – 5 sessions",height=420)
        st.plotly_chart(fig,use_container_width=True)
    else: st.info("Sector data is currently unavailable.")
    st.info("This dashboard is an informational overview, not a real-time exchange feed or a trade recommendation.")

elif page=="Market Breadth & Sector Strength":
    st.title("Market Breadth & Sector Strength")
    st.caption("Breadth is calculated from the configured sample of large-cap stocks; it is not full-market NSE breadth.")
    if st.button("Refresh breadth and sector data",type="primary"):
        st.cache_data.clear()
    with st.spinner("Checking constituent prices..."):
        breadth=fetch_change(BREADTH_SYMBOLS)
        sectors=fetch_change(SECTOR_SYMBOLS)
    if not breadth.empty:
        adv=int((breadth["Day %"]>0).sum()); dec=int((breadth["Day %"]<0).sum()); unchanged=len(breadth)-adv-dec
        a,b,c,d=st.columns(4); a.metric("Advancers",adv); b.metric("Decliners",dec); c.metric("Unchanged",unchanged); d.metric("Advance / Decline",f"{adv/max(dec,1):.2f}")
        breadth["Bias"]=np.where(breadth["Day %"]>0,"Advancing",np.where(breadth["Day %"]<0,"Declining","Flat"))
        st.subheader("Sample stock breadth")
        st.dataframe(breadth.sort_values("Day %",ascending=False).style.format({"Last":"{:,.2f}","Day %":"{:+.2f}%","5D %":"{:+.2f}%"}),use_container_width=True,hide_index=True)
    else: st.warning("Could not retrieve sample stock prices.")
    if not sectors.empty:
        st.subheader("Sector strength ranking")
        st.dataframe(sectors.sort_values("5D %",ascending=False).style.format({"Last":"{:,.2f}","Day %":"{:+.2f}%","5D %":"{:+.2f}%"}),use_container_width=True,hide_index=True)

elif page=="Market Alerts":
    st.title("Market Price Alerts")
    st.caption("Alerts are checked when this page is opened/refreshed. They are not push notifications and require the app to be running.")
    with st.form("create_price_alert"):
        a,b,c=st.columns(3)
        alert_symbol=a.text_input("Yahoo Finance symbol",symbol).strip().upper()
        condition=b.selectbox("Trigger when price is",["Above","Below"])
        target=c.number_input("Target price",min_value=0.01,value=100.0,step=1.0)
        submitted=st.form_submit_button("Save alert")
        if submitted:
            add_alert(alert_symbol,condition,target); st.success("Alert saved locally.")
    if st.button("Check active alerts now",type="primary"):
        fired=check_alerts()
        if fired: st.success(f"{len(fired)} alert(s) triggered."); st.dataframe(pd.DataFrame(fired),use_container_width=True,hide_index=True)
        else: st.info("No active alert triggered, or price data was unavailable.")
    alerts=list_alerts()
    if not alerts.empty:
        st.subheader("Saved alerts")
        st.dataframe(alerts,use_container_width=True,hide_index=True)
        active=alerts[alerts.active==1]
        if not active.empty:
            chosen=st.selectbox("Select alert to deactivate",active.id.tolist())
            if st.button("Deactivate selected alert"):
                remove_alert(chosen); st.rerun()

elif page=="ML Prediction & Backtesting":
    st.title("ML Prediction & Historical Backtesting")
    st.caption("Experimental logistic-regression model using OHLCV-derived features. Chronological holdout; no random shuffle.")
    st.warning("Research only: historical test results do not predict future returns. Yahoo Finance data may be delayed or incomplete. This page does not place orders.")
    a,b,c,d=st.columns(4)
    train_fraction=a.slider("Training data share",0.60,0.85,0.70,0.05)
    long_threshold=b.slider("Long probability threshold",0.51,0.80,0.55,0.01)
    short_threshold=c.slider("Short threshold",0.20,0.49,0.45,0.01)
    cost_bps=d.number_input("Estimated cost per exposure change (bps)",min_value=0.0,max_value=200.0,value=10.0,step=1.0)
    allow_short=st.checkbox("Allow short signals in backtest",value=False,help="Shorting may not be available for every instrument or account. Results are theoretical.")
    neutral_band=st.number_input("Next-candle neutral band (%)",min_value=0.0,max_value=2.0,value=0.0,step=0.05)/100
    st.caption(f"Selected data: {symbol} · {period} · {interval} · {len(raw):,} candles")
    if st.button("Train model and run out-of-sample backtest",type="primary"):
        if raw.empty:
            st.error("No OHLCV history is available for this symbol and interval.")
        else:
            try:
                metrics, results=run_ml_backtest(raw,train_fraction=train_fraction,
                    long_threshold=long_threshold,short_threshold=short_threshold,
                    allow_short=allow_short,cost_bps=cost_bps,neutral_band=neutral_band)
                st.session_state["v10_ml_metrics"]=metrics
                st.session_state["v10_ml_results"]=results
                st.session_state["v10_ml_symbol"]=symbol
            except Exception as exc:
                st.error(f"Model/backtest could not run: {exc}")
    metrics=st.session_state.get("v10_ml_metrics")
    results=st.session_state.get("v10_ml_results")
    if metrics and results is not None:
        st.subheader("Out-of-sample results")
        m1,m2,m3,m4=st.columns(4)
        m1.metric("Direction accuracy",f"{metrics['accuracy']*100:.1f}%")
        m2.metric("Strategy return",f"{metrics['strategy_return']*100:+.2f}%")
        m3.metric("Buy & hold return",f"{metrics['buy_hold_return']*100:+.2f}%")
        m4.metric("Maximum drawdown",f"{metrics['max_drawdown']*100:.2f}%")
        m5,m6,m7,m8=st.columns(4)
        m5.metric("Test candles",metrics["test_samples"])
        m6.metric("Active signals",metrics["trades"])
        m7.metric("Win rate on active candles",f"{metrics['win_rate_active']*100:.1f}%")
        m8.metric("Approx. annualized Sharpe",f"{metrics['sharpe_annualized_approx']:.2f}")
        st.caption(f"Train: {metrics['train_samples']} samples · Test: {metrics['test_samples']} samples · Exposure: {metrics['exposure']*100:.1f}% · Cost assumption: {metrics['cost_bps']:.1f} bps per exposure change")
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=results.index,y=results["Equity"],name="ML strategy equity"))
        # Normalize buy-and-hold to the same starting equity for visual comparison.
        bh=(1+results["Next candle return %"]/100).cumprod()
        fig.add_trace(go.Scatter(x=results.index,y=bh,name="Buy & hold",line=dict(dash="dot")))
        fig.update_layout(title="Out-of-sample equity curves (starting value = 1.0)",template="plotly_dark",height=420)
        st.plotly_chart(fig,use_container_width=True)
        last_p=metrics["last_probability_up"]
        st.info(f"Last test observation model probability of an up candle: {last_p*100:.1f}%. This is a model estimate, not a guaranteed probability or a live trade signal.")
        st.subheader("Recent out-of-sample predictions")
        view=results.tail(100).copy()
        view["Model probability Up"]=view["Model probability Up"]*100
        st.dataframe(view.style.format({"Model probability Up":"{:.1f}%","Next candle return %":"{:+.2f}%","Strategy return %":"{:+.2f}%","Equity":"{:.4f}"}),use_container_width=True)
        st.download_button("Download out-of-sample results CSV",results.to_csv().encode("utf-8"),file_name=f"{symbol.replace('^','')}_ml_backtest.csv",mime="text/csv")
    else:
        st.info("Choose a symbol and historical interval in the sidebar, then run the backtest. Daily candles are a sensible starting point; allow at least 1 year of history when available.")

elif page=="AI Patterns & Opportunity Lab":
    st.title("AI Patterns & Opportunity Lab")
    st.caption("V11 OHLCV research: candlestick patterns, chart setups, historical pattern outcomes, breakout context, market regime and a small chronological EMA parameter search.")
    st.warning("Research tools only. Pattern matches and heuristic scores are not guaranteed probabilities or trading recommendations. Validate setups and execution prices with your broker.")
    if data.empty or len(data)<30:
        st.error("Insufficient OHLCV history. Select a symbol with at least 30 candles in the sidebar.")
    else:
        regime=classify_market_regime(raw)
        r1,r2,r3=st.columns(3)
        r1.metric("Market regime",regime["regime"])
        r2.metric("ATR / price",f"{regime['atr_pct']:.2f}%" if pd.notna(regime["atr_pct"]) else "—")
        r3.metric("Candles loaded",f"{len(raw):,}")
        st.subheader("Latest candlestick patterns")
        flags=detect_candlestick_patterns(raw)
        latest=flags.iloc[-1]
        active=[name for name,value in latest.items() if bool(value)]
        if active:
            st.success("Latest candle matches: " + ", ".join(active))
        else:
            st.info("No listed candlestick pattern detected on the latest candle.")
        st.subheader("Historical pattern outcomes")
        horizon=st.slider("Forward evaluation horizon (candles)",2,15,5)
        hist=pattern_history(raw,horizon=horizon)
        st.dataframe(hist.style.format({"Positive forward return %":"{:.1f}%","Average forward return %":"{:+.2f}%"}),use_container_width=True,hide_index=True)
        st.caption("Historical positive-return frequency is descriptive, uses overlapping forward windows, and is not a calibrated forecast. Patterns with few occurrences are especially unreliable.")
        st.subheader("Chart pattern candidates")
        setups=detect_chart_setups(raw)
        st.dataframe(pd.DataFrame(setups),use_container_width=True,hide_index=True)
        st.subheader("Breakout context")
        bc=breakout_context(raw,horizon=horizon)
        b1,b2,b3=st.columns(3)
        b1.metric("Current range status",bc["status"])
        b2.metric("Historical up-break rate",f"{bc['historical_up_rate']:.1f}%" if pd.notna(bc["historical_up_rate"]) else "—")
        b3.metric("Historical down-break rate",f"{bc['historical_down_rate']:.1f}%" if pd.notna(bc["historical_down_rate"]) else "—")
        st.write(f"20-candle range: {bc['range_low']:.2f} – {bc['range_high']:.2f} · Similar historical observations: {bc['samples']} · Current volume ratio: {bc.get('volume_ratio',np.nan):.2f}x" if pd.notna(bc.get("volume_ratio",np.nan)) else f"20-candle range: {bc['range_low']:.2f} – {bc['range_high']:.2f} · Similar historical observations: {bc['samples']}")
        st.caption("Breakout rates are empirical frequencies from similar compression plus volume contexts, not live breakout probabilities. Small samples may be misleading.")
        st.subheader("EMA strategy parameter research")
        cost=st.number_input("Estimated transaction cost per exposure change (bps)",min_value=0.0,max_value=200.0,value=10.0,step=1.0,key="v11_cost")
        if st.button("Optimize EMA parameters on training history",type="primary"):
            try:
                grid,opt,curve=optimize_ema_strategy(raw,cost_bps=cost)
                st.session_state["v11_ema_grid"]=grid
                st.session_state["v11_ema_result"]=opt
                st.session_state["v11_ema_curve"]=curve
            except Exception as exc:
                st.error(f"Optimization could not run: {exc}")
        if "v11_ema_result" in st.session_state:
            opt=st.session_state["v11_ema_result"]
            q1,q2,q3=st.columns(3)
            q1.metric("Selected EMA pair",f"{opt['fast_ema']} / {opt['slow_ema']}")
            q2.metric("Untouched holdout return",f"{opt['holdout_return_pct']:+.2f}%")
            q3.metric("Holdout max drawdown",f"{opt['holdout_max_drawdown_pct']:.2f}%")
            st.dataframe(st.session_state["v11_ema_grid"],use_container_width=True,hide_index=True)
            curve=st.session_state["v11_ema_curve"]
            fig=go.Figure()
            fig.add_trace(go.Scatter(x=curve.index,y=curve["Strategy equity"],name="EMA strategy"))
            fig.add_trace(go.Scatter(x=curve.index,y=curve["Buy & hold equity"],name="Buy & hold",line=dict(dash="dot")))
            fig.update_layout(title="Chronological holdout equity (parameters selected on training segment)",template="plotly_dark",height=380)
            st.plotly_chart(fig,use_container_width=True)
            st.caption(f"Training observations: {opt['train_samples']} · Holdout observations: {opt['holdout_samples']} · Cost assumption: {opt['cost_bps']:.1f} bps. This is a compact parameter search, not proof of a profitable strategy.")
        st.subheader("Multi-symbol opportunity ranking")
        symbols_text=st.text_input("Symbols separated by commas", "RELIANCE.NS,TCS.NS,SBIN.NS,INFY.NS,HDFCBANK.NS",key="v11_symbols")
        if st.button("Scan and rank symbols"):
            items=[]
            symbols=list(dict.fromkeys(z.strip().upper() for z in symbols_text.split(",") if z.strip()))[:15]
            with st.spinner("Loading selected symbols..."):
                for sym in symbols:
                    hist_data=load_data(sym,period,interval)
                    if hist_data.empty or len(hist_data)<60: continue
                    ind=add_indicators(hist_data)
                    score,reasons=score_trend(ind)
                    last=ind.iloc[-1]
                    vr=float(last.Volume/last.Volume_Avg20) if pd.notna(last.Volume_Avg20) and last.Volume_Avg20 else 0.0
                    recent_high=float(ind.High.iloc[-21:-1].max()) if len(ind)>21 else float(ind.High.max())
                    recent_low=float(ind.Low.iloc[-21:-1].min()) if len(ind)>21 else float(ind.Low.min())
                    is_breakout=bool(last.Close>recent_high or last.Close<recent_low)
                    rg=classify_market_regime(hist_data)
                    items.append({"symbol":sym,"trend_score":score,"volume_ratio":vr,"breakout":is_breakout,"regime":rg["regime"],"regime_trend":rg["trend"]})
            ranked=rank_opportunities(items)
            if ranked.empty: st.warning("No symbols returned enough usable data. Check symbols, interval and connection.")
            else:
                st.session_state["v11_ranked"]=ranked
        if "v11_ranked" in st.session_state:
            st.dataframe(st.session_state["v11_ranked"],use_container_width=True,hide_index=True)
            st.download_button("Download opportunity ranking CSV",st.session_state["v11_ranked"].to_csv(index=False).encode("utf-8"),file_name="v11_opportunity_ranking.csv",mime="text/csv")
        st.caption("Opportunity score is a transparent heuristic combining trend score, a range break and relative volume. It is not an ML probability or a buy/sell instruction.")

elif page=="V12 Market Intelligence":
    st.title("V12 · Advanced Market Intelligence")
    st.caption("OHLCV-derived volume context, confirmed swing structure, candidate supply/demand zones and relative sector strength.")
    st.warning("These are technical price/volume proxies. They do not reveal actual institutional orders, participant positions or guaranteed support/resistance.")
    if raw.empty or len(raw) < 30:
        st.error("Load at least 30 usable OHLCV candles using the sidebar symbol and interval.")
    else:
        vol = volume_intelligence(raw)
        structure = market_structure(raw)
        zones = supply_demand_zones(raw)
        st.subheader(f"{symbol} · Volume intelligence")
        a,b,c = st.columns(3)
        a.metric("Relative volume", f"{vol['relative_volume']:.2f}x" if pd.notna(vol['relative_volume']) else "—")
        b.metric("OBV direction", vol["obv_trend"])
        c.metric("Chaikin Money Flow", f"{vol['cmf']:.3f}" if pd.notna(vol["cmf"]) else "—")
        st.caption(f"Activity classification: {vol['volume_label']}. Relative volume compares the latest candle with the prior 20-candle average. CMF is a rolling OHLCV estimate.")
        st.subheader("Confirmed swing market structure")
        x,y,z = st.columns(3)
        x.metric("Structure bias", structure["bias"])
        y.metric("Latest event", structure["event"])
        z.metric("Latest close", f"{float(raw.Close.iloc[-1]):,.2f}")
        st.write(f"Last confirmed swing high: {structure['swing_high']:.2f} · Last confirmed swing low: {structure['swing_low']:.2f}" if pd.notna(structure['swing_high']) and pd.notna(structure['swing_low']) else "Not enough confirmed swing points yet.")
        st.caption("Swing points require candles to the right for confirmation; the newest unconfirmed extreme is intentionally excluded.")
        st.subheader("Candidate supply & demand zones")
        if zones.empty:
            st.info("No nearby candidate zones found in the selected lookback.")
        else:
            st.dataframe(zones.style.format({"Low":"{:,.2f}","High":"{:,.2f}","Distance %":"{:+.2f}%"}),use_container_width=True,hide_index=True)
        st.caption("Zones are clustered from confirmed pivot candles and ATR proximity. They are historical reaction areas, not guaranteed levels.")
        st.subheader("Sector rotation & relative strength")
        st.write("Fetches sector-index performance from Yahoo Finance and ranks it against NIFTY 50's five-session return.")
        if st.button("Refresh sector rotation", type="primary"):
            with st.spinner("Fetching sector and benchmark data..."):
                sectors = fetch_change(SECTOR_SYMBOLS, period="1mo")
                benchmark = fetch_change({"NIFTY 50":"^NSEI"}, period="1mo")
                bench = float(benchmark.iloc[0]["5D %"]) if not benchmark.empty else 0.0
                ranked = sector_rotation(sectors, benchmark_return=bench)
                st.session_state["v12_sector_rotation"] = ranked
                st.session_state["v12_benchmark_return"] = bench
        if "v12_sector_rotation" in st.session_state:
            ranked = st.session_state["v12_sector_rotation"]
            st.metric("NIFTY 50 5-session return", f"{st.session_state['v12_benchmark_return']:+.2f}%")
            if ranked.empty:
                st.warning("No sector data returned. Check internet access or retry later.")
            else:
                st.dataframe(ranked.style.format({"Day %":"{:+.2f}%","5D %":"{:+.2f}%","Relative 5D %":"{:+.2f}%"}),use_container_width=True,hide_index=True)
                st.download_button("Download sector rotation CSV",ranked.to_csv(index=False).encode("utf-8"),file_name="v12_sector_rotation.csv",mime="text/csv")
        st.caption("Sector leadership is based on five-session price return relative to NIFTY 50, not fund flows or institutional allocation.")

elif page=="V13 AI Market Command Centre":
    st.title("V13 · AI Market Command Centre")
    st.caption("Transparent regime classification, NIFTY/BANKNIFTY confluence and OHLCV opportunity ranking.")
    st.warning("Scores are technical heuristics from historical OHLCV data—not prediction probabilities, verified institutional flows or trading instructions.")
    current = regime_intelligence(raw) if not raw.empty else {"status":"Insufficient history"}
    if current.get("status")=="OK":
        a,b,c,d=st.columns(4)
        a.metric("Market regime",current["regime"]); b.metric("Trend",current["trend"])
        c.metric("Volatility",current["volatility"]); d.metric("Trend score",f"{current['trend_score']:+.1f}")
        st.write(f"ATR: {current['atr_pct']:.3f}% · Efficiency ratio: {current['efficiency_ratio']:.3f} · Volatility percentile: {current['volatility_percentile']:.1f}%")
    else: st.info("Load at least 50 candles in the sidebar to classify the selected symbol.")
    st.subheader("NIFTY 50 + BANKNIFTY confluence")
    if st.button("Analyse NIFTY and BANKNIFTY",type="primary"):
        with st.spinner("Loading index history..."):
            nifty=load_data("^NSEI","6mo","1d")
            bank=load_data("^NSEBANK","6mo","1d")
            st.session_state["v13_index_result"]=index_confluence({"NIFTY 50":nifty,"BANKNIFTY":bank})
    if "v13_index_result" in st.session_state:
        result=st.session_state["v13_index_result"]
        if result["status"]=="OK":
            a,b,c=st.columns(3); a.metric("Combined bias",result["bias"]); b.metric("Confluence score",f"{result['score']:+.1f}"); c.metric("Directional agreement",f"{result['agreement']:.1f}%")
            st.dataframe(pd.DataFrame([{"Index":k,**v} for k,v in result["components"].items()]),use_container_width=True,hide_index=True)
        else: st.warning("Index data unavailable or insufficient. Retry when Yahoo Finance responds.")
    st.subheader("Multi-stock opportunity ranking")
    symbols_text=st.text_input("Symbols separated by commas","RELIANCE.NS,TCS.NS,SBIN.NS,INFY.NS,HDFCBANK.NS")
    if st.button("Scan opportunity list"):
        frames={}
        with st.spinner("Fetching daily candles for requested symbols..."):
            for item in symbols_text.split(","):
                sym=item.strip().upper()
                if sym:
                    frame=load_data(sym,"6mo","1d")
                    if not frame.empty: frames[sym]=frame
        st.session_state["v13_opportunities"]=rank_intraday_opportunities(frames)
    if "v13_opportunities" in st.session_state:
        ranked=st.session_state["v13_opportunities"]
        if ranked.empty: st.info("No usable symbol data returned. Check Yahoo Finance symbols and retry.")
        else:
            st.dataframe(ranked,use_container_width=True,hide_index=True)
            st.download_button("Download V13 opportunity ranking",ranked.to_csv(index=False).encode("utf-8"),file_name="v13_opportunity_ranking.csv",mime="text/csv")
    st.caption("The score ranks relative trend/volume context only. Validate liquidity, spreads, event risk and position sizing independently.")

elif page=="Portfolio & Trade Journal":
    st.title("Portfolio & Trade Journal")
    st.caption("Closed trades are stored locally in a SQLite database in this project folder. This is not broker-connected.")
    with st.form("journal_add_trade"):
        a,b,c=st.columns(3)
        with a:
            trade_symbol=st.text_input("Symbol",symbol).strip().upper(); side=st.selectbox("Side",["BUY","SELL"])
        with b:
            qty=st.number_input("Quantity",min_value=1,value=1,step=1); entry_price=st.number_input("Entry price",min_value=0.0,value=100.0,step=0.5)
        with c:
            exit_price=st.number_input("Exit price",min_value=0.0,value=100.0,step=0.5); charges=st.number_input("Charges (₹)",min_value=0.0,value=0.0,step=1.0)
        notes=st.text_input("Setup / notes"); save=st.form_submit_button("Add closed trade")
        if save:
            gross=(exit_price-entry_price)*qty*(1 if side=="BUY" else -1); net=gross-charges
            save_trade({"Date":datetime.now().strftime("%Y-%m-%d %H:%M"),"Symbol":trade_symbol,"Side":side,"Quantity":int(qty),"Entry":float(entry_price),"Exit":float(exit_price),"Charges":float(charges),"Gross P&L":round(gross,2),"Net P&L":round(net,2),"Notes":notes})
            st.success(f"Trade saved permanently in local database. Net P&L: ₹{net:,.2f}")
    journal=load_trades()
    if not journal.empty:
        total=float(journal["Net P&L"].sum()); wins=int((journal["Net P&L"]>0).sum()); losses=int((journal["Net P&L"]<0).sum())
        x,y,z,w=st.columns(4); x.metric("Closed trades",len(journal)); y.metric("Net realized P&L",f"₹{total:,.2f}"); z.metric("Win rate",f"{wins/len(journal)*100:.1f}%"); w.metric("Wins / Losses",f"{wins} / {losses}")
        st.dataframe(journal,use_container_width=True,hide_index=True)
        st.download_button("Download trade journal CSV",journal.to_csv(index=False).encode("utf-8"),file_name="ai_trade_journal.csv",mime="text/csv")
        if st.button("Clear all locally saved journal trades"):
            clear_trades(); st.rerun()
    else: st.info("No closed trades recorded yet. Add a trade above to begin tracking performance.")



elif page=="V14 Live Feed Monitor":
    st.title("V14 · Upstox Live Feed Monitor")
    st.caption("Read-only websocket diagnostics for NIFTY 50, BANKNIFTY and India VIX. No orders are placed.")
    from live_market_feed import start_live_feed, get_market_data, get_feed_status, stop_live_feed
    left, middle, right = st.columns(3)
    if left.button("Start / Connect feed", type="primary"):
        st.info(start_live_feed())
    if middle.button("Stop feed"):
        st.info(stop_live_feed())
    if right.button("Refresh status"):
        st.rerun()
    status = get_feed_status()
    a,b,c,d = st.columns(4)
    a.metric("Connection", status.get("state", "unknown").upper())
    b.metric("Messages received", int(status.get("message_count", 0)))
    c.metric("Last message", status.get("last_message_at") or "Waiting")
    d.metric("Connected", "YES" if status.get("connected") else "NO")
    st.write(status.get("message", ""))
    if status.get("last_error"):
        st.error(status["last_error"])
    market = get_market_data()
    if market:
        rows=[]
        for key, payload in market.items():
            if key in {"last_update", "message_type"} or not isinstance(payload, dict):
                continue
            full = payload.get("fullFeed", {}) if isinstance(payload.get("fullFeed"), dict) else {}
            index_ff = full.get("indexFF", {}) if isinstance(full.get("indexFF"), dict) else {}
            ltpc = index_ff.get("ltpc", {}) if isinstance(index_ff.get("ltpc"), dict) else {}
            ltp = ltpc.get("ltp")
            cp = ltpc.get("cp")
            pct = ((float(ltp)-float(cp))/float(cp)*100) if ltp is not None and cp not in (None, 0) else None
            rows.append({"Instrument": key, "LTP": ltp, "Change %": round(pct, 2) if pct is not None else None})
        if rows:
            st.subheader("Latest index snapshots")
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption(f"Last payload update: {market.get('last_update', 'not available')} · Type: {market.get('message_type', 'unknown')}")
        with st.expander("Raw feed payload (diagnostics)"):
            st.json(market)
    else:
        st.info("No market payload received yet. Confirm the token, market hours, instrument permissions and network connection.")
    st.warning("A successful websocket connection does not guarantee fresh ticks. Check the last-message timestamp and message count. Quotes may be unavailable outside market hours.")

elif page=="V35 Central AI Brain – 25 Tools":
    st.title("V35 · Central AI Brain | 25 Specialist Tools")
    st.caption("One coordinated decision workspace. Transparent rule-based evidence, shared market context and no automatic broker orders.")
    from central_ai_brain_v35 import TOOL_CATALOG, analyze_market as analyze_central_market, rank_symbols as rank_central_symbols
    top1,top2,top3=st.columns(3)
    top1.metric("Specialist tools", "25")
    top2.metric("Selected instrument", symbol)
    top3.metric("Current candle rows", len(data) if data is not None else 0)
    tabs=st.tabs(["Central AI Brain","Multi-Asset Quick Scan","25-Tool Directory","Risk & Correlation"])
    with tabs[0]:
        st.subheader("Unified market assessment")
        st.write("The brain combines technical trend, momentum, volatility, volume and breakout evidence. Optional manual inputs are clearly labelled and are not treated as verified exchange data.")
        opt_pcr=st.number_input("Optional option-chain PCR (leave 0 if unavailable)",min_value=0.0,max_value=10.0,value=0.0,step=0.05,key="v35_pcr")
        fii_net=st.number_input("Optional verified FII/DII net-flow value (₹ crore; leave 0 if unavailable)",value=0.0,step=100.0,key="v35_fii")
        news_score=st.selectbox("Optional news sentiment contribution",["Not supplied",-2,-1,0,1,2],key="v35_news_score")
        if st.button("Run Central AI Brain",type="primary",key="v35_run_brain"):
            result=analyze_central_market(data,option_pcr=opt_pcr if opt_pcr>0 else None,
                fii_net=fii_net if fii_net!=0 else None,
                news_score=None if news_score=="Not supplied" else news_score)
            result["symbol"]=symbol
            st.session_state["v35_brain_result"]=result
        result=st.session_state.get("v35_brain_result")
        if result:
            if result.get("status")!="OK": st.warning("Insufficient data: "+" ".join(result.get("warnings",[])))
            else:
                a,b,c,d=st.columns(4)
                a.metric("Overall assessment",result["direction"])
                b.metric("Evidence score",f'{result["score"]:+d}')
                c.metric("Evidence quality",result["quality"])
                d.metric("RSI",f'{result["rsi"]:.1f}' if result.get("rsi") is not None else "—")
                a,b,c,d=st.columns(4)
                a.metric("Last candle close",f'{result["last_close"]:,.2f}')
                b.metric("ATR(14)",f'{result["atr"]:,.2f}')
                c.metric("Support reference",f'{result["support"]:,.2f}')
                d.metric("Resistance reference",f'{result["resistance"]:,.2f}')
                st.subheader("Evidence and conflicts")
                for item in result["evidence"]: st.success(item)
                for item in result["warnings"]: st.warning(item)
                st.subheader("Illustrative trade preparation levels")
                if result["direction"]=="BULLISH_CANDIDATE":
                    st.write(f'Entry watch zone: {result["entry_reference"][0]:,.2f} – {result["entry_reference"][1]:,.2f} · Stop reference: {result["stop_long"]:,.2f} · Target reference: {result["target_long"]:,.2f}')
                elif result["direction"]=="BEARISH_CANDIDATE":
                    st.write(f'Entry watch zone: {result["entry_reference"][0]:,.2f} – {result["entry_reference"][1]:,.2f} · Stop reference: {result["stop_short"]:,.2f} · Target reference: {result["target_short"]:,.2f}')
                else: st.info("No directional trade plan: evidence is mixed. Wait for stronger confirmation.")
                st.caption("Rule-based evidence score, not a win probability. ATR levels are illustrative and do not account for gaps, liquidity, brokerage, taxes or option lot sizing.")
        else: st.info("Press Run Central AI Brain to assess the currently selected symbol and loaded candle history.")
    with tabs[1]:
        st.subheader("Multi-asset quick scan")
        default_scan="RELIANCE.NS,TCS.NS,INFY.NS,SBIN.NS,HDFCBANK.NS,ICICIBANK.NS,^NSEI,^NSEBANK,GC=F,CL=F,BTC-USD,ETH-USD,USDINR=X,EURUSD=X"
        scan_text=st.text_area("Symbols (comma separated; Yahoo Finance tickers)",value=default_scan,height=90,key="v35_scan_symbols")
        if st.button("Scan symbols",key="v35_scan_btn"):
            rows=[]
            scan_syms=[v.strip().upper() for v in scan_text.split(",") if v.strip()][:30]
            with st.spinner(f"Loading available history for {len(scan_syms)} symbols..."):
                for sym in scan_syms:
                    frame=load_data(sym,"6mo","1d")
                    rr=analyze_central_market(frame)
                    rows.append({"Symbol":sym,"Status":rr.get("status"),"Bias":rr.get("direction","N/A"),"Score":rr.get("score"),"RSI":rr.get("rsi"),"Breakout":rr.get("breakout"),"Last close":rr.get("last_close")})
            st.session_state["v35_scan_results"]=pd.DataFrame(rows)
        scan_df=st.session_state.get("v35_scan_results",pd.DataFrame())
        if not scan_df.empty:
            st.dataframe(scan_df,use_container_width=True,hide_index=True)
            st.download_button("Download scan CSV",scan_df.to_csv(index=False).encode("utf-8"),"v35_multi_asset_scan.csv","text/csv")
        st.caption("Availability and quote freshness vary by Yahoo Finance symbol and market. These are screening snapshots, not exchange-certified live quotes.")
    with tabs[2]:
        st.subheader("25 specialist tools")
        directory=pd.DataFrame([{"#":n,"AI Tool":name,"Function":desc} for n,name,desc in TOOL_CATALOG])
        st.dataframe(directory,use_container_width=True,hide_index=True)
        st.info("Existing V28–V34 modules remain available in their own navigation pages. V35 connects their shared evidence into this central workspace; some specialist tools still require their own source data or user-supplied verified inputs.")
    with tabs[3]:
        st.subheader("Risk sizing calculator")
        r1,r2,r3=st.columns(3)
        capital=r1.number_input("Trading capital (₹)",min_value=1.0,value=100000.0,step=5000.0,key="v35_capital")
        risk_pct=r2.number_input("Risk per trade (%)",min_value=0.1,max_value=5.0,value=1.0,step=0.1,key="v35_riskpct")
        stop_dist=r3.number_input("Entry-to-stop distance (₹ per unit)",min_value=0.01,value=10.0,step=0.5,key="v35_stopdist")
        max_loss=capital*risk_pct/100
        qty=int(max_loss/stop_dist)
        st.metric("Illustrative cash-equity quantity",f"{qty:,}")
        st.caption(f"Approximate planned risk ₹{qty*stop_dist:,.2f}; excludes costs, slippage and gap risk. Not valid as an options lot calculator.")
        st.subheader("Correlation analysis")
        st.write("Use the V21 cross-asset dashboard for its existing correlation matrix. V35 correlation calculations require aligned historical close series for each selected asset; unavailable data is not fabricated.")
        if st.button("Build correlation matrix for scan symbols",key="v35_corr_btn"):
            symbols=[v.strip().upper() for v in st.session_state.get("v35_scan_symbols","").split(",") if v.strip()][:12]
            prices={}
            for sym in symbols:
                frame=load_data(sym,"6mo","1d")
                if not frame.empty: prices[sym]=frame["Close"]
            if len(prices)>=2:
                from central_ai_brain_v35 import correlation_matrix as _corr
                corr=_corr(prices)
                st.session_state["v35_corr"]=corr
            else: st.warning("At least two symbols need usable historical data.")
        corr=st.session_state.get("v35_corr")
        if corr is not None: st.dataframe(corr.style.format("{:.2f}"),use_container_width=True)
    st.warning("V35 is a decision-support workspace. News, institutional flows, option-chain Greeks, Max Pain and event calendar are scored only when valid source data is available. No automated order execution or guaranteed prediction is provided.")

elif page=="V34 Portfolio & Watchlist Intelligence":
    st.title("V34 · Portfolio & Watchlist Intelligence")
    st.caption("Local portfolio ledger, watchlists, one-shot price alerts and marked-to-market risk. No broker account connection or order placement.")
    from portfolio_watchlist_v34 import (add_watchlist, remove_watchlist, list_watchlist, add_position,
        remove_position, list_positions, add_price_alert, list_price_alerts, evaluate_alerts, mark_to_market)
    tab_watch, tab_positions, tab_alerts = st.tabs(["Watchlists", "Open positions & risk", "Price alerts"])

    with tab_watch:
        st.subheader("Build your watchlist")
        with st.form("v34_add_watch"):
            wa, wb, wc = st.columns([2,1,2])
            w_symbol = wa.text_input("Yahoo Finance symbol", value=symbol).strip().upper()
            w_class = wb.selectbox("Asset class", ["Equity", "Index", "Commodity", "Forex", "Crypto", "Other"])
            w_note = wc.text_input("Note (optional)")
            w_save = st.form_submit_button("Add to watchlist")
            if w_save:
                try:
                    add_watchlist(w_symbol, w_class, w_note); st.success(f"Added {w_symbol}")
                except Exception as exc: st.error(str(exc))
        watch = list_watchlist()
        if not watch.empty:
            st.dataframe(watch.drop(columns=["id","created_at"], errors="ignore"), use_container_width=True, hide_index=True)
            remove_sym = st.selectbox("Remove symbol", watch.symbol.tolist(), key="v34_remove_watch")
            if st.button("Remove selected watchlist symbol"):
                remove_watchlist(remove_sym); st.rerun()
        else: st.info("Your watchlist is empty. Add symbols above.")

    with tab_positions:
        st.subheader("Record an open position")
        with st.form("v34_add_position"):
            p1,p2,p3 = st.columns(3)
            p_symbol = p1.text_input("Symbol", value=symbol, key="v34_pos_symbol").strip().upper()
            p_side = p2.selectbox("Position side", ["LONG", "SHORT"])
            p_qty = p3.number_input("Quantity", min_value=0.0001, value=1.0, step=1.0, format="%.4f")
            p4,p5,p6 = st.columns(3)
            p_entry = p4.number_input("Average entry", min_value=0.01, value=100.0, step=0.5)
            p_sl = p5.number_input("Stop-loss reference (0 = none)", min_value=0.0, value=0.0, step=0.5)
            p_target = p6.number_input("Target reference (0 = none)", min_value=0.0, value=0.0, step=0.5)
            p_note = st.text_input("Position note")
            p_save = st.form_submit_button("Save open position")
            if p_save:
                try:
                    add_position(p_symbol,p_side,p_qty,p_entry,p_sl,p_target,p_note)
                    st.success("Position saved in the local project database."); st.rerun()
                except Exception as exc: st.error(str(exc))
        positions = list_positions()
        if not positions.empty:
            symbols_to_quote = sorted(set(positions.symbol.str.upper().tolist()))
            if st.button("Refresh position valuations", type="primary"):
                quotes={}
                with st.spinner("Fetching latest available Yahoo Finance candles..."):
                    for sym in symbols_to_quote:
                        qdf=load_data(sym,"5d","1d")
                        if not qdf.empty: quotes[sym]=float(qdf.Close.iloc[-1])
                st.session_state["v34_quotes"] = quotes
                st.session_state["v34_quote_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            quotes=st.session_state.get("v34_quotes", {})
            marked, totals = mark_to_market(positions, quotes)
            a,b,c,d=st.columns(4)
            a.metric("Open positions", totals["positions"])
            b.metric("Marked value", f"₹{totals['market_value']:,.2f}" if quotes else "—")
            pnl=totals['unrealized_pnl']
            c.metric("Unrealized P&L", f"₹{pnl:,.2f}" if quotes else "—")
            d.metric("Risk to entered stops", f"₹{totals['risk_to_stops']:,.2f}" if quotes and marked.risk_to_stop.notna().any() else "—")
            st.dataframe(marked, use_container_width=True, hide_index=True)
            if quotes: st.caption("Valuation snapshot: " + st.session_state.get("v34_quote_time","unknown") + ". Missing quotes remain blank; prices may be delayed or unavailable.")
            else: st.info("Click Refresh position valuations to request latest available daily candles for your symbols.")
            remove_id = st.selectbox("Close/remove position record", positions.id.tolist(), format_func=lambda x: f"Position #{x} · {positions.loc[positions.id==x,'symbol'].iloc[0]}")
            if st.button("Remove selected position record"):
                remove_position(remove_id); st.rerun()
            st.download_button("Download position ledger CSV", marked.to_csv(index=False).encode("utf-8"), "v34_positions.csv", "text/csv")
        else: st.info("No open positions recorded yet.")

    with tab_alerts:
        st.subheader("Create price alerts")
        with st.form("v34_add_alert"):
            aa,ab,ac=st.columns(3)
            a_symbol=aa.text_input("Alert symbol", value=symbol).strip().upper()
            a_condition=ab.selectbox("Trigger when price is", ["ABOVE","BELOW"])
            a_price=ac.number_input("Trigger price", min_value=0.01, value=100.0, step=0.5)
            a_save=st.form_submit_button("Create one-shot alert")
            if a_save:
                try: add_price_alert(a_symbol,a_condition,a_price); st.success("Alert saved locally.")
                except Exception as exc: st.error(str(exc))
        alerts=list_price_alerts()
        if not alerts.empty:
            st.dataframe(alerts, use_container_width=True, hide_index=True)
            active_symbols=sorted(set(alerts.loc[alerts.active==1,"symbol"].tolist()))
            if st.button("Check active alerts against latest available candles"):
                quotes={}
                with st.spinner("Checking alert symbols..."):
                    for sym in active_symbols:
                        qdf=load_data(sym,"5d","1d")
                        if not qdf.empty: quotes[sym]=float(qdf.Close.iloc[-1])
                hits=evaluate_alerts(quotes)
                st.session_state["v34_alert_hits"]=hits
                st.session_state["v34_alert_check_time"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            hits=st.session_state.get("v34_alert_hits",[])
            if hits:
                for hit in hits: st.success(f"{hit['symbol']} crossed {hit['condition']} ₹{hit['trigger_price']:,.2f}; observed ₹{hit['observed_price']:,.2f}")
            elif "v34_alert_check_time" in st.session_state:
                st.info("No new alert triggers found in the latest available candle snapshot.")
            st.caption("Alerts are checked only when you press the button; they are not background or push notifications.")
        else: st.info("No price alerts created yet.")
    st.warning("Portfolio and alert records are stored locally in this app folder, not synced to your broker or cloud. Mark-to-market uses the latest available Yahoo Finance daily candle and may be delayed; it is not an exchange-live valuation. Verify quotes independently before acting.")

elif page=="V33 Multi-Asset AI Scanner":
    st.title("V33 · Advanced Multi-Asset Scanner")
    st.caption("Read-only cross-market screening across Indian indices, NSE large caps, commodities, forex and crypto. Uses hourly + daily OHLCV confluence; scores are heuristic, not probabilities.")
    from multi_asset_scanner_v33 import ASSET_UNIVERSE, scan_multi_asset
    selected_classes = st.multiselect("Asset classes", list(ASSET_UNIVERSE), default=list(ASSET_UNIVERSE))
    f1, f2 = st.columns(2)
    max_symbols = f1.slider("Maximum symbols per asset class", 1, 20, 8)
    min_score = f2.slider("Minimum absolute combined score", 1, 8, 2)
    st.info("The scanner fetches 1-hour (3 months) and daily (6 months) history. Yahoo Finance coverage varies by symbol and market; commodity/forex/crypto tickers are indicative proxies, not verified exchange feeds.")
    if st.button("Run multi-asset scan", type="primary", disabled=not selected_classes):
        with st.spinner("Scanning selected markets and checking timeframe alignment..."):
            scan_result, scan_coverage = scan_multi_asset(load_data, selected_classes, max_symbols, min_score)
            st.session_state["v33_scan_result"] = scan_result
            st.session_state["v33_scan_coverage"] = scan_coverage
            st.session_state["v33_scan_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    scan_result = st.session_state.get("v33_scan_result")
    scan_coverage = st.session_state.get("v33_scan_coverage")
    if isinstance(scan_result, pd.DataFrame):
        st.caption("Last scan: " + st.session_state.get("v33_scan_time", "unknown") + " · Results are based on the fetched historical candles, not guaranteed live ticks.")
        aligned = int((scan_result["Status"] == "ALIGNED").sum()) if not scan_result.empty else 0
        conflicts = int((scan_result["Status"] == "CONFLICT").sum()) if not scan_result.empty else 0
        unavailable = int((scan_result["Status"] == "INSUFFICIENT DATA").sum()) if not scan_result.empty else 0
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Symbols scanned", len(scan_result)); m2.metric("Aligned candidates", aligned)
        m3.metric("Timeframe conflicts", conflicts); m4.metric("Insufficient data", unavailable)
        st.subheader("Scanner results")
        if not scan_result.empty:
            st.dataframe(scan_result, use_container_width=True, hide_index=True)
            st.download_button("Download scan results (CSV)", scan_result.to_csv(index=False).encode("utf-8"), "v33_multi_asset_scan.csv", "text/csv")
        else:
            st.info("No symbols returned. Try another asset class or a larger symbol limit.")
        if isinstance(scan_coverage, pd.DataFrame):
            st.subheader("Data coverage by asset class")
            st.dataframe(scan_coverage, use_container_width=True, hide_index=True)
    else:
        st.info("Choose asset classes and click Run multi-asset scan. Scanning is manual to avoid repeated provider requests.")
    with st.expander("Scoring and data limitations"):
        st.write("""• Each asset is assessed independently on 1-hour and 1-day OHLCV using EMA 9/20/50 structure, RSI and relative volume.
• ALIGNED means both timeframes point in the same bullish or bearish direction and the combined score clears the selected threshold.
• CONFLICT and WAIT are not trade setups. INSUFFICIENT DATA means the provider did not return enough valid candles.
• No options-chain, order-book, spread, funding-rate or exchange-session validation is performed by this scanner. No broker orders are placed.""")
    st.warning("Research shortlist only. Verify the primary exchange quote, liquidity, spread, event risk and your own risk limits before considering any trade. This is not personalized financial advice.")

elif page=="V32 Chart Pattern & Smart Entry":
    st.title("V32 · Chart Pattern Recognition & Smart Entry")
    st.caption("OHLCV-based pattern screening, range breakout context, support/resistance references and illustrative ATR zones. No automated orders.")
    from chart_intelligence_v32 import analyze_chart_v32
    if data.empty:
        st.warning("No OHLCV candles are loaded. Select a supported symbol, history period and interval in the sidebar.")
    else:
        result=analyze_chart_v32(data)
        if result["status"]=="Insufficient history":
            st.warning("At least 30 valid candles are required for this analysis.")
        else:
            a,b,c,d=st.columns(4)
            a.metric("Pattern context",result["status"])
            b.metric("Setup assessment",result["direction"])
            c.metric("ATR (14)",f"{result['atr']:,.2f}")
            d.metric("Volume vs avg",f"{result['volume_ratio']:.2f}x" if pd.notna(result['volume_ratio']) else "Unavailable")
            st.subheader("Detected chart evidence")
            if result["setups"]:
                for item in result["setups"]: st.write("• "+item)
            else: st.info("No qualifying pattern detected in the latest candle/range.")
            st.subheader("Support, resistance and smart-entry reference")
            x1,x2,x3=st.columns(3)
            x1.metric("Rolling support",f"{result['support']:,.2f}")
            x2.metric("Rolling resistance",f"{result['resistance']:,.2f}")
            x3.metric("Last close",f"{result['last']:,.2f}")
            if result["entry"]:
                p,q,r=st.columns(3)
                p.metric("Illustrative entry zone",f"{result['entry'][0]:,.2f} – {result['entry'][1]:,.2f}")
                q.metric("ATR invalidation reference",f"{result['stop']:,.2f}")
                r.metric("2 ATR objective reference",f"{result['target']:,.2f}")
            else:
                st.info("No entry zone generated: wait for a clearer range break or another independently confirmed setup.")
            fig=go.Figure(data=[go.Candlestick(x=data.tail(160).index,open=data.tail(160).Open,high=data.tail(160).High,low=data.tail(160).Low,close=data.tail(160).Close,name="Price")])
            fig.add_hline(y=result["support"],line_dash="dot",annotation_text="Rolling support")
            fig.add_hline(y=result["resistance"],line_dash="dot",annotation_text="Rolling resistance")
            if result["entry"]:
                fig.add_hrect(y0=result["entry"][0],y1=result["entry"][1],opacity=.15,line_width=0,annotation_text="Entry reference zone")
                fig.add_hline(y=result["stop"],line_dash="dash",annotation_text="Invalidation")
                fig.add_hline(y=result["target"],line_dash="dash",annotation_text="2 ATR objective")
            fig.update_layout(template="plotly_dark",height=600,xaxis_rangeslider_visible=False,title=f"{symbol} · {interval} chart evidence")
            st.plotly_chart(fig,use_container_width=True)
            with st.expander("Methodology and limitations"):
                for warning in result["warnings"]: st.write("• "+warning)
                st.caption(f"Computed from {result['candles']} candles in the currently selected sidebar dataset. Source: {symbol} history feed; freshness depends on provider.")
    st.warning("Educational decision support only. Confirm the chart, data timestamp, liquidity and risk independently. Nothing here is a guaranteed prediction or personalized financial advice.")

elif page=="V31 AI Trading Assistant":
    st.title("V31 · AI Trading Assistant")
    st.caption("Ask questions using the market evidence already loaded in this app session. Explanations are rule-based/local; no external LLM or broker execution is connected.")
    from trading_assistant_v31 import answer_question
    frames=st.session_state.get("ati_v30_frames", {})
    v30_result=st.session_state.get("ati_v30_result")
    chain=st.session_state.get("v15_chain")
    chain_meta=st.session_state.get("v15_chain_meta", {})
    st.subheader("Ask the trading assistant")
    st.write("Try: What is the current bias? · Explain RSI · What does PCR mean? · How should I calculate position size? · Explain the options context.")
    if "ati_v31_chat" not in st.session_state:
        st.session_state["ati_v31_chat"]=[]
    if st.button("Clear assistant conversation", key="v31_clear_chat"):
        st.session_state["ati_v31_chat"]=[]
    for msg in st.session_state["ati_v31_chat"]:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    prompt=st.chat_input("Ask about indicators, market bias, options or risk…", key="v31_chat_input")
    if prompt:
        st.session_state["ati_v31_chat"].append({"role":"user","content":prompt})
        response=answer_question(prompt, symbol, frames, v30_result, chain if isinstance(chain,pd.DataFrame) else None, chain_meta)
        st.session_state["ati_v31_chat"].append({"role":"assistant","content":response})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"): st.markdown(response)
    st.divider()
    st.subheader("Data available to the assistant")
    c1,c2,c3=st.columns(3)
    c1.metric("Selected instrument",symbol)
    c2.metric("V30 assessment", "Loaded" if v30_result else "Not refreshed")
    c3.metric("Options chain", "Loaded" if isinstance(chain,pd.DataFrame) and not chain.empty else "Not loaded")
    st.info("For current technical bias, refresh evidence in V30 Trade Confirmation. For option-chain questions, fetch an expiry in V15 first. The assistant will clearly state when data is missing.")
    st.warning("Educational decision support only. Verify quotes and timestamps independently. This assistant does not provide guaranteed predictions, personalized financial advice or place orders.")

elif page=="V30 Trade Confirmation":
    st.title("V30 · AI Trade Confirmation & Execution Preparation")
    st.caption("One review desk combining multi-timeframe technicals, optional-chain positioning and multi-source news risk. No orders are placed.")
    from trade_confirmation_v30 import evaluate_v30
    from trade_confirmation_engine import build_atr_trade_plan
    left, right = st.columns([1, 1])
    if left.button("Refresh V30 market evidence", type="primary"):
        specs = {"5m": ("5d", "5m"), "15m": ("30d", "15m"), "1H": ("60d", "1h"), "1D": ("1y", "1d")}
        frames = {}
        with st.spinner("Fetching multi-timeframe candles and market news..."):
            for tf, (per, inter) in specs.items():
                frames[tf] = load_data(symbol, per, inter)
            news, status = fetch_all_news()
            news = enrich_news(news) if not news.empty else news
        st.session_state["ati_v30_frames"] = frames
        st.session_state["ati_v30_news"] = news
        st.session_state["ati_v30_feed_status"] = status
    frames = st.session_state.get("ati_v30_frames", {})
    news = st.session_state.get("ati_v30_news", pd.DataFrame())
    chain = st.session_state.get("v15_chain")
    meta = st.session_state.get("v15_chain_meta", {})
    if not frames:
        st.info("Select an instrument in the sidebar, then click Refresh V30 market evidence. Option-chain context is optional; fetch it in V15 first.")
    else:
        try:
            result = evaluate_v30(frames, news, chain if isinstance(chain, pd.DataFrame) else None)
            st.session_state["ati_v30_result"] = result
            st.subheader("Trade decision gate")
            st.markdown(f"### {result['verdict']}")
            a,b,c,d = st.columns(4)
            a.metric("Confluence score", result["confluence_score"])
            b.metric("Technical quality", result["technical"]["quality"])
            c.metric("News risk", result["news_risk"])
            d.metric("Timeframes", f"{result['technical']['available_count']}/4")
            st.caption(result["technical"]["agreement"])
            st.subheader("Evidence by timeframe")
            rows=[]
            for tf, reading in result["technical"]["timeframes"].items():
                fresh=result["technical"]["freshness"][tf]
                rows.append({"Timeframe":tf,"Bias":reading["bias"],"Score":reading["score"],"RSI":reading["rsi"],"Relative volume":reading["relative_volume"],"Freshness":fresh["status"],"Age hours":fresh["age_hours"]})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.subheader("Confluence evidence")
            for item in result["evidence"]: st.write("• " + item)
            if result["options"]:
                opt=result["options"]
                st.subheader("Options positioning · Upstox V15 snapshot")
                st.caption(f"{meta.get('underlying','Unknown')} · expiry {meta.get('expiry','Unknown')} · fetched {meta.get('fetched','Unknown')}")
                x1,x2,x3,x4=st.columns(4)
                x1.metric("PCR", f"{opt['pcr']:.2f}" if opt['pcr'] is not None else "N/A")
                x2.metric("Max Pain", f"{opt['max_pain']:,.2f}" if opt['max_pain'] is not None else "N/A")
                x3.metric("Call OI wall", f"{opt['max_call_oi_strike']:,.2f}" if opt['max_call_oi_strike'] is not None else "N/A")
                x4.metric("Put OI wall", f"{opt['max_put_oi_strike']:,.2f}" if opt['max_put_oi_strike'] is not None else "N/A")
                st.caption("OI concentration and Max Pain are descriptive chain statistics, not support/resistance guarantees or forecasts.")
            else:
                st.info("Options context not attached. Fetch a chain in V15 Live Options Intelligence to include PCR, OI concentration and Max Pain.")
            st.subheader("News and event-risk review")
            st.write(f"{len(news)} headlines available in the cached session feed; {len(result['technical']['high_priority_news'])} currently meet the high-priority threshold.")
            if not result['technical']['high_priority_news'].empty:
                cols=[c for c in ["Source","Published (UTC)","Headline","Priority score","Priority","Link"] if c in news.columns]
                st.dataframe(result['technical']['high_priority_news'][cols], use_container_width=True, hide_index=True)
            st.subheader("Warnings / blockers")
            if result['warnings']:
                for warning in result['warnings']: st.warning(warning)
            else: st.success("No additional rule-based blockers flagged. Complete the checklist below before any decision.")
            st.subheader("Execution-preparation checklist")
            for item in result['review_checklist']: st.checkbox(item, key="v30_check_"+str(result['review_checklist'].index(item)))
            daily=frames.get("1D", pd.DataFrame())
            if not daily.empty and len(daily)>=20:
                st.subheader("Illustrative cash-equity risk ticket")
                tr=pd.concat([daily.High-daily.Low,(daily.High-daily.Close.shift()).abs(),(daily.Low-daily.Close.shift()).abs()],axis=1).max(axis=1)
                atr=float(tr.ewm(alpha=1/14,adjust=False).mean().iloc[-1]); latest=float(daily.Close.iloc[-1])
                q1,q2,q3=st.columns(3)
                entry=q1.number_input("Entry reference",min_value=0.01,value=latest,step=0.05,key="v30_entry")
                budget=q2.number_input("Risk budget (₹)",min_value=1.0,value=1000.0,step=100.0,key="v30_budget")
                default_dir="LONG" if result['technical']['direction'].startswith("BULLISH") else "SHORT"
                direction=q3.selectbox("Direction",[default_dir,"SHORT" if default_dir=="LONG" else "LONG"],key="v30_direction")
                plan=build_atr_trade_plan(entry,atr,direction,budget)
                r1,r2,r3,r4=st.columns(4)
                r1.metric("ATR (14)",f"₹{atr:,.2f}"); r2.metric("Stop reference",f"₹{plan['stop_loss']:,.2f}")
                r3.metric("Target reference",f"₹{plan['target']:,.2f}"); r4.metric("Quantity",plan['quantity'])
                st.caption("Illustrative cash-equity sizing only; excludes costs, gaps and liquidity. This is not an options contract quantity or broker-ready order.")
            st.warning(result['disclaimer'])
        except Exception as exc:
            st.error(f"V30 assessment could not complete: {exc}")

elif page=="V29 Strategy Generator":
    st.title("V29 · Advanced Options Strategy Generator")
    st.caption("Builds illustrative expiry-payoff strategies from the last fetched Upstox option-chain snapshot. No orders are placed.")
    from options_strategy_v29 import generate_strategies
    chain=st.session_state.get("v15_chain")
    meta=st.session_state.get("v15_chain_meta",{})
    if not isinstance(chain,pd.DataFrame) or chain.empty:
        st.warning("No option-chain snapshot is loaded. Open V15 Live Options Intelligence, select an expiry and fetch the chain first.")
    else:
        st.caption(f"Source: Upstox snapshot · {meta.get('underlying','Unknown')} · Expiry {meta.get('expiry','Unknown')} · fetched {meta.get('fetched','Unknown')}")
        c1,c2,c3=st.columns(3)
        lot_size=c1.number_input("Lot size / quantity",min_value=1,value=1,step=1,key="v29_lot_size")
        iv_threshold=c2.number_input("Elevated IV threshold (%)",min_value=1.0,value=25.0,step=1.0,key="v29_iv_threshold")
        risk_budget=c3.number_input("Maximum capital risk budget (₹)",min_value=0.0,value=5000.0,step=500.0,key="v29_risk_budget")
        try:
            strategies=generate_strategies(chain,int(lot_size),float(iv_threshold))
            names=[x['name'] for x in strategies]
            selected_name=st.selectbox("Compare strategy",names,key="v29_strategy_choice")
            selected=next(x for x in strategies if x['name']==selected_name)
            a,b,c,d=st.columns(4)
            a.metric("Net premium / unit",f"₹{selected['net_premium_per_unit']:,.2f}")
            b.metric("Net debit / credit × quantity",f"₹{selected['net_debit_or_credit']:,.2f}")
            b.caption("Positive = net debit; negative = net credit")
            c.metric("Worst loss in displayed range",f"₹{abs(selected['max_loss_grid']):,.2f}")
            d.metric("Breakeven(s)",", ".join(f"{v:,.2f}" for v in selected['breakevens']) or "Not crossed in range")
            if selected['unlimited_profit']:
                st.success("Profit potential is theoretically unlimited for this long-option structure; displayed chart is a finite price window.")
            else:
                st.metric("Best profit in displayed range",f"₹{selected['max_profit_grid']:,.2f}")
            st.subheader("Selected strategy legs")
            legs=pd.DataFrame([{"Option":"Call" if l['side']=='CE' else "Put","Action":"Buy" if l['qty']>0 else "Sell",
                "Strike":l['strike'],"Premium":l['premium'],"Quantity":abs(l['qty'])*int(lot_size)} for l in selected['legs']])
            st.dataframe(legs,use_container_width=True,hide_index=True)
            fig=go.Figure(go.Scatter(x=selected['payoff']['Underlying at expiry'],y=selected['payoff']['Estimated P&L'],mode='lines',fill='tozeroy',name='Expiry P&L'))
            fig.add_hline(y=0,line_dash='dash'); fig.add_vline(x=float(pd.to_numeric(chain['Spot'],errors='coerce').dropna().iloc[0]),line_dash='dot',annotation_text='Spot')
            fig.update_layout(template='plotly_dark',height=420,title=f"{selected_name} · Illustrative expiry payoff",xaxis_title='Underlying at expiry',yaxis_title='Estimated P&L (₹)')
            st.plotly_chart(fig,use_container_width=True)
            loss=max(0.0,abs(float(selected['max_loss_grid'])))
            if risk_budget>0 and loss>0:
                st.info(f"Approximate strategy units within entered risk budget: {int(risk_budget//loss)} (based on worst loss in displayed price range; not a margin or guaranteed-risk calculation).")
            st.caption(selected['iv_context'])
            summary=pd.DataFrame([{"Strategy":x['name'],"Net premium/unit":x['net_premium_per_unit'],"Net debit/credit":x['net_debit_or_credit'],
                "Worst P&L in range":x['max_loss_grid'],"Best P&L in range":x['max_profit_grid'],"Breakevens":', '.join(map(str,x['breakevens']))} for x in strategies])
            st.subheader("Strategy comparison")
            st.dataframe(summary,use_container_width=True,hide_index=True)
            st.download_button("Download strategy comparison CSV",summary.to_csv(index=False).encode('utf-8'),file_name='v29_strategy_comparison.csv',mime='text/csv')
            st.warning("Premiums use option-chain LTP, not executable bid/ask. Lot size is manually entered and must be verified for the selected contract. Payoff is at expiry and excludes brokerage, taxes, slippage, margin, early exercise/assignment and liquidity effects. Max profit/loss values are limited to the displayed underlying-price range except the explicit unlimited-profit note. Educational decision support only; verify all legs and risk with your broker.")
        except (ValueError,KeyError,TypeError,IndexError) as exc:
            st.error(f"Could not build strategies from this snapshot: {exc}")

elif page=="V28 Options Intelligence":
    st.title("V28 · Advanced Options Intelligence")
    st.caption("Expiry-specific option-chain positioning, OI changes, PCR, Max Pain and IV overview using the last successfully fetched Upstox snapshot.")
    from options_intelligence_v28 import analyze_option_chain, strike_activity
    chain=st.session_state.get("v15_chain")
    meta=st.session_state.get("v15_chain_meta",{})
    if not isinstance(chain,pd.DataFrame) or chain.empty:
        st.warning("No live option-chain snapshot is loaded. Open V15 Live Options Intelligence, load expiries and fetch a chain first.")
    else:
        try:
            result=analyze_option_chain(chain)
            st.caption(f"Source: Upstox option-chain response · {meta.get('underlying','Unknown')} · Expiry {meta.get('expiry','Unknown')} · fetched {meta.get('fetched','Unknown')}")
            k1,k2,k3,k4,k5=st.columns(5)
            k1.metric("Underlying spot",f"{result['spot']:,.2f}" if result['spot'] is not None else "N/A")
            k2.metric("PCR",f"{result['pcr']:.3f}" if result['pcr'] is not None else "N/A")
            k3.metric("Max Pain",f"{result['max_pain']:,.0f}" if result['max_pain'] is not None else "N/A")
            k4.metric("Call OI wall",f"{result['max_call_oi_strike']:,.0f}" if result['max_call_oi_strike'] is not None else "N/A")
            k5.metric("Put OI wall",f"{result['max_put_oi_strike']:,.0f}" if result['max_put_oi_strike'] is not None else "N/A")
            st.write(f"Positioning description: **{result['positioning']}** · ATM strike: **{result['atm']:,.0f}**" if result['atm'] is not None else f"Positioning description: **{result['positioning']}**")
            a,b,c,d=st.columns(4)
            a.metric("Call OI change",f"{result['ce_oi_change']:+,.0f}")
            b.metric("Put OI change",f"{result['pe_oi_change']:+,.0f}")
            c.metric("Average Call IV",f"{result['avg_ce_iv']:.2f}%" if result['avg_ce_iv'] is not None else "N/A")
            d.metric("Average Put IV",f"{result['avg_pe_iv']:.2f}%" if result['avg_pe_iv'] is not None else "N/A")
            st.subheader("Strike-wise OI positioning")
            fig=go.Figure()
            fig.add_bar(x=result['strikes']['Strike'],y=result['strikes']['CE OI'],name='Call OI')
            fig.add_bar(x=result['strikes']['Strike'],y=result['strikes']['PE OI'],name='Put OI')
            fig.update_layout(barmode='group',height=390,xaxis_title='Strike',yaxis_title='Open interest')
            st.plotly_chart(fig,use_container_width=True)
            st.subheader("OI change and volume activity")
            activity=strike_activity(chain)
            st.dataframe(activity,use_container_width=True,hide_index=True)
            st.download_button("Download V28 strike analytics CSV",activity.to_csv(index=False).encode('utf-8'),file_name='v28_option_strike_activity.csv',mime='text/csv')
            st.subheader("Estimated expiry payout curve")
            curve=result['payout_curve']
            if not curve.empty:
                pf=go.Figure(go.Scatter(x=curve['Settlement'],y=curve['Estimated payout'],mode='lines+markers',name='Estimated payout'))
                pf.update_layout(height=300,xaxis_title='Hypothetical settlement',yaxis_title='Estimated intrinsic payout')
                st.plotly_chart(pf,use_container_width=True)
            with st.expander("Interpretation and limitations",expanded=True):
                for note in result['notes']: st.write('• '+note)
            st.warning("This is positioning analysis, not a directional prediction or strategy recommendation. IV averages are simple averages across available strikes, not ATM IV or a volatility surface. Confirm live bid/ask, liquidity, expiry, lot size and broker data timestamp before any trade.")
        except (ValueError,KeyError,TypeError) as exc:
            st.error(f"Could not analyze this option-chain snapshot: {exc}")

elif page=="V15 Live Options Intelligence":
    st.title("V15 · Live Options Intelligence")
    st.caption("Read-only option-chain analytics through the official Upstox REST API. This page does not place orders.")
    from live_options_chain import UNDERLYINGS, get_expiries, get_option_chain, flatten_chain, UpstoxOptionsError
    token = str(st.secrets.get("UPSTOX_ACCESS_TOKEN", "")).strip()
    if not token:
        st.warning("Upstox token not found. Add UPSTOX_ACCESS_TOKEN to .streamlit/secrets.toml, save, and restart Streamlit.")
        st.code('UPSTOX_ACCESS_TOKEN = "paste_your_token_locally"')
    else:
        a, b = st.columns([1, 1])
        label = a.selectbox("Underlying", list(UNDERLYINGS), key="v15_underlying")
        underlying_key = UNDERLYINGS[label]
        if b.button("Load available expiries", type="primary"):
            try:
                st.session_state["v15_expiries"] = get_expiries(token, underlying_key)
                st.session_state["v15_expiry_for"] = underlying_key
                st.success(f"Loaded {len(st.session_state['v15_expiries'])} expiry dates.")
            except UpstoxOptionsError as exc:
                st.error(str(exc))
        expiries = st.session_state.get("v15_expiries", []) if st.session_state.get("v15_expiry_for") == underlying_key else []
        if expiries:
            expiry = st.selectbox("Expiry", expiries, key="v15_expiry")
            if st.button("Fetch live option chain", type="primary", key="v15_fetch_chain"):
                try:
                    rows = get_option_chain(token, underlying_key, expiry)
                    chain = flatten_chain(rows)
                    st.session_state["v15_chain"] = chain
                    st.session_state["v15_chain_meta"] = {"underlying": label, "expiry": expiry, "fetched": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")}
                    st.success(f"Received {len(chain)} strikes from Upstox.")
                except UpstoxOptionsError as exc:
                    st.error(str(exc))
        chain = st.session_state.get("v15_chain")
        meta = st.session_state.get("v15_chain_meta", {})
        if isinstance(chain, pd.DataFrame) and not chain.empty and meta.get("underlying") == label:
            spot = pd.to_numeric(chain["Spot"], errors="coerce").dropna()
            ce_oi = pd.to_numeric(chain["CE OI"], errors="coerce").fillna(0)
            pe_oi = pd.to_numeric(chain["PE OI"], errors="coerce").fillna(0)
            total_ce, total_pe = float(ce_oi.sum()), float(pe_oi.sum())
            pcr = total_pe / total_ce if total_ce else float("nan")
            atm_idx = (pd.to_numeric(chain["Strike"], errors="coerce") - (float(spot.iloc[0]) if not spot.empty else 0)).abs().idxmin()
            atm = float(chain.loc[atm_idx, "Strike"])
            call_wall = float(chain.loc[ce_oi.idxmax(), "Strike"]) if len(chain) else float("nan")
            put_wall = float(chain.loc[pe_oi.idxmax(), "Strike"]) if len(chain) else float("nan")
            try:
                pain_strike, _ = max_pain(chain, "Strike", "CE OI", "PE OI")
            except Exception:
                pain_strike = float("nan")
            st.caption(f"{meta.get('underlying')} · {meta.get('expiry')} · Retrieved {meta.get('fetched')}")
            m1,m2,m3,m4,m5 = st.columns(5)
            m1.metric("Underlying spot", f"{float(spot.iloc[0]):,.2f}" if not spot.empty else "N/A")
            m2.metric("ATM strike", f"{atm:,.0f}")
            m3.metric("OI PCR", f"{pcr:.3f}" if np.isfinite(pcr) else "N/A")
            m4.metric("Max call OI strike", f"{call_wall:,.0f}")
            m5.metric("Max put OI strike", f"{put_wall:,.0f}")
            st.metric("Estimated Max Pain", f"{pain_strike:,.0f}" if np.isfinite(pain_strike) else "N/A")
            chart = go.Figure()
            chart.add_bar(x=chain["Strike"], y=ce_oi, name="Call OI")
            chart.add_bar(x=chain["Strike"], y=pe_oi, name="Put OI")
            chart.update_layout(barmode="group", title="Strike-wise Open Interest", xaxis_title="Strike", yaxis_title="Open Interest", height=430)
            st.plotly_chart(chart, use_container_width=True)
            st.subheader("Live option chain")
            st.dataframe(chain, use_container_width=True, hide_index=True)
            st.download_button("Download option chain CSV", chain.to_csv(index=False).encode("utf-8"), file_name=f"{label.lower().replace(' ','_')}_{meta.get('expiry')}_option_chain.csv", mime="text/csv")
            st.info("PCR and OI walls are descriptive positioning measures, not directional guarantees. Greeks and IV are supplied by Upstox; values may be unavailable for some strikes.")
        else:
            st.info("Select an underlying, load expiries, then fetch its option chain. No market values are shown until the API returns actual data.")
    st.caption("API reference: Upstox Option Contracts and Put/Call Option Chain endpoints. Access depends on your Upstox token, account permissions, and API availability.")

elif page=="V18 Opportunity Scanner":
    st.title("V18 · Multi-Stock Intraday Opportunity Scanner")
    st.caption("Read-only 5-minute / 15-minute confluence screen. Heuristic scores are not probabilities, recommendations, or executable signals.")
    from opportunity_scanner_v18 import scan_symbols
    default_symbols = "RELIANCE.NS,TCS.NS,INFY.NS,SBIN.NS,HDFCBANK.NS,ICICIBANK.NS,LT.NS,ITC.NS"
    raw_symbols = st.text_area("NSE symbols (comma-separated; use Yahoo Finance suffix .NS)", default_symbols, height=90)
    symbols = list(dict.fromkeys(x.strip().upper() for x in raw_symbols.split(",") if x.strip()))[:15]
    st.caption(f"Scanning {len(symbols)} symbols maximum per run. Data source: Yahoo Finance intraday history.")
    if st.button("Scan intraday opportunities", type="primary", disabled=not symbols):
        with st.spinner("Fetching 5-minute and 15-minute candles for each symbol..."):
            result_df = scan_symbols(symbols, load_data, min_score=2)
            st.session_state["v18_scan_results"] = result_df
            st.session_state["v18_scan_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result_df = st.session_state.get("v18_scan_results", pd.DataFrame())
    if isinstance(result_df, pd.DataFrame) and not result_df.empty:
        st.caption(f"Last scan: {st.session_state.get('v18_scan_time', 'Unknown')} · {len(result_df)} symbols")
        aligned = int((result_df["Status"] == "ALIGNED").sum())
        waiting = int((result_df["Status"] == "WAIT").sum())
        unavailable = int((result_df["Status"] == "FETCH ERROR").sum() + (result_df["Status"] == "INSUFFICIENT DATA").sum())
        a,b,c = st.columns(3)
        a.metric("Aligned directional screens", aligned)
        b.metric("WAIT", waiting)
        c.metric("Unavailable / insufficient", unavailable)
        st.dataframe(result_df, use_container_width=True, hide_index=True)
        st.download_button("Download scan results CSV", result_df.to_csv(index=False).encode("utf-8"),
                           file_name="v18_intraday_opportunity_scan.csv", mime="text/csv")
        st.info("ALIGNED means the 5-minute and 15-minute rule-based biases agree. It does not indicate a measured probability of success. Verify fresh quotes, spreads, liquidity, news, and risk independently.")
    else:
        st.info("Enter symbols and click Scan. Results appear only when both timeframes return enough valid candles.")
    st.caption("Yahoo Finance intraday history can be delayed, incomplete, rate-limited, or unavailable. This scanner does not use continuous Upstox ticks and never places orders.")

elif page=="V17 Intraday Signal Engine":
    st.title("V17 · Intraday Signal & Confluence Desk")
    st.caption("Read-only 5-minute / 15-minute technical confluence from Yahoo Finance candles. Heuristic scores are not forecasts or trade recommendations.")
    from intraday_signal_engine import combine_timeframes
    st.write(f"Selected symbol: **{symbol}**")
    if st.button("Fetch 5-minute and 15-minute candles", type="primary"):
        with st.spinner("Fetching intraday candles..."):
            five = load_data(symbol, "5d", "5m")
            fifteen = load_data(symbol, "1mo", "15m")
            st.session_state["v17_five"] = five
            st.session_state["v17_fifteen"] = fifteen
            st.session_state["v17_fetch_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    five = st.session_state.get("v17_five", pd.DataFrame())
    fifteen = st.session_state.get("v17_fifteen", pd.DataFrame())
    if isinstance(five, pd.DataFrame) and isinstance(fifteen, pd.DataFrame) and not five.empty and not fifteen.empty:
        result = combine_timeframes(five, fifteen)
        st.caption(f"Last fetch: {st.session_state.get('v17_fetch_time', 'Unknown')} · Source: Yahoo Finance; data may be delayed or unavailable.")
        st.subheader("Combined market bias")
        x1, x2, x3 = st.columns(3)
        x1.metric("Confluence bias", result["bias"])
        x2.metric("Combined score", result["score"])
        x3.metric("Timeframe agreement", result["agreement"])
        rows = []
        for snap in result["snapshots"]:
            rows.append({"Timeframe": snap["timeframe"], "Bias": snap["bias"], "Score": snap["score"],
                         "Last close": snap["close"], "RSI": snap["rsi"], "Relative volume": snap["relative_volume"],
                         "Evidence": " · ".join(snap["reasons"])})
        st.subheader("5-minute and 15-minute evidence")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.info(result["note"])
        if result["bias"] == "WAIT":
            st.warning("Timeframes are not aligned. The engine deliberately returns WAIT rather than forcing a directional setup.")
        st.caption("This module does not use Upstox streaming ticks and does not place orders. Yahoo Finance intraday history can be delayed, incomplete, rate-limited, or unavailable for some symbols.")
    else:
        st.info("Click Fetch to load the latest available 5-minute and 15-minute candles. No signal is generated until both datasets are available.")

elif page=="V16 AI Options Strategy Engine":
    st.title("V16 · AI Options Strategy Engine")
    st.caption("Read-only screening of the most recently fetched V15 option-chain snapshot. Scores are transparent heuristics, not AI predictions or trade recommendations.")
    from options_strategy_engine import analyze_option_opportunities, premium_risk_plan
    chain = st.session_state.get("v15_chain")
    meta = st.session_state.get("v15_chain_meta", {})
    if not isinstance(chain, pd.DataFrame) or chain.empty:
        st.warning("No option-chain snapshot is available. Open V15 Live Options Intelligence, fetch a chain successfully, then return here.")
    else:
        spot_values = pd.to_numeric(chain.get("Spot"), errors="coerce").dropna()
        if spot_values.empty:
            st.error("The fetched chain does not contain a valid underlying spot price.")
        else:
            spot = float(spot_values.iloc[0])
            st.caption(f"Snapshot: {meta.get('underlying', 'Unknown')} · {meta.get('expiry', 'Unknown expiry')} · {meta.get('fetched', 'Unknown time')}")
            c1, c2, c3 = st.columns(3)
            distance = c1.slider("Maximum strike distance from spot (%)", 0.5, 10.0, 3.0, 0.5)
            min_volume = c2.number_input("Minimum traded volume", min_value=0, value=1, step=100)
            min_oi = c3.number_input("Minimum open interest", min_value=0, value=1, step=100)
            try:
                opportunities = analyze_option_opportunities(chain, spot, distance, int(min_volume), int(min_oi))
                if opportunities.empty:
                    st.info("No contracts passed the selected liquidity and distance filters. This is not a buy/sell signal.")
                else:
                    st.subheader("Ranked option-contract screen")
                    st.dataframe(opportunities, use_container_width=True, hide_index=True)
                    st.download_button("Download screening results CSV", opportunities.to_csv(index=False).encode("utf-8"), file_name="options_opportunity_screen.csv", mime="text/csv")
                    selected = st.selectbox("Choose a contract for an illustrative premium risk plan", opportunities.index.tolist(), format_func=lambda i: f"{opportunities.loc[i, 'Side']} {opportunities.loc[i, 'Strike']:.0f} · premium {opportunities.loc[i, 'LTP']:.2f} · score {opportunities.loc[i, 'Score / 100']}/100")
                    row = opportunities.loc[selected]
                    st.markdown("#### Illustrative premium risk calculator")
                    x1, x2, x3 = st.columns(3)
                    stop_pct = x1.slider("Stop distance from premium (%)", 5, 60, 20, 5)
                    target_r = x2.selectbox("Target risk multiple", [1.0, 1.5, 2.0, 3.0], index=2)
                    lot_size = x3.number_input("Lot size (verify current exchange contract specification)", min_value=1, value=25, step=1)
                    lots = st.number_input("Number of lots", min_value=1, value=1, step=1)
                    plan = premium_risk_plan(float(row["LTP"]), float(stop_pct), float(target_r), int(lot_size), int(lots))
                    a,b,c,d = st.columns(4)
                    a.metric("Reference premium", f"₹{plan['entry_premium']:.2f}")
                    b.metric("Illustrative stop", f"₹{plan['stop_premium']:.2f}")
                    c.metric("Illustrative target", f"₹{plan['target_premium']:.2f}")
                    d.metric("Planned quantity", f"{plan['quantity']:,}")
                    e,f = st.columns(2)
                    e.metric("Planned loss at stop", f"₹{plan['maximum_planned_loss']:,.2f}")
                    f.metric("Planned gain at target", f"₹{plan['planned_profit_at_target']:,.2f}")
                    st.caption("Screening points: rising OI, volume/OI activity, moderate delta, IV filter and distance from spot. Missing fields receive no points. Verify contract lot size, bid/ask spread, liquidity, charges and live quotes before any decision.")
            except (ValueError, KeyError) as exc:
                st.error(f"Could not analyze this option-chain snapshot: {exc}")
    st.warning("This tool does not place orders. Option buying can lose the entire premium; stops may slip or fail during gaps and fast markets. Historical OI/volume snapshots do not prove institutional activity or future direction.")

elif page=="V37 Ultimate Platform & Paper Trading":
    st.title("V37 · Ultimate Trading Intelligence Platform")
    st.caption("40-module unified workspace: existing V28–V36 specialist pages remain intact; V37 adds an integrated capability directory, persistent paper-trade ledger, risk sizing and chronological validation tools.")
    from platform_ultimate_v37 import (catalog as v37_catalog, risk_position_size, add_paper_trade,
        list_paper_trades, close_paper_trade, paper_trade_metrics, walk_forward_ema_test)
    v37_catalog_data=v37_catalog()
    specialist=v37_catalog_data["specialist_tools"]
    capabilities=v37_catalog_data["platform_capabilities"]
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Specialist AI tools",len(specialist)); c2.metric("Platform capabilities",len(capabilities))
    c3.metric("Total roadmap modules",len(specialist)+len(capabilities)); c4.metric("Broker execution","Disabled")
    tabs=st.tabs(["Unified Command Overview","40-Module Directory","Paper Trading","Risk & Validation"])
    with tabs[0]:
        st.subheader("Unified intelligence workflow")
        st.markdown("**Market data → data-quality checks → specialist analysis → Central AI Brain → risk gate → human review → paper trade / broker hand-off.**")
        st.info("Existing V28–V36 features are preserved as separate navigation pages. V37 does not falsely mark every catalogue item as fully autonomous: some require connected data, manual input or future production hardening.")
        st.subheader("Implementation status")
        status_rows=[
          ("Available in inherited project","V28 options intelligence, V29 strategy generator, V30 trade confirmation, V31 copilot, V32 pattern analysis, V33 scanner, V34 portfolio/watchlists, V35 central brain, V36 Upstox feed monitor"),
          ("Added in V37","Persistent paper-trade ledger, risk-based position sizing, test-only EMA walk-forward evaluation, 40-module capability catalogue"),
          ("Requires additional integration / validation","Production multi-user authentication, background daemon hosting, push notifications, exchange-grade multi-asset feeds, verified institutional-flow data, broker order lifecycle"),
        ]
        st.table(pd.DataFrame(status_rows,columns=["Status","Details"]))
        st.warning("This is decision-support software, not an autonomous trading system. Market data may be delayed or incomplete. No real-money order placement is enabled.")
    with tabs[1]:
        st.subheader("25 specialist AI tools")
        st.dataframe(pd.DataFrame(specialist),use_container_width=True,hide_index=True)
        st.subheader("15 professional platform capabilities")
        st.dataframe(pd.DataFrame(capabilities),use_container_width=True,hide_index=True)
    with tabs[2]:
        st.subheader("Persistent paper-trade simulator")
        with st.form("v37_paper_trade_form"):
            p1,p2,p3=st.columns(3)
            pt_symbol=p1.text_input("Symbol",symbol,key="v37_pt_symbol").strip().upper()
            pt_side=p2.selectbox("Side",["LONG","SHORT"],key="v37_pt_side")
            pt_qty=p3.number_input("Quantity",min_value=1,value=1,step=1,key="v37_pt_qty")
            p4,p5,p6=st.columns(3)
            pt_entry=p4.number_input("Entry price",min_value=0.01,value=100.0,key="v37_pt_entry")
            pt_stop=p5.number_input("Stop (0 = none)",min_value=0.0,value=0.0,key="v37_pt_stop")
            pt_target=p6.number_input("Target (0 = none)",min_value=0.0,value=0.0,key="v37_pt_target")
            pt_notes=st.text_input("Notes",key="v37_pt_notes")
            save_pt=st.form_submit_button("Save simulated trade")
        if save_pt:
            try:
                tid=add_paper_trade(pt_symbol,pt_side,pt_qty,pt_entry,pt_stop or None,pt_target or None,pt_notes)
                st.success(f"Paper trade #{tid} saved locally.")
            except Exception as exc: st.error(str(exc))
        trades=list_paper_trades(); metrics=paper_trade_metrics(trades)
        m1,m2,m3,m4=st.columns(4)
        m1.metric("Paper trades",metrics['trades']); m2.metric("Closed",metrics['closed'])
        m3.metric("Win rate",f"{metrics['win_rate_pct']:.1f}%" if metrics['win_rate_pct'] is not None else "—")
        m4.metric("Net realised P&L",f"{metrics['net_pnl']:,.2f}")
        if not trades.empty:
            st.dataframe(trades,use_container_width=True,hide_index=True)
            open_trades=trades[trades.status=="OPEN"]
            if not open_trades.empty:
                with st.form("v37_close_paper_trade"):
                    close_id=st.selectbox("Open paper trade",open_trades.id.tolist(),format_func=lambda i:f"#{i} · {open_trades.loc[open_trades.id==i,'symbol'].iloc[0]}")
                    close_px=st.number_input("Simulated exit price",min_value=0.01,value=100.0)
                    close_submit=st.form_submit_button("Close paper trade")
                if close_submit:
                    if close_paper_trade(close_id,close_px): st.success("Paper trade closed."); st.rerun()
                    else: st.error("Trade could not be closed.")
            st.download_button("Download paper-trade ledger CSV",trades.to_csv(index=False).encode(),"v37_paper_trades.csv","text/csv")
        else: st.info("No paper trades recorded yet. The ledger is stored in a separate V37 SQLite database; existing V34 portfolio records are not modified.")
    with tabs[3]:
        st.subheader("Risk-based position sizing")
        r1,r2,r3,r4=st.columns(4)
        capital=r1.number_input("Account capital",min_value=1.0,value=100000.0,step=5000.0)
        risk_pct=r2.number_input("Risk per trade (%)",min_value=0.01,max_value=5.0,value=1.0,step=0.1)
        entry_px=r3.number_input("Planned entry",min_value=0.01,value=100.0)
        stop_px=r4.number_input("Stop-loss price",min_value=0.01,value=98.0)
        lot=r1.number_input("Lot size / quantity step",min_value=1,value=1,step=1)
        if st.button("Calculate position size",key="v37_risk_calc"):
            try:
                result=risk_position_size(capital,risk_pct,entry_px,stop_px,int(lot))
                a,b,c=st.columns(3); a.metric("Suggested quantity",result['quantity']); b.metric("Risk budget",f"{result['risk_budget']:,.2f}"); c.metric("Estimated stop risk",f"{result['estimated_stop_risk']:,.2f}")
                st.caption(result['warning'])
            except Exception as exc: st.error(str(exc))
        st.divider(); st.subheader("Chronological walk-forward example")
        st.caption("Uses currently loaded historical closes for the selected symbol. Test window is kept chronologically after the training window; this is a simple baseline, not a production strategy optimiser.")
        if st.button("Run EMA walk-forward test",key="v37_walkforward"):
            if raw is None or raw.empty: st.warning("No historical candles are available.")
            else:
                try:
                    wf=walk_forward_ema_test(raw["Close"])
                    st.json(wf)
                except Exception as exc: st.error(f"Validation unavailable: {exc}")

elif page=="Central AI Command Centre":
    from central_ai_brain_v35 import TOOL_CATALOG, analyze_market as analyze_central_market
    st.markdown("""<div class="ati-hero"><h1>🧠 Central AI Command Centre</h1>
    <p>Dedicated AI workspace · 25 specialist tools · one evidence-led market assessment · human approval required</p></div>""", unsafe_allow_html=True)
    st.caption(f"Active instrument: {symbol} · Interval: {interval} · History: {period}")
    if data is None or data.empty:
        st.warning("No market history is available. Select a valid instrument in the sidebar.")
    else:
        with st.spinner("Coordinating available specialist analysis..."):
            brain = analyze_central_market(data)
        a,b,c,d=st.columns(4)
        a.metric("Instrument",symbol)
        b.metric("AI evidence score",f"{brain.get('score',0):+d}")
        c.metric("Directional assessment",brain.get('direction','WAIT'))
        d.metric("Evidence quality",brain.get('quality','N/A'))
        st.subheader("Central decision summary")
        st.info("This is a deterministic, rule-based evidence synthesis—not 25 autonomous trained models. It only scores inputs currently available to the platform.")
        left,right=st.columns([1.2,1])
        with left:
            st.markdown("#### Evidence supporting the assessment")
            for item in brain.get('evidence',[]): st.success(item)
            if not brain.get('evidence'): st.info("No positive evidence supplied.")
        with right:
            st.markdown("#### Missing inputs and cautions")
            for item in brain.get('warnings',[]): st.warning(item)
            st.metric("Latest close",f"{brain.get('last_close',0):,.2f}" if brain.get('last_close') else "—")
            st.metric("RSI (14)",f"{brain.get('rsi'):.1f}" if brain.get('rsi') is not None else "—")
            st.metric("ATR",f"{brain.get('atr'):.3f}" if brain.get('atr') is not None else "—")
        st.subheader("Reference levels · analysis only")
        lv1,lv2,lv3=st.columns(3)
        lv1.metric("Support reference",f"{brain.get('support',0):,.2f}" if brain.get('support') else "—")
        lv2.metric("Resistance reference",f"{brain.get('resistance',0):,.2f}" if brain.get('resistance') else "—")
        lv3.metric("Breakout state",str(brain.get('breakout','N/A')))
        st.divider()
        st.subheader("25 specialist tools")
        st.dataframe(pd.DataFrame([{'#':n,'AI specialist':name,'Scope':desc} for n,name,desc in TOOL_CATALOG]),use_container_width=True,hide_index=True)
        st.caption("Unavailable options-chain, verified FII/DII, news or multi-timeframe inputs are not invented. The Brain does not place orders.")

elif page=="AI Market & Option Chain Assistant":
    from performance_analytics_v41 import strategy_advice
    st.markdown("""<div class="ati-hero"><h1>AI Market &amp; Option Chain Assistant</h1>
    <p>Scalping · Intraday · Hedging · Long-term context · Technical and options intelligence</p></div>""", unsafe_allow_html=True)
    h1,h2=st.columns([3,1])
    h1.markdown(f"**Instrument:** `{symbol}` · **Chart interval:** `{interval}` · **History:** `{period}`")
    if h2.button("↻ Refresh snapshot",use_container_width=True,key="v41_assistant_refresh"):
        st.cache_data.clear(); st.rerun()
    if data is not None and not data.empty:
        last=data.iloc[-1]; prev=data.iloc[-2] if len(data)>1 else last
        change=(float(last.Close)/float(prev.Close)-1)*100 if float(prev.Close) else 0
        metric_cols=st.columns(5)
        metric_cols[0].metric("Spot / latest close",f"{float(last.Close):,.2f}",f"{change:+.2f}%")
        metric_cols[1].metric("VWAP proxy",f"{(data.Close*data.Volume).tail(20).sum()/data.Volume.tail(20).sum():,.2f}" if data.Volume.tail(20).sum()>0 else "—")
        metric_cols[2].metric("RSI (14)",f"{float(last.RSI):.1f}" if pd.notna(last.RSI) else "—")
        metric_cols[3].metric("ATR",f"{float(last.ATR):.2f}" if pd.notna(last.ATR) else "—")
        metric_cols[4].metric("Volume",f"{float(last.Volume):,.0f}")
    else:
        st.warning("Market snapshot unavailable. No sample price or indicator values are substituted.")
    tabs=st.tabs(["Strategy","Chart & History","Option Chain","News & AI Context"])
    with tabs[0]:
        st.markdown("#### AI-supported trade ideas")
        st.caption("These are transparent rule-based candidate assessments using the loaded OHLCV history. They are not guaranteed signals or personal financial advice.")
        modes=[("Scalping","1m–5m"),("Intraday","15m–1h"),("Hedging","Options / portfolio protection")]
        cols=st.columns(3)
        for col,(mode,tag) in zip(cols,modes):
            with col:
                result=strategy_advice(data,mode)
                st.markdown(f"<div class='ati-terminal-card'><h3>{mode}</h3><span class='small-note'>{tag}</span></div>",unsafe_allow_html=True)
                st.metric("AI bias",result.get('bias','WAIT'))
                st.write(result.get('summary',''))
                if result.get('entry_zone'):
                    st.write(f"**Entry reference:** {result['entry_zone'][0]:,.2f} – {result['entry_zone'][1]:,.2f}")
                    st.write(f"**Stop reference:** {result['stop']:,.2f}")
                    st.write(f"**Target reference:** {result['target']:,.2f}")
                    st.write(f"**R:R reference:** 1 : {result['risk_reward']:.2f}" if result.get('risk_reward') else "**R:R:** —")
                else:
                    st.warning("No actionable entry levels: wait for stronger confirmation.")
                with st.expander("Evidence and risk checks"):
                    for item in result.get('evidence',[]): st.success(item)
                    for item in result.get('warnings',[]): st.warning(item)
                    st.write("Horizon:",result.get('horizon','—'))
        st.warning("Scalping requires a genuine 1m/5m feed. The current assessment uses the interval selected in the sidebar; it does not silently convert daily candles into scalping data.")
        st.info("Hedging: the platform will not invent a put/call strike, premium, expiry, IV, Greeks or hedge ratio. Load a verified option chain and portfolio exposure in the Options modules before choosing a hedge.")
    with tabs[1]:
        st.subheader("Chart and historical context")
        if data is not None and not data.empty:
            st.plotly_chart(price_chart(data.tail(250),f"{symbol} · candles, EMA, volume, RSI and MACD"),use_container_width=True)
            st.dataframe(data.tail(30),use_container_width=True)
        else: st.info("No candle history available.")
    with tabs[2]:
        st.subheader("Option-chain analysis")
        st.info("No live option-chain values are fabricated in this assistant. Select the correct underlying and expiry in a connected provider module.")
        for label,target in [("V15 Live Options Intelligence","V15 Live Options Intelligence"),("V28 Options Intelligence","V28 Options Intelligence"),("V29 Strategy Generator","V29 Strategy Generator"),("Options & OI Analytics","Options & OI Analytics")]:
            if st.button("Open "+label+" →",key="v41_opt_"+target,use_container_width=True): navigate_to(target); st.rerun()
    with tabs[3]:
        st.subheader("News, macro and market context")
        st.write("News sentiment, economic events and FII/DII flow are only included when their source modules provide verified data.")
        for label,target in [("Global Market News","Global Market News"),("Multi-Source News & Forex Factory","Multi-Source News & Forex Factory"),("V35 Central AI Brain","Central AI Command Centre")]:
            if st.button("Open "+label+" →",key="v41_ctx_"+target,use_container_width=True): navigate_to(target); st.rerun()

elif page=="V43 Live Market Intelligence":
    from market_intelligence_v43 import (scan_market_frame, data_quality_report, add_alert_rule,
        list_alert_rules, deactivate_alert_rule, evaluate_feed_alerts, list_alert_events)
    from live_market_feed import start_live_feed, stop_live_feed, get_feed_status, get_market_data
    from live_operations_v36 import build_operations_report
    st.markdown("""<div class="ati-hero"><h1>V43 · Live Market Intelligence & Monitoring</h1>
    <p>Read-only Upstox streaming · market-data health · historical opportunity scan · persistent price alerts</p></div>""", unsafe_allow_html=True)
    st.warning("Live streaming requires a valid local Upstox token and the Upstox SDK. Historical Yahoo candles are not a substitute for live ticks. This workspace is read-only and does not place orders.")
    v43_tabs=st.tabs(["Live Feed Monitor","Opportunity Scanner","Smart Alert Centre","Data Quality"])
    with v43_tabs[0]:
        st.subheader("Upstox V3 market stream")
        default_keys="NSE_INDEX|Nifty 50, NSE_INDEX|Nifty Bank, NSE_INDEX|India VIX"
        key_text=st.text_input("Upstox instrument keys (comma-separated)",value=default_keys,key="v43_keys")
        st.caption("Use valid Upstox instrument keys from your broker instrument master. The defaults are examples and may require verification against your account/API version.")
        c1,c2,c3=st.columns(3)
        with c1:
            if st.button("▶ Start live feed",type="primary",key="v43_start"):
                keys=[x.strip() for x in key_text.split(",") if x.strip()]
                st.info(start_live_feed(keys))
        with c2:
            if st.button("■ Stop live feed",key="v43_stop"): st.info(stop_live_feed())
        with c3:
            if st.button("↻ Refresh feed status",key="v43_refresh"): st.rerun()
        status=get_feed_status(); snapshot=get_market_data(); report=build_operations_report(snapshot,status)
        m1,m2,m3=st.columns(3); m1.metric("Feed state",report.get("health","Unknown")); m2.metric("Messages",report.get("message_count",0)); m3.metric("Recognised instruments",report.get("instrument_count",0))
        st.write("**Connection:**",status.get("message","")," · **Last message:**",status.get("last_message_at") or "Not received")
        if report.get("instruments"):
            st.dataframe(pd.DataFrame([{"Instrument key":k,**v} for k,v in report["instruments"].items()]),use_container_width=True,hide_index=True)
            fired=evaluate_feed_alerts(report["instruments"])
            for event in fired: st.warning(f"PRICE ALERT: {event['name']} · {event['instrument_key']} LTP {event['ltp']:,.2f} {event['direction']} {event['threshold']:,.2f}")
        for warning in report.get("warnings",[]): st.warning(warning)
        st.caption("The Streamlit process must remain active for this in-process websocket. This is not a managed 24/7 background service or guaranteed push-notification system.")
    with v43_tabs[1]:
        st.subheader("Historical opportunity scan")
        st.write(f"Current selected instrument: **{symbol}** · interval **{interval}**")
        result=scan_market_frame(data,symbol,interval)
        a,b,c=st.columns(3); a.metric("Scan bias",result.get("signal","WAIT")); b.metric("Evidence score",result.get("score",0)); c.metric("Last candle close",f"{result['last_close']:,.2f}" if result.get("last_close") is not None else "Unavailable")
        for item in result.get("evidence",[]): st.success(item)
        for item in result.get("warnings",[]): st.warning(item)
        st.caption(result.get("disclaimer","Scanner requires valid historical OHLCV candles."))
        st.info("This scanner analyses the currently selected Yahoo Finance historical series. It does not scan every exchange-listed symbol or claim live tick coverage.")
    with v43_tabs[2]:
        st.subheader("Persistent live-price alert rules")
        with st.form("v43_alert_form"):
            n1,n2=st.columns(2)
            alert_name=n1.text_input("Alert name",value=symbol+" price alert")
            instrument_key=n2.text_input("Upstox instrument key",value="NSE_EQ|INE002A01018")
            n3,n4=st.columns(2)
            direction=n3.selectbox("Trigger when LTP is",["above","below"])
            threshold=n4.number_input("Threshold price",min_value=0.01,value=float(data.Close.iloc[-1]) if data is not None and not data.empty else 100.0)
            submitted=st.form_submit_button("Save alert rule")
        if submitted:
            try: st.success(f"Saved alert rule #{add_alert_rule(alert_name,instrument_key,direction,threshold)}")
            except Exception as exc: st.error(str(exc))
        rules=list_alert_rules()
        if not rules.empty:
            st.dataframe(rules,use_container_width=True,hide_index=True)
            active_ids=rules[rules.active==1]["id"].astype(int).tolist()
            if active_ids:
                rid=st.selectbox("Deactivate rule ID",active_ids,key="v43_deactivate_id")
                if st.button("Deactivate selected rule",key="v43_deactivate"):
                    deactivate_alert_rule(rid); st.success("Rule deactivated."); st.rerun()
        else: st.info("No alert rules saved yet.")
        events=list_alert_events()
        st.markdown("#### Trigger history")
        if not events.empty: st.dataframe(events,use_container_width=True,hide_index=True)
        else: st.caption("No alert triggers recorded. Rules are evaluated when recognised feed quotes are received/refreshed in this workspace.")
    with v43_tabs[3]:
        st.subheader("Selected historical data validation")
        quality=data_quality_report(data,symbol)
        st.json(quality)
        st.caption("Quality checks cover required OHLCV fields, missing values and internally inconsistent candle ranges. They cannot verify exchange provenance or guarantee data completeness.")

elif page=="V42 AI Decision & Broker Hub":
    from ai_decision_broker_v42 import (evaluate_strategy as evaluate_v42_strategy,
        analyze_hedge_candidates, position_size as v42_position_size,
        broker_order_preview, upstox_profile)
    from sim_execution_v39 import create_order as create_paper_order, list_orders as list_paper_orders
    st.markdown("""<div class="ati-hero"><h1>V42 · AI Trade Decision & Broker Hub</h1>
    <p>Central Brain coordination · Scalping · Intraday · Hedging · risk validation · Upstox read-only connection · paper execution</p></div>""", unsafe_allow_html=True)
    st.caption(f"Selected instrument: {symbol} · Loaded interval: {interval} · History: {period}")
    st.warning("Decision support is rule-based and evidence-led, not a guaranteed prediction. Real-money order submission is disabled. Review every setup before paper execution.")
    v42_tabs=st.tabs(["AI Decision Centre","Options Hedge Lab","Risk & Paper Execution","Broker Connection"])
    with v42_tabs[0]:
        st.subheader("Three independent strategy assessments")
        risk_col,cap_col=st.columns(2)
        with risk_col: risk_pct=st.number_input("Risk budget (%)",min_value=0.1,max_value=5.0,value=1.0,step=0.1,key="v42_risk_pct")
        with cap_col: capital=st.number_input("Reference capital",min_value=0.0,value=100000.0,step=10000.0,key="v42_capital")
        mt1,mt2,mt3=st.columns(3)
        mt_inputs={"5m":mt1.selectbox("5m context",["Not supplied","Bullish","Bearish","Neutral"],key="v42_5m"),
                   "15m":mt2.selectbox("15m context",["Not supplied","Bullish","Bearish","Neutral"],key="v42_15m"),
                   "1h":mt3.selectbox("1h context",["Not supplied","Bullish","Bearish","Neutral"],key="v42_1h")}
        mt_map={k:v for k,v in mt_inputs.items() if v!="Not supplied"}
        cards=st.columns(3)
        v42_results={}
        for col,mode in zip(cards,["Scalping","Intraday","Hedging"]):
            with col:
                result=evaluate_v42_strategy(data,mode,interval,risk_pct,capital,mt_map)
                v42_results[mode]=result
                st.markdown(f"<div class='ati-terminal-card'><h3>{mode}</h3><span class='small-note'>{result.get('horizon','')}</span></div>",unsafe_allow_html=True)
                st.metric("Decision",result.get("bias","WAIT"),f"Evidence score {result.get('score',0):+d}")
                st.write(result.get("summary",""))
                if result.get("entry_zone"):
                    st.write(f"**Entry zone:** {result['entry_zone'][0]:,.2f} – {result['entry_zone'][1]:,.2f}")
                    st.write(f"**Stop:** {result['stop']:,.2f} · **Target:** {result['target']:,.2f}")
                    st.write(f"**Risk/reward:** 1 : {result['risk_reward']:.2f}")
                    if result.get("illustrative_quantity") is not None: st.write(f"**Indicative quantity:** {result['illustrative_quantity']:,}")
                else: st.info("No trade levels generated. Wait for confirmation.")
                with st.expander("Evidence, missing inputs & risk gates"):
                    for item in result.get("evidence",[]): st.success(item)
                    for item in result.get("warnings",[]): st.warning(item)
        if st.button("↻ Re-run all AI assessments",type="primary",key="v42_recalc"):
            st.rerun()
        st.caption("Scalping is automatically gated to WAIT unless the selected chart interval is 1m, 2m or 5m. Multi-timeframe labels above are manual context inputs, not live fetched candles.")
    with v42_tabs[1]:
        st.subheader("Hedging analysis from an actual option-chain snapshot")
        st.write("Upload a CSV exported from the existing Upstox option-chain module. Candidate rows are ranked from supplied strikes, premiums and OI only.")
        hedge_side=st.selectbox("Exposure to protect",["PROTECT_LONG","PROTECT_SHORT"],format_func=lambda x:"Protect a long position (PUT candidates)" if x=="PROTECT_LONG" else "Protect a short position (CALL candidates)",key="v42_hedge_side")
        spot_ref=st.number_input("Underlying spot/reference price",min_value=0.0,value=float(data.Close.iloc[-1]) if data is not None and not data.empty else 0.0,key="v42_spot_ref")
        min_oi=st.number_input("Minimum open interest",min_value=0,value=0,step=100,key="v42_min_oi")
        chain_file=st.file_uploader("Upload option-chain CSV",type=["csv"],key="v42_chain_csv")
        if chain_file is not None:
            try:
                chain_frame=pd.read_csv(chain_file)
                candidates=analyze_hedge_candidates(chain_frame,spot_ref,hedge_side,int(min_oi))
                if candidates.empty: st.warning("No usable candidate rows. CSV must include Strike, PE LTP, PE OI for long protection or CE LTP, CE OI for short protection.")
                else:
                    st.dataframe(candidates.head(30),use_container_width=True,hide_index=True)
                    st.download_button("Download hedge candidate analysis",candidates.to_csv(index=False),file_name="v42_hedge_candidates.csv",mime="text/csv")
                    st.info("These are ranked contract candidates, not an instruction to buy. Confirm expiry, bid/ask spread, lot size, Greeks, liquidity and portfolio delta before choosing a hedge.")
            except Exception as exc: st.error(f"Could not analyse uploaded chain: {exc}")
        else: st.info("No option chain uploaded. The assistant will not fabricate strikes, premiums, expiry or Greeks.")
    with v42_tabs[2]:
        st.subheader("Risk validation and paper-only order ticket")
        z1,z2,z3,z4=st.columns(4)
        with z1: z_cap=st.number_input("Capital",min_value=1.0,value=100000.0,key="v42_size_cap")
        with z2: z_risk=st.number_input("Risk %",min_value=0.1,max_value=5.0,value=1.0,key="v42_size_risk")
        with z3: z_entry=st.number_input("Entry reference",min_value=0.01,value=float(data.Close.iloc[-1]) if data is not None and not data.empty else 100.0,key="v42_size_entry")
        with z4: z_stop=st.number_input("Stop reference",min_value=0.01,value=float(data.Close.iloc[-1]*0.99) if data is not None and not data.empty else 99.0,key="v42_size_stop")
        lot=st.number_input("Lot size (1 for shares)",min_value=1,value=1,step=1,key="v42_lot")
        try:
            sizing=v42_position_size(z_cap,z_risk,z_entry,z_stop,int(lot))
            a,b,c=st.columns(3); a.metric("Risk budget",f"₹{sizing['risk_budget']:,.2f}"); b.metric("Quantity",f"{sizing['quantity']:,}"); c.metric("Estimated stop risk",f"₹{sizing['estimated_stop_risk']:,.2f}")
            st.caption(sizing["warning"])
        except Exception as exc: st.error(str(exc))
        st.divider(); st.markdown("#### Create a paper order from a reviewed AI setup")
        selected_mode=st.selectbox("Strategy setup",["Scalping","Intraday","Hedging"],key="v42_paper_mode")
        selected_result=v42_results.get(selected_mode,{})
        if selected_result.get("bias") in {"LONG","SHORT"} and selected_result.get("entry_zone"):
            paper_qty=st.number_input("Paper quantity",min_value=1,value=max(1,int(selected_result.get("illustrative_quantity") or 1)),key="v42_paper_qty")
            paper_price=st.number_input("Paper reference price",min_value=0.01,value=float(selected_result["last_price"]),key="v42_paper_price")
            paper_side="BUY" if selected_result["bias"]=="LONG" else "SELL"
            st.write(f"AI assessment: **{selected_result['bias']}** · Paper side: **{paper_side}**")
            if st.button("Create PAPER MARKET order",type="primary",key="v42_create_paper"):
                try:
                    oid=create_paper_order(symbol,paper_side,"MARKET",paper_qty,reference_price=paper_price,notes=f"V42 reviewed {selected_mode} setup; AI score {selected_result.get('score')}")
                    st.success(f"Paper order #{oid} created. No broker order was sent.")
                except Exception as exc: st.error(f"Paper order failed: {exc}")
        else: st.info("Selected strategy is WAIT or lacks valid levels. No paper order ticket is offered.")
        st.markdown("#### Recent paper orders")
        try:
            recent_orders=list_paper_orders()
            if not recent_orders.empty: st.dataframe(recent_orders.head(20),use_container_width=True,hide_index=True)
            else: st.info("No paper orders recorded yet.")
        except Exception as exc: st.warning(f"Paper ledger unavailable: {exc}")
    with v42_tabs[3]:
        st.subheader("Upstox broker connection · read-only")
        st.write("The broker gateway checks your authenticated profile only. V42 does not submit real-money orders.")
        if st.button("Test Upstox connection",type="primary",key="v42_test_broker"):
            try: token=st.secrets.get("UPSTOX_ACCESS_TOKEN","")
            except Exception: token=""
            report=upstox_profile(token)
            if report.get("ok"):
                st.success(report["message"])
                st.write("Broker:",report.get("broker")); st.write("Profile name:",report.get("user_name") or "Not returned")
            else: st.error(report.get("message","Connection unavailable."))
            st.caption("Access token is never displayed. Store it in local .streamlit/secrets.toml, not in chat or source code.")
        st.markdown("#### Broker order review preview (not executable)")
        with st.form("v42_broker_preview_form"):
            pv_symbol=st.text_input("Broker instrument key",value="NSE_EQ|INE002A01018")
            pv_side=st.selectbox("Transaction",["BUY","SELL"])
            pv_qty=st.number_input("Quantity",min_value=1,value=1,step=1)
            pv_type=st.selectbox("Order type",["MARKET","LIMIT","SL","SL-M"])
            pv_price=st.number_input("Price (required for LIMIT/SL)",min_value=0.0,value=0.0)
            submitted=st.form_submit_button("Validate order preview")
        if submitted:
            try:
                preview=broker_order_preview(pv_symbol,pv_side,int(pv_qty),pv_type,pv_price if pv_type in {"LIMIT","SL"} else None)
                st.json(preview)
                st.error("PREVIEW ONLY — real broker execution is disabled in V42. No order endpoint was called.")
            except Exception as exc: st.error(str(exc))

elif page=="V41 Performance Analytics":
    from sim_execution_v39 import list_positions
    from performance_analytics_v41 import summarize_closed_positions, daily_pnl
    st.markdown("""<div class="ati-hero"><h1>V41 · Professional Performance Analytics</h1>
    <p>Paper-trade performance · P&amp;L tracking · win/loss analysis · fees · drawdown and trade review</p></div>""",unsafe_allow_html=True)
    positions=list_positions()
    summary=summarize_closed_positions(positions)
    a,b,c,d,e=st.columns(5)
    a.metric("Closed trades",summary['closed_trades'])
    b.metric("Win rate",f"{summary['win_rate_pct']:.1f}%" if summary['win_rate_pct'] is not None else "—")
    c.metric("Net P&L",f"₹{summary['net_pnl']:,.2f}")
    d.metric("Profit factor",f"{summary['profit_factor']:.2f}" if summary['profit_factor'] is not None and np.isfinite(summary['profit_factor']) else "—")
    e.metric("Estimated fees",f"₹{summary['fees']:,.2f}")
    st.caption("Metrics are calculated from V39's local paper-execution ledger only. They do not include broker trades unless imported separately. No sample trades are inserted.")
    if summary['closed_trades']:
        p1,p2,p3,p4=st.columns(4)
        p1.metric("Winning trades",summary['wins']); p2.metric("Losing trades",summary['losses'])
        p3.metric("Average win",f"₹{summary['avg_win']:,.2f}" if summary['avg_win'] is not None else "—")
        p4.metric("Average loss",f"₹{summary['avg_loss']:,.2f}" if summary['avg_loss'] is not None else "—")
        pnl=daily_pnl(positions)
        if not pnl.empty:
            fig=go.Figure(); fig.add_trace(go.Bar(x=pnl['Date'],y=pnl['Net P&L'],name='Daily net P&L'))
            fig.add_trace(go.Scatter(x=pnl['Date'],y=pnl['Cumulative P&L'],name='Cumulative P&L',yaxis='y2'))
            fig.update_layout(title='Daily and cumulative paper-trading P&L',template='plotly_dark',height=380,
                yaxis=dict(title='Daily P&L (₹)'),yaxis2=dict(title='Cumulative P&L (₹)',overlaying='y',side='right'))
            st.plotly_chart(fig,use_container_width=True)
        st.subheader("Closed paper positions")
        closed=positions[positions.status.astype(str).str.upper()=='CLOSED'].copy()
        st.dataframe(closed,use_container_width=True,hide_index=True)
        st.download_button("Download performance CSV",closed.to_csv(index=False).encode(),"v41_paper_performance.csv","text/csv")
        st.subheader("Trade outcome distribution")
        outcome=pd.DataFrame({'Outcome':['Wins','Losses','Flat'],'Count':[summary['wins'],summary['losses'],summary['closed_trades']-summary['wins']-summary['losses']]})
        st.bar_chart(outcome.set_index('Outcome'))
    else:
        st.info("No closed V39 paper trades yet. Use V39 Paper Execution Simulator to create and close simulated positions; analytics will populate automatically.")
    st.subheader("Open paper positions")
    opened=positions[positions.status.astype(str).str.upper()=='OPEN'] if not positions.empty else positions
    if not opened.empty: st.dataframe(opened,use_container_width=True,hide_index=True)
    else: st.caption("No open paper positions in the V39 ledger.")
    st.warning("Performance statistics are descriptive, not predictive. Small samples, simulated fills, missing fees and market-data limitations can materially distort results.")

elif page=="V40 Advanced Backtesting Lab":
    from backtesting_lab_v40 import STRATEGIES, run_backtest, compare_strategies
    st.markdown("""<div class="ati-hero"><h1>V40 · Advanced Backtesting Lab</h1>
    <p>Chronological strategy simulation · realistic cost assumptions · out-of-sample review · equity and drawdown analytics</p></div>""", unsafe_allow_html=True)
    st.caption(f"Instrument: {symbol} · Loaded history: {period} · Interval: {interval}. Results use the currently loaded OHLCV candles and are historical simulations, not forecasts or guaranteed future performance.")
    if data is None or data.empty:
        st.warning("No OHLCV data is available. Select a valid symbol and history interval in the sidebar.")
    else:
        st.info("Execution convention: a signal calculated from a completed candle is applied to the following candle's return. Estimated transaction costs are charged on changes in exposure. This reduces look-ahead bias but does not model intrabar fills, gaps, liquidity, partial fills or market impact.")
        with st.form("v40_backtest_controls"):
            c1,c2,c3,c4=st.columns(4)
            strategy=c1.selectbox("Strategy",STRATEGIES,index=0)
            capital=c2.number_input("Starting capital",min_value=1000.0,value=100000.0,step=10000.0)
            cost_bps=c3.number_input("Estimated cost per turnover (bps)",min_value=0.0,value=10.0,step=1.0)
            test_fraction=c4.slider("Out-of-sample portion",min_value=0.10,max_value=0.50,value=0.30,step=0.05)
            p1,p2,p3,p4=st.columns(4)
            fast=p1.number_input("EMA fast",min_value=2,max_value=100,value=10,step=1)
            slow=p2.number_input("EMA slow",min_value=3,max_value=250,value=30,step=1)
            rsi_period=p3.number_input("RSI period",min_value=2,max_value=50,value=14,step=1)
            breakout_window=p4.number_input("Breakout window",min_value=5,max_value=100,value=20,step=1)
            q1,q2,q3=st.columns(3)
            oversold=q1.number_input("RSI oversold",min_value=5.0,max_value=45.0,value=30.0,step=1.0)
            overbought=q2.number_input("RSI overbought",min_value=55.0,max_value=95.0,value=70.0,step=1.0)
            allow_short=q3.checkbox("Allow short signals",value=False)
            run=st.form_submit_button("Run historical backtest",type="primary",use_container_width=True)
        if run:
            try:
                metrics,curve,trades=run_backtest(data,strategy,initial_capital=capital,cost_bps=cost_bps,
                    fast=int(fast),slow=int(slow),rsi_period=int(rsi_period),oversold=oversold,
                    overbought=overbought,breakout_window=int(breakout_window),allow_short=allow_short,
                    test_fraction=test_fraction)
                comparison=compare_strategies(data,initial_capital=capital,cost_bps=cost_bps,
                    fast=int(fast),slow=int(slow),rsi_period=int(rsi_period),oversold=oversold,
                    overbought=overbought,breakout_window=int(breakout_window),allow_short=allow_short,
                    test_fraction=test_fraction)
                st.session_state["v40_backtest_result"]={"metrics":metrics,"curve":curve,"trades":trades,"comparison":comparison}
            except Exception as exc:
                st.error(f"Backtest could not run: {exc}")
        result=st.session_state.get("v40_backtest_result")
        if result:
            m=result["metrics"]
            st.subheader("Backtest performance")
            a,b,c,d=st.columns(4)
            a.metric("Net strategy return",f"{m['net_return_pct']:+.2f}%")
            b.metric("Buy & hold return",f"{m['buy_hold_return_pct']:+.2f}%")
            c.metric("Maximum drawdown",f"{m['max_drawdown_pct']:.2f}%")
            d.metric("Final simulated equity",f"₹{m['final_equity']:,.2f}")
            a,b,c,d=st.columns(4)
            a.metric("Closed trade segments",m["trade_count"])
            b.metric("Win rate",f"{m['win_rate_pct']:.1f}%" if m["win_rate_pct"] is not None else "—")
            c.metric("Profit factor",f"{m['profit_factor']:.2f}" if m["profit_factor"] is not None and np.isfinite(m["profit_factor"]) else "—")
            d.metric("Out-of-sample return",f"{m['oos_return_pct']:+.2f}%")
            st.caption(f"Out-of-sample begins {m['oos_start']} · {m['oos_candles']} candles · Approx. annualised Sharpe: {m['sharpe_approx']:.2f}" if m["sharpe_approx"] is not None else f"Out-of-sample begins {m['oos_start']} · {m['oos_candles']} candles · Sharpe unavailable")
            curve=result["curve"]
            fig=go.Figure()
            fig.add_trace(go.Scatter(x=curve.index,y=curve["Strategy equity"],name="Strategy equity",line=dict(width=2)))
            fig.add_trace(go.Scatter(x=curve.index,y=curve["Buy & hold equity"],name="Buy & hold",line=dict(width=1.5,dash="dot")))
            fig.update_layout(title="Equity curve",xaxis_title="Date",yaxis_title="Simulated account value",height=390,template="plotly_dark",legend=dict(orientation="h"))
            st.plotly_chart(fig,use_container_width=True)
            ddfig=go.Figure(go.Scatter(x=curve.index,y=curve["Drawdown %"],name="Drawdown",fill="tozeroy"))
            ddfig.update_layout(title="Strategy drawdown",xaxis_title="Date",yaxis_title="Drawdown %",height=260,template="plotly_dark")
            st.plotly_chart(ddfig,use_container_width=True)
            st.subheader("Strategy comparison")
            st.dataframe(result["comparison"],use_container_width=True,hide_index=True)
            st.subheader("Trade log")
            trades=result["trades"]
            if not trades.empty:
                st.dataframe(trades,use_container_width=True,hide_index=True)
                st.download_button("Download trade log CSV",trades.to_csv(index=False).encode(),"v40_backtest_trades.csv","text/csv")
            else:
                st.info("No completed position segments were generated for these settings.")
            st.download_button("Download full backtest curve CSV",curve.to_csv().encode(),"v40_backtest_equity_curve.csv","text/csv")
            st.caption(f"Model assumptions: {m['strategy']} · estimated turnover cost {m['estimated_turnover_cost_pct']:.3f}% of equity-return units · exposure {m['exposure_pct']:.1f}%. Cost inputs are user estimates, not a statutory broker-fee calculator.")
        else:
            st.info("Choose the strategy assumptions and press Run historical backtest. No result is pre-filled or fabricated.")
    st.divider()
    st.markdown("**V40 integrity:** This is an offline historical simulation using the selected data adapter. It does not place broker orders, predict future prices, or guarantee fills. Use out-of-sample results and keep costs, data quality and survivorship bias in mind.")

elif page=="V39 Paper Execution Simulator":
    from sim_execution_v39 import (create_order, process_market_data, cancel_order,
        close_position, list_orders, list_positions, list_events, performance_summary,
        estimate_costs)
    st.markdown("""<div class="ati-hero"><h1>V39 · Paper Execution Simulator</h1>
    <p>Simulated order lifecycle · limit and stop orders · adverse slippage · configurable costs · position P&amp;L</p></div>""", unsafe_allow_html=True)
    st.warning("SIMULATION ONLY — no broker connection, exchange routing, or real-money order placement. Fills are generated only from prices supplied to this page or manually entered by you.")
    quote_price = float(data.Close.iloc[-1]) if not data.empty else None
    quote_asof = str(data.index[-1]) if not data.empty else "Unavailable"
    cfg_col, quote_col = st.columns([1.2, 1])
    with cfg_col:
        with st.expander("Estimated execution-cost assumptions", expanded=False):
            c1,c2,c3=st.columns(3)
            brokerage_bps=c1.number_input("Brokerage (bps)",min_value=0.0,value=3.0,step=0.5,key="v39_brokerage")
            exchange_bps=c2.number_input("Exchange (bps)",min_value=0.0,value=3.0,step=0.5,key="v39_exchange")
            regulatory_bps=c3.number_input("Regulatory (bps)",min_value=0.0,value=0.1,step=0.1,key="v39_reg")
            c4,c5=st.columns(2)
            tax_bps=c4.number_input("Other tax estimate (bps)",min_value=0.0,value=0.0,step=0.5,key="v39_tax")
            slippage_bps=c5.number_input("Slippage (bps)",min_value=0.0,value=2.0,step=0.5,key="v39_slip")
            st.caption("Basis-point assumptions are illustrative and user-configurable, not actual statutory charges or a broker fee schedule.")
    cost_cfg={"brokerage_bps":brokerage_bps,"exchange_bps":exchange_bps,"regulatory_bps":regulatory_bps,"tax_bps":tax_bps,"slippage_bps":slippage_bps}
    with quote_col:
        st.metric(f"{symbol} latest available close", f"{quote_price:,.2f}" if quote_price else "Unavailable")
        st.caption(f"Source: existing history adapter · bar: {quote_asof} · not guaranteed real-time")
    t1,t2,t3,t4=st.tabs(["Order Ticket","Orders & Lifecycle","Open Positions","Performance & Audit"])
    with t1:
        st.subheader("Create simulated order")
        with st.form("v39_order_ticket"):
            a,b,c=st.columns(3)
            order_symbol=a.text_input("Symbol",value=symbol,key="v39_symbol").strip().upper()
            side=b.selectbox("Side",["BUY","SELL"])
            order_type=c.selectbox("Order type",["MARKET","LIMIT","STOP_MARKET","STOP_LIMIT"])
            d,e,f=st.columns(3)
            qty=d.number_input("Quantity",min_value=1.0,value=1.0,step=1.0)
            limit_val=e.number_input("Limit price",min_value=0.01,value=float(quote_price or 100),step=0.5,disabled=order_type not in ("LIMIT","STOP_LIMIT"))
            stop_val=f.number_input("Stop trigger",min_value=0.01,value=float(quote_price or 100),step=0.5,disabled=order_type not in ("STOP_MARKET","STOP_LIMIT"))
            notes=st.text_input("Order note (optional)")
            st.caption("Market orders use the latest available close shown above as a simulated reference. Pending orders require a later price evaluation.")
            submit_order=st.form_submit_button("Submit paper order",type="primary")
        if submit_order:
            try:
                market_reference=None
                if order_type=="MARKET":
                    market_hist=data if order_symbol==symbol else load_data(order_symbol,"1mo","1d")
                    if not market_hist.empty: market_reference=float(market_hist.Close.iloc[-1])
                oid=create_order(order_symbol,side,order_type,qty,
                    limit_price=limit_val if order_type in ("LIMIT","STOP_LIMIT") else None,
                    stop_price=stop_val if order_type in ("STOP_MARKET","STOP_LIMIT") else None,
                    reference_price=market_reference,
                    notes=notes,cost_config=cost_cfg)
                st.success(f"Paper order #{oid} recorded. Check its lifecycle in Orders & Lifecycle.")
                st.rerun()
            except Exception as exc: st.error(f"Order not submitted: {exc}")
        if quote_price:
            try:
                preview=estimate_costs(quote_price,1,**cost_cfg)
                st.caption(f"One-unit illustrative cost preview at {quote_price:,.2f}: fees {preview['fees']:.2f}; slippage estimate {preview['slippage_estimate']:.2f}; total {preview['total_estimated_cost']:.2f}.")
            except Exception as exc: st.info(str(exc))
    with t2:
        st.subheader("Order book and lifecycle")
        orders=list_orders()
        if not orders.empty:
            st.dataframe(orders,use_container_width=True,hide_index=True)
            pending=orders[orders.status.isin(["PENDING","TRIGGERED"])]
            if not pending.empty:
                st.markdown("**Evaluate pending orders**")
                manual_px=st.number_input("Observed price for selected symbol",min_value=0.01,value=float(quote_price or 100),step=0.5,key="v39_manual_px")
                symbols_pending=sorted(pending.symbol.unique().tolist())
                chosen_pending=st.selectbox("Symbol to evaluate",symbols_pending,key="v39_eval_symbol")
                p1,p2=st.columns(2)
                if p1.button("Evaluate using available close",key="v39_eval_close"):
                    prices={}
                    for sym in symbols_pending:
                        hist=load_data(sym,"1mo","1d")
                        if not hist.empty: prices[sym]=float(hist.Close.iloc[-1])
                    ev=process_market_data(prices,cost_config=cost_cfg)
                    st.success(f"Evaluation complete: {len(ev)} lifecycle event(s).")
                    if ev: st.dataframe(pd.DataFrame(ev),use_container_width=True,hide_index=True)
                    st.rerun()
                if p2.button("Evaluate selected symbol at entered price",key="v39_eval_manual"):
                    ev=process_market_data({chosen_pending:manual_px},cost_config=cost_cfg)
                    st.success(f"Recorded {len(ev)} event(s).")
                    if ev: st.dataframe(pd.DataFrame(ev),use_container_width=True,hide_index=True)
                    st.rerun()
                cancel_id=st.selectbox("Cancel pending order ID",pending.id.tolist(),key="v39_cancel_id")
                if st.button("Cancel selected order",key="v39_cancel"):
                    st.success("Order cancelled." if cancel_order(cancel_id) else "Order could not be cancelled."); st.rerun()
        else: st.info("No paper orders yet. Submit an order in Order Ticket.")
    with t3:
        st.subheader("Open and closed simulated positions")
        positions=list_positions()
        if not positions.empty: st.dataframe(positions,use_container_width=True,hide_index=True)
        open_pos=list_positions(status="OPEN")
        if not open_pos.empty:
            st.markdown("**Close a position**")
            pos_id=st.selectbox("Open position ID",open_pos.id.tolist(),key="v39_close_id")
            selected_pos=open_pos[open_pos.id==pos_id].iloc[0]
            hist=load_data(selected_pos.symbol,"1mo","1d")
            fallback=float(hist.Close.iloc[-1]) if not hist.empty else float(selected_pos.entry_price)
            exit_ref=st.number_input("Exit reference price",min_value=0.01,value=fallback,step=0.5,key="v39_exit_price")
            if st.button("Close simulated position",type="primary",key="v39_close_position"):
                try:
                    result=close_position(pos_id,exit_ref,cost_config=cost_cfg)
                    st.success(f"Position closed. Net P&L: {result['net_pnl']:.2f}")
                    st.json(result); st.rerun()
                except Exception as exc: st.error(str(exc))
        else: st.info("No open positions.")
    with t4:
        summary=performance_summary(list_positions())
        m1,m2,m3,m4=st.columns(4)
        m1.metric("Closed positions",summary["closed_positions"])
        m2.metric("Win rate",f"{summary['win_rate_pct']:.1f}%" if summary["win_rate_pct"] is not None else "—")
        m3.metric("Net P&L",f"{summary['net_pnl']:,.2f}")
        m4.metric("Total estimated fees",f"{summary['total_fees']:,.2f}")
        st.json(summary)
        st.subheader("Execution event log")
        events=list_events()
        if not events.empty: st.dataframe(events,use_container_width=True,hide_index=True)
        st.caption("Performance is calculated from closed simulated positions. No live fills, queue priority, partial fills, market impact, exchange matching, or broker charges are represented.")
    st.divider()
    st.markdown("**Data integrity:** V39 uses its own `ati_v39_paper_execution.sqlite3` database. It does not modify the V34 portfolio DB, V37 paper ledger, or V38 watchlist/alert store. All execution is local simulation only.")

elif page=="V38 Professional Trading Terminal":
    from terminal_v38 import (add_symbol, remove_symbol, get_watchlist, add_alert,
        get_alerts, evaluate_alerts, deactivate_alert)
    st.markdown("""<div class="ati-hero"><h1>V38 · Professional Trading Terminal</h1>
    <p>Unified market workspace · watchlist · chart analysis · option-chain snapshot · smart price alerts</p></div>""", unsafe_allow_html=True)
    st.caption("Market data in this build uses the selected Yahoo Finance history adapter unless a separate broker feed is connected. Quotes are not guaranteed real-time.")
    wl=get_watchlist()
    quote_rows=[]
    symbols=list(dict.fromkeys(([symbol] if symbol else []) + wl.symbol.tolist()))[:12]
    for sym in symbols:
        qdf=load_data(sym,"1mo","1d")
        if not qdf.empty:
            last=qdf.iloc[-1]; prev=qdf.Close.iloc[-2] if len(qdf)>1 else last.Close
            quote_rows.append({"Symbol":sym,"Last":float(last.Close),"Change":float(last.Close-prev),"Change %":float((last.Close/prev-1)*100) if prev else 0,"As of":str(qdf.index[-1])})
    quotes=pd.DataFrame(quote_rows)
    if not quotes.empty:
        q1,q2,q3,q4=st.columns(4)
        q1.metric("Workspace symbols",len(quotes)); q2.metric("Selected instrument",symbol)
        selected=quotes[quotes.Symbol==symbol]
        if not selected.empty:
            q3.metric("Latest close",f"₹{selected.iloc[0]['Last']:,.2f}",f"{selected.iloc[0]['Change %']:+.2f}%")
        else: q3.metric("Latest close","—")
        q4.metric("Execution mode","Paper / analysis only")
    tab1,tab2,tab3,tab4=st.tabs(["Market Overview","Advanced Chart","Options Intelligence","Smart Alert Centre"])
    with tab1:
        left,right=st.columns([1.25,1])
        with left:
            st.subheader("Multi-market watchlist")
            if not quotes.empty: st.dataframe(quotes,use_container_width=True,hide_index=True)
            else: st.info("No quote history available for the selected symbols.")
            with st.form("v38_add_watchlist"):
                a,b=st.columns([2,1]); new_sym=a.text_input("Add symbol",placeholder="e.g. TCS.NS").strip().upper()
                asset=a.selectbox("Asset class",["Equity","Index","ETF","Commodity","FX","Crypto"])
                note=b.text_input("Note",placeholder="Optional")
                add_wl=st.form_submit_button("Add to watchlist")
            if add_wl:
                try: add_symbol(new_sym,asset,note); st.success(f"Added {new_sym}"); st.rerun()
                except Exception as exc: st.error(str(exc))
            if not wl.empty:
                rm=st.selectbox("Remove watchlist symbol",wl.symbol.tolist(),key="v38_remove_symbol")
                if st.button("Remove selected symbol"): remove_symbol(rm); st.rerun()
        with right:
            st.subheader("Market snapshot")
            if not data.empty:
                latest=data.iloc[-1]
                for label,col in [("EMA 20","EMA20"),("EMA 50","EMA50"),("RSI 14","RSI"),("ATR 14","ATR")]:
                    val=latest.get(col,float('nan'))
                    st.metric(label,f"{val:,.2f}" if pd.notna(val) else "—")
                score,reasons=score_trend(data)
                st.metric("Technical confluence score",f"{score:+d} / 5")
                st.write(" · ".join(reasons))
            else: st.warning("Price history is unavailable for the selected symbol.")
            st.info("Use the existing V37 Paper Trading page for the persistent simulated trade ledger. Real-money execution remains disabled.")
            if st.button("Open V37 Paper Trading workspace"): navigate_to("V37 Ultimate Platform & Paper Trading"); st.rerun()
    with tab2:
        st.subheader(f"{symbol} · Candlestick and indicator workspace")
        if not data.empty:
            st.plotly_chart(price_chart(data,f"{symbol} · OHLCV / EMA / RSI / MACD"),use_container_width=True)
            st.caption(f"History: {period} · Interval: {interval} · Latest bar: {data.index[-1]}")
        else: st.warning("No chart data available. Change the symbol or history interval in the sidebar.")
    with tab3:
        st.subheader("Option-chain snapshot analysis")
        st.write("Upload a broker/exported option-chain CSV. This workspace analyses the supplied snapshot; it does not imply a live options feed.")
        opt_file=st.file_uploader("Upload option-chain CSV",type=["csv"],key="v38_option_csv")
        if opt_file:
            try:
                opt_df,strike_col,ce_col,pe_col,cc_col,pc_col=parse_options(opt_file)
                if not strike_col: st.error("CSV needs a strike/strike price column.")
                else:
                    st.dataframe(opt_df,use_container_width=True,hide_index=True)
                    if ce_col and pe_col:
                        ce_total=pd.to_numeric(opt_df[ce_col],errors="coerce").sum(); pe_total=pd.to_numeric(opt_df[pe_col],errors="coerce").sum()
                        a,b,c=st.columns(3); a.metric("Call OI",f"{ce_total:,.0f}"); b.metric("Put OI",f"{pe_total:,.0f}"); c.metric("PCR (OI)",f"{pe_total/ce_total:.2f}" if ce_total else "—")
                    st.download_button("Download uploaded snapshot",opt_df.to_csv(index=False).encode(),"v38_option_chain_snapshot.csv","text/csv")
            except Exception as exc: st.error(f"Could not parse this option-chain file: {exc}")
        else: st.info("No option-chain file uploaded. Existing V15/V28/V29 option modules remain available in the sidebar.")
    with tab4:
        st.subheader("Persistent price-alert rules")
        st.caption("Alerts are evaluated when you press the button; this local app does not run a background monitor or send push notifications.")
        with st.form("v38_alert_form"):
            a,b,c=st.columns(3); alert_sym=a.text_input("Alert symbol",symbol).strip().upper()
            cond=b.selectbox("Condition",["ABOVE","BELOW"]); level=c.number_input("Trigger price",min_value=0.01,value=100.0)
            create_alert=st.form_submit_button("Create alert")
        if create_alert:
            try: add_alert(alert_sym,cond,level); st.success("Alert rule saved locally."); st.rerun()
            except Exception as exc: st.error(str(exc))
        if st.button("Evaluate alerts against latest available daily closes"):
            prices={}
            for sym in get_watchlist().symbol.tolist()+[symbol]:
                qdf=load_data(sym,"1mo","1d")
                if not qdf.empty: prices[sym]=float(qdf.Close.iloc[-1])
            events=evaluate_alerts(prices)
            if events: st.warning(pd.DataFrame(events).to_string(index=False))
            else: st.success("No alert thresholds crossed using the available latest closes.")
        alerts=get_alerts()
        if not alerts.empty:
            st.dataframe(alerts,use_container_width=True,hide_index=True)
            active_ids=alerts[alerts.active==1].id.tolist()
            if active_ids:
                disable_id=st.selectbox("Deactivate alert",active_ids,key="v38_disable_alert")
                if st.button("Deactivate selected alert"): deactivate_alert(disable_id); st.rerun()
        else: st.info("No alert rules created yet.")
    st.divider()
    st.markdown("**Platform integrity:** V37's 40-module directory, Central AI Brain, existing V28–V36 pages, V37 paper ledger and risk tools remain in place. V38 adds this terminal as a new page and a separate local SQLite store; it does not overwrite the V34 or V37 databases. No broker order placement is enabled.")

elif page=="V36 Live Operations & Institutional Monitor":
    st.title("V36 · Live Operations & Institutional Monitor")
    st.caption("Read-only Upstox V3 feed diagnostics, normalized quotes and threshold checks. Institutional-flow figures are not inferred from price candles.")
    from live_market_feed import start_live_feed, stop_live_feed, get_feed_status, get_market_data
    from live_operations_v36 import build_operations_report, evaluate_price_alerts
    left, right = st.columns([2, 1])
    with left:
        keys_text = st.text_area("Instrument keys (one per line)", "NSE_INDEX|Nifty 50\nNSE_INDEX|Nifty Bank\nNSE_INDEX|India VIX", height=100, key="v36_keys")
    with right:
        st.write("**Feed controls**")
        if st.button("Start / connect feed", type="primary", key="v36_start"):
            keys = [x.strip() for x in keys_text.splitlines() if x.strip()]
            st.info(start_live_feed(keys or None))
        if st.button("Stop feed", key="v36_stop"):
            st.info(stop_live_feed())
        if st.button("Refresh diagnostics", key="v36_refresh"):
            st.rerun()
    status = get_feed_status()
    snapshot = get_market_data()
    report = build_operations_report(snapshot, status)
    a,b,c,d = st.columns(4)
    a.metric("Feed health", report["health"])
    b.metric("WebSocket messages", report["message_count"])
    c.metric("Recognized instruments", report["instrument_count"])
    d.metric("Connection state", report["state"])
    st.write("Last message:", report["last_message_at"] or "Not received")
    st.write("Last feed update label:", report["last_update"] or "Unavailable")
    if report["warnings"]:
        for warning in report["warnings"]: st.warning(warning)
    if report["instruments"]:
        quote_rows = []
        for key, q in report["instruments"].items():
            quote_rows.append({"Instrument key": key, "LTP": q.get("ltp"), "Change %": q.get("change_pct"),
                               "Volume": q.get("volume"), "OI": q.get("oi"), "Day high": q.get("high"), "Day low": q.get("low")})
        st.subheader("Normalized live quotes")
        st.dataframe(pd.DataFrame(quote_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No parseable live quote is available yet. Start the feed and wait for instrument ticks.")
    st.subheader("Live price threshold checks")
    with st.form("v36_alert_form"):
        alert_key = st.text_input("Exact instrument key", "NSE_INDEX|Nifty 50")
        alert_direction = st.selectbox("Condition", ["above", "below"])
        alert_level = st.number_input("Price threshold", min_value=0.0, value=22000.0, step=10.0)
        alert_name = st.text_input("Alert label", "My live price alert")
        submitted = st.form_submit_button("Evaluate alert against latest tick")
    if submitted:
        checks = evaluate_price_alerts(report["instruments"], [{"name": alert_name, "instrument_key": alert_key,
                            "direction": alert_direction, "threshold": alert_level}])
        if checks:
            item = checks[0]
            if item["triggered"]: st.success(f"TRIGGERED · {item['name']} · LTP {item['ltp']:,.2f} {item['direction']} {item['threshold']:,.2f}")
            else: st.info(f"Not triggered · LTP {item['ltp']:,.2f} · threshold {item['threshold']:,.2f}")
        else:
            st.warning("No current LTP for that exact instrument key. Check the key and wait for a tick.")
    with st.expander("Raw feed diagnostics"):
        st.json({"status": status, "snapshot_keys": list(snapshot.keys())})
    st.warning("V36 is a monitoring and decision-support layer, not a guaranteed real-time alerting service. Streamlit must remain open and the websocket must be connected. It does not calculate verified FII/DII flows, exchange order-book depth or institutional trades, and it never places orders.")

elif page=="Upstox Live Data":
    st.title("Upstox Live Market Data")
    st.caption("Read-only connection using your Upstox Analytics Token. No order placement is enabled.")
    token = st.secrets.get("UPSTOX_ACCESS_TOKEN", "")
    if not token:
        st.error("Token not found. Check .streamlit/secrets.toml and restart Streamlit.")
        st.code('UPSTOX_ACCESS_TOKEN = "paste_your_token_locally"')
    else:
        st.success("Analytics Token detected locally. Your token is not displayed.")
        st.markdown("### Instrument lookup")
        st.write("Enter the exact Upstox instrument key. Examples: `NSE_INDEX|Nifty 50`, `NSE_INDEX|Nifty Bank`. For an equity, use its exact key from the Upstox instrument master.")
        instrument_key = st.text_input("Upstox instrument key", "NSE_INDEX|Nifty 50", key="upstox_instrument_key")
        if st.button("Fetch Upstox market quote", type="primary"):
            quote_response = upstox_full_quote(instrument_key.strip(), token)
            if "error" in quote_response:
                st.error(quote_response["error"])
            else:
                quote_data = quote_response.get("data", {})
                if not quote_data:
                    st.warning("No quote returned. Check the instrument key.")
                    st.json(quote_response)
                else:
                    quote = next(iter(quote_data.values()))
                    ltp = quote.get("last_price")
                    close = quote.get("cp") or quote.get("close_price")
                    change = ((ltp-close)/close*100) if ltp is not None and close else None
                    a,b,c,d = st.columns(4)
                    a.metric("Last traded price", f"{ltp:,.2f}" if ltp is not None else "—",
                             f"{change:+.2f}%" if change is not None else None)
                    a2 = quote.get("ohlc", {}) or {}
                    b.metric("Open", f"{a2.get('open',0):,.2f}" if a2.get("open") is not None else "—")
                    c.metric("Day high", f"{a2.get('high',0):,.2f}" if a2.get("high") is not None else "—")
                    d.metric("Day low", f"{a2.get('low',0):,.2f}" if a2.get("low") is not None else "—")
                    st.subheader("Raw quote details")
                    st.json(quote)
        st.markdown("---")
        st.markdown("### Historical candles from Upstox")
        st.caption("Historical candles are fetched from Upstox and are separate from the Yahoo Finance chart used by other existing dashboard pages.")
        hist_interval = st.selectbox("Candle interval", ["1minute","30minute","day"], index=2)
        days_back = st.selectbox("History window", [7,30,90,180], index=2)
        if st.button("Load Upstox historical chart"):
            from datetime import date, timedelta
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            hist = upstox_historical(instrument_key.strip(), hist_interval,
                                     end_date.isoformat(), start_date.isoformat(), token)
            if "error" in hist:
                st.error(hist["error"])
            else:
                candles = hist.get("data", {}).get("candles", [])
                if not candles:
                    st.warning("No candles returned for this instrument/interval.")
                else:
                    # Upstox candle order: timestamp, open, high, low, close, volume, OI
                    candle_df = pd.DataFrame(candles, columns=["Timestamp","Open","High","Low","Close","Volume","OI"][:len(candles[0])])
                    candle_df["Timestamp"] = pd.to_datetime(candle_df["Timestamp"])
                    candle_df = candle_df.set_index("Timestamp").sort_index()
                    st.plotly_chart(price_chart(add_indicators(candle_df[["Open","High","Low","Close","Volume"]]),
                                                f"{instrument_key} | Upstox historical candles"),
                                    use_container_width=True)
                    st.dataframe(candle_df.tail(20), use_container_width=True)
        st.info("This first integration step validates REST access and retrieves quotes/candles. Live streaming WebSocket and option-chain integration will be added after this test passes.")


elif page=="V22 Trading Signal Intelligence":
    st.title("🚦 V22 Advanced Trading Signal Intelligence")
    st.caption("Multi-timeframe confirmation · data freshness checks · market-news risk context · reference risk plan")
    from signal_intelligence_v22 import assess_signal_quality
    from trade_confirmation_engine import build_atr_trade_plan

    st.info(f"Selected instrument: **{symbol}**. Yahoo Finance is used here for OHLCV history only; news is collected separately from multiple Indian, international and official publishers.")
    if st.button("Run V22 signal assessment", type="primary"):
        specs = {"5m": ("5d", "5m"), "15m": ("30d", "15m"), "1H": ("60d", "1h"), "1D": ("1y", "1d")}
        frames = {}
        with st.spinner("Fetching 5m, 15m, 1H and daily candles..."):
            for tf, (per, inter) in specs.items():
                frames[tf] = load_data(symbol, per, inter)
        st.session_state["ati_v22_frames"] = frames
        st.session_state.pop("ati_v22_result", None)

    if st.button("Refresh multi-source market news"):
        with st.spinner("Checking available Indian, international and official news feeds..."):
            news_df, feed_status = fetch_all_news()
            news_df = enrich_news(news_df) if not news_df.empty else news_df
            st.session_state["ati_v22_news"] = news_df
            st.session_state["ati_v22_feed_status"] = feed_status
        st.success(f"News refresh complete: {len(news_df)} headlines collected from available feeds.")

    frames = st.session_state.get("ati_v22_frames", {})
    news_df = st.session_state.get("ati_v22_news", pd.DataFrame())
    if frames:
        result = assess_signal_quality(frames, news_df)
        st.session_state["ati_v22_result"] = result
        a,b,c,d = st.columns(4)
        a.metric("Directional assessment", result["direction"])
        b.metric("Signal quality", result["quality"])
        c.metric("Timeframes available", f"{result['available_count']}/4")
        d.metric("High-priority headlines", len(result["high_priority_news"]))

        st.subheader("Multi-timeframe confirmation")
        rows=[]
        for tf, reading in result["timeframes"].items():
            fresh=result["freshness"][tf]
            rows.append({"Timeframe":tf,"Bias":reading["bias"],"Score":reading["score"],
                         "RSI":reading["rsi"],"Relative volume":reading["relative_volume"],
                         "Data status":fresh["status"],"Age (hours)":fresh["age_hours"]})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption(result["agreement"])

        st.subheader("Signal evidence")
        for tf, reading in result["timeframes"].items():
            with st.expander(f"{tf} · {reading['bias']}"):
                for reason in reading.get("reasons", []): st.write("• " + reason)
                st.write("Latest candle timestamp:", result["freshness"][tf]["latest"] or "Unavailable")

        if not news_df.empty:
            st.subheader("Market news risk context")
            if result["high_priority_news"].empty:
                st.success("No headlines crossed the current keyword-based high-priority threshold in the collected feed.")
            else:
                show_cols=[c for c in ["Source","Published (UTC)","Headline","Priority score","Priority","Potential sectors","Link"] if c in result["high_priority_news"].columns]
                st.dataframe(result["high_priority_news"][show_cols], use_container_width=True, hide_index=True)
            feed_status=st.session_state.get("ati_v22_feed_status")
            if feed_status is not None:
                with st.expander("News feed availability"):
                    st.dataframe(feed_status, use_container_width=True, hide_index=True)
        else:
            st.info("News has not been refreshed in this session. Use the news refresh button to add multi-source event context.")

        st.subheader("ATR-based reference risk plan")
        daily=frames.get("1D", pd.DataFrame())
        if not daily.empty and len(daily)>=20:
            tr=pd.concat([daily.High-daily.Low,(daily.High-daily.Close.shift()).abs(),(daily.Low-daily.Close.shift()).abs()],axis=1).max(axis=1)
            atr=float(tr.ewm(alpha=1/14,adjust=False).mean().iloc[-1])
            latest=float(daily.Close.iloc[-1])
            p1,p2,p3=st.columns(3)
            entry=p1.number_input("Entry reference",min_value=0.01,value=latest,step=0.05,key="v22_entry")
            budget=p2.number_input("Risk budget (₹)",min_value=1.0,value=1000.0,step=100.0,key="v22_budget")
            default_dir="LONG" if result["direction"].startswith("BULLISH") else "SHORT"
            direction=p3.selectbox("Plan direction",[default_dir,"SHORT" if default_dir=="LONG" else "LONG"],key="v22_direction")
            try:
                plan=build_atr_trade_plan(entry,atr,direction,budget)
                x1,x2,x3,x4=st.columns(4)
                x1.metric("Stop reference",f"₹{plan['stop_loss']:,.2f}")
                x2.metric("Target reference",f"₹{plan['target']:,.2f}")
                x3.metric("Cash-equity quantity",f"{plan['quantity']:,}")
                x4.metric("Estimated risk",f"₹{plan['estimated_risk_before_costs']:,.2f}")
                st.caption(f"Daily ATR: ₹{atr:.2f} · Position value: ₹{plan['estimated_position_value']:,.2f}. Before brokerage, taxes, slippage and gaps; cash-equity units only, not options lots or leverage.")
            except ValueError as exc: st.error(str(exc))
        else:
            st.warning("A daily candle history with at least 20 rows is required for the ATR reference plan.")
        for warning in result["warnings"]: st.warning(warning)
        st.warning(result["disclaimer"])
    else:
        st.info("Click **Run V22 signal assessment** to fetch candles. No existing module or broker integration is changed.")



st.divider()
st.markdown("<div class='small-note'>AI Trade Intelligence V22 · Market data may be delayed · Educational use only · No broker execution · No guaranteed signals</div>",unsafe_allow_html=True)
