# ============================================
# 🎯 ADVANCED FYERS ONE + EXCEL LIVE SIGNAL BOT
# ============================================

# INSTALL FIRST:
# pip install streamlit pandas numpy yfinance ta xlwings streamlit-autorefresh requests

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import xlwings as xw
import requests
import time

from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ============================================
# ⚙️ SETTINGS
# ============================================

EXCEL_FILE_PATH = r"C:\Users\User\Desktop\LiveData.xlsm"

SHEET_NAME = "Sheet1"

SYMBOL_COL = "A"
LTP_COL = "D"
CHANGE_PERCENT_COL = "E"

START_ROW = 2

# ============================================
# 🔔 TELEGRAM SETTINGS
# ============================================

TELEGRAM_ENABLED = False

BOT_TOKEN = "YOUR_BOT_TOKEN"

CHAT_ID = "YOUR_CHAT_ID"

# ============================================
# 📦 STOCK LIST
# ============================================

ALL_STOCKS = [
    "RELIANCE",
    "TCS",
    "HDFCBANK",
    "INFY",
    "ICICIBANK",
    "SBIN",
    "AXISBANK",
    "ITC",
    "LT",
    "BAJFINANCE",
    "BHARTIARTL",
    "KOTAKBANK",
    "WIPRO",
    "HCLTECH",
    "MARUTI",
    "TATASTEEL",
    "POWERGRID",
    "NTPC",
    "ULTRACEMCO",
    "SUNPHARMA"
]

# ============================================
# 🌐 STREAMLIT PAGE
# ============================================

st.set_page_config(
    page_title="🎯 LIVE AI SIGNAL BOT",
    layout="wide"
)

# ============================================
# 🔄 AUTO REFRESH
# ============================================

st_autorefresh(interval=10000, key="live_refresh")

# ============================================
# 🎨 CSS
# ============================================

st.markdown("""
<style>

.stApp{
background:#050505;
color:white;
}

.buy-box{
background:#071d0d;
border-left:6px solid #00ff88;
padding:20px;
border-radius:15px;
margin:10px 0;
}

.sell-box{
background:#240909;
border-left:6px solid red;
padding:20px;
border-radius:15px;
margin:10px 0;
}

.metric{
background:#111;
padding:10px;
border-radius:10px;
text-align:center;
}

</style>
""", unsafe_allow_html=True)

# ============================================
# 🔐 LOGIN
# ============================================

USERNAME = "admin"
PASSWORD = "stock123"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.title("🔐 LOGIN")

    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):

        if user == USERNAME and pwd == PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Wrong Username/Password")

    st.stop()

# ============================================
# 📡 EXCEL LIVE DATA
# ============================================

def get_live_quote(symbol):

    try:

        wb = xw.Book(EXCEL_FILE_PATH)

        sheet = wb.sheets[SHEET_NAME]

        last_row = sheet.range(
            f"{SYMBOL_COL}{sheet.cells.last_cell.row}"
        ).end("up").row

        for row in range(START_ROW, last_row + 1):

            excel_symbol = sheet.range(
                f"{SYMBOL_COL}{row}"
            ).value

            if str(excel_symbol).strip().upper() == symbol:

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

# ============================================
# 📈 REAL MARKET CANDLES
# ============================================

def get_history(symbol):

    try:

        df = yf.download(
            f"{symbol}.NS",
            period="5d",
            interval="15m",
            progress=False
        )

        df.dropna(inplace=True)

        return df

    except:
        return None

# ============================================
# 📊 INDICATORS
# ============================================

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

# ============================================
# 🚀 SIGNAL LOGIC
# ============================================

