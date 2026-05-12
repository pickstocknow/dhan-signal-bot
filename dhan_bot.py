import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from dhanhq import dhanhq

# ========== DHAN CREDENTIALS ==========
DHAN_CLIENT_ID = "1103750176"
# Access token से लीक को रोकने के लिए मैं यह हटा रहा हूँ। आपको इसे अपनी फ़ाइल में जरूर डालना है।
DHAN_ACCESS_TOKEN = "YOUR_NEW_ACCESS_TOKEN_HERE"

# Initialize Dhan client
dh = dhanhq(DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)

# ========== USER PASSWORD PROTECTION ==========
USER_CREDENTIALS = {
    "admin": "stock123",
    "trader": "dhan2024",
    "user": "password",
    "vip": "vip2024"
}

st.set_page_config(layout="wide", page_title="🔥 90% Dhan Signal Bot", page_icon="🎯")

# ========== LOGIN ==========
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.markdown("<h1 style='text-align: center;'>🔐 LOGIN REQUIRED</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            with st.form("login_form"):
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    if u in USER_CREDENTIALS and USER_CREDENTIALS[u] == p:
                        st.session_state.logged_in = True
                        st.session_state.username = u
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
        st.stop()
    return True
check_login()

# ========== CSS STYLING ==========
st.markdown("""
<style>
    .stApp { background-color: #050505; }
    h1 { color: #00ff88 !important; text-align: center; }
    .strong-buy { border-left: 8px solid #00ff88; background: #0a2a0a; border-radius: 20px; padding: 20px; margin: 15px 0; }
    .strong-sell { border-left: 8px solid #ff3333; background: #2a0a0a; border-radius: 20px; padding: 20px; margin: 15px 0; }
    .badge-buy { background: #00ff88; color: #000; padding: 5px 15px; border-radius: 20px; }
    .badge-sell { background: #ff3333; color: #fff; padding: 5px 15px; border-radius: 20px; }
    .metric-box { background: #0d0d0d; border-radius: 12px; padding: 10px; text-align: center; display: inline-block; margin: 5px; }
    .price-up { color: #00ff88; font-size: 28px; font-weight: bold; }
    .price-down { color: #ff3333; font-size: 28px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ========== SESSION STATE ==========
for key in ["signals", "last_scan", "top_gainers", "top_losers", "market_trend"]:
    if key not in st.session_state:
        if key == "signals": st.session_state.signals = []
        elif key == "last_scan": st.session_state.last_scan = None
        elif key == "top_gainers": st.session_state.top_gainers = []
        elif key == "top_losers": st.session_state.top_losers = []
        elif key == "market_trend": st.session_state.market_trend = "NEUTRAL"

# ========== CORRECT DHAN API FUNCTIONS ==========
def get_dhan_history(symbol, interval="5", days=5):
    """Fetch historical data using correct dhanhq method"""
    try:
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        candles = dh.get_historical_data(
            symbol=symbol,
            exchange_segment="NSE",
            instrument="EQUITY",
            from_date=from_date.strftime("%Y-%m-%d"),
            to_date=to_date.strftime("%Y-%m-%d"),
            interval=interval
        )
        if candles and isinstance(candles, list) and len(candles) > 0:
            df_data = []
            for c in candles:
                df_data.append({
                    'timestamp': pd.to_datetime(c['timestamp'], unit='ms'),
                    'Open': float(c['open']),
                    'High': float(c['high']),
                    'Low': float(c['low']),
                    'Close': float(c['close']),
                    'Volume': int(c['volume'])
                })
            df = pd.DataFrame(df_data)
            df.set_index('timestamp', inplace=True)
            return df
        else:
            st.warning(f"No historical data for {symbol}")
    except Exception as e:
        st.error(f"History error {symbol}: {e}")
    return None

def get_live_quote(symbol):
    """Get live quote using correct dhanhq method"""
    try:
        quote = dh.get_quote(symbol=symbol, exchange_segment="NSE", instrument="EQUITY")
        if quote and 'lastTradedPrice' in quote:
            return {
                'ltp': float(quote['lastTradedPrice']),
                'change': float(quote['netChange']),
                'change_percent': float(quote['percentChange'])
            }
        else:
            st.error(f"No quote data for {symbol}")
    except Exception as e:
        st.error(f"Quote error {symbol}: {e}")
    return None

# ========== STOCKS LIST ==========
ALL_STOCKS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL",
    "KOTAKBANK", "BAJFINANCE", "ITC", "LT", "WIPRO", "AXISBANK", "HCLTECH"
]

# ========== TECHNICAL INDICATORS (same as your original) ==========
# ... (आपके सारे indicators और generate_signal का फंक्शन उसी तरह रखें जैसे आपने पिछली बार दिए थे। वो बिलकुल सही हैं।)
# ... (बस स्पेस बचाने के लिए उन्हें यहाँ दोबारा नहीं लिख रहा हूँ।)

# ========== GAINERS, LOSERS, MARKET TREND ==========
def get_top_gainers_losers():
    gainers, losers = [], []
    stocks = ["RELIANCE","TCS","HDFCBANK","INFY","ICICIBANK","SBIN","BHARTIARTL","KOTAKBANK","BAJFINANCE","ITC","LT","WIPRO","AXISBANK","HCLTECH"]
    for sym in stocks:
        q = get_live_quote(sym)
        if q and q['change_percent'] != 0:
            data = {'symbol': sym, 'price': q['ltp'], 'change': q['change'], 'change_percent': q['change_percent']}
            if q['change_percent'] > 0:
                gainers.append(data)
            else:
                losers.append(data)
        time.sleep(0.05)
    gainers.sort(key=lambda x: x['change_percent'], reverse=True)
    losers.sort(key=lambda x: x['change_percent'])
    return gainers[:5], losers[:5]

def detect_market_trend():
    bullish, bearish = 0, 0
    for sym in ["RELIANCE","TCS","HDFCBANK","INFY","ICICIBANK","SBIN","BHARTIARTL"]:
        q = get_live_quote(sym)
        if q:
            if q['change'] > 0:
                bullish += 1
            else:
                bearish += 1
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
        df = get_dhan_history(sym, interval="5", days=5)
        if df is not None and len(df) > 50:
            sig = generate_signal(df, sym) # यह फंक्शन आपने पहले से define किया है
            if sig:
                sig['symbol'] = sym
                sig['entry_time'] = datetime.now().strftime("%H:%M:%S")
                signals.append(sig)
        time.sleep(0.1)
    progress.empty()
    status.empty()
    signals.sort(key=lambda x: x['probability'], reverse=True)
    return signals

def get_tradingview_chart(symbol, timeframe="5"):
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

# ========== MAIN APP (बाकी सब कुछ आपके पिछले कोड जैसा ही रहेगा) ==========
def main():
    # ... (आपका पिछला main फंक्शन, इसमें कोई बदलाव नहीं)
    # ... (बस ऊपर दिए गए नए फंक्शंस को call करेगा)
    pass

if __name__ == "__main__":
    main()
