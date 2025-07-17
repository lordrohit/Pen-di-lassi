import os
import pandas as pd
from dotenv import load_dotenv
from patterns_custom import detect_all_patterns
from strategy import calculate_trade_levels
from datetime import datetime
from strategy import smart_trade_signal
from utils import get_futures_symbols

from utils import get_ohlcv, create_chart, send_photo, send_message

load_dotenv()

symbols = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "MATICUSDT", "AVAXUSDT", "DOTUSDT",
    "LTCUSDT", "TRXUSDT", "SHIBUSDT", "NEARUSDT", "LINKUSDT",
    "FILUSDT", "ATOMUSDT", "UNIUSDT", "ICPUSDT", "PEPEUSDT"
]

log_file = "trades_log.csv"

# ✅ Create the log file if it doesn’t exist
if not os.path.exists(log_file):
    pd.DataFrame(columns=["Time", "Symbol", "Pattern", "Direction", "Entry", "TP", "SL", "RR", "Command"])\
      .to_csv(log_file, index=False)

# ✅ Main scan function
def run_auto_scan(bot, mode="both"):
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    for symbol in symbols:
        try:
            df = get_ohlcv(symbol)
            if df is None or len(df) < 30:
                send_message(bot, f"⚠️ Skipping {symbol} — not enough candles ({len(df) if df is not None else 0} rows)")
                continue

            # Indicators
            df['EMA20'] = df['close'].ewm(span=20).mean()
            df['EMA50'] = df['close'].ewm(span=50).mean()

            patterns = detect_all_patterns(df)
            if not patterns:
                continue

            for pattern in patterns:
                direction = pattern['direction']
                name = pattern['name']

                if mode == "bullish" and direction != "bullish":
                    continue
                if mode == "bearish" and direction != "bearish":
                    continue

                levels = calculate_trade_levels(df, direction)
                if levels and levels['rr'] >= 1.5:
                    chart = create_chart(df, symbol)
                    leverage = "20x" if levels['rr'] >= 3 else "10x" if levels['rr'] >= 2 else "5x"

                    caption = (
                        f"🧠 {name} ({direction})\n"
                        f"📊 Symbol: {symbol}\n"
                        f"📈 Entry: {levels['entry']}\n"
                        f"🌟 TP: {levels['tp']}\n"
                        f"🛡 SL: {levels['sl']}\n"
                        f"⚖ R:R = {levels['rr']}\n"
                        f"⚡ Suggested Leverage: {leverage}"
                    )
                    send_photo(bot, chart, caption)

                    # ✅ Optional logging
                    log_entry = {
                        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Symbol": symbol,
                        "Pattern": name,
                        "Direction": direction,
                        "Entry": levels['entry'],
                        "TP": levels['tp'],
                        "SL": levels['sl'],
                        "RR": levels['rr'],
                        "Command": mode
                    }
                    pd.DataFrame([log_entry]).to_csv(log_file, mode='a', header=False, index=False)

        except Exception as e:
            send_message(bot, f"❌ Error on {symbol}: {e}")
def run_smart_scan(bot):
    from utils import get_futures_symbols, get_ohlcv, send_message
    from strategy import smart_trade_signal

    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    coins = get_futures_symbols()

    send_message(bot, f"🧠 SmartScan started for {len(coins)} coins...")

    for symbol in coins:
        df = get_ohlcv(symbol, interval="15m", limit=100)
        if df is None or df.empty:
            continue

        signals, rsi, vol, avg_vol = smart_trade_signal(df)

        if signals:
            send_message(bot, f"🚀 SIGNAL on {symbol} | RSI: {rsi:.2f} | Vol: {vol:.2f} > Avg: {avg_vol:.2f} | Signal: {signals}")

            direction = signals[0]
            message = f"""
🚀 Smart Trade Signal Detected:
Symbol: {symbol}
Trend: {direction}
RSI: {round(rsi, 2)}
Volume: {round(vol)} > Avg {round(avg_vol)}
Entry: {df['close'].iloc[-1]}
Timeframe: 15m
"""
            send_message(bot, message.strip())
# ✅ End message
    send_message(bot, "✅ SmartScan complete.")