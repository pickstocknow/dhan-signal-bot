import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
from fyers_apiv3 import fyersModel
from fyers_apiv3.FyersWebsocket import data_ws

# ========== FYERS CREDENTIALS ==========
# FYERS Developer Portal से लें
CLIENT_ID = "ER78MCCWG0-100"  # Example: "XCXXXXXXM-100"
SECRET_KEY = "9MLTKAAHCQ"
REDIRECT_URI = "https://trade.fyers.in/api-login/redirect-uri/index.html"
ACCESS_TOKEN = "JVHC6XLKBY6OOII5VSAKRTA3QTOIO2MM"  # Generate करने के बाद डालें

# ========== USER LOGIN (Same as before) ==========
USER_CREDENTIALS = {
    "admin": "stock123",
    "trader": "dhan2024",
    "user": "password",
    "vip": "vip2024"
}

st.set_page_config(layout="wide", page_title="🔥 90% Accuracy FYERS Signal Bot", page_icon="🎯")

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

# ========== CSS STYLING (Same as before) ==========
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

# ========== FYERS API FUNCTIONS ==========
def get_live_quote_fyers(symbol):
    """FYERS API से Live Quote लेना - Bridge के जरिए"""
    try:
        # Initialize Fyers Model
        fyers = fyersModel.FyersModel(
            client_id=CLIENT_ID,
            token=ACCESS_TOKEN,
            is_async=False,
            log_path=""
        )
        
        # Format symbol for FYERS (NSE:RELIANCE-EQ)
        fyers_symbol = f"NSE:{symbol}-EQ"
        
        # Get quote data
        data = {"symbols": fyers_symbol}
        response = fyers.quotes(data=data)
        
        if response["s"] == "ok":
            item = response["d"][0]
            v_data = item.get("v", {})
            return {
                'ltp': float(v_data.get("lp", 0)),
                'change': float(v_data.get("ch", 0)),
                'change_percent': float(v_data.get("chp", 0)),
                'open': float(v_data.get("open_price", 0)),
                'high': float(v_data.get("high_price", 0)),
                'low': float(v_data.get("low_price", 0)),
                'volume': int(v_data.get("volume", 0))
            }
    except Exception as e:
        st.error(f"FYERS Quote error {symbol}: {str(e)}")
    return None

def get_historical_data_fyers(symbol, interval="5", days=5):
    """FYERS से Historical Data लेना"""
    try:
        fyers = fyersModel.FyersModel(
            client_id=CLIENT_ID,
            token=ACCESS_TOKEN,
            is_async=False,
            log_path=""
        )
        
        fyers_symbol = f"NSE:{symbol}-EQ"
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        
        # Convert to required format "YYYY-MM-DD"
        from_str = from_date.strftime("%Y-%m-%d")
        to_str = to_date.strftime("%Y-%m-%d")
        
        data = {
            "symbol": fyers_symbol,
            "resolution": interval,  # "1", "5", "15", "60", "D"
            "date_format": "1",
            "range_from": from_str,
            "range_to": to_str,
            "cont_flag": "1"
        }
        
        response = fyers.history(data=data)
        
        if response["s"] == "ok":
            candles = response.get("candles", [])
            if candles:
                df_data = []
                for candle in candles:
                    # candle format: [timestamp, open, high, low, close, volume]
                    df_data.append({
                        'timestamp': pd.to_datetime(candle[0], unit='s'),
                        'Open': candle[1],
                        'High': candle[2],
                        'Low': candle[3],
                        'Close': candle[4],
                        'Volume': candle[5]
                    })
                df = pd.DataFrame(df_data)
                df.set_index('timestamp', inplace=True)
                return df
    except Exception as e:
        st.error(f"FYERS History error {symbol}: {str(e)}")
    return None

# ========== WEBSOCKET FOR REAL-TIME DATA (Optional - Best Performance) ==========
def websocket_realtime_data():
    """WebSocket से Real-time Data लेना - सबसे तेज़ तरीका"""
    
    def on_message(message):
        """WebSocket से message आने पर"""
        print("Live Data:", message)
        # यहाँ अपने सिग्नल लॉजिक को कॉल करें
    
    def on_error(message):
        print("Error:", message)
    
    def on_close(message):
        print("Connection closed:", message)
    
    def on_open():
        """WebSocket open होने पर सब्सक्राइब करें"""
        data_type = "SymbolUpdate"  # LTP के लिए Lite mode
        symbols = ['NSE:RELIANCE-EQ', 'NSE:TCS-EQ', 'NSE:HDFCBANK-EQ']
        fyers.subscribe(symbols=symbols, data_type=data_type)
        fyers.keep_running()
    
    # WebSocket Connection
    fyers = data_ws.FyersDataSocket(
        access_token=ACCESS_TOKEN,
        log_path="",
        litemode=True,  # True = सिर्फ LTP आएगा (fastest)
        write_to_file=False,
        reconnect=True,
        on_connect=on_open,
        on_close=on_close,
        on_error=on_error,
        on_message=on_message
    )
    
    fyers.connect()

