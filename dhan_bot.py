import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from dhanhq import dhanhq

# ==============================
# DHAN API DETAILS
# ==============================

DHAN_CLIENT_ID = "YOUR_CLIENT_ID"
DHAN_ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"

# ==============================
# DHAN CONNECTION
# ==============================

dhan = dhanhq(DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)

# ==============================
# PAGE CONFIG
# ==============================

st.set_page_config(
    page_title="🔥 Dhan Signal Bot",
    layout="wide",
    page_icon="📈"
)

# ==============================
# CSS
# ==============================

st.markdown("""
<style>
.stApp{
    background:#050505;
    color:white;
}
.buy{
    background:#071a0d;
    border-left:6px solid #00ff88;
    padding:15px;
    border-radius:10px;
    margin-bottom:15px;
}
.sell{
    background:#220909;
    border-left:6px solid #ff4444;
    padding:15px;
    border-radius:10px;
    margin-bottom:15px;
}
.metric{
    background:#111;
    padding:10px;
    border-radius:10px;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# STOCK IDS
# ==============================

STOCK_IDS = {
    "RELIANCE": "2885",
    "TCS": "11536",
    "HDFCBANK": "1333",
    "INFY": "1594",
    "ICICIBANK": "4963",
    "SBIN": "3045",
    "ITC": "1660",
    "LT": "11483",
    "AXISBANK": "5900",
    "WIPRO": "3787",
    "BHARTIARTL": "10604",
    "KOTAKBANK": "1922",
    "BAJFINANCE": "317",
    "HCLTECH": "7229",
    "TATASTEEL": "3499",
    "TATAMOTORS": "3456",
    "MARUTI": "10999",
    "ASIANPAINT": "236",
    "SUNPHARMA": "3351",
    "POWERGRID": "14977"
}

ALL_STOCKS = list(STOCK_IDS.keys())

# ==============================
# EMA
# ==============================

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

# ==============================
# RSI
# ==============================

def rsi(series, period=14):

    delta = series.diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))

# ==============================
# MACD
# ==============================

def macd(series):

    exp1 = series.ewm(span=12, adjust=False).mean()
    exp2 = series.ewm(span=26, adjust=False).mean()

    macd_line = exp1 - exp2
    signal = macd_line.ewm(span=9, adjust=False).mean()

    return macd_line - signal

# ==============================
# GET DATA
# ==============================

def get_data(symbol):

    try:

        security_id = STOCK_IDS[symbol]

        from_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")

        data = dhan.intraday_minute_data(
            security_id=security_id,
            exchange_segment="NSE_EQ",
            instrument_type="EQUITY",
            interval="5",
            from_date=from_date,
            to_date=to_date
        )

        if not data:
            return None

        candles = data["data"]

        df = pd.DataFrame({
            "Open": candles["open"],
            "High": candles["high"],
            "Low": candles["low"],
            "Close": candles["close"],
            "Volume": candles["volume"]
        })

        return df

    except Exception as e:

        st.error(f"{symbol} Error : {e}")

        return None

# ==============================
# SIGNAL LOGIC
# ==============================

def generate_signal(df):

    if df is None:
        return None

    if len(df) < 50:
        return None

    close = df["Close"]

    ema9 = ema(close, 9)
    ema21 = ema(close, 21)
    ema50 = ema(close, 50)

    r = rsi(close)

    m = macd(close)

    latest_close = close.iloc[-1]

    bullish = 0
    bearish = 0

    # EMA

    if ema9.iloc[-1] > ema21.iloc[-1] > ema50.iloc[-1]:
        bullish += 30

    if ema9.iloc[-1] < ema21.iloc[-1] < ema50.iloc[-1]:
        bearish += 30

    # RSI

    if r.iloc[-1] < 35:
        bullish += 20

    if r.iloc[-1] > 65:
        bearish += 20

    # MACD

    if m.iloc[-1] > 0:
        bullish += 20

    if m.iloc[-1] < 0:
        bearish += 20

    # Volume

    avg_vol = df["Volume"].rolling(20).mean().iloc[-1]

    if avg_vol > 0:

        vol_ratio = df["Volume"].iloc[-1] / avg_vol

        if vol_ratio > 1.5:

            if bullish > bearish:
                bullish += 15
            else:
                bearish += 15

    # FINAL

    if bullish >= 60:

        return {
            "signal": "BUY",
            "probability": bullish,
            "price": latest_close,
            "rsi": r.iloc[-1]
        }

    if bearish >= 60:

        return {
            "signal": "SELL",
            "probability": bearish,
            "price": latest_close,
            "rsi": r.iloc[-1]
        }

    return None

# ==============================
# TRADINGVIEW CHART
# ==============================

def tradingview_chart(symbol):

    return f"""
    <div class="tradingview-widget-container">
      <div id="tradingview_chart"></div>

      <script type="text/javascript"
      src="https://s3.tradingview.com/tv.js">
      </script>

      <script type="text/javascript">

      new TradingView.widget(
      {{
      "width": "100%",
      "height": 500,
      "symbol": "NSE:{symbol}",
      "interval": "5",
      "timezone": "Asia/Kolkata",
      "theme": "dark",
      "style": "1",
      "locale": "in",
      "toolbar_bg": "#111",
      "enable_publishing": false,
      "hide_side_toolbar": false,
      "allow_symbol_change": true,
      "container_id": "tradingview_chart"
    }}
      );

      </script>
    </div>
    """

# ==============================
# TITLE
# ==============================

st.title("🔥 DHAN AI SIGNAL BOT")
st.caption("📈 5-Minute Auto Scanner")

# ==============================
# BUTTON
# ==============================

scan = st.button(
    "🔍 SCAN ALL STOCKS",
    use_container_width=True
)

# ==============================
# SCAN
# ==============================

if scan:

    progress = st.progress(0)

    signals = []

    for i, stock in enumerate(ALL_STOCKS):

        progress.progress((i + 1) / len(ALL_STOCKS))

        df = get_data(stock)

        signal = generate_signal(df)

        if signal:

            signal["symbol"] = stock

            signals.append(signal)

        time.sleep(0.2)

    # SORT

    signals = sorted(
        signals,
        key=lambda x: x["probability"],
        reverse=True
    )

    # DISPLAY

    if signals:

        st.success(f"✅ {len(signals)} SIGNALS FOUND")

        for sig in signals:

            if sig["signal"] == "BUY":

                st.markdown(f"""
                <div class="buy">
                <h2>🟢 BUY : {sig['symbol']}</h2>
                <h3>🎯 Accuracy : {sig['probability']}%</h3>
                <p>💰 Price : ₹{sig['price']:.2f}</p>
                <p>📊 RSI : {sig['rsi']:.2f}</p>
                </div>
                """, unsafe_allow_html=True)

            else:

                st.markdown(f"""
                <div class="sell">
                <h2>🔴 SELL : {sig['symbol']}</h2>
                <h3>🎯 Accuracy : {sig['probability']}%</h3>
                <p>💰 Price : ₹{sig['price']:.2f}</p>
                <p>📊 RSI : {sig['rsi']:.2f}</p>
                </div>
                """, unsafe_allow_html=True)

            st.components.v1.html(
                tradingview_chart(sig["symbol"]),
                height=520
            )

    else:

        st.warning("❌ No Signals Found")

# ==============================
# FOOTER
# ==============================

st.markdown("---")

st.caption("🚀 Powered By Dhan API + Streamlit")
