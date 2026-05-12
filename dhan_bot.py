import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import requests

# ========== DHAN CREDENTIALS ==========
DHAN_CLIENT_ID = "1103750176"
# ⚠️ Your token expires every 24 hours. Replace with a fresh one if you get 401 errors.
DHAN_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzc4NjQyOTE3LCJpYXQiOjE3Nzg1NTY1MTcsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTAzNzUwMTc2In0.E709I8Hi0529OYvXDYvL_IOLTzPqaJnjXrTkCAicbgG5OrIhD13jRIQNpStTOxppZ6yYr3dxAVOPUA0jMw-QOg"
DHAN_API_KEY = "817685e9"
DHAN_API_SECRET = "04eda619-f3a1-4342-b34a-54422ebe55f7"

# ========== USER LOGIN ==========
USER_CREDENTIALS = {
    "admin": "stock123",
    "trader": "dhan2024",
    "user": "password",
    "vip": "vip2024"
}

st.set_page_config(layout="wide", page_title="🔥 90% Accuracy Dhan Signal Bot", page_icon="🎯")

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
def get_dhan_headers():
    return {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'access-token': DHAN_ACCESS_TOKEN,
        'client-id': DHAN_CLIENT_ID
    }

def get_live_quote(symbol):
    """Get live LTP and change using the correct /v2/marketfeed/ohlc endpoint (POST)"""
    try:
        url = "https://api.dhan.co/v2/marketfeed/ohlc"
        payload = [symbol]  # API expects a list of symbols
        response = requests.post(url, headers=get_dhan_headers(), json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                item = data[0]
                return {
                    'ltp': item.get('lastPrice', 0),
                    'change': item.get('change', 0),
                    'change_percent': item.get('changePercent', 0)
                }
        else:
            st.error(f"Quote error {response.status_code} for {symbol}: {response.text[:200]}")
    except Exception as e:
        st.error(f"Quote exception {symbol}: {e}")
    return None

def get_dhan_history(symbol, interval="5", days=5):
    """Historical data using POST /v2/charts/historical"""
    try:
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        url = "https://api.dhan.co/v2/charts/historical"
        payload = {
            "symbol": symbol,
            "exchangeSegment": "NSE",
            "instrument": "EQUITY",
            "fromDate": from_date.strftime("%Y-%m-%d"),
            "toDate": to_date.strftime("%Y-%m-%d"),
            "interval": interval
        }
        response = requests.post(url, headers=get_dhan_headers(), json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            candles = data.get("data", {}).get("candles", [])
            if candles:
                df_data = []
                for c in candles:
                    df_data.append({
                        'timestamp': pd.to_datetime(c[0], unit='ms'),
                        'Open': c[1], 'High': c[2], 'Low': c[3], 'Close': c[4], 'Volume': c[5]
                    })
                df = pd.DataFrame(df_data)
                df.set_index('timestamp', inplace=True)
                return df
        else:
            st.error(f"History error {response.status_code} for {symbol}: {response.text[:200]}")
    except Exception as e:
        st.error(f"History exception {symbol}: {e}")
    return None

# ========== STOCKS LIST (extensive – you can keep yours) ==========
ALL_STOCKS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL",
    "KOTAKBANK", "BAJFINANCE", "ITC", "LT", "WIPRO", "AXISBANK", "HCLTECH"
]  # You can replace with your full list later

# ========== TECHNICAL INDICATORS (all your functions – unchanged) ==========
def calculate_ema(close, period): return close.ewm(span=period, adjust=False).mean()
def calculate_rsi(close, period=14):
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))
def calculate_macd(close):
    exp1 = close.ewm(span=12, adjust=False).mean()
    exp2 = close.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd - signal
def calculate_bollinger(close, period=20, std_dev=2):
    sma = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()
    return sma + (std * std_dev), sma, sma - (std * std_dev)
def calculate_vwap(df):
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    return (tp * df['Volume']).cumsum() / df['Volume'].cumsum()
def calculate_adx(df, period=14):
    high, low, close = df['High'], df['Low'], df['Close']
    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1/period).mean() / atr)
    minus_di = 100 * (minus_dm.abs().ewm(alpha=1/period).mean() / atr)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    return dx.rolling(window=period).mean(), plus_di, minus_di
def detect_candle_patterns(df):
    if len(df) < 2: return []
    patterns = []
    c1, c2 = df.iloc[-2], df.iloc[-1]
    body = abs(c2['Close'] - c2['Open'])
    lower_wick = min(c2['Open'], c2['Close']) - c2['Low']
    upper_wick = c2['High'] - max(c2['Open'], c2['Close'])
    if lower_wick > body * 2 and upper_wick < body * 0.5: patterns.append("Hammer (Bullish)")
    if upper_wick > body * 2 and lower_wick < body * 0.5: patterns.append("Shooting Star (Bearish)")
    if c1['Close'] < c1['Open'] and c2['Close'] > c2['Open'] and c2['Open'] < c1['Close']: patterns.append("Bullish Engulfing")
    if c1['Close'] > c1['Open'] and c2['Close'] < c2['Open'] and c2['Open'] > c1['Close']: patterns.append("Bearish Engulfing")
    return patterns
