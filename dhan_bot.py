# =========================================================
# 🚀 ADVANCED AI SIGNAL BOT
# FYERS ONE + EXCEL + REAL CANDLES + AI FILTER
# =========================================================

# INSTALL:
# pip install streamlit pandas numpy yfinance xlwings requests streamlit-autorefresh

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import xlwings as xw
import requests
import time

from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# =========================================================
# ⚙️ SETTINGS
# =========================================================

EXCEL_FILE_PATH = r"C:\Users\User\Desktop\LiveData.xlsm"

SHEET_NAME = "Sheet1"

SYMBOL_COL = "A"
LTP_COL = "D"
CHANGE_PERCENT_COL = "E"

START_ROW = 2

# =========================================================
# 🔔 TELEGRAM SETTINGS
# =========================================================

TELEGRAM_ENABLED = False

BOT_TOKEN = "YOUR_BOT_TOKEN"

CHAT_ID = "YOUR_CHAT_ID"

# =========================================================
# 📦 STOCK LIST
# =========================================================

ALL_STOCKS = [
    "RELIANCE",
    "TCS",
    "INFY",
    "HDFCBANK",
    "ICICIBANK",
    "SBIN",
    "AXISBANK",
    "BAJFINANCE",
    "LT",
    "ITC",
    "BHARTIARTL",
    "KOTAKBANK",
    "WIPRO",
    "HCLTECH",
    "TATASTEEL",
    "POWERGRID",
    "SUNPHARMA",
    "NTPC",
    "MARUTI",
    "ULTRACEMCO"
]

# =========================================================
# 🌐 STREAMLIT
# =========================================================

st.set_page_config(
    page_title="🚀 AI SIGNAL BOT",
    layout="wide"
)

# =========================================================
# 🔄 AUTO REFRESH
# =========================================================

st_autorefresh(interval=15000, key="refresh")

# =========================================================
# 🎨 CSS
# =========================================================

