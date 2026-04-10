import pandas as pd
import numpy as np
import yfinance as yf

# NIFTY 5m 2 months
df = yf.download("^NSEI", period="60d", interval="5m")

if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)


def supertrend_with_ema(df, ema_period=4, atr_period=7, factor=1.7):

    high = df['High']
    low = df['Low']
    close = df['Close']

    ema = close.ewm(span=ema_period, adjust=False).mean()

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(atr_period).mean()

    up = ema - factor * atr
    down = ema + factor * atr

    TUp = np.full(len(df), np.nan)
    TDown = np.full(len(df), np.nan)
    Trend = np.full(len(df), 1)

    for i in range(1, len(df)):

        if ema.iloc[i-1] > TUp[i-1] if not np.isnan(TUp[i-1]) else True:
            TUp[i] = max(up.iloc[i], TUp[i-1]) if not np.isnan(TUp[i-1]) else up.iloc[i]
        else:
            TUp[i] = up.iloc[i]

        if ema.iloc[i-1] < TDown[i-1] if not np.isnan(TDown[i-1]) else True:
            TDown[i] = min(down.iloc[i], TDown[i-1]) if not np.isnan(TDown[i-1]) else down.iloc[i]
        else:
            TDown[i] = down.iloc[i]

        if ema.iloc[i] > TDown[i-1]:
            Trend[i] = 1
        elif ema.iloc[i] < TUp[i-1]:
            Trend[i] = -1
        else:
            Trend[i] = Trend[i-1]

    df['Trend'] = Trend
    df['Buy'] = (df['Trend'] == 1) & (df['Trend'].shift(1) == -1)
    df['Sell'] = (df['Trend'] == -1) & (df['Trend'].shift(1) == 1)

    return df


def backtest(df, capital=100000):

    position = 0
    entry = 0
    qty = 0

    for i in range(len(df)):

        if df['Buy'].iloc[i] and position == 0:
            entry = df['Close'].iloc[i]
            qty = capital // entry
            position = 1

        elif df['Sell'].iloc[i] and position == 1:
            exit = df['Close'].iloc[i]
            capital += (exit - entry) * qty
            position = 0

    return capital


df = supertrend_with_ema(df)
final_capital = backtest(df)

ret = (final_capital - 100000) / 100000 * 100

print("Final Capital:", final_capital)
print("Return %:", ret)
print("Trades:", (df['Buy']).sum())