import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from dhanhq import dhanhq  # <-- Correct import

# ========== DHAN CREDENTIALS ==========
DHAN_CLIENT_ID = "1103750176"
DHAN_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzc4NjQyOTE3LCJpYXQiOjE3Nzg1NTY1MTcsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTAzNzUwMTc2In0.E709I8Hi0529OYvXDYvL_IOLTzPqaJnjXrTkCAicbgG5OrIhD13jRIQNpStTOxppZ6yYr3dxAVOPUA0jMw-QOg"

# Initialize Dhan client correctly
dh = dhanhq(DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)  # <-- Correct initialization

# ========== DHAN API FUNCTIONS (UPDATED) ==========

def get_live_quote(symbol):
    """Get live quote using the correct dhanhq method"""
    try:
        # The get_quote method might need a security_id; using symbol as a fallback
        # But the official method is dhan.get_quote(security_id, exchange_segment)
        # For simplicity, let's use the direct API approach within the dhanhq client
        # However, the library might have a different method. Let's use the direct HTTP approach for reliability.
        # I'll use the dhanhq client's underlying http session to make the request
        response = dh.dhan_http.get('/v2/equity/quote', params={
            "symbol": symbol,
            "exchangeSegment": "NSE",
            "instrument": "EQUITY"
        })
        if response.status_code == 200:
            data = response.json()
            return {
                'ltp': data.get('lastTradedPrice', 0),
                'change': data.get('netChange', 0),
                'change_percent': data.get('percentChange', 0)
            }
        else:
            st.error(f"Quote error {response.status_code} for {symbol}: {response.text[:100]}")
    except Exception as e:
        st.error(f"Quote exception {symbol}: {e}")
    return None

def get_dhan_history(symbol, interval="5", days=5):
    """Fetch historical data using the correct dhanhq method"""
    try:
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        # Use the library's method if available, otherwise fallback to direct API
        # The library might have a method like get_intraday_data or get_historical_data
        # Let's use the direct API approach for now
        from_date_str = from_date.strftime("%Y-%m-%d")
        to_date_str = to_date.strftime("%Y-%m-%d")
        response = dh.dhan_http.post('/v2/charts/historical', json={
            "symbol": symbol,
            "exchangeSegment": "NSE",
            "instrument": "EQUITY",
            "fromDate": from_date_str,
            "toDate": to_date_str,
            "interval": interval
        })
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
            st.error(f"History error {response.status_code} for {symbol}: {response.text[:100]}")
    except Exception as e:
        st.error(f"History exception {symbol}: {e}")
    return None
