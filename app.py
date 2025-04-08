import streamlit as st
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
import requests

# === Parameters ===
ticker = "RELIANCE.NS"  # Change to your stock symbol
ema_fast = 9
ema_slow = 21
rsi_period = 14
bot_token = "7729849752:AAGz21aRdIrrGIDtQ_7ByBCRWDBIafUAalg"
chat_id = "YOUR_CHAT_ID"  # Replace with your Telegram ID

# === Signal Detection ===
def compute_signals(df):
    df = df.copy()
    df['Close'] = df['Close'].squeeze()
    df['RSI'] = RSIIndicator(df['Close'], window=rsi_period).rsi()
    df['EMA_Fast'] = EMAIndicator(df['Close'], window=ema_fast).ema_indicator()
    df['EMA_Slow'] = EMAIndicator(df['Close'], window=ema_slow).ema_indicator()

    df['Signal'] = 0
    df.loc[(df['RSI'] < 30) & (df['EMA_Fast'] > df['EMA_Slow']), 'Signal'] = 1
    df.loc[(df['RSI'] > 70) & (df['EMA_Fast'] < df['EMA_Slow']), 'Signal'] = -1
    return df

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            st.success("Alert sent to Telegram!")
        else:
            st.error("Failed to send alert.")
    except Exception as e:
        st.error(f"Telegram error: {e}")

# === Streamlit UI ===
st.set_page_config(page_title="Live Stock Signal Tracker", layout="wide")
st.title("📈 Live Signal Tracker with Telegram Alerts")

st.sidebar.header("Settings")
ticker = st.sidebar.text_input("Enter Stock Ticker", ticker)
ema_fast = st.sidebar.slider("Fast EMA", 5, 20, ema_fast)
ema_slow = st.sidebar.slider("Slow EMA", 10, 50, ema_slow)
rsi_period = st.sidebar.slider("RSI Period", 7, 21, rsi_period)

data = yf.download(ticker, period="1mo", interval="1h")
if data.empty:
    st.error("No data found.")
else:
    df = compute_signals(data)

    last_signal = df['Signal'].iloc[-1]
    signal_text = "🔍 No Signal"
    if last_signal == 1:
        signal_text = "✅ BUY SIGNAL!"
        send_telegram_alert(f"📈 {ticker} - Buy Signal Detected!")
    elif last_signal == -1:
        signal_text = "❌ SELL SIGNAL!"
        send_telegram_alert(f"📉 {ticker} - Sell Signal Detected!")

    st.subheader(f"Signal for {ticker}: {signal_text}")
    st.line_chart(df[['Close', 'EMA_Fast', 'EMA_Slow']])
    st.dataframe(df.tail(10))