# ========== STOCKS LIST ==========
ALL_STOCKS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL",
    "KOTAKBANK", "BAJFINANCE", "ITC", "LT", "WIPRO", "AXISBANK", "HCLTECH"
]

# ========== TECHNICAL INDICATORS (Same as before) ==========
# ... (आपके सारे technical indicator functions यहाँ रहेंगे)
def calculate_ema(close, period): return close.ewm(span=period, adjust=False).mean()
# ... (बाकी सारे functions जो आपने पहले लिखे थे)

def generate_signal(df, symbol=None):
    if df is None or len(df) < 50: return None
    # ... (आपका पुराना generate_signal function वैसा ही रहेगा)
    # बस इसमें FYERS के data के साथ काम करेगा
    pass

# ========== GAINERS/LOSERS ==========
def get_top_gainers_losers():
    gainers, losers = [], []
    stocks = ["RELIANCE","TCS","HDFCBANK","INFY","ICICIBANK","SBIN","BHARTIARTL","KOTAKBANK","BAJFINANCE","ITC","LT","WIPRO","AXISBANK","HCLTECH"]
    
    for sym in stocks:
        q = get_live_quote_fyers(sym)
        if q and q['change_percent'] != 0:
            data = {'symbol': sym, 'price': q['ltp'], 'change': q['change'], 'change_percent': q['change_percent']}
            if q['change_percent'] > 0:
                gainers.append(data)
            else:
                losers.append(data)
        time.sleep(0.1)  # Rate limit से बचने के लिए
    
    gainers.sort(key=lambda x: x['change_percent'], reverse=True)
    losers.sort(key=lambda x: x['change_percent'])
    return gainers[:5], losers[:5]

def detect_market_trend():
    bullish, bearish = 0, 0
    trend_stocks = ["RELIANCE","TCS","HDFCBANK","INFY","ICICIBANK","SBIN","BHARTIARTL"]
    
    for sym in trend_stocks:
        q = get_live_quote_fyers(sym)
        if q:
            if q['change'] > 0:
                bullish += 1
            else:
                bearish += 1
        time.sleep(0.1)
    
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
        status.text(f"🎯 Analyzing: {sym} ({i+1}/{total})")
        progress.progress((i+1)/total)
        
        df = get_historical_data_fyers(sym, interval="5", days=5)
        if df is not None and len(df) > 50:
            sig = generate_signal(df, sym)
            if sig:
                sig['symbol'] = sym
                sig['entry_time'] = datetime.now().strftime("%H:%M:%S")
                signals.append(sig)
        time.sleep(0.2)
    
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