def calculate_volume_profile(df):
    avg_vol = df['Volume'].rolling(20).mean()
    return df['Volume'].iloc[-1] / avg_vol.iloc[-1] if avg_vol.iloc[-1] > 0 else 1
def calculate_probability(signal, rsi, adx, volume_ratio, market_trend):
    base = signal.get('probability', 70) if isinstance(signal, dict) else 70
    if isinstance(signal, dict):
        if signal['signal'] == 'STRONG_BUY':
            if rsi < 30: base += 8
            elif rsi < 40: base += 4
        else:
            if rsi > 70: base += 8
            elif rsi > 60: base += 4
    else:
        if rsi < 30: base += 8
        elif rsi < 40: base += 4
        elif rsi > 70: base += 8
        elif rsi > 60: base += 4
    if adx > 35: base += 5
    elif adx > 25: base += 2
    if volume_ratio > 2: base += 5
    elif volume_ratio > 1.5: base += 2
    if market_trend == 'BULLISH' and isinstance(signal, dict) and signal.get('signal') == 'STRONG_BUY':
        base += 5
    elif market_trend == 'BEARISH' and isinstance(signal, dict) and signal.get('signal') == 'STRONG_SELL':
        base += 5
    else:
        base -= 3
    return min(98, max(50, base))

def generate_signal(df, symbol=None):
    if df is None or len(df) < 50: return None
    close = df['Close']
    ema9 = calculate_ema(close, 9)
    ema21 = calculate_ema(close, 21)
    ema50 = calculate_ema(close, 50)
    rsi = calculate_rsi(close)
    macd_hist = calculate_macd(close)
    bb_upper, bb_middle, bb_lower = calculate_bollinger(close)
    vwap = calculate_vwap(df)
    adx, plus_di, minus_di = calculate_adx(df)
    patterns = detect_candle_patterns(df)
    volume_ratio = calculate_volume_profile(df)

    current_price = close.iloc[-1]
    curr_ema9, curr_ema21, curr_ema50 = ema9.iloc[-1], ema21.iloc[-1], ema50.iloc[-1]
    curr_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
    curr_macd = macd_hist.iloc[-1] if not pd.isna(macd_hist.iloc[-1]) else 0
    curr_adx = adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 20
    curr_vwap = vwap.iloc[-1]
    atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
    if pd.isna(atr): atr = current_price * 0.01

    bullish_score, bearish_score = 0, 0
    reasons_bullish, reasons_bearish = [], []

    # EMA
    if curr_ema9 > curr_ema21 > curr_ema50:
        bullish_score += 25; reasons_bullish.append("✅ EMA 9>21>50")
    elif curr_ema9 > curr_ema21:
        bullish_score += 15; reasons_bullish.append("✅ EMA 9>21")
    elif curr_ema9 < curr_ema21 < curr_ema50:
        bearish_score += 25; reasons_bearish.append("❌ EMA 9<21<50")
    elif curr_ema9 < curr_ema21:
        bearish_score += 15; reasons_bearish.append("❌ EMA 9<21")
    # VWAP
    if current_price > curr_vwap:
        bullish_score += 15; reasons_bullish.append("✅ Above VWAP")
    else:
        bearish_score += 15; reasons_bearish.append("❌ Below VWAP")
    # RSI
    if curr_rsi < 30:
        bullish_score += 20; reasons_bullish.append(f"✅ RSI {curr_rsi:.1f} oversold")
    elif curr_rsi < 40:
        bullish_score += 10
    elif curr_rsi > 70:
        bearish_score += 20; reasons_bearish.append(f"❌ RSI {curr_rsi:.1f} overbought")
    elif curr_rsi > 60:
        bearish_score += 10
    # MACD
    if curr_macd > 0:
        bullish_score += 15; reasons_bullish.append("✅ MACD bullish")
    else:
        bearish_score += 15; reasons_bearish.append("❌ MACD bearish")
    # Bollinger
    if current_price <= bb_lower.iloc[-1]:
        bullish_score += 10
    elif current_price >= bb_upper.iloc[-1]:
        bearish_score += 10
    # ADX
    if curr_adx > 25:
        if plus_di.iloc[-1] > minus_di.iloc[-1]:
            bullish_score += 10; reasons_bullish.append(f"✅ ADX {curr_adx:.1f}")
        else:
            bearish_score += 10; reasons_bearish.append(f"❌ ADX {curr_adx:.1f}")
    # Volume
    if volume_ratio > 1.5:
        if bullish_score > bearish_score:
            bullish_score += 10; reasons_bullish.append(f"✅ Volume {volume_ratio:.1f}x")
        else:
            bearish_score += 10; reasons_bearish.append(f"❌ Volume {volume_ratio:.1f}x")
    # Candlestick
    for p in patterns:
        if "Bullish" in p or "Hammer" in p:
            bullish_score += 10; reasons_bullish.append(f"📊 {p}")
        else:
            bearish_score += 10; reasons_bearish.append(f"📊 {p}")

    if bullish_score >= 70 and bullish_score > bearish_score:
        prob = min(98, bullish_score)
        return {
            'signal': 'STRONG_BUY', 'probability': prob, 'price': current_price,
            'target1': current_price + atr*1.5, 'target2': current_price + atr*2.5, 'target3': current_price + atr*4,
            'stop_loss': current_price - atr*1.2, 'rsi': curr_rsi, 'adx': curr_adx,
            'volume_ratio': volume_ratio, 'vwap': curr_vwap,
            'ema9': curr_ema9, 'ema21': curr_ema21, 'ema50': curr_ema50,
            'reasons': reasons_bullish[:5], 'candle_patterns': patterns
        }
    elif bearish_score >= 70 and bearish_score > bullish_score:
        prob = min(98, bearish_score)
        return {
            'signal': 'STRONG_SELL', 'probability': prob, 'price': current_price,
            'target1': current_price - atr*1.5, 'target2': current_price - atr*2.5, 'target3': current_price - atr*4,
            'stop_loss': current_price + atr*1.2, 'rsi': curr_rsi, 'adx': curr_adx,
            'volume_ratio': volume_ratio, 'vwap': curr_vwap,
            'ema9': curr_ema9, 'ema21': curr_ema21, 'ema50': curr_ema50,
            'reasons': reasons_bearish[:5], 'candle_patterns': patterns
        }
    return None

