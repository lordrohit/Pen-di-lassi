import os
import requests
import pandas as pd
from dotenv import load_dotenv
from io import BytesIO
import mplfinance as mpf

load_dotenv()

BASE_URL = "https://fapi.binance.com"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ✅ Get OHLCV data from Binance Futures
def get_ohlcv(symbol, interval="15m", limit=100):
    url = f"{BASE_URL}/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        raw_data = res.json()

        if not raw_data:
            print(f"⚠️ Binance returned empty candles for {symbol}")
            return None

        df = pd.DataFrame(raw_data, columns=[
            'time', 'open', 'high', 'low', 'close', 'volume',
            'c1', 'c2', 'c3', 'c4', 'c5', 'c6'
        ])
        df = df[['time', 'open', 'high', 'low', 'close', 'volume']].astype(float)
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        df.set_index('time', inplace=True)
        return df

    except Exception as e:
        print(f"❌ Error fetching OHLCV for {symbol}: {e}")
        return None

# ✅ Send photo to Telegram (if from file path)
def send_photo(bot, photo_path_or_buffer, caption):
    bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=photo_path_or_buffer, caption=caption)

# ✅ Send message to Telegram
def send_message(bot, message):
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

# ✅ Create candlestick chart in memory (BytesIO)
def create_chart(df, symbol):
    buf = BytesIO()
    mpf.plot(
        df,
        type='candle',
        style='charles',
        title=symbol,
        ylabel='Price',
        volume=True,
        savefig=dict(fname=buf, dpi=100, bbox_inches='tight')
    )
    buf.seek(0)
    return buf

# ✅ Calculate ATR (Average True Range)
def calculate_atr(df, period=14):
    df['H-L'] = df['high'] - df['low']
    df['H-PC'] = abs(df['high'] - df['close'].shift(1))
    df['L-PC'] = abs(df['low'] - df['close'].shift(1))
    tr = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr