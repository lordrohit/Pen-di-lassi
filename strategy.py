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