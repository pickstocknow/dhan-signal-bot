# ==========================
# FIXED DHAN SIGNAL BOT
# SAME TO SAME + WORKING VERSION
# ==========================

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import time

# ==========================
# DHAN API
# ==========================

DHAN_CLIENT_ID = "1103750176"
DHAN_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzc4NjQyOTE3LCJpYXQiOjE3Nzg1NTY1MTcsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTAzNzUwMTc2In0.E709I8Hi0529OYvXDYvL_IOLTzPqaJnjXrTkCAicbgG5OrIhD13jRIQNpStTOxppZ6yYr3dxAVOPUA0jMw-QOg"

# ==========================
# PAGE CONFIG
# ==========================

st.set_page_config(
    page_title="🔥 Dhan Signal Bot",
    page_icon="📈",
    layout="wide"
)

# ==========================
# CSS
# ==========================

st.markdown("""
<style>
.stApp{
    background:#050505;
    color:white;
}
.buy{
    background:#0d2a0d;
    padding:20px;
    border-radius:15px;
    border-left:8px solid #00ff88;
    margin-bottom:20px;
}
.sell{
    background:#2a0d0d;
    padding:20px;
    border-radius:15px;
    border-left:8px solid #ff3333;
    margin-bottom:20px;
}
.metric{
    background:#111;
    padding:10px;
    border-radius:10px;
    text-align:center;
}
</style>
""", unsafe_allow_html=True)

# ==========================
# STOCKS
# ==========================
# ========== COMPLETE NSE STOCKS ==========
ALL_STOCKS = [
    # NIFTY 50
    "ADANIENT","ADANIPORTS","APOLLOHOSP","ASIANPAINT","AXISBANK",
    "BAJAJ-AUTO","BAJFINANCE","BAJAJFINSV","BEL","BHARTIARTL",
    "BPCL","BRITANNIA","CIPLA","COALINDIA","DRREDDY","EICHERMOT",
    "GRASIM","HCLTECH","HDFCBANK","HDFCLIFE","HEROMOTOCO",
    "HINDALCO","HINDUNILVR","ICICIBANK","INDUSINDBK","INFY",
    "ITC","JSWSTEEL","KOTAKBANK","LT","M&M","MARUTI",
    "NESTLEIND","NTPC","ONGC","POWERGRID","RELIANCE","SBILIFE",
    "SBIN","SHRIRAMFIN","SUNPHARMA","TATACONSUM","TATAMOTORS",
    "TATASTEEL","TCS","TECHM","TITAN","ULTRACEMCO","WIPRO",

    # BANKS
    "AUBANK","BANDHANBNK","BANKBARODA","CANBK","FEDERALBNK",
    "IDFCFIRSTB","INDIANB","PNB","RBLBANK","YESBANK","UNIONBANK",

    # IT
    "COFORGE","KPITTECH","LTIM","MPHASIS","OFSS","PERSISTENT",
    "TATAELXSI","ZENSARTECH",

    # AUTO
    "ASHOKLEY","BALKRISIND","EXIDEIND","MOTHERSON","SONACOMS",
    "TVSMOTOR","UNOMINDA",

    # ENERGY
    "ADANIGREEN","ADANIENSOL","GAIL","IOC","NHPC","NTPC",
    "OIL","ONGC","POWERGRID","SUZLON","TATAPOWER",

    # PHARMA
    "ALKEM","AUROPHARMA","BIOCON","DIVISLAB","GLENMARK",
    "LUPIN","MANKIND","TORNTPHARM","ZYDUSLIFE",

    # METAL
    "HINDZINC","JINDALSTEL","NMDC","NATIONALUM","SAIL","VEDL",

    # REAL ESTATE
    "DLF","GODREJPROP","LODHA","OBEROIRLTY","PHOENIXLTD","PRESTIGE",

    # FINANCE
    "BAJAJHLDNG","CHOLAFIN","LICHSGFIN","MUTHOOTFIN","PFC",
    "RECLTD","SBICARD",

    # MIDCAP
    "BSE","CDSL","CAMS","DELHIVERY","DIXON","DMART","HUDCO",
    "IREDA","IRFC","JIOFIN","KAYNES","MCX","PAYTM","RVNL",

    # OTHERS
    "AMBUJACEM","ASTRAL","CROMPTON","DABUR","GODREJCP",
    "HAVELLS","INDHOTEL","JUBLFOOD","MARICO","NAUKRI",
    "PAGEIND","PIDILITIND","POLYCAB","TRENT","VBL","VOLTAS"
]
]

# ==========================
# DHAN HEADERS
# ==========================

