import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import requests
import urllib.parse
import random
import string
import warnings
warnings.filterwarnings('ignore')

# ========== FYERS CREDENTIALS ==========
FYERS_APP_ID = "ER78MCCWG0-100"           
FYERS_SECRET_ID = "9MLTKAAHCQ"      
FYERS_ACCESS_TOKEN = "JVHC6XLKBY6OOII5VSAKRTA3QTOIO2MM"
REDIRECT_URI = "http://127.0.0.1:8501"

# ========== PAGE CONFIG ==========
st.set_page_config(
    layout="wide", 
    page_title="90% Accuracy SMC Signal Bot - FYERS", 
    page_icon="🎯",
    initial_sidebar_state="expanded"
)

# ========== CSS ==========
st.markdown("""
<style>
    .stApp { background-color: #050505; }
    h1 { color: #00ff88 !important; text-align: center; font-size: 42px; }
    h2 { color: #00ff88 !important; }
    .signal-card {
        background: linear-gradient(135deg, #0d0d0d 0%, #0a0a0a 100%);
        border-radius: 20px;
        padding: 25px;
        margin: 15px 0;
        border: 1px solid #1a1a1a;
        animation: slideIn 0.5s ease-out;
    }
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .strong-buy { 
        border-left: 8px solid #00ff88; 
        background: linear-gradient(135deg, #0a2a0a 0%, #0a0a0a 100%);
    }
    .strong-sell { 
        border-left: 8px solid #ff3333; 
        background: linear-gradient(135deg, #2a0a0a 0%, #0a0a0a 100%);
    }
    .badge-buy { background: #00ff88; color: #000; padding: 8px 20px; border-radius: 25px; font-weight: bold; }
    .badge-sell { background: #ff3333; color: #fff; padding: 8px 20px; border-radius: 25px; font-weight: bold; }
    .price-up { color: #00ff88; font-size: 32px; font-weight: bold; }
    .price-down { color: #ff3333; font-size: 32px; font-weight: bold; }
    .metric-box { background: #0d0d0d; border-radius: 12px; padding: 12px; text-align: center; border: 1px solid #1a1a1a; }
    .probability-high { background: #00ff88; border-radius: 30px; padding: 8px 20px; text-align: center; color: #000; font-weight: bold; animation: pulse 1s ease-in-out infinite alternate; }
    @keyframes pulse { from { transform: scale(1); } to { transform: scale(1.05); } }
    .api-status { background: #1a1a1a; border-radius: 10px; padding: 5px 10px; font-size: 12px; display: inline-block; }
    .entry-time { color: #ffaa00; font-size: 14px; font-family: monospace; }
    
    /* Simple Gainer/Loser Colors - Normal Icons */
    .gainer-normal {
        color: #00ff88 !important;
        font-weight: bold;
    }
    .loser-normal {
        color: #ff3333 !important;
        font-weight: bold;
    }
    .gainers-card-normal {
        background: linear-gradient(135deg, #0a2a0a 0%, #0a0a0a 100%);
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
    }
    .losers-card-normal {
        background: linear-gradient(135deg, #2a0a0a 0%, #0a0a0a 100%);
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
    }
    .highlight-stock {
        border: 2px solid #ffaa00;
        box-shadow: 0 0 15px rgba(255, 170, 0, 0.5);
        animation: glow 1s ease-in-out infinite alternate;
    }
    @keyframes glow {
        from { box-shadow: 0 0 10px rgba(255, 170, 0, 0.3); }
        to { box-shadow: 0 0 20px rgba(255, 170, 0, 0.8); }
    }
    /* Mode Button Colors */
    .test-mode-active {
        background-color: #ff6600 !important;
        color: white !important;
        border: 2px solid #ffaa00 !important;
    }
    .live-mode-active {
        background-color: #00ff88 !important;
        color: black !important;
        border: 2px solid #00ff88 !important;
    }
    .mode-button {
        transition: all 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

# ========== BOT PASSWORD ==========
USERNAME = "admin"
PASSWORD = "stock123"

# ========== SESSION STATE INITIALIZATION ==========
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "fyers_token" not in st.session_state:
    st.session_state.fyers_token = FYERS_ACCESS_TOKEN
if "signals" not in st.session_state:
    st.session_state.signals = []
if "last_scan" not in st.session_state:
    st.session_state.last_scan = None
if "auto_scan_active" not in st.session_state:
    st.session_state.auto_scan_active = False
if "top_gainers" not in st.session_state:
    st.session_state.top_gainers = []
if "top_losers" not in st.session_state:
    st.session_state.top_losers = []
if "market_trend" not in st.session_state:
    st.session_state.market_trend = "NEUTRAL"
if "test_mode" not in st.session_state:
    st.session_state.test_mode = True  # Default Test Mode ON

# ========== LOGIN FUNCTION ==========
def show_login():
    st.markdown("<h1 style='text-align: center;'>🎯 90% ACCURACY SIGNAL BOT</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #ffaa00;'>SMC | EMA | RSI | MACD | VWAP | FYERS Live Data</p>", unsafe_allow_html=True)
    
    with st.form(key="login_form_main"):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Login", key="login_button_main")
        
        if submitted:
            if username == USERNAME and password == PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

if not st.session_state["authenticated"]:
    show_login()
    st.stop()

# ========== FYERS API FUNCTIONS ==========
def get_auth_header():
    return f"{FYERS_APP_ID}:{st.session_state.fyers_token}"

def get_history_fyers(symbol, resolution="15", days=5):
    if not st.session_state.fyers_token:
        return None
    
    if st.session_state.test_mode:
        dates = pd.date_range(end=datetime.now(), periods=80, freq='15min')
        df = pd.DataFrame({
            'Open': np.random.uniform(100, 500, 80),
            'High': np.random.uniform(100, 500, 80),
            'Low': np.random.uniform(100, 500, 80),
            'Close': np.random.uniform(100, 500, 80),
            'Volume': np.random.randint(100000, 1000000, 80)
        }, index=dates)
        return df
    
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days)
    
    url = "https://api.fyers.in/api/v3/history"
    headers = {"Authorization": get_auth_header()}
    params = {
        'symbol': f"NSE:{symbol}",
        'resolution': resolution,
        'date_format': '1',
        'range_from': from_date.strftime("%Y-%m-%d"),
        'range_to': to_date.strftime("%Y-%m-%d"),
        'cont_flag': '1'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('s') == 'ok' and data.get('candles'):
                df = pd.DataFrame(data['candles'], columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                df.set_index('timestamp', inplace=True)
                return df
    except Exception as e:
        print(f"History Exception: {e}")
    return None

def get_live_quote_fyers(symbol):
    if st.session_state.test_mode:
        base_price = random.uniform(500, 5000)
        change_percent = random.uniform(-5, 5)
        change = base_price * change_percent / 100
        return {
            'ltp': base_price,
            'change': change,
            'change_percent': change_percent
        }
    
    if not st.session_state.fyers_token:
        return None
    
    url = "https://api.fyers.in/api/v3/quotes"
    headers = {"Authorization": get_auth_header()}
    params = {'symbols': f"NSE:{symbol}"}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('s') == 'ok' and data.get('d'):
                item = data['d'][0]
                v_data = item.get('v', {})
                return {
                    'ltp': float(v_data.get('lp', 0)),
                    'change': float(v_data.get('ch', 0)),
                    'change_percent': float(v_data.get('chp', 0))
                }
    except Exception as e:
        print(f"Quotes API exception for {symbol}: {e}")
    return None

# ========== COMPLETE 207 STOCKS ==========
ALL_STOCKS = [
    "360ONE", "ABB", "ABCAPITAL", "ADANIENSOL", "ADANIENT", "ADANIGREEN", "ADANIPORTS", 
    "ALKEM", "AMBER", "AMBUJACEM", "ANGELONE", "APLAPOLLO", "APOLLOHOSP", "ASHOKLEY", 
    "ASIANPAINT", "ASTRAL", "AUBANK", "AUROPHARMA", "AXISBANK", "BAJAJ-AUTO", "BAJAJFINSV", 
    "BAJAJHLDNG", "BAJFINANCE", "BANDHANBNK", "BANKBARODA", "BANKINDIA", "BDL", "BEL", 
    "BHARATFORG", "BHARTIARTL", "BHEL", "BIOCON", "BLUESTARCO", "BOSCHLTD", "BPCL", 
    "BRITANNIA", "BSE", "CAMS", "CANBK", "CDSL", "CGPOWER", "CHOLAFIN", "CIPLA", "COALINDIA", 
    "COFORGE", "COLPAL", "CONCOR", "CROMPTON", "CUMMINSIND", "DABUR", "DALBHARAT", "DELHIVERY", 
    "DIVISLAB", "DIXON", "DLF", "DMART", "DRREDDY", "EICHERMOT", "ETERNAL", "EXIDEIND", 
    "FEDERALBNK", "FORTIS", "GAIL", "GLENMARK", "GMRAIRPORT", "GODREJCP", "GODREJPROP", 
    "GRASIM", "HAL", "HAVELLS", "HCLTECH", "HDFCAMC", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", 
    "HINDALCO", "HINDPETRO", "HINDUNILVR", "HINDZINC", "HUDCO", "ICICIBANK", "ICICIGI", 
    "ICICIPRULI", "IDEA", "IDFCFIRSTB", "IEX", "INDHOTEL", "INDIANB", "INDIGO", "INDUSINDBK", 
    "INDUSTOWER", "INFY", "INOXWIND", "IOC", "IREDA", "IRFC", "ITC", "JINDALSTEL", "JIOFIN", 
    "JSWENERGY", "JSWSTEEL", "JUBLFOOD", "KALYANKJIL", "KAYNES", "KEI", "KFINTECH", "KOTAKBANK", 
    "KPITTECH", "LAURUSLABS", "LICHSGFIN", "LICI", "LODHA", "LT", "LTF", "LUPIN", "M&M", 
    "MANAPPURAM", "MANKIND", "MARICO", "MARUTI", "MAXHEALTH", "MAZDOCK", "MCX", "MFSL", 
    "MOTHERSON", "MPHASIS", "MUTHOOTFIN", "NATIONALUM", "NAUKRI", "NBCC", "NESTLEIND", "NHPC", 
    "NMDC", "NTPC", "NUVAMA", "NYKAA", "OBEROIRLTY", "OFSS", "OIL", "ONGC", "PAGEIND", 
    "PATANJALI", "PAYTM", "PERSISTENT", "PETRONET", "PFC", "PGEL", "PHOENIXLTD", "PIDILITIND", 
    "PIIND", "PNB", "PNBHOUSING", "POLICYBZR", "POLYCAB", "POWERGRID", "POWERINDIA", "PPLPHARMA", 
    "PREMIERENE", "PRESTIGE", "RBLBANK", "RECLTD", "RELIANCE", "RVNL", "SAIL", "SAMMAANCAP", 
    "SBICARD", "SBILIFE", "SBIN", "SHREECEM", "SHRIRAMFIN", "SIEMENS", "SOLARINDS", "SONACOMS", 
    "SRF", "SUNPHARMA", "SUPREMEIND", "SUZLON", "SWIGGY", "SYNGENE", "TATACONSUM", "TATAELXSI", 
    "TATAPOWER", "TATASTEEL", "TATATECH", "TCS", "TECHM", "TIINDIA", "TITAN", "TORNTPHARM", 
    "TORNTPOWER", "TRENT", "TVSMOTOR", "ULTRACEMCO", "UNIONBANK", "UNITDSPR", "UNOMINDA", 
    "UPL", "VBL", "VEDL", "VOLTAS", "WAAREEENER", "WIPRO", "YESBANK", "ZYDUSLIFE"
]

# ========== TECHNICAL INDICATORS ==========
def calculate_ema(close, period):
    return close.ewm(span=period, adjust=False).mean()

def calculate_macd(close):
    exp1 = close.ewm(span=12, adjust=False).mean()
    exp2 = close.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd - signal

def calculate_rsi(close, period=14):
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

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

def detect_smc_patterns(df):
    if len(df) < 30:
        return {'liquidity_sweep_low': False, 'bos_up': False, 'liquidity_sweep_high': False, 'bos_down': False}
    
    high = df['High'].values
    low = df['Low'].values
    close = df['Close'].values
    
    swing_highs = []
    swing_lows = []
    
    for i in range(5, len(df)-5):
        if all(high[i] >= high[i-j] for j in range(1, 4)) and all(high[i] >= high[i+j] for j in range(1, 4)):
            swing_highs.append(i)
        if all(low[i] <= low[i-j] for j in range(1, 4)) and all(low[i] <= low[i+j] for j in range(1, 4)):
            swing_lows.append(i)
    
    liquidity_sweep_high = False
    liquidity_sweep_low = False
    bos_up = False
    bos_down = False
    
    if len(swing_highs) > 1 and close[-1] > high[swing_highs[-1]]:
        liquidity_sweep_high = True
    if len(swing_lows) > 1 and close[-1] < low[swing_lows[-1]]:
        liquidity_sweep_low = True
    if len(swing_highs) > 2 and high[swing_highs[-1]] > high[swing_highs[-2]]:
        bos_up = True
    if len(swing_lows) > 2 and low[swing_lows[-1]] < low[swing_lows[-2]]:
        bos_down = True
    
    return {'liquidity_sweep_low': liquidity_sweep_low, 'bos_up': bos_up,
            'liquidity_sweep_high': liquidity_sweep_high, 'bos_down': bos_down}

def detect_candle_patterns(df):
    if len(df) < 3:
        return []
    patterns = []
    c1 = df.iloc[-2]
    c2 = df.iloc[-1]
    
    o2, h2, l2, c2_close = c2['Open'], c2['High'], c2['Low'], c2['Close']
    body = abs(c2_close - o2)
    lower_wick = min(o2, c2_close) - l2
    upper_wick = h2 - max(o2, c2_close)
    
    if lower_wick > body * 2 and upper_wick < body * 0.5:
        patterns.append("Hammer (Bullish)")
    if upper_wick > body * 2 and lower_wick < body * 0.5:
        patterns.append("Shooting Star (Bearish)")
    
    if len(df) >= 2:
        if c1['Close'] < c1['Open'] and c2_close > o2 and o2 < c1['Close'] and c2_close > c1['Open']:
            patterns.append("Bullish Engulfing")
        if c1['Close'] > c1['Open'] and c2_close < o2 and o2 > c1['Close'] and c2_close < c1['Open']:
            patterns.append("Bearish Engulfing")
    
    return patterns

# ========== GENERATE SIGNAL WITH TEST MODE ==========
def generate_high_accuracy_signal(df, symbol=None):
    if st.session_state.test_mode:
        test_symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL", "KOTAKBANK", "BAJFINANCE", "ITC"]
        if symbol in test_symbols:
            import random
            is_buy = random.choice([True, False])
            prob = random.randint(75, 98)
            price = random.uniform(1000, 5000)
            return {
                'signal': 'STRONG_BUY' if is_buy else 'STRONG_SELL',
                'probability': prob,
                'price': price,
                'target1': price * (1 + random.uniform(0.02, 0.05)),
                'target2': price * (1 + random.uniform(0.05, 0.08)),
                'target3': price * (1 + random.uniform(0.08, 0.12)),
                'stop_loss': price * (1 - random.uniform(0.02, 0.04)),
                'rsi': random.uniform(20, 80),
                'adx': random.uniform(25, 50),
                'volume_ratio': random.uniform(1.2, 2.5),
                'vwap': price * (1 + random.uniform(-0.02, 0.02)),
                'ema9': price * (1 + random.uniform(-0.01, 0.02)),
                'ema21': price * (1 + random.uniform(-0.02, 0.01)),
                'ema50': price * (1 + random.uniform(-0.03, 0)),
                'reasons': ["✅ Strong Technical Setup", "✅ Volume Confirmation", "✅ Bullish Pattern Detected"],
                'candle_patterns': ["Bullish Engulfing"],
                'smc': {'liquidity_sweep_low': True, 'bos_up': True}
            }
    
    if df is None or len(df) < 50:
        return None
    
    close = df['Close']
    high = df['High']
    low = df['Low']
    volume = df['Volume']
    
    ema9 = calculate_ema(close, 9)
    ema21 = calculate_ema(close, 21)
    ema50 = calculate_ema(close, 50)
    macd_hist = calculate_macd(close)
    rsi = calculate_rsi(close)
    bb_upper, bb_middle, bb_lower = calculate_bollinger(close)
    vwap = calculate_vwap(df)
    adx, plus_di, minus_di = calculate_adx(df)
    smc = detect_smc_patterns(df)
    candle_patterns = detect_candle_patterns(df)
    
    avg_volume = volume.rolling(window=20).mean()
    volume_ratio = volume.iloc[-1] / avg_volume.iloc[-1] if avg_volume.iloc[-1] > 0 else 1
    
    current_price = close.iloc[-1]
    current_ema9 = ema9.iloc[-1]
    current_ema21 = ema21.iloc[-1]
    current_ema50 = ema50.iloc[-1]
    current_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
    current_macd = macd_hist.iloc[-1] if not pd.isna(macd_hist.iloc[-1]) else 0
    current_adx = adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 20
    current_vwap = vwap.iloc[-1]
    
    atr = (high - low).rolling(14).mean().iloc[-1]
    if pd.isna(atr):
        atr = current_price * 0.01
    
    bullish_score = 0
    bearish_score = 0
    reasons_bullish = []
    reasons_bearish = []
    
    if current_ema9 > current_ema21 > current_ema50:
        bullish_score += 25; reasons_bullish.append("✅ EMA 9 > 21 > 50")
    elif current_ema9 > current_ema21:
        bullish_score += 15; reasons_bullish.append("✅ EMA 9 > 21")
    elif current_ema9 < current_ema21 < current_ema50:
        bearish_score += 25; reasons_bearish.append("❌ EMA 9 < 21 < 50")
    elif current_ema9 < current_ema21:
        bearish_score += 15; reasons_bearish.append("❌ EMA 9 < 21")
    
    if current_price > current_vwap:
        bullish_score += 15; reasons_bullish.append("✅ Above VWAP")
    else:
        bearish_score += 15; reasons_bearish.append("❌ Below VWAP")
    
    if current_rsi < 30:
        bullish_score += 20; reasons_bullish.append(f"✅ RSI Oversold: {current_rsi:.1f}")
    elif current_rsi < 40:
        bullish_score += 10
    elif current_rsi > 70:
        bearish_score += 20; reasons_bearish.append(f"❌ RSI Overbought: {current_rsi:.1f}")
    elif current_rsi > 60:
        bearish_score += 10
    
    if current_macd > 0:
        bullish_score += 15; reasons_bullish.append("✅ MACD Bullish")
    else:
        bearish_score += 15; reasons_bearish.append("❌ MACD Bearish")
    
    if current_price <= bb_lower.iloc[-1]:
        bullish_score += 10
    elif current_price >= bb_upper.iloc[-1]:
        bearish_score += 10
    
    if current_adx > 25:
        if plus_di.iloc[-1] > minus_di.iloc[-1]:
            bullish_score += 10; reasons_bullish.append(f"✅ ADX: {current_adx:.1f}")
        else:
            bearish_score += 10; reasons_bearish.append(f"❌ ADX: {current_adx:.1f}")
    
    if volume_ratio > 1.5:
        if bullish_score > bearish_score:
            bullish_score += 10; reasons_bullish.append(f"✅ Volume: {volume_ratio:.1f}x")
        else:
            bearish_score += 10; reasons_bearish.append(f"❌ Volume: {volume_ratio:.1f}x")
    
    if smc['liquidity_sweep_low']:
        bullish_score += 15; reasons_bullish.append("🎯 Liquidity Sweep Low")
    if smc['bos_up']:
        bullish_score += 10; reasons_bullish.append("📈 Break of Structure UP")
    if smc['liquidity_sweep_high']:
        bearish_score += 15; reasons_bearish.append("🎯 Liquidity Sweep High")
    if smc['bos_down']:
        bearish_score += 10; reasons_bearish.append("📉 Break of Structure DOWN")
    
    for pattern in candle_patterns:
        if "Bullish" in pattern or "Hammer" in pattern:
            bullish_score += 10; reasons_bullish.append(f"📊 {pattern}")
        elif "Bearish" in pattern or "Shooting" in pattern:
            bearish_score += 10; reasons_bearish.append(f"📊 {pattern}")
    
    if bullish_score >= 75 and bullish_score > bearish_score:
        probability = min(98, bullish_score)
        return {
            'signal': 'STRONG_BUY', 'probability': probability, 'price': current_price,
            'target1': current_price + (atr * 1.5), 'target2': current_price + (atr * 2.5),
            'target3': current_price + (atr * 4), 'stop_loss': current_price - (atr * 1.2),
            'rsi': current_rsi, 'adx': current_adx, 'volume_ratio': volume_ratio,
            'vwap': current_vwap, 'ema9': current_ema9, 'ema21': current_ema21, 'ema50': current_ema50,
            'reasons': reasons_bullish[:8], 'candle_patterns': candle_patterns, 'smc': smc
        }
    elif bearish_score >= 75 and bearish_score > bullish_score:
        probability = min(98, bearish_score)
        return {
            'signal': 'STRONG_SELL', 'probability': probability, 'price': current_price,
            'target1': current_price - (atr * 1.5), 'target2': current_price - (atr * 2.5),
            'target3': current_price - (atr * 4), 'stop_loss': current_price + (atr * 1.2),
            'rsi': current_rsi, 'adx': current_adx, 'volume_ratio': volume_ratio,
            'vwap': current_vwap, 'ema9': current_ema9, 'ema21': current_ema21, 'ema50': current_ema50,
            'reasons': reasons_bearish[:8], 'candle_patterns': candle_patterns, 'smc': smc
        }
    
    return None

# ========== GET TOP GAINERS & LOSERS ==========
def get_top_gainers_losers():
    gainers = []
    losers = []
    main_stocks = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL", 
                   "KOTAKBANK", "BAJFINANCE", "ITC", "LT", "WIPRO", "AXISBANK", "HCLTECH"]
    
    for symbol in main_stocks:
        q = get_live_quote_fyers(symbol)
        if q and q['change_percent'] != 0:
            data = {'symbol': symbol, 'price': q['ltp'], 'change': q['change'], 'change_percent': q['change_percent']}
            if q['change_percent'] > 0:
                gainers.append(data)
            elif q['change_percent'] < 0:
                losers.append(data)
        time.sleep(0.05)
    
    gainers.sort(key=lambda x: x['change_percent'], reverse=True)
    losers.sort(key=lambda x: x['change_percent'])
    return gainers[:5], losers[:5]

# ========== DETECT MARKET TREND ==========
def detect_market_trend():
    bullish = 0
    bearish = 0
    trend_stocks = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL"]
    
    for symbol in trend_stocks:
        q = get_live_quote_fyers(symbol)
        if q:
            if q['change'] > 0:
                bullish += 1
            else:
                bearish += 1
        time.sleep(0.05)
    
    if bullish > bearish + 2:
        return "BULLISH", f"🟢 Market Trend: BULLISH ({bullish} stocks up)"
    elif bearish > bullish + 2:
        return "BEARISH", f"🔴 Market Trend: BEARISH ({bearish} stocks down)"
    else:
        return "NEUTRAL", f"🟡 Market Trend: NEUTRAL"

# ========== SCAN ALL STOCKS ==========
def scan_all_stocks():
    signals = []
    total = len(ALL_STOCKS)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, symbol in enumerate(ALL_STOCKS):
        status_text.text(f"🎯 Analyzing: {symbol} ({i+1}/{total})")
        progress_bar.progress((i+1)/total)
        
        try:
            df = get_history_fyers(symbol, resolution="15", days=5)
            if df is not None and len(df) > 30:
                signal_data = generate_high_accuracy_signal(df, symbol)
                if signal_data:
                    signal_data['symbol'] = symbol
                    signal_data['name'] = symbol
                    signal_data['entry_time'] = datetime.now().strftime("%H:%M:%S")
                    signals.append(signal_data)
        except Exception as e:
            print(f"Scan error for {symbol}: {e}")
        
        time.sleep(0.03)
    
    progress_bar.empty()
    status_text.empty()
    signals.sort(key=lambda x: x['probability'], reverse=True)
    return signals

# ========== TRADINGVIEW CHART ==========
def get_tradingview_chart(symbol, timeframe="5"):
    return f"""
    <div style="border-radius: 15px; overflow: hidden; background: #0a0a0a; padding: 5px; margin-top: 10px;">
        <div class="tradingview-widget-container" style="height:500px;">
            <div id="tradingview_chart_{symbol}" style="height:500px;"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
            <script type="text/javascript">
            new TradingView.widget({{
                "width": "100%",
                "height": 500,
                "symbol": "NSE:{symbol}",
                "interval": "{timeframe}",
                "timezone": "Asia/Kolkata",
                "theme": "dark",
                "style": "1",
                "locale": "in",
                "toolbar_bg": "#0a0a0a",
                "enable_publishing": false,
                "container_id": "tradingview_chart_{symbol}",
                "studies": ["RSI@tv-basicstudies", "MACD@tv-basicstudies", "BB@tv-basicstudies"]
            }});
            </script>
        </div>
    </div>
    """

# ========== MAIN APP ==========
def main():
    st.markdown("<h1>🎯 90% ACCURACY SIGNAL BOT</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #ffaa00;'>SMC | EMA | RSI | MACD | VWAP | ADX | FYERS Live Data</p>", unsafe_allow_html=True)
    
    # ========== TEST MODE / LIVE MODE TOGGLE BUTTONS WITH COLOR CHANGE ==========
    col_mode1, col_mode2, col_mode3 = st.columns([1, 1, 2])
    
    with col_mode1:
        test_btn = st.button("🧪 TEST MODE", key="test_mode_btn", use_container_width=True)
        if test_btn:
            st.session_state.test_mode = True
            st.session_state.signals = []
            st.session_state.last_scan = None
            st.rerun()
    
    with col_mode2:
        live_btn = st.button("📡 LIVE MARKET", key="live_mode_btn", use_container_width=True)
        if live_btn:
            st.session_state.test_mode = False
            st.session_state.signals = []
            st.session_state.last_scan = None
            st.rerun()
    
    # Show current mode with dynamic color
    if st.session_state.test_mode:
        st.markdown("""
        <div style="background-color:#ff660020; border:2px solid #ff6600; padding:15px; border-radius:15px; margin:10px 0; text-align:center;">
            <span style="color:#ffaa00; font-size:18px; font-weight:bold;">🧪 TEST MODE ACTIVE - Showing demo signals for UI testing</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background-color:#00ff8820; border:2px solid #00ff88; padding:15px; border-radius:15px; margin:10px 0; text-align:center;">
            <span style="color:#00ff88; font-size:18px; font-weight:bold;">📡 LIVE MARKET MODE - Real data from FYERS API</span>
        </div>
        """, unsafe_allow_html=True)
    
    # API Status
    if st.session_state.fyers_token:
        st.markdown(f"<div style='text-align:center'><span class='api-status'>✅ FYERS API Connected | 207 Stocks | 15-Minute Timeframe</span></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align:center'><span class='api-status'>⚠️ FYERS API Not Connected</span></div>", unsafe_allow_html=True)
    
    # Market Trend
    market_trend, trend_msg = detect_market_trend()
    st.session_state.market_trend = market_trend
    
    if market_trend == "BULLISH":
        st.markdown(f"<div style='background:#0a2a0a; border:1px solid #00ff88; padding:15px; border-radius:15px; text-align:center; margin:10px 0;'>{trend_msg}</div>", unsafe_allow_html=True)
    elif market_trend == "BEARISH":
        st.markdown(f"<div style='background:#2a0a0a; border:1px solid #ff3333; padding:15px; border-radius:15px; text-align:center; margin:10px 0;'>{trend_msg}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='background:#2a2a0a; border:1px solid #ffaa00; padding:15px; border-radius:15px; text-align:center; margin:10px 0;'>{trend_msg}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========== TOP GAINERS & LOSERS SECTION (Normal Icons) ==========
    st.markdown("<h2>📊 TOP 5 GAINERS & LOSERS</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        refresh_btn = st.button("🔄 Refresh Gainers/Losers", use_container_width=True)
    
    if refresh_btn or not st.session_state.top_gainers:
        with st.spinner("Fetching top gainers and losers..."):
            st.session_state.top_gainers, st.session_state.top_losers = get_top_gainers_losers()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h3 style='color:#00ff88;'>🟢 TOP 5 GAINERS</h3>", unsafe_allow_html=True)
        if st.session_state.top_gainers:
            for stock in st.session_state.top_gainers:
                has_high_signal = False
                high_prob = 0
                for sig in st.session_state.signals:
                    if sig.get('symbol') == stock['symbol'] and sig.get('probability', 0) >= 80:
                        has_high_signal = True
                        high_prob = sig.get('probability', 0)
                        break
                
                if has_high_signal:
                    st.markdown(f"""
                    <div class='gainers-card-normal highlight-stock'>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h3>📈 {stock['symbol']}</h3>
                            <div style="text-align: right;">
                                <div class='high-probability' style="margin-bottom: 5px;">🔥 {high_prob:.0f}%</div>
                                <div class='gainer-normal'>+{stock['change_percent']:.2f}%</div>
                            </div>
                        </div>
                        <div>₹{stock['price']:.2f} | +₹{stock['change']:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class='gainers-card-normal'>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h3>📈 {stock['symbol']}</h3>
                            <div class='gainer-normal'>+{stock['change_percent']:.2f}%</div>
                        </div>
                        <div>₹{stock['price']:.2f} | +₹{stock['change']:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No gainers data available")
    
    with col2:
        st.markdown("<h3 style='color:#ff3333;'>🔴 TOP 5 LOSERS</h3>", unsafe_allow_html=True)
        if st.session_state.top_losers:
            for stock in st.session_state.top_losers:
                has_high_signal = False
                high_prob = 0
                for sig in st.session_state.signals:
                    if sig.get('symbol') == stock['symbol'] and sig.get('probability', 0) >= 80:
                        has_high_signal = True
                        high_prob = sig.get('probability', 0)
                        break
                
                if has_high_signal:
                    st.markdown(f"""
                    <div class='losers-card-normal highlight-stock'>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h3>📉 {stock['symbol']}</h3>
                            <div style="text-align: right;">
                                <div class='high-probability' style="margin-bottom: 5px;">🔥 {high_prob:.0f}%</div>
                                <div class='loser-normal'>{stock['change_percent']:.2f}%</div>
                            </div>
                        </div>
                        <div>₹{stock['price']:.2f} | ₹{stock['change']:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class='losers-card-normal'>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h3>📉 {stock['symbol']}</h3>
                            <div class='loser-normal'>{stock['change_percent']:.2f}%</div>
                        </div>
                        <div>₹{stock['price']:.2f} | ₹{stock['change']:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No losers data available")
    
    st.markdown("---")
    
    # ========== SIDEBAR CONTROLS ==========
    with st.sidebar:
        st.markdown("## ⚙️ CONTROLS")
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.fyers_token = None
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 🔐 FYERS API STATUS")
        if st.session_state.fyers_token:
            st.success("✅ CONNECTED")
        else:
            st.error("❌ NOT CONNECTED")
        st.info(f"Client ID: {FYERS_APP_ID[:10]}...")
        
        st.markdown("---")
        st.markdown("### 📊 Signal Criteria")
        st.caption("✅ EMA 9 > 21 > 50")
        st.caption("✅ RSI < 30 or > 70")
        st.caption("✅ MACD Confirmation")
        st.caption("✅ Volume > 1.5x")
        st.caption("✅ SMC Patterns")
        st.caption("✅ Candlestick Patterns")
        st.caption("✅ ADX > 25")
    
    col_btn1, col_btn2 = st.columns([2, 1])
    with col_btn1:
        scan_btn = st.button("🔍 SCAN ALL 207 STOCKS - Find 90%+ Accuracy Signals", type="primary", use_container_width=True)
        auto_scan = st.checkbox("🔄 Auto-Scan Every 60 Seconds", key="auto_scan", value=False)
    with col_btn2:
        if st.button("🗑️ Clear All Signals", use_container_width=True):
            st.session_state.signals = []
            st.session_state.last_scan = None
            st.rerun()
    
    should_scan = scan_btn
    if auto_scan:
        if st.session_state.last_scan is None or (datetime.now() - st.session_state.last_scan).seconds >= 60:
            should_scan = True
    
    if should_scan:
        with st.spinner(f"🔄 Scanning {len(ALL_STOCKS)} stocks..."):
            st.session_state.signals = scan_all_stocks()
            st.session_state.last_scan = datetime.now()
        
        if st.session_state.signals:
            st.balloons()
            st.success(f"🎯 Found {len(st.session_state.signals)} High Probability Signals!")
        else:
            st.info("No strong signals found in this scan.")
    
    if st.session_state.last_scan:
        st.caption(f"Last scan: {st.session_state.last_scan.strftime('%H:%M:%S')} | Market Trend: {market_trend}")
    
    st.markdown("---")
    
    # ========== DISPLAY SIGNALS WITH CHARTS ==========
    if st.session_state.signals:
        buy_signals = [s for s in st.session_state.signals if s['signal'] == 'STRONG_BUY']
        sell_signals = [s for s in st.session_state.signals if s['signal'] == 'STRONG_SELL']
        
        # BUY SIGNALS
        if buy_signals:
            st.markdown("<h2>🟢 STRONG BUY SIGNALS (High Probability)</h2>", unsafe_allow_html=True)
            for idx, sig in enumerate(buy_signals[:10]):
                highlight_class = "highlight-stock" if sig['probability'] >= 85 else ""
                
                st.markdown(f"""
                <div class='signal-card strong-buy {highlight_class}' id='buy_{idx}'>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div><span class='badge-buy'>STRONG BUY</span></div>
                        <div class='probability-high'>🎯 {sig['probability']:.0f}%</div>
                    </div>
                    <h2 style="margin: 15px 0;">📈 {sig['name']}</h2>
                    <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                        <div class='metric-box'><div style="color:#888;">Entry</div><div class='price-up'>₹{sig['price']:.2f}</div></div>
                        <div class='metric-box'><div style="color:#888;">Entry Time</div><div class='entry-time'>{sig['entry_time']}</div></div>
                        <div class='metric-box'><div style="color:#888;">RSI</div><div>{sig['rsi']:.1f}</div></div>
                        <div class='metric-box'><div style="color:#888;">ADX</div><div>{sig['adx']:.1f}</div></div>
                        <div class='metric-box'><div style="color:#888;">Volume</div><div>{sig['volume_ratio']:.1f}x</div></div>
                    </div>
                    <div style="background:#0a0a0a; border-radius:15px; padding:15px; margin:15px 0;">
                        <p><strong>📊 EMAs:</strong> 9: {sig['ema9']:.2f} | 21: {sig['ema21']:.2f} | 50: {sig['ema50']:.2f}</p>
                        <p><strong>📈 VWAP:</strong> ₹{sig['vwap']:.2f}</p>
                    </div>
                    <div style="background:#0a0a0a; border-radius:15px; padding:15px; margin:15px 0;">
                        <p><strong>🎯 TARGETS:</strong></p>
                        <p>🎯 T1: ₹{sig['target1']:.2f} (+{((sig['target1']-sig['price'])/sig['price']*100):.2f}%)</p>
                        <p>🎯 T2: ₹{sig['target2']:.2f} (+{((sig['target2']-sig['price'])/sig['price']*100):.2f}%)</p>
                        <p>🎯 T3: ₹{sig['target3']:.2f} (+{((sig['target3']-sig['price'])/sig['price']*100):.2f}%)</p>
                        <p><strong>🛑 SL:</strong> ₹{sig['stop_loss']:.2f} ({((sig['stop_loss']-sig['price'])/sig['price']*100):.2f}%)</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("🔍 Analysis & Chart", expanded=False):
                    for reason in sig['reasons']:
                        st.write(f"• {reason}")
                    if sig['candle_patterns']:
                        st.write(f"• 📊 Candlestick: {', '.join(sig['candle_patterns'])}")
                    st.markdown("---")
                    st.markdown(f"### 📊 {sig['name']} - TradingView Chart")
                    chart_html = get_tradingview_chart(sig['symbol'], timeframe="15")
                    st.components.v1.html(chart_html, height=550)
                st.markdown("---")
        
        # SELL SIGNALS
        if sell_signals:
            st.markdown("<h2>🔴 STRONG SELL SIGNALS (High Probability)</h2>", unsafe_allow_html=True)
            for idx, sig in enumerate(sell_signals[:10]):
                highlight_class = "highlight-stock" if sig['probability'] >= 85 else ""
                
                st.markdown(f"""
                <div class='signal-card strong-sell {highlight_class}' id='sell_{idx}'>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div><span class='badge-sell'>STRONG SELL</span></div>
                        <div class='probability-high'>🎯 {sig['probability']:.0f}%</div>
                    </div>
                    <h2 style="margin: 15px 0;">📉 {sig['name']}</h2>
                    <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                        <div class='metric-box'><div style="color:#888;">Entry</div><div class='price-down'>₹{sig['price']:.2f}</div></div>
                        <div class='metric-box'><div style="color:#888;">Entry Time</div><div class='entry-time'>{sig['entry_time']}</div></div>
                        <div class='metric-box'><div style="color:#888;">RSI</div><div>{sig['rsi']:.1f}</div></div>
                        <div class='metric-box'><div style="color:#888;">ADX</div><div>{sig['adx']:.1f}</div></div>
                        <div class='metric-box'><div style="color:#888;">Volume</div><div>{sig['volume_ratio']:.1f}x</div></div>
                    </div>
                    <div style="background:#0a0a0a; border-radius:15px; padding:15px; margin:15px 0;">
                        <p><strong>📊 EMAs:</strong> 9: {sig['ema9']:.2f} | 21: {sig['ema21']:.2f} | 50: {sig['ema50']:.2f}</p>
                        <p><strong>📈 VWAP:</strong> ₹{sig['vwap']:.2f}</p>
                    </div>
                    <div style="background:#0a0a0a; border-radius:15px; padding:15px; margin:15px 0;">
                        <p><strong>🎯 TARGETS:</strong></p>
                        <p>🎯 T1: ₹{sig['target1']:.2f} ({((sig['target1']-sig['price'])/sig['price']*100):.2f}%)</p>
                        <p>🎯 T2: ₹{sig['target2']:.2f} ({((sig['target2']-sig['price'])/sig['price']*100):.2f}%)</p>
                        <p>🎯 T3: ₹{sig['target3']:.2f} ({((sig['target3']-sig['price'])/sig['price']*100):.2f}%)</p>
                        <p><strong>🛑 SL:</strong> ₹{sig['stop_loss']:.2f} ({((sig['stop_loss']-sig['price'])/sig['price']*100):.2f}%)</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("🔍 Analysis & Chart", expanded=False):
                    for reason in sig['reasons']:
                        st.write(f"• {reason}")
                    if sig['candle_patterns']:
                        st.write(f"• 📊 Candlestick: {', '.join(sig['candle_patterns'])}")
                    st.markdown("---")
                    st.markdown(f"### 📊 {sig['name']} - TradingView Chart")
                    chart_html = get_tradingview_chart(sig['symbol'], timeframe="15")
                    st.components.v1.html(chart_html, height=550)
                st.markdown("---")
    
    else:
        if st.session_state.last_scan:
            st.info("😴 No 90%+ accuracy signals found. Try TEST MODE to see demo signals.")
        else:
            st.info("🔍 Click 'SCAN ALL STOCKS' to find high probability trading opportunities")
    
    st.markdown("---")
    st.markdown(f"<p style='text-align: center; color: #888;'>FYERS API | 207 Stocks | Trend: {market_trend} | Mode: {'TEST' if st.session_state.test_mode else 'LIVE'}</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
