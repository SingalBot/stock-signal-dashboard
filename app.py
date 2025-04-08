import streamlit as st
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
import requests
import time

# --- Telegram Bot Setup ---
TELEGRAM_TOKEN = '7729849752:AAGz21aRdIrrGIDtQ_7ByBCRWDBIafUAalg'
TELEGRAM_CHAT_ID = '@Signaltrends_bot'

# --- App Title ---
st.set_page_config(page_title="📈 Live Stock Signal Dashboard", layout="wide")
st.title("📈 Live Stock Signal Dashboard with RSI + Telegram Alerts")

# --- Sidebar Input ---
ticker = st.sidebar.text_input("Enter Stock Symbol (e.g., AAPL, TCS.NS)", value="AAPL")
rsi_period = st.sidebar.slider("RSI Period", min_value=2, max_value=30, value=14)
refresh_interval = st.sidebar.slider("Auto Refresh Every (seconds)", 10, 300, 60)

# --- Function to Compute RSI and Signal ---
def compute_signals(df, rsi_period=14):
    df['Close'] = df['Close'].astype(float)
    rsi = RSIIndicator(close=df['Close'].squeeze(), window=rsi_period)
    df['RSI'] = rsi.rsi()
    df['Signal'] = 'HOLD'
    df.loc[df['RSI'] < 30, 'Signal'] = 'BUY'
    df.loc[df['RSI'] > 70, 'Signal'] = 'SELL'
    return df

# --- Function to Send Telegram Alert ---
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    requests.post(url, data=payload)

# --- Session State to Prevent Repeated Alerts ---
if 'last_signal' not in st.session_state:
    st.session_state.last_signal = ''

# --- Live Signal Tracking ---
placeholder = st.empty()

while True:
    data = yf.download(ticker, period="7d", interval="15m", progress=False)
    if not data.empty:
        df = compute_signals(data)
        latest = df.iloc[-1]
        signal = latest['Signal']

        with placeholder.container():
            st.subheader(f"📊 {ticker} - Latest Signal: **{signal}**")
            st.line_chart(df[['Close']])
            st.dataframe(df.tail(10)[['Close', 'RSI', 'Signal']])

        if signal != st.session_state.last_signal:
            message = f"📢 {ticker} Signal Alert:\n\nCurrent Price: {latest['Close']:.2f}\nRSI: {latest['RSI']:.2f}\nSignal: {signal}"
            send_telegram_alert(message)
            st.session_state.last_signal = signal

    else:
        st.warning("⚠️ Failed to fetch data. Please check the symbol or your internet connection.")

    time.sleep(refresh_interval)