# ========== MAIN APP ==========
def main():
    st.sidebar.write(f"👤 Welcome {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    st.markdown("<h1>🎯 90% ACCURACY SIGNAL BOT (FYERS)</h1>", unsafe_allow_html=True)
    st.markdown("⚡ 5-MINUTE TIMEFRAME | REAL-TIME DATA | AUTO-SCAN", unsafe_allow_html=True)

    market_trend, trend_msg = detect_market_trend()
    st.session_state.market_trend = market_trend
    st.info(trend_msg)

    # Gainers / Losers
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("🔄 Refresh Gainers/Losers"):
            with st.spinner("Fetching..."):
                st.session_state.top_gainers, st.session_state.top_losers = get_top_gainers_losers()
    if not st.session_state.top_gainers:
        with st.spinner("Initial load..."):
            st.session_state.top_gainers, st.session_state.top_losers = get_top_gainers_losers()

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🟢 TOP 5 GAINERS")
        for g in st.session_state.top_gainers:
            st.markdown(f"📈 **{g['symbol']}** +{g['change_percent']:.2f}%  ₹{g['price']:.2f}")
    with col_b:
        st.subheader("🔴 TOP 5 LOSERS")
        for l in st.session_state.top_losers:
            st.markdown(f"📉 **{l['symbol']}** {l['change_percent']:.2f}%  ₹{l['price']:.2f}")

    st.markdown("---")
    col_btn1, col_btn2 = st.columns([2,1])
    with col_btn1:
        scan = st.button("🔍 SCAN ALL STOCKS - FIND 90%+ SIGNALS", type="primary", use_container_width=True)
        auto = st.checkbox("🔄 AUTO-SCAN (Every 60 sec)", value=True, key="auto_scan")
    with col_btn2:
        if st.button("🗑️ Clear Signals"):
            st.session_state.signals = []
            st.session_state.last_scan = None
            st.rerun()

    should_scan = scan
    if auto and (st.session_state.last_scan is None or (datetime.now() - st.session_state.last_scan).seconds >= 60):
        should_scan = True

    if should_scan:
        with st.spinner(f"Scanning {len(ALL_STOCKS)} stocks..."):
            st.session_state.signals = scan_all_stocks()
            st.session_state.last_scan = datetime.now()
        if st.session_state.signals:
            st.balloons()
            st.success(f"🎯 Found {len(st.session_state.signals)} signals!")
        else:
            st.info("No strong signals found.")

    if st.session_state.last_scan:
        st.caption(f"Last scan: {st.session_state.last_scan.strftime('%H:%M:%S')} | Market Trend: {market_trend}")

    # Display signals (same as before)
    if st.session_state.signals:
        for sig in st.session_state.signals[:10]:
            if sig['signal'] == 'STRONG_BUY':
                st.markdown(f"""
                <div class='strong-buy'>
                    <span class='badge-buy'>STRONG BUY</span> <span style="float:right">🎯 Accuracy: {sig['probability']:.0f}%</span>
                    <h2>📈 {sig['symbol']}</h2>
                    <div style="display:flex; gap:10px; flex-wrap:wrap;">
                        <div class='metric-box'>Entry<br><span class='price-up'>₹{sig['price']:.2f}</span></div>
                        <div class='metric-box'>Target1<br>₹{sig['target1']:.2f}</div>
                        <div class='metric-box'>Target2<br>₹{sig['target2']:.2f}</div>
                        <div class='metric-box'>Target3<br>₹{sig['target3']:.2f}</div>
                        <div class='metric-box'>Stop Loss<br>₹{sig['stop_loss']:.2f}</div>
                        <div class='metric-box'>RSI<br>{sig['rsi']:.1f}</div>
                        <div class='metric-box'>ADX<br>{sig['adx']:.1f}</div>
                    </div>
                    <p><strong>EMA:</strong> {sig['ema9']:.2f} / {sig['ema21']:.2f} / {sig['ema50']:.2f}</p>
                    <p><strong>Signals:</strong> {', '.join(sig['reasons'])}</p>
                </div>
                """, unsafe_allow_html=True)
                with st.expander("📊 Chart"):
                    st.components.v1.html(get_tradingview_chart(sig['symbol']), height=540)
            else:
                st.markdown(f"""
                <div class='strong-sell'>
                    <span class='badge-sell'>STRONG SELL</span> <span style="float:right">🎯 Accuracy: {sig['probability']:.0f}%</span>
                    <h2>📉 {sig['symbol']}</h2>
                    <div style="display:flex; gap:10px; flex-wrap:wrap;">
                        <div class='metric-box'>Entry<br><span class='price-down'>₹{sig['price']:.2f}</span></div>
                        <div class='metric-box'>Target1<br>₹{sig['target1']:.2f}</div>
                        <div class='metric-box'>Target2<br>₹{sig['target2']:.2f}</div>
                        <div class='metric-box'>Target3<br>₹{sig['target3']:.2f}</div>
                        <div class='metric-box'>Stop Loss<br>₹{sig['stop_loss']:.2f}</div>
                        <div class='metric-box'>RSI<br>{sig['rsi']:.1f}</div>
                        <div class='metric-box'>ADX<br>{sig['adx']:.1f}</div>
                    </div>
                    <p><strong>EMA:</strong> {sig['ema9']:.2f} / {sig['ema21']:.2f} / {sig['ema50']:.2f}</p>
                    <p><strong>Signals:</strong> {', '.join(sig['reasons'])}</p>
                </div>
                """, unsafe_allow_html=True)
                with st.expander("📊 Chart"):
                    st.components.v1.html(get_tradingview_chart(sig['symbol']), height=540)
    else:
        st.info("Click 'SCAN ALL STOCKS' to get signals.")

if __name__ == "__main__":
    main()
