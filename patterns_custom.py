def detect_all_patterns(df):
    patterns = []

    # ❗ Skip if DataFrame too short
    if df is None or len(df) < 20:
        return []

    try:
        # ➕ Safely calculate RSI
        df['price_change'] = df['close'].diff()
        df['gain'] = df['price_change'].clip(lower=0)
        df['loss'] = -df['price_change'].clip(upper=0)
        avg_gain = df['gain'].rolling(window=14).mean()
        avg_loss = df['loss'].rolling(window=14).mean()
        rs = avg_gain / (avg_loss + 1e-6)
        df['RSI'] = 100 - (100 / (1 + rs))

        # ➕ Calculate EMAs
        df['EMA20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()

        # Clean the last two rows for pattern checks
        last = df.iloc[-1]
        prev = df.iloc[-2]

        # ✅ EMA Bullish Crossover
        if last['EMA20'] > last['EMA50'] and prev['EMA20'] < prev['EMA50']:
            patterns.append({"name": "EMA Bullish Crossover", "direction": "bullish"})

        # ✅ EMA Bearish Crossover
        if last['EMA20'] < last['EMA50'] and prev['EMA20'] > prev['EMA50']:
            patterns.append({"name": "EMA Bearish Crossover", "direction": "bearish"})

        # ✅ RSI Oversold Bounce
        if last['RSI'] > 30 and prev['RSI'] < 30:
            patterns.append({"name": "RSI Oversold Bounce", "direction": "bullish"})

        # ✅ RSI Overbought Drop
        if last['RSI'] < 70 and prev['RSI'] > 70:
            patterns.append({"name": "RSI Overbought Drop", "direction": "bearish"})

    except Exception as e:
        print(f"⚠️ Pattern detection failed: {e}")
        return []

    return patterns