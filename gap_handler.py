import pandas as pd

GAP_THRESHOLD = 0.005
ATR_TRAIL_MULT = 1

def handle_gap(df, i, position, sl):
    if i == 0:
        return sl

    atr = df['ATR'].iloc[i]

    if pd.isna(atr):
        return sl

    today_open = df['Open'].iloc[i]
    prev_close = df['Close'].iloc[i-1]

    gap = (today_open - prev_close) / prev_close

    if position == 1:
        if gap <= -GAP_THRESHOLD:
            new_sl = today_open - ATR_TRAIL_MULT * atr
            sl = max(sl, new_sl)

    elif position == -1:
        if gap >= GAP_THRESHOLD:
            new_sl = today_open + ATR_TRAIL_MULT * atr
            sl = min(sl, new_sl)

    return sl