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

def smart_trade_signal(df):
    signals = []

    # EMA
    df['EMA_50'] = df['close'].ewm(span=50).mean()
    df['EMA_200'] = df['close'].ewm(span=200).mean()

    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Volume spike detection
    avg_volume = df['volume'].iloc[-11:-1].mean()
    latest_volume = df['volume'].iloc[-1]

    # RSI crossover from below 50 to above 50 (bullish momentum)
    rsi_cross_up = df['RSI'].iloc[-2] < 50 and df['RSI'].iloc[-1] > 50
    rsi_cross_down = df['RSI'].iloc[-2] > 50 and df['RSI'].iloc[-1] < 50

    # Long Setup
    if (
        df['close'].iloc[-1] > df['EMA_50'].iloc[-1] and
        df['EMA_50'].iloc[-1] > df['EMA_200'].iloc[-1] and
        rsi_cross_up and
        latest_volume > avg_volume
    ):
        signals.append("LONG")

    # Short Setup
    elif (
        df['close'].iloc[-1] < df['EMA_50'].iloc[-1] and
        df['EMA_50'].iloc[-1] < df['EMA_200'].iloc[-1] and
        rsi_cross_down and
        latest_volume > avg_volume
    ):
        signals.append("SHORT")

    return signals, df['RSI'].iloc[-1], latest_volume, avg_volume