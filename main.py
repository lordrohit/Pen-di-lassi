import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
from dotenv import load_dotenv
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

from telegram.ext import Updater, CommandHandler
from autoscan import run_auto_scan

# Load environment variables
load_dotenv()

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BASE_URL = "https://fapi.binance.com"

# Set up Telegram bot
updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# ========== COMMAND HANDLERS ==========


def handle_longs_command(update, context):
    bot = context.bot
    chat_id = update.effective_chat.id
    bot.send_message(chat_id=chat_id, text="🟢 Scanning for bullish trade setups...")
    run_auto_scan(bot, mode="bullish")

def handle_shorts_command(update, context):
    bot = context.bot
    chat_id = update.effective_chat.id
    bot.send_message(chat_id=chat_id, text="🔴 Scanning for bearish trade setups...")
    run_auto_scan(bot, mode="bearish")

# Register commands
dispatcher.add_handler(CommandHandler("longs", handle_longs_command))
dispatcher.add_handler(CommandHandler("shorts", handle_shorts_command))

# ========== OHLCV FETCHER (USED BY autoscan) ==========

def get_ohlcv(symbol, interval="15m", limit=100):
    url = f"{BASE_URL}/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()

        # Create dataframe
        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close",
            "volume", "close_time", "quote_asset_volume",
            "num_trades", "taker_buy_base_volume",
            "taker_buy_quote_volume", "ignore"
        ])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        df = df.astype(float)
        return df

    except Exception as e:
        print(f"❌ Error fetching OHLCV for {symbol}: {e}")
        return None

# ========== START THE BOT ==========

if __name__ == '__main__':
    print("🚀 Bot started!")
    updater.start_polling()
    updater.idle()
    print("✅ Bot is running!")
