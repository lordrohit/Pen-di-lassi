import os
import requests
import pandas as pd
import pytz
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from telegram.ext import Updater, CommandHandler

from autoscan import run_smart_scan, run_auto_scan
from utils import is_within_working_hours
from strategy import smart_trade_signal  # ✅ Make sure this is correct
from patterns_custom import detect_all_patterns  # ✅ Your pattern detector

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
bot = updater.bot

# Scheduler for smart scan every 10 min
scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Kolkata'))
scheduler.add_job(lambda: run_smart_scan(bot), 'interval', minutes=10)
scheduler.start()

# ========== COMMAND HANDLERS ==========

def error_handler(update, context):
    print(f"Exception while handling an update: {context.error}")

def handle_longs_command(update, context):
    bot = context.bot
    chat_id = update.effective_chat.id
    if not is_within_working_hours():
        bot.send_message(chat_id=chat_id, text="⏱ Bot active only from 5:00 AM to 12:00 AM.")
        return
    bot.send_message(chat_id=chat_id, text="🟢 Scanning for bullish trade setups...")
    run_auto_scan(bot, mode="bullish")

def handle_shorts_command(update, context):
    bot = context.bot
    chat_id = update.effective_chat.id
    if not is_within_working_hours():
        bot.send_message(chat_id=chat_id, text="⏱ Bot active only from 5:00 AM to 12:00 AM.")
        return
    bot.send_message(chat_id=chat_id, text="🔴 Scanning for bearish trade setups...")
    run_auto_scan(bot, mode="bearish")

def handle_smartscan_command(update, context):
    bot = context.bot
    chat_id = update.effective_chat.id
    if not is_within_working_hours():
        bot.send_message(chat_id=chat_id, text="⏱ Bot active only from 5:00 AM to 12:00 AM.")
        return
    bot.send_message(chat_id=chat_id, text="🧠 Running smart scan...")
    run_smart_scan(bot)

# Register commands
dispatcher.add_error_handler(error_handler)
dispatcher.add_handler(CommandHandler("longs", handle_longs_command))
dispatcher.add_handler(CommandHandler("shorts", handle_shorts_command))
dispatcher.add_handler(CommandHandler("smartscan", handle_smartscan_command))

# ========== OHLCV FETCHER ==========

def get_ohlcv(symbol, interval="15m", limit=100):
    url = f"{BASE_URL}/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()

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

# ========== SIGNAL DEMO RUNNER (OPTIONAL) ==========

def run_single_scan(symbol="BCHUSDT"):
    df = get_ohlcv(symbol)
    if df is None:
        return

    pattern = detect_all_patterns(df)
    signal = smart_trade_signal(df, pattern)

    if signal:
        message = f"""🚀 Smart Trade Signal Detected:
Symbol: {symbol}
Trend: {signal['direction']}
RSI: {signal['rsi']}
Volume: {signal['volume']} > Avg {signal['avg_volume']}
Pattern: {signal['pattern']}
Entry: {signal['entry']}
Stop Loss: {signal['sl']}
Take Profit: {signal['tp']}
Risk:Reward: {signal['rr']}
Score: {signal['score']} → {signal['quality']}
Timeframe: 15m
"""
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

# ========== START THE BOT ==========

if __name__ == '__main__':
    print("🚀 Bot started!")
    updater.start_polling()
    updater.idle()
    print("✅ Bot is running!")