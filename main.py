import os
import requests
import pandas as pd
import pytz
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from telegram.ext import Updater, CommandHandler
import telegram.error

from autoscan import run_smart_scan, run_auto_scan
from utils import is_within_working_hours
from strategy import smart_trade_signal
from patterns_custom import detect_all_patterns

# Load .env variables
load_dotenv()
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BASE_URL = "https://fapi.binance.com"

# Telegram setup
updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher
bot = updater.bot

# ========== FIXED OHLCV FETCHER ==========
def get_ohlcv(symbol, interval="15m", limit=100):
    url = f"{BASE_URL}/fapi/v1/klines?symbol={symbol.upper()}&interval={interval}&limit={limit}"
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

# ========== BOT COMMAND HANDLERS ==========
def safe_send(chat_id, text):
    try:
        bot.send_message(chat_id=chat_id, text=text)
    except telegram.error.TelegramError as e:
        print(f"❌ Telegram send error: {e}")

def error_handler(update, context):
    print(f"Exception while handling an update: {context.error}")

def handle_longs_command(update, context):
    chat_id = update.effective_chat.id
    if not is_within_working_hours():
        return safe_send(chat_id, "⏱ Bot active only from 5:00 AM to 12:00 AM.")
    safe_send(chat_id, "🟢 Scanning for bullish trade setups...")
    run_auto_scan(bot, mode="bullish")

def handle_shorts_command(update, context):
    chat_id = update.effective_chat.id
    if not is_within_working_hours():
        return safe_send(chat_id, "⏱ Bot active only from 5:00 AM to 12:00 AM.")
    safe_send(chat_id, "🔴 Scanning for bearish trade setups...")
    run_auto_scan(bot, mode="bearish")

def handle_smartscan_command(update, context):
    chat_id = update.effective_chat.id
    if not is_within_working_hours():
        return safe_send(chat_id, "⏱ Bot active only from 5:00 AM to 12:00 AM.")
    safe_send(chat_id, "🧠 Running smart scan...")
    run_smart_scan(bot)

def handle_top3_command(update, context):
    chat_id = update.effective_chat.id
    if not is_within_working_hours():
        return safe_send(chat_id, "⏱ Bot active only from 5:00 AM to 12:00 AM.")
    safe_send(chat_id, "📊 Scanning all coins to find the Top 3 setups...")
    from autoscan import run_top3_scan
    run_top3_scan(bot, chat_id)

# Register handlers
dispatcher.add_error_handler(error_handler)
dispatcher.add_handler(CommandHandler("longs", handle_longs_command))
dispatcher.add_handler(CommandHandler("shorts", handle_shorts_command))
dispatcher.add_handler(CommandHandler("smartscan", handle_smartscan_command))
dispatcher.add_handler(CommandHandler("top3", handle_top3_command))

# ========== SIGNAL DEMO TESTER ==========
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
        safe_send(TELEGRAM_CHAT_ID, message)

# ========== SCHEDULER ==========
scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Kolkata'))
scheduler.add_job(lambda: run_smart_scan(bot), 'interval', minutes=10, max_instances=1)
scheduler.start()

# ========== START BOT ==========
if __name__ == '__main__':
    print("🚀 Bot started!")
    updater.start_polling()
    updater.idle()
    print("✅ Bot is running!")