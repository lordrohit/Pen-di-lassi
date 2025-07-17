import pandas as pd

def calculate_trade_levels(df, direction):
    close = df['close'].iloc[-1]

    # Calculate ATR (Average True Range)
    df['H-L'] = df['high'] - df['low']
    df['H-PC'] = abs(df['high'] - df['close'].shift(1))
    df['L-PC'] = abs(df['low'] - df['close'].shift(1))
    tr = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    atr = tr.rolling(14).mean().iloc[-1]

    if direction == "bullish":
        entry = close
        tp = entry + (1.5 * atr)
        sl = entry - (1 * atr)
    else:  # bearish
        entry = close
        tp = entry - (1.5 * atr)
        sl = entry + (1 * atr)

    rr = abs(tp - entry) / abs(sl - entry)

    return {
        "entry": round(entry, 2),
        "tp": round(tp, 2),
        "sl": round(sl, 2),
        "rr": round(rr, 2)
    }

def score_trade(rsi, volume, avg_volume, pattern, ma_below, direction):
    score = 0

    if direction == "SHORT" and rsi < 45:
        score += 20
    elif direction == "LONG" and rsi > 55:
        score += 20

    if volume > avg_volume * 1.5:
        score += 25
    elif volume > avg_volume * 1.2:
        score += 15

    if pattern in ["Bearish Engulfing", "Breakout", "Double Top", "Evening Star"]:
        score += 20

    if ma_below:
        score += 15

    return score

def trade_quality(score):
    if score >= 70:
        return "🔥 ULTRA RARE"
    elif score >= 50:
        return "⚡ HIGH PROBABILITY"
    else:
        return "🌱 NORMAL" 

def smart_trade_signal(df, pattern):
    signals = []

    # EMA
    df['EMA_50'] = df['close'].ewm(span=50).mean()
    df['EMA_200'] = df['close'].ewm(span=200).mean()
    ma_below = df['EMA_50'].iloc[-1] < df['EMA_200'].iloc[-1]

    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    rsi = df['RSI'].iloc[-1]

    # Volume spike detection
    avg_volume = df['volume'].iloc[-11:-1].mean()
    latest_volume = df['volume'].iloc[-1]

    # RSI crossover
    rsi_cross_up = df['RSI'].iloc[-2] < 50 and df['RSI'].iloc[-1] > 50
    rsi_cross_down = df['RSI'].iloc[-2] > 50 and df['RSI'].iloc[-1] < 50

    # Detect trend
    if (
        df['close'].iloc[-1] > df['EMA_50'].iloc[-1] and
        df['EMA_50'].iloc[-1] > df['EMA_200'].iloc[-1] and
        rsi_cross_up and
        latest_volume > avg_volume
    ):
        direction = "LONG"
        levels = calculate_trade_levels(df, "bullish")
    elif (
        df['close'].iloc[-1] < df['EMA_50'].iloc[-1] and
        df['EMA_50'].iloc[-1] < df['EMA_200'].iloc[-1] and
        rsi_cross_down and
        latest_volume > avg_volume
    ):
        direction = "SHORT"
        levels = calculate_trade_levels(df, "bearish")
    else:
        return None  # No signal

    score = score_trade(rsi, latest_volume, avg_volume, pattern, ma_below, direction)
    quality = trade_quality(score)

    signal = {
        "direction": direction,
        "rsi": round(rsi, 2),
        "volume": int(latest_volume),
        "avg_volume": int(avg_volume),
        "entry": levels["entry"],
        "tp": levels["tp"],
        "sl": levels["sl"],
        "rr": levels["rr"],
        "score": score,
        "quality": quality,
        "pattern": pattern
    }

    return signal