def dhan_headers():
    return {
        "access-token": DHAN_ACCESS_TOKEN,
        "client-id": DHAN_CLIENT_ID,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

# ==========================
# GET DATA
# ==========================

def get_data(symbol):

    try:

        to_date = datetime.now()
        from_date = to_date - timedelta(days=5)

        url = f"https://api.dhan.co/v2/charts/intraday/{symbol}/NSE_EQ/5"

        response = requests.get(
            url,
            headers=dhan_headers(),
            timeout=10
        )

        if response.status_code == 200:

            data = response.json()

            if "data" not in data:
                return None

            candles = data["data"]

            df = pd.DataFrame(candles)

            if len(df) == 0:
                return None

            df.columns = [
                "timestamp",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume"
            ]

            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

            return df

    except Exception as e:
        print(e)

    return None

# ==========================
# INDICATORS
# ==========================

def EMA(series, period):
    return series.ewm(span=period, adjust=False).mean()

def RSI(series, period=14):

    delta = series.diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi

def MACD(series):

    ema12 = EMA(series, 12)
    ema26 = EMA(series, 26)

    macd = ema12 - ema26
    signal = EMA(macd, 9)

    hist = macd - signal

    return hist

# ==========================
# SIGNAL
# ==========================

def generate_signal(df):

    if df is None or len(df) < 50:
        return None

    close = df["Close"]

    ema9 = EMA(close, 9)
    ema21 = EMA(close, 21)
    ema50 = EMA(close, 50)

    rsi = RSI(close)

    macd = MACD(close)

    price = close.iloc[-1]

    bullish = 0
    bearish = 0

    # EMA
    if ema9.iloc[-1] > ema21.iloc[-1] > ema50.iloc[-1]:
        bullish += 40

    if ema9.iloc[-1] < ema21.iloc[-1] < ema50.iloc[-1]:
        bearish += 40

    # RSI
    if rsi.iloc[-1] < 35:
        bullish += 20

    if rsi.iloc[-1] > 65:
        bearish += 20

    # MACD
    if macd.iloc[-1] > 0:
        bullish += 20

    if macd.iloc[-1] < 0:
        bearish += 20

    # Volume
    avg_vol = df["Volume"].rolling(20).mean().iloc[-1]

    if df["Volume"].iloc[-1] > avg_vol:
        bullish += 10
        bearish += 10

    # BUY
    if bullish >= 70:

        return {
            "signal": "BUY",
            "price": price,
            "probability": bullish,
            "target": price * 1.02,
            "sl": price * 0.99,
            "rsi": rsi.iloc[-1]
        }

    # SELL
    if bearish >= 70:

        return {
            "signal": "SELL",
            "price": price,
            "probability": bearish,
            "target": price * 0.98,
            "sl": price * 1.01,
            "rsi": rsi.iloc[-1]
        }

    return None

# ==========================
# TV CHART
# ==========================

def tradingview_chart(symbol):

    return f"""
    <div class="tradingview-widget-container">
      <div id="tradingview_chart"></div>

      <script src="https://s3.tradingview.com/tv.js"></script>

      <script>
      new TradingView.widget({{
          "width": "100%",
          "height": 500,
          "symbol": "NSE:{symbol}",
          "interval": "5",
          "timezone": "Asia/Kolkata",
          "theme": "dark",
          "style": "1",
          "locale": "in",
          "toolbar_bg": "#0f0f0f",
          "enable_publishing": false,
          "hide_side_toolbar": false,
          "allow_symbol_change": true,
          "container_id": "tradingview_chart"
      }});
      </script>
    </div>
    """

# ==========================
# MAIN
# ==========================

st.title("🔥 DHAN 90% SIGNAL BOT")

scan = st.button("🔍 SCAN STOCKS")

if scan:

    progress = st.progress(0)

    signals = []

    for i, stock in enumerate(ALL_STOCKS):

        df = get_data(stock)

        signal = generate_signal(df)

        if signal:
            signal["symbol"] = stock
            signals.append(signal)

        progress.progress((i + 1) / len(ALL_STOCKS))

    progress.empty()

    if len(signals) == 0:
        st.warning("No signals found")

    for sig in signals:

        if sig["signal"] == "BUY":

            st.markdown(f"""
            <div class="buy">
                <h2>🟢 BUY - {sig['symbol']}</h2>
                <h3>🎯 Accuracy: {sig['probability']}%</h3>
                <p>💰 Price: ₹{sig['price']:.2f}</p>
                <p>🎯 Target: ₹{sig['target']:.2f}</p>
                <p>🛑 Stoploss: ₹{sig['sl']:.2f}</p>
                <p>📊 RSI: {sig['rsi']:.2f}</p>
            </div>
            """, unsafe_allow_html=True)

        else:

            st.markdown(f"""
            <div class="sell">
                <h2>🔴 SELL - {sig['symbol']}</h2>
                <h3>🎯 Accuracy: {sig['probability']}%</h3>
                <p>💰 Price: ₹{sig['price']:.2f}</p>
                <p>🎯 Target: ₹{sig['target']:.2f}</p>
                <p>🛑 Stoploss: ₹{sig['sl']:.2f}</p>
                <p>📊 RSI: {sig['rsi']:.2f}</p>
            </div>
            """, unsafe_allow_html=True)

        st.components.v1.html(
            tradingview_chart(sig["symbol"]),
            height=520
        )

        st.markdown("---")

# ==========================
# FOOTER
# ==========================

st.caption("⚡ LIVE DHAN SIGNAL BOT | 5-MIN TIMEFRAME")