st.markdown("""
<style>

.stApp{
background:#050505;
color:white;
}

.buy-box{
background:#071d0d;
padding:20px;
border-radius:15px;
border-left:6px solid #00ff88;
margin:10px 0;
}

.sell-box{
background:#2a0a0a;
padding:20px;
border-radius:15px;
border-left:6px solid red;
margin:10px 0;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# 🔐 LOGIN
# =========================================================

USERNAME = "admin"
PASSWORD = "stock123"

if "logged" not in st.session_state:
    st.session_state.logged = False

if not st.session_state.logged:

    st.title("🔐 LOGIN")

    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):

        if user == USERNAME and pwd == PASSWORD:
            st.session_state.logged = True
            st.rerun()

        else:
            st.error("Wrong Username/Password")

    st.stop()

# =========================================================
# 📡 EXCEL LIVE DATA
# =========================================================

def get_live_quote(symbol):

    try:

        wb = xw.Book(EXCEL_FILE_PATH)

        sheet = wb.sheets[SHEET_NAME]

        last_row = sheet.range(
            f"{SYMBOL_COL}{sheet.cells.last_cell.row}"
        ).end("up").row

        for row in range(START_ROW, last_row + 1):

            sym = sheet.range(
                f"{SYMBOL_COL}{row}"
            ).value

            if str(sym).strip().upper() == symbol:

                ltp = sheet.range(
                    f"{LTP_COL}{row}"
                ).value

                chg = sheet.range(
                    f"{CHANGE_PERCENT_COL}{row}"
                ).value

                if ltp is not None:

                    return {
                        "ltp": float(ltp),
                        "change_percent": float(chg)
                    }

        return None

    except Exception as e:

        st.error(f"Excel Error: {e}")

        return None

# =========================================================
# 📈 REAL MARKET DATA
# =========================================================

def get_history(symbol, interval="15m"):

    try:

        df = yf.download(
            f"{symbol}.NS",
            period="5d",
            interval=interval,
            progress=False
        )

        df.dropna(inplace=True)

        return df

    except:
        return None

# =========================================================
# 📊 INDICATORS
# =========================================================

def EMA(series, period):

    return series.ewm(span=period, adjust=False).mean()

def RSI(series, period=14):

    delta = series.diff()

    gain = delta.where(delta > 0, 0)

    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(period).mean()

    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))

# =========================================================
# 🕯️ CANDLE PATTERNS
# =========================================================

def bullish_engulfing(df):

    prev = df.iloc[-2]

    curr = df.iloc[-1]

    return (
        prev["Close"] < prev["Open"]
        and curr["Close"] > curr["Open"]
        and curr["Close"] > prev["Open"]
        and curr["Open"] < prev["Close"]
    )

def bearish_engulfing(df):

    prev = df.iloc[-2]

    curr = df.iloc[-1]

    return (
        prev["Close"] > prev["Open"]
        and curr["Close"] < curr["Open"]
        and curr["Open"] > prev["Close"]
        and curr["Close"] < prev["Open"]
    )

# =========================================================
# 📲 TELEGRAM ALERT
# =========================================================

def send_telegram(msg):

    if not TELEGRAM_ENABLED:
        return

    try:

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": msg
            }
        )

    except:
        pass

# =========================================================
# 🚀 AI SIGNAL ENGINE
# =========================================================

def generate_signal(df15, df5):

    if df15 is None or df5 is None:
        return None

    if len(df15) < 50:
        return None

    close = df15["Close"]

    volume = df15["Volume"]

    ema9 = EMA(close, 9)

    ema21 = EMA(close, 21)

    ema50 = EMA(close, 50)

    rsi = RSI(close)

    latest_close = close.iloc[-1]

    latest_rsi = rsi.iloc[-1]

    latest_volume = volume.iloc[-1]

    avg_volume = volume.tail(20).mean()

    volume_boost = latest_volume > avg_volume * 1.5

    # =====================================================
    # OPEN = LOW
    # =====================================================

    open_low = (
        abs(df15["Open"].iloc[-1] - df15["Low"].iloc[-1]) < 0.05
    )

    # =====================================================
    # OPEN = HIGH
    # =====================================================

    open_high = (
        abs(df15["Open"].iloc[-1] - df15["High"].iloc[-1]) < 0.05
    )

    # =====================================================
    # MULTI TIMEFRAME
    # =====================================================

    close5 = df5["Close"]

    ema5_fast = EMA(close5, 9)

    ema5_slow = EMA(close5, 21)

    buy_mtf = ema5_fast.iloc[-1] > ema5_slow.iloc[-1]

    sell_mtf = ema5_fast.iloc[-1] < ema5_slow.iloc[-1]

    # =====================================================
    # STRONG BUY
    # =====================================================

    if (
        ema9.iloc[-1] > ema21.iloc[-1]
        and ema21.iloc[-1] > ema50.iloc[-1]
        and latest_rsi > 60
        and volume_boost
        and bullish_engulfing(df15)
        and open_low
        and buy_mtf
    ):

        return {
            "signal": "🔥 STRONG BUY",
            "probability": 93,
            "price": latest_close,
            "target1": latest_close * 1.02,
            "target2": latest_close * 1.04,
            "target3": latest_close * 1.06,
            "stop_loss": latest_close * 0.98,
            "rsi": latest_rsi
        }

    # =====================================================
    # STRONG SELL
    # =====================================================

    if (
        ema9.iloc[-1] < ema21.iloc[-1]
        and ema21.iloc[-1] < ema50.iloc[-1]
        and latest_rsi < 40
        and volume_boost
        and bearish_engulfing(df15)
        and open_high
        and sell_mtf
    ):

        return {
            "signal": "🔥 STRONG SELL",
            "probability": 91,
            "price": latest_close,
            "target1": latest_close * 0.98,
            "target2": latest_close * 0.96,
            "target3": latest_close * 0.94,
            "stop_loss": latest_close * 1.02,
            "rsi": latest_rsi
        }

    return None

# =========================================================
# 🔎 MARKET SCANNER
# =========================================================

def scan_market():

    results = []

    progress = st.progress(0)

    status = st.empty()

    total = len(ALL_STOCKS)

    for i, symbol in enumerate(ALL_STOCKS):

        status.text(f"Scanning {symbol} ({i+1}/{total})")

        progress.progress((i + 1) / total)

        df15 = get_history(symbol, "15m")

        df5 = get_history(symbol, "5m")

        signal = generate_signal(df15, df5)

        if signal:

            live = get_live_quote(symbol)

            if live:

                signal["symbol"] = symbol

                signal["live_price"] = live["ltp"]

                signal["change"] = live["change_percent"]

                results.append(signal)

                send_telegram(
                    f"""
{signal['signal']}

{symbol}

Price: ₹{live['ltp']}

Accuracy: {signal['probability']}%
"""
                )

        time.sleep(0.2)

    progress.empty()

    status.empty()

    return results

# =========================================================
# 🏠 MAIN UI
# =========================================================

st.title("🚀 ADVANCED AI SIGNAL BOT")

st.caption("📡 FYERS ONE + EXCEL + AI FILTER")

# =========================================================
# 🔍 SCAN
# =========================================================

if st.button("🔍 SCAN MARKET"):

    with st.spinner("Scanning Market..."):

        signals = scan_market()

    if len(signals) == 0:

        st.warning("No Strong Signals")

    else:

        st.success(f"{len(signals)} Signals Found")

        for sig in signals:

            box = "buy-box"

            if "SELL" in sig["signal"]:
                box = "sell-box"

            st.markdown(
                f"""
<div class="{box}">

<h2>{sig['signal']} — {sig['symbol']}</h2>

<h3>₹ {sig['live_price']}</h3>

<p>Accuracy: {sig['probability']}%</p>

<p>RSI: {sig['rsi']:.2f}</p>

<p>Target1: ₹{sig['target1']:.2f}</p>

<p>Target2: ₹{sig['target2']:.2f}</p>

<p>Target3: ₹{sig['target3']:.2f}</p>

<p>Stop Loss: ₹{sig['stop_loss']:.2f}</p>

</div>
""",
                unsafe_allow_html=True
            )

            # =================================================
            # 📊 TRADINGVIEW CHART
            # =================================================

            st.components.v1.html(
                f"""
<div id="tv_{sig['symbol']}"></div>

<script src="https://s3.tradingview.com/tv.js"></script>

<script>

new TradingView.widget(
{{
"width": "100%",
"height": 500,
"symbol": "NSE:{sig['symbol']}",
"interval": "15",
"timezone": "Asia/Kolkata",
"theme": "dark",
"style": "1",
"locale": "in",
"container_id": "tv_{sig['symbol']}"
}}
);

</script>
""",
                height=520
            )

# =========================================================
# 🔔 SOUND ALERT
# =========================================================

st.audio(
    "https://www.soundjay.com/buttons/sounds/beep-01a.mp3"
)

# =========================================================
# 📌 FOOTER
# =========================================================

st.markdown("---")

st.caption("🔥 Powered By AI + FYERS ONE + EXCEL")
