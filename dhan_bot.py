import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import random
import warnings
from fyers_apiv3 import fyersModel   # ✅ correct import

warnings.filterwarnings('ignore')

# ========== FYERS CREDENTIALS ==========
FYERS_CLIENT_ID = "ER78MCCWG0-100"
FYERS_SECRET_KEY = "9MLTKAAHCQ"
FYERS_ACCESS_TOKEN = "JVHC6XLKBY6OOII5VSAKRTA3QTOIO2MM"  # Token expired? Generate new one!

# ========== PAGE CONFIG ==========
st.set_page_config(
    layout="wide",
    page_title="90% Accuracy Signal Bot - FYERS v3",
    page_icon="🎯",
    initial_sidebar_state="expanded"
)

# ========== LOGIN (same as before) ==========
USERNAME = "admin"
PASSWORD = "stock123"

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "signals" not in st.session_state:
    st.session_state.signals = []
if "last_scan" not in st.session_state:
    st.session_state.last_scan = None
if "top_gainers" not in st.session_state:
    st.session_state.top_gainers = []
if "top_losers" not in st.session_state:
    st.session_state.top_losers = []
if "market_trend" not in st.session_state:
    st.session_state.market_trend = "NEUTRAL"
if "test_mode" not in st.session_state:
    st.session_state.test_mode = True   # Keep True for now

