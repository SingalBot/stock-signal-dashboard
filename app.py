import streamlit as st
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import MACD
import datetime
import requests

# Telegram Bot Config
TELEGRAM_TOKEN = '7729849752:AAGz21aRdIrrGIDtQ_7ByBCRWDBIafUAalg'
TELEGRAM_CHAT_ID = '@Signaltrends_bot'

# Streamlit Dashboard Title
st.title("📊 Live Stock Signal Dashboard")

# Sidebar for user input
symbol = st.sidebar.text_input("Enter Stock Symbol (e.g., AAPL, RELIANCE.BO):", value='AAPL')
rsi_period = st.sidebar.slider("RSI Period", min_value=7, max_value=21, value=14)
macd_fast = st.sidebar.slider("MACD Fast", min_value=8, max_value=16, value=12)
macd_slow = st.sidebar.slider("MACD Slow", min_value=20, max_value=30, value=26)
macd_signal = st.sidebar.slider("MACD Signal", min_value=5, max_value=12, value=9)

# Fetch historical data
data = yf.download(symbol, period="1mo", interval="15m")

# Flatten MultiIndex columns if needed
if isinstance(data.columns, pd.MultiIndex):
    data.columns = [' '.join(col).strip() for col in data.columns]

# Reset index
data.reset_index(inplace=True)

# Signal Calculation Function
def compute_signals(df):
    df = df.copy()
    df['RSI'] = RSIIndicator(df['Close'], window=rsi_period).rsi()
    macd = MACD(df['Close'], window_fast=macd_fast, window_slow=macd_slow, window_sign=macd_signal)
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    df['Signal'] = 'Hold'

    df.loc[(df['RSI'] < 30) & (df['MACD'] > df['MACD_Signal']), 'Signal'] = 'Buy'
    df.loc[(df['RSI'] > 70) & (df['MACD'] < df['MACD_Signal']), 'Signal'] = 'Sell'
    return df

# Apply signal calculation
data = compute_signals(data)

# Display chart
if 'Close' in data.columns:
    st.line_chart(data[['Close']].set_index('Datetime'))
else:
    st.warning("The 'Close' column is not found. Here's the data:")
    st.write(data.head())

# Display last signals
st.subheader("📈 Last Signals")
st.write(data[['Datetime', 'Close', 'RSI', 'MACD', 'MACD_Signal', 'Signal']].tail(10))

# Send Telegram Alert if Buy or Sell signal found in last row
latest_signal = data.iloc[-1]['Signal']
latest_price = data.iloc[-1]['Close']
latest_time = data.iloc[-1]['Datetime']

if latest_signal in ['Buy', 'Sell']:
    message = f"📢 *{symbol}* Signal Alert\n\n*Signal:* {latest_signal}\n*Price:* ${latest_price:.2f}\n*Time:* {latest_time}"
    send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(send_url, data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    })

# Auto refresh every 60 seconds
st_autorefresh = st.experimental_rerun
