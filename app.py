import streamlit as st
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import MACD
import time
import requests

# Telegram Bot Credentials
TELEGRAM_TOKEN = "7729849752:AAGz21aRdIrrGIDtQ_7ByBCRWDBIafUAalg"
TELEGRAM_CHAT_ID = "@Signaltrends_bot"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram Error:", e)

def compute_signals(df):
    rsi_period = 14
    macd = MACD(df["Close"])
    rsi = RSIIndicator(df["Close"], window=rsi_period)

    df["MACD"] = macd.macd()
    df["Signal"] = macd.macd_signal()
    df["RSI"] = rsi.rsi()

    df["Buy_Signal"] = (df["MACD"] > df["Signal"]) & (df["RSI"] < 30)
    df["Sell_Signal"] = (df["MACD"] < df["Signal"]) & (df["RSI"] > 70)
    return df

def get_stock_data(symbol, period="1d", interval="5m"):
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    if df.empty:
        st.error("No data found. Please check the symbol.")
        return pd.DataFrame()
    df = df.reset_index()
    df.columns = [col if isinstance(col, str) else col.strftime('%Y-%m-%d %H:%M:%S') for col in df.columns]
    return df

st.set_page_config(page_title="Stock Signal Dashboard", layout="wide")
st.title("📈 Live Stock Signal Dashboard")

symbol = st.text_input("Enter stock symbol (e.g., AAPL, RELIANCE.NS):", "AAPL")
refresh_interval = st.slider("Refresh Interval (seconds):", 10, 300, 60)

placeholder = st.empty()

while True:
    with placeholder.container():
        data = get_stock_data(symbol)

        if not data.empty and "Close" in data.columns:
            data = compute_signals(data)
            latest = data.iloc[-1]

            st.subheader(f"Live Signals for {symbol.upper()}")
            st.line_chart(data.set_index("Datetime")["Close"])

            if latest["Buy_Signal"]:
                st.success("✅ Buy Signal Detected!")
                send_telegram_message(f"📈 Buy Signal for {symbol.upper()} at {latest['Close']:.2f}")
            elif latest["Sell_Signal"]:
                st.error("🔻 Sell Signal Detected!")
                send_telegram_message(f"📉 Sell Signal for {symbol.upper()} at {latest['Close']:.2f}")
            else:
                st.info("🔍 No strong signal currently.")

            with st.expander("📊 Full Data Table"):
                st.dataframe(data.tail(10))

        time.sleep(refresh_interval)
        st.rerun()