def check_login():
    if not st.session_state["authenticated"]:
        st.markdown("<h1 style='text-align: center;'>🔐 LOGIN REQUIRED</h1>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if u == USERNAME and p == PASSWORD:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
        st.stop()

check_login()

# ========== FYERS CLIENT ==========
def get_fyers_client():
    """initialize Fyers client using fyers_apiv3"""
    try:
        fyers = fyersModel.FyersModel(
            client_id=FYERS_CLIENT_ID,
            token=FYERS_ACCESS_TOKEN,
            is_async=False,
            log_path=""
        )
        return fyers
    except Exception as e:
        st.error(f"FYERS init error: {e}")
        return None

# ========== LIVE QUOTE ==========
def get_live_quote(symbol):
    if st.session_state.test_mode:
        # dummy data
        base_price = random.uniform(1000, 5000)
        change_percent = random.uniform(-5, 5)
        return {
            'ltp': base_price,
            'change': base_price * change_percent / 100,
            'change_percent': change_percent
        }
    
    fyers = get_fyers_client()
    if not fyers:
        return None
    try:
        resp = fyers.quotes({"symbols": f"NSE:{symbol}-EQ"})
        if resp.get('s') == 'ok':
            v = resp['d'][0]['v']
            return {
                'ltp': v['lp'],
                'change': v['ch'],
                'change_percent': v['chp']
            }
    except Exception as e:
        st.error(f"Quote error {symbol}: {e}")
    return None

# ========== HISTORICAL DATA ==========
def get_history(symbol, resolution="15", days=5):
    if st.session_state.test_mode:
        # dummy candles for test mode
        periods = 80
        dates = pd.date_range(end=datetime.now(), periods=periods, freq='15min')
        return pd.DataFrame({
            'Open': np.random.uniform(100, 500, periods),
            'High': np.random.uniform(100, 500, periods),
            'Low': np.random.uniform(100, 500, periods),
            'Close': np.random.uniform(100, 500, periods),
            'Volume': np.random.randint(100000, 1000000, periods)
        }, index=dates)
    
    fyers = get_fyers_client()
    if not fyers:
        return None
    try:
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        data = {
            "symbol": f"NSE:{symbol}-EQ",
            "resolution": resolution,
            "date_format": "1",
            "range_from": from_date.strftime("%Y-%m-%d"),
            "range_to": to_date.strftime("%Y-%m-%d"),
            "cont_flag": "1"
        }
        resp = fyers.history(data=data)
        if resp.get('s') == 'ok' and resp.get('candles'):
            candles = resp['candles']
            df = pd.DataFrame(candles, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df.set_index('timestamp', inplace=True)
            return df
    except Exception as e:
        st.error(f"History error {symbol}: {e}")
    return None

# ========== STOCKS ==========
ALL_STOCKS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL",
    "KOTAKBANK", "BAJFINANCE", "ITC", "LT", "WIPRO", "AXISBANK", "HCLTECH"
]   # for testing; full list later

# ========== SIMPLE SIGNAL (placeholder - replace with your full logic) ==========
def generate_signal(df, symbol):
    # dummy signal for test mode
    if st.session_state.test_mode and symbol in ALL_STOCKS[:10]:
        return {
            'signal': random.choice(['STRONG_BUY', 'STRONG_SELL']),
            'probability': random.randint(75, 98),
            'price': float(df['Close'].iloc[-1]),
            'target1': float(df['Close'].iloc[-1]) * 1.03,
            'target2': float(df['Close'].iloc[-1]) * 1.05,
            'target3': float(df['Close'].iloc[-1]) * 1.08,
            'stop_loss': float(df['Close'].iloc[-1]) * 0.97,
            'rsi': random.uniform(25, 75),
            'adx': random.uniform(20, 50)
        }
    return None   # no real signal for now

# ========== GAINERS / LOSERS ==========
def get_top_gainers_losers():
    gainers, losers = [], []
    stocks = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL"]
    for sym in stocks:
        q = get_live_quote(sym)
        if q and q['change_percent'] != 0:
            data = {'symbol': sym, 'price': q['ltp'], 'change': q['change'], 'change_percent': q['change_percent']}
            if q['change_percent'] > 0:
                gainers.append(data)
            else:
                losers.append(data)
        time.sleep(0.1)
    gainers.sort(key=lambda x: x['change_percent'], reverse=True)
    losers.sort(key=lambda x: x['change_percent'])
    return gainers[:5], losers[:5]

def detect_market_trend():
    bullish = sum(1 for sym in ["RELIANCE","TCS","HDFCBANK","INFY","ICICIBANK","SBIN","BHARTIARTL"]
                  if (q := get_live_quote(sym)) and q['change'] > 0)
    bearish = 7 - bullish
    if bullish > bearish + 2:
        return "BULLISH", f"🟢 BULLISH ({bullish} up)"
    if bearish > bullish + 2:
        return "BEARISH", f"🔴 BEARISH ({bearish} down)"
    return "NEUTRAL", "🟡 NEUTRAL"

def scan_all_stocks():
    signals = []
    total = len(ALL_STOCKS)
    progress = st.progress(0)
    status = st.empty()
    for i, sym in enumerate(ALL_STOCKS):
        status.text(f"Scanning {sym} ({i+1}/{total})")
        progress.progress((i+1)/total)
        df = get_history(sym, resolution="15", days=5)
        if df is not None and len(df) > 30:
            sig = generate_signal(df, sym)
            if sig:
                sig['symbol'] = sym
                sig['name'] = sym
                sig['entry_time'] = datetime.now().strftime("%H:%M:%S")
                signals.append(sig)
        time.sleep(0.1)
    progress.empty()
    status.empty()
    signals.sort(key=lambda x: x['probability'], reverse=True)
    return signals

def get_tradingview_chart(symbol, timeframe="15"):
    return f"""
    <div style="height:500px;">
        <div class="tradingview-widget-container" style="height:500px;">
            <div id="tv_{symbol}" style="height:500px;"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
            <script>
            new TradingView.widget({{
                "width": "100%", "height": 500, "symbol": "NSE:{symbol}", "interval": "{timeframe}",
                "timezone": "Asia/Kolkata", "theme": "dark", "style": "1", "locale": "in",
                "container_id": "tv_{symbol}",
                "studies": ["RSI@tv-basicstudies", "MACD@tv-basicstudies", "BB@tv-basicstudies"]
            }});
            </script>
        </div>
    </div>
    """

def main():
    st.markdown("<h1>🎯 90% ACCURACY SIGNAL BOT - FYERS v3</h1>", unsafe_allow_html=True)
    
    col1, col2, _ = st.columns([1,1,2])
    with col1:
        if st.button("🧪 TEST MODE"):
            st.session_state.test_mode = True
            st.session_state.signals = []
            st.session_state.last_scan = None
            st.rerun()
    with col2:
        if st.button("📡 LIVE MARKET"):
            st.session_state.test_mode = False
            st.session_state.signals = []
            st.session_state.last_scan = None
            st.rerun()
    
    if st.session_state.test_mode:
        st.warning("🧪 TEST MODE ACTIVE - Using dummy data")
    else:
        st.success("📡 LIVE MARKET MODE - Using FYERS API")
    
    market_trend, trend_msg = detect_market_trend()
    st.info(trend_msg)
    
    # refresh gainers/losers
    if st.button("🔄 Refresh Gainers/Losers"):
        with st.spinner("Fetching..."):
            st.session_state.top_gainers, st.session_state.top_losers = get_top_gainers_losers()
    if not st.session_state.top_gainers:
        with st.spinner("Initial load..."):
            st.session_state.top_gainers, st.session_state.top_losers = get_top_gainers_losers()
    
    col_g, col_l = st.columns(2)
    with col_g:
        st.subheader("🟢 TOP 5 GAINERS")
        for g in st.session_state.top_gainers:
            st.markdown(f"📈 **{g['symbol']}** +{g['change_percent']:.2f}%  ₹{g['price']:.2f}")
    with col_l:
        st.subheader("🔴 TOP 5 LOSERS")
        for l in st.session_state.top_losers:
            st.markdown(f"📉 **{l['symbol']}** {l['change_percent']:.2f}%  ₹{l['price']:.2f}")
    
    if st.button("🔍 SCAN ALL STOCKS"):
        with st.spinner(f"Scanning {len(ALL_STOCKS)} stocks..."):
            st.session_state.signals = scan_all_stocks()
            st.session_state.last_scan = datetime.now()
        if st.session_state.signals:
            st.balloons()
            st.success(f"Found {len(st.session_state.signals)} signals!")
        else:
            st.info("No signals found.")
    
    if st.session_state.last_scan:
        st.caption(f"Last scan: {st.session_state.last_scan.strftime('%H:%M:%S')}")
    
    for sig in st.session_state.signals[:5]:
        with st.container():
            st.markdown(f"## {sig['signal']} {sig['name']}  (Acc: {sig['probability']:.0f}%)")
            st.write(f"**Entry:** ₹{sig['price']:.2f}")
            st.write(f"**Targets:** ₹{sig['target1']:.2f} → ₹{sig['target2']:.2f} → ₹{sig['target3']:.2f}")
            st.write(f"**Stop Loss:** ₹{sig['stop_loss']:.2f}")
            st.write(f"**RSI:** {sig['rsi']:.1f}  |  **ADX:** {sig['adx']:.1f}")
            with st.expander("📊 Chart"):
                st.components.v1.html(get_tradingview_chart(sig['symbol']), height=550)
            st.markdown("---")

if __name__ == "__main__":
    main()
