print("✅ Loaded calculate_trade_levels() with direction param")
def calculate_trade_levels(df, direction):
    close = df['close'].iloc[-1]

    if direction == "bullish":
        entry = close
        tp = entry * 1.05  # Take profit: +5%
        sl = entry * 0.98  # Stop loss: -2%
    else:  # bearish
        entry = close
        tp = entry * 0.95  # Take profit: -5%
        sl = entry * 1.02  # Stop loss: +2%

    rr = abs(tp - entry) / abs(sl - entry)

    return {
        "entry": round(entry, 2),
        "tp": round(tp, 2),
        "sl": round(sl, 2),
        "rr": round(rr, 2)
    }
def smart_trade_signal(df):
    signals = []

    # Calculate EMAs
    df['EMA_50'] = df['close'].ewm(span=50).mean()
    df['EMA_200'] = df['close'].ewm(span=200).mean()

    # Calculate RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Volume spike (compare last bar to average of previous 10)
    avg_volume = df['volume'].iloc[-11:-1].mean()
    latest_volume = df['volume'].iloc[-1]

    # Trend condition
    if (
        df['close'].iloc[-1] > df['EMA_50'].iloc[-1] and
        df['EMA_50'].iloc[-1] > df['EMA_200'].iloc[-1] and
        45 < df['RSI'].iloc[-1] < 55 and
        latest_volume > avg_volume
    ):
        signals.append("LONG")

    elif (
        df['close'].iloc[-1] < df['EMA_50'].iloc[-1] and
        df['EMA_50'].iloc[-1] < df['EMA_200'].iloc[-1] and
        45 < df['RSI'].iloc[-1] < 55 and
        latest_volume > avg_volume
    ):
        signals.append("SHORT")

    return signals, df['RSI'].iloc[-1], latest_volume, avg_volume