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
    
    # Validate Close column
    if "Close" not in df.columns:
        st.error("Close column not found in data.")
        return df
    if not pd.api.types.is_numeric_dtype(df["Close"]):
        st.error("Close column contains non-numeric data.")
        return df
    
    # Handle NaN values
    if df["Close"].isna().any():
        st.warning("NaN values found in Close column. Dropping NaNs.")
        df = df.dropna(subset=["Close"])
        if df.empty:
            st.error("No valid data after dropping NaNs.")
            return df
    
    # Compute indicators
    try:
        macd = MACD(df["Close"])
        rsi = RSIIndicator(df["Close"], window=rsi_period)

        df["MACD"] = macd.macd()
        df["Signal"] = macd.macd_signal()
        df["RSI"] = rsi.rsi()

        df["Buy_Signal"] = (df["MACD"] > df["Signal"]) & (df["RSI"] < 30)
        df["Sell_Signal"] = (df["MACD"] < df["Signal"]) & (df["RSI"] > 70)
    except Exception as e:
        st.error(f"Error computing indicators: {str(e)}")
        return df
    
    return df

def get_stock_data(symbol, period="1d", interval="5m"):
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    if df.empty:
        st.error("No data found. Please check the symbol.")
        return pd.DataFrame()
    
    # Reset index to make 'Date' or 'Datetime' a column
    df = df.reset_index()
    
    # Handle multi-level columns
    if isinstance(df.columns, pd.MultiIndex):
        # For single ticker, take the first level of column names (ignore ticker level)
        df.columns = [col[0] if col[1] == '' else col[0] for col in df.columns]
    
    # Ensure the datetime column is named consistently
    if 'Date' in df.columns:
        df.rename(columns={'Date': 'Datetime'}, inplace=True)
    elif 'Datetime' not in df.columns:
        st.error("Datetime column not found in data.")
        return pd.DataFrame()
    
    # Ensure Close column exists and is numeric
    if 'Close' not in df.columns:
        st.error("Close column not found in data.")
        return pd.DataFrame()
    
    # Convert Close to numeric, if possible
    try:
        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    except Exception as e:
        st.error(f"Error converting Close column to numeric: {str(e)}")
        return pd.DataFrame()
    
    # Log column info for debugging
    st.write(f"Columns: {list(df.columns)}")
    st.write(f"Close column dtype: {df['Close'].dtype}")
    
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
