import pandas as pd
import numpy as np
import yfinance as yf


# =============================
# LOAD DATA
# =============================
df = yf.download("^NSEI", period="60d", interval="5m")

if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)


# =============================
# SUPER TREND + EMA
# =============================
def supertrend_with_ema(df, ema_period=4, atr_period=7, factor=1.7):

    high = df['High']
    low = df['Low']
    close = df['Close']

    # EMA
    ema = close.ewm(span=ema_period, adjust=False).mean()

    # ATR
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(atr_period).mean()

    # Bands
    up = ema - factor * atr
    down = ema + factor * atr

    TUp = np.full(len(df), np.nan)
    TDown = np.full(len(df), np.nan)
    Trend = np.full(len(df), 1)

    for i in range(1, len(df)):

        if np.isnan(TUp[i-1]) or ema.iloc[i-1] > TUp[i-1]:
            TUp[i] = up.iloc[i] if np.isnan(TUp[i-1]) else max(up.iloc[i], TUp[i-1])
        else:
            TUp[i] = up.iloc[i]

        if np.isnan(TDown[i-1]) or ema.iloc[i-1] < TDown[i-1]:
            TDown[i] = down.iloc[i] if np.isnan(TDown[i-1]) else min(down.iloc[i], TDown[i-1])
        else:
            TDown[i] = down.iloc[i]

        if ema.iloc[i] > TDown[i-1]:
            Trend[i] = 1
        elif ema.iloc[i] < TUp[i-1]:
            Trend[i] = -1
        else:
            Trend[i] = Trend[i-1]

    df['EMA'] = ema
    df['Trend'] = Trend
    df['Supertrend'] = np.where(Trend == 1, TUp, TDown)

    return df


# =============================
# BUILD SYSTEM (PULLBACK ENTRY)
# =============================
def build_system(df):

    df['LongEntry'] = (
        (df['Trend'] == 1) &
        (df['Close'].shift(1) < df['EMA'].shift(1)) &
        (df['Close'] > df['EMA'])
    )

    df['Exit'] = (df['Trend'] == -1)

    return df


# =============================
# BACKTEST
# =============================
def backtest(df, capital=100000):

    position = 0
    entry_price = 0
    qty = 0

    trades = []

    for i in range(len(df)):

        # ENTRY
        if df['LongEntry'].iloc[i] and position == 0:
            entry_price = df['Close'].iloc[i]
            qty = capital // entry_price
            position = 1

        # EXIT
        elif df['Exit'].iloc[i] and position == 1:
            exit_price = df['Close'].iloc[i]

            pnl = (exit_price - entry_price) * qty
            capital += pnl

            trades.append(pnl)

            position = 0

    return trades, capital


# =============================
# RUN
# =============================
df = supertrend_with_ema(df)

df = build_system(df)

trades, final_capital = backtest(df)

ret = (final_capital - 100000) / 100000 * 100

print("Final Capital:", final_capital)
print("Return %:", ret)
print("Total Trades:", len(trades))
print("Win Rate:", (np.array(trades) > 0).mean() * 100)