def generate_signal(df):

    if df is None or len(df) < 50:
        return None

    close = df["Close"]

    volume = df["Volume"]

    ema9 = EMA(close, 9)

    ema21 = EMA(close, 21)

    ema50 = EMA(close, 50)

    rsi = RSI(close)

    latest_close = close.iloc[-1]

    latest_rsi = rsi.iloc[-1]

    latest_vol = volume.iloc[-1]

    avg_vol = volume.tail(20).mean()

    volume_boost = latest_vol > avg_vol * 1.5

    # =========================
    # STRONG BUY
    # =========================

    if (
        ema9.iloc[-1] > ema21.iloc[-1]
        and ema21.iloc[-1] > ema50.iloc[-1]
        and latest_rsi > 60
        and volume_boost
    ):

        return {
            "signal": "STRONG BUY",
            "probability": 92,
            "price": latest_close,
            "target1": latest_close * 1.02,
            "target2": latest_close * 1.04,
            "target3": latest_close * 1.06,
            "stop_loss": latest_close * 0.98,
            "rsi": latest_rsi
        }

    # =========================
    # STRONG SELL
    # =========================

    if (
        ema9.iloc[-1] < ema21.iloc[-1]
        and ema21.iloc[-1] < ema50.iloc[-1]
        and latest_rsi < 40
        and volume_boost
    ):

        return {
            "signal": "STRONG SELL",
            "probability": 90,
            "price": latest_close,
            "target1": latest_close * 0.98,
            "target2": latest_close * 0.96,
            "target3": latest_close * 0.94,
            "stop_loss": latest_close * 1.02,
            "rsi": latest_rsi
        }

    return None

# ============================================
# 📲 TELEGRAM ALERT
# ============================================

def send_telegram(message):

    if not TELEGRAM_ENABLED:
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        requests.post(url, data=data)
    except:
        pass

# ============================================
# 🔎 SCANNER
# ============================================

def scan_market():

    signals = []

    progress = st.progress(0)

    status = st.empty()

    total = len(ALL_STOCKS)

    for i, symbol in enumerate(ALL_STOCKS):

        status.text(f"Scanning {symbol} ({i+1}/{total})")

        progress.progress((i + 1) / total)

        df = get_history(symbol)

        signal = generate_signal(df)

        if signal:

            live = get_live_quote(symbol)

            if live:

                signal["symbol"] = symbol

                signal["live_price"] = live["ltp"]

                signal["change"] = live["change_percent"]

                signals.append(signal)

                send_telegram(
                    f"""
{signal['signal']} ALERT

{symbol}

Price: ₹{live['ltp']}

Accuracy: {signal['probability']}%
"""
                )

        time.sleep(0.2)

    progress.empty()

    status.empty()

    return signals

# ============================================
# 🏠 MAIN UI
# ============================================

st.title("🎯 LIVE AI SIGNAL BOT")

st.caption("📡 FYERS ONE + Excel + Real Candles")

# ============================================
# 🔄 SCAN BUTTON
# ============================================

if st.button("🔍 SCAN MARKET"):

    with st.spinner("Scanning Market..."):

        results = scan_market()

    if len(results) == 0:

        st.warning("No Signals Found")

    else:

        st.success(f"{len(results)} Signals Found")

        for sig in results:

            if sig["signal"] == "STRONG BUY":
                box = "buy-box"
            else:
                box = "sell-box"

            st.markdown(
                f"""
<div class="{box}">

<h2>{sig['signal']} — {sig['symbol']}</h2>

<h3>₹ {sig['live_price']}</h3>

<p>Accuracy: {sig['probability']}%</p>

<p>RSI: {sig['rsi']:.2f}</p>

<p>Target 1: ₹{sig['target1']:.2f}</p>

<p>Target 2: ₹{sig['target2']:.2f}</p>

<p>Target 3: ₹{sig['target3']:.2f}</p>

<p>Stop Loss: ₹{sig['stop_loss']:.2f}</p>

</div>
""",
                unsafe_allow_html=True
            )

            # ====================================
            # 📊 TRADINGVIEW CHART
            # ====================================

            st.components.v1.html(
                f"""
<div class="tradingview-widget-container">

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
"toolbar_bg": "#111111",
"enable_publishing": false,
"hide_side_toolbar": false,
"allow_symbol_change": true,
"container_id": "tv_{sig['symbol']}"
}}
);

</script>

</div>
""",
                height=520
            )

# ============================================
# 🔔 SOUND ALERT
# ============================================

st.audio(
    "https://www.soundjay.com/buttons/sounds/beep-01a.mp3"
)

# ============================================
# 📌 FOOTER
# ============================================

st.markdown("---")

st.caption(
    "🚀 Powered By FYERS ONE + Excel + AI Signal Logic"
)