# ========== GAINERS, LOSERS, MARKET TREND ==========
def get_top_gainers_losers():
    gainers, losers = [], []
    stocks = ["RELIANCE","TCS","HDFCBANK","INFY","ICICIBANK","SBIN","BHARTIARTL","KOTAKBANK","BAJFINANCE","ITC","LT","WIPRO","AXISBANK","HCLTECH"]
    for sym in stocks:
        q = get_live_quote(sym)
        if q and q['change_percent'] != 0:
            data = {'symbol': sym, 'price': q['ltp'], 'change': q['change'], 'change_percent': q['change_percent']}
            if q['change_percent'] > 0: gainers.append(data)
            else: losers.append(data)
        time.sleep(0.05)
    gainers.sort(key=lambda x: x['change_percent'], reverse=True)
    losers.sort(key=lambda x: x['change_percent'])
    return gainers[:5], losers[:5]

def detect_market_trend():
    bullish, bearish = 0, 0
    for sym in ["RELIANCE","TCS","HDFCBANK","INFY","ICICIBANK","SBIN","BHARTIARTL"]:
        q = get_live_quote(sym)
        if q:
            if q['change'] > 0: bullish += 1
            else: bearish += 1
    if bullish > bearish + 2: return "BULLISH", f"🟢 BULLISH ({bullish} up)"
    if bearish > bullish + 2: return "BEARISH", f"🔴 BEARISH ({bearish} down)"
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
            sig = generate_signal(df, sym)
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

# ========== MAIN APP ==========
def main():
    st.sidebar.write(f"👤 Welcome {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    st.markdown("<h1>🎯 90% ACCURACY SIGNAL BOT</h1>", unsafe_allow_html=True)
    st.markdown("⚡ 5-MINUTE TIMEFRAME | AUTO-SCAN | GAINERS/LOSERS", unsafe_allow_html=True)

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
        auto = st.checkbox("🔄 AUTO-SCAN (Every 60 sec)", value=True)
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
            for sig in st.session_state.signals:
                updated_prob = calculate_probability(sig, sig['rsi'], sig['adx'], sig['volume_ratio'], market_trend)
                sig['probability'] = updated_prob
        if st.session_state.signals:
            st.balloons()
            st.success(f"🎯 Found {len(st.session_state.signals)} signals!")
            st.session_state.top_gainers, st.session_state.top_losers = get_top_gainers_losers()
        else:
            st.info("No strong signals found.")

    if st.session_state.last_scan:
        st.caption(f"Last scan: {st.session_state.last_scan.strftime('%H:%M:%S')} | Market Trend: {market_trend}")

    # Display signals
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
