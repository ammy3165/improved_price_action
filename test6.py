import pandas as pd
import numpy as np
import yfinance as yf

# =============================
# LOAD DATA (NIFTY 5m, 2 months)
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
# BUILD SYSTEM (LONG + SHORT)
# =============================
def build_system(df):

    df['LongEntry'] = (
        (df['Trend'] == 1) &
        (df['Close'].shift(1) < df['EMA'].shift(1)) &
        (df['Close'] > df['EMA'])
    )

    df['ShortEntry'] = (
        (df['Trend'] == -1) &
        (df['Close'].shift(1) > df['EMA'].shift(1)) &
        (df['Close'] < df['EMA'])
    )

    return df

# =============================
# BACKTEST (LONG + SHORT with timestamps)
# =============================
def backtest_with_trades(df, capital=100000):
    trades = []
    position = 0
    entry_price = 0
    qty = 0
    entry_time = None

    equity_curve = []

    for i in range(len(df)):
        price = df['Close'].iloc[i]
        timestamp = df.index[i]

        # LONG ENTRY
        if df['LongEntry'].iloc[i] and position == 0:
            entry_price = price
            qty = capital // price
            entry_time = timestamp
            position = 1

        # SHORT ENTRY
        elif df['ShortEntry'].iloc[i] and position == 0:
            entry_price = price
            qty = capital // price
            entry_time = timestamp
            position = -1

        # LONG EXIT
        elif position == 1 and df['Trend'].iloc[i] == -1:
            exit_price = price
            exit_time = timestamp
            pnl = (exit_price - entry_price) * qty
            capital += pnl
            trades.append({
                'Type': 'LONG',
                'Entry Time': entry_time,
                'Entry': entry_price,
                'Exit Time': exit_time,
                'Exit': exit_price,
                'PnL': pnl
            })
            position = 0

        # SHORT EXIT
        elif position == -1 and df['Trend'].iloc[i] == 1:
            exit_price = price
            exit_time = timestamp
            pnl = (entry_price - exit_price) * qty
            capital += pnl
            trades.append({
                'Type': 'SHORT',
                'Entry Time': entry_time,
                'Entry': entry_price,
                'Exit Time': exit_time,
                'Exit': exit_price,
                'PnL': pnl
            })
            position = 0

        equity_curve.append(capital)

    trades_df = pd.DataFrame(trades)

    # Convert UTC to IST
    trades_df['Entry Time'] = trades_df['Entry Time'].dt.tz_convert('Asia/Kolkata')
    trades_df['Exit Time'] = trades_df['Exit Time'].dt.tz_convert('Asia/Kolkata')

    equity_series = pd.Series(equity_curve, index=df.index)
    return trades_df, equity_series, capital

# =============================
# METRICS
# =============================
def calculate_metrics(trades_df, equity_series, capital=100000):
    # Strategy return
    strategy_return = (equity_series.iloc[-1] - capital) / capital * 100

    # Max Drawdown
    cumulative_max = equity_series.cummax()
    drawdown = (equity_series - cumulative_max) / cumulative_max
    max_dd = drawdown.min() * 100

    # Win rate
    if len(trades_df) > 0:
        win_rate = (trades_df['PnL'] > 0).mean() * 100
    else:
        win_rate = np.nan

    # Sharpe Ratio (using 5m returns)
    returns = equity_series.pct_change().dropna()
    sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252 * 78)  # 78 5-min bars per day

    return strategy_return, max_dd, win_rate, sharpe_ratio

# =============================
# BENCHMARK
# =============================
def benchmark_return(df, capital=100000):
    start = df['Close'].iloc[0]
    end = df['Close'].iloc[-1]
    qty = capital // start
    final = capital + (end - start) * qty
    return final, (final - capital) / capital * 100

# =============================
# RUN
# =============================
df = supertrend_with_ema(df)
df = build_system(df)

trades_df, equity_series, final_capital = backtest_with_trades(df)
strategy_return, max_dd, win_rate, sharpe_ratio = calculate_metrics(trades_df, equity_series)
bench_final, bench_return_pct = benchmark_return(df)

# =============================
# RESULTS
# =============================
print("===== RESULTS =====")
print(f"Final Capital: {final_capital:.2f}")
print(f"Strategy Return %: {strategy_return:.2f}%")
print(f"Benchmark Return %: {bench_return_pct:.2f}%")
print(f"Max Drawdown: {max_dd:.2f}%")
print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
print(f"Win Rate: {win_rate:.2f}%")
print(f"Total Trades: {len(trades_df)}")

# Show last 10 trades
print("\nLast 10 Trades:")
print(trades_df.tail(30))