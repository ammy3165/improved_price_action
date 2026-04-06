import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
from trading_cost import calculate_cost

# ==============================
# CONFIG
# ==============================
capital = 100000
initial_capital = capital
risk_per_trade = 0.03
symbol = "^NSEI"

# ==============================
# LOAD DATA
# ==============================
df = yf.download(symbol, start="2026-03-4", end="2026-04-4", interval="5m")

if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

# Timezone handling
if df.index.tz is None:
    df = df.tz_localize('UTC')
df = df.tz_convert('Asia/Kolkata')    

df.dropna(inplace=True)

# ==============================
# STRATEGY LOGIC
# ==============================
df['Prev_High'] = df['High'].shift(1)
df['Prev_Low'] = df['Low'].shift(1)

threshold = 0.001  # 0.1%

df['Buy_Signal'] = df['Close'] > df['Prev_High'] * (1 + threshold)
df['Sell_Signal'] = df['Close'] < df['Prev_Low'] * (1 - threshold)


# ==============================
# BACKTEST
# ==============================
position = 0
entry_price = 0
sl = 0
qty = 0

equity_curve = []
trade_pnls = []
trades = []
current_trade = {}

for i in range(2, len(df)):

    row = df.iloc[i]
    prev = df.iloc[i-1]

    mtm = 0

    # ==============================
    # ENTRY
    # ==============================
    if position == 0:

        if row['Buy_Signal']:
            entry_price = row['Close']

            sl = max(prev['Low'], entry_price * (1 - 0.005))
           
            risk = abs(entry_price - sl)
            if risk <= 0:
                continue

            qty_risk = (capital * risk_per_trade) / risk
            qty_capital = capital / entry_price
            qty = math.floor(min(qty_risk, qty_capital))

            position = 1

            current_trade = {
                "Type": "LONG",
                "Entry_Date": df.index[i],
                "Entry_Price": entry_price,
                "Qty": qty
            }

        elif row['Sell_Signal']:
            entry_price = row['Close']
            sl = min(prev['High'], entry_price * (1 + 0.005))

            risk = sl - entry_price
            if risk <= 0:
                continue

            qty_risk = (capital * risk_per_trade) / risk
            qty_capital = capital / entry_price
            qty = math.floor(min(qty_risk, qty_capital))

            position = -1

            current_trade = {
                "Type": "SHORT",
                "Entry_Date": df.index[i],
                "Entry_Price": entry_price,
                "Qty": qty
            }

    # ==============================
    # LONG POSITION
    # ==============================
    elif position == 1:

        sl = prev['Low']
        mtm = (row['Close'] - entry_price) * qty

        exit_price = None

        if row['Low'] <= sl:
            exit_price = sl
        elif row['Sell_Signal']:
            exit_price = row['Close']

        if exit_price:
            pnl = (exit_price - entry_price) * qty
            cost_value = calculate_cost(entry_price, exit_price, qty)
            pnl -= cost_value

            capital += pnl
            trade_pnls.append(pnl)

            current_trade.update({
                "Exit_Date": df.index[i],
                "Exit_Price": exit_price,
                "PnL": pnl,
                "Return_%": (exit_price / entry_price - 1) * 100,
                "Cost": cost_value
            })

            trades.append(current_trade)
            position = 0

    # ==============================
    # SHORT POSITION
    # ==============================
    elif position == -1:

        sl = prev['High']
        mtm = (entry_price - row['Close']) * qty

        exit_price = None

        if row['High'] >= sl:
            exit_price = sl
        elif row['Buy_Signal']:
            exit_price = row['Close']

        if exit_price:
            pnl = (entry_price - exit_price) * qty
            cost_value = calculate_cost(entry_price, exit_price, qty)
            pnl -= cost_value 
            
            capital += pnl
            trade_pnls.append(pnl)

            current_trade.update({
                "Exit_Date": df.index[i],
                "Exit_Price": exit_price,
                "PnL": pnl,
                "Return_%": (entry_price / exit_price - 1) * 100,
                "Cost": cost_value
            })

            trades.append(current_trade)
            position = 0

    equity_curve.append(capital + mtm)

# ==============================
# TRADES DATAFRAME
# ==============================
trades_df = pd.DataFrame(trades)

buy_trades = trades_df[trades_df["Type"] == "LONG"].round(2)
sell_trades = trades_df[trades_df["Type"] == "SHORT"].round(2)

# ==============================
# EQUITY SERIES
# ==============================
equity = pd.Series(equity_curve, index=df.index[2:])

# ==============================
# METRICS
# ==============================
total_return = (equity.iloc[-1] / initial_capital) - 1

drawdown = (equity / equity.cummax()) - 1
max_dd = drawdown.min()

returns = equity.pct_change().dropna()
sharpe = (returns.mean() / returns.std()) * np.sqrt(252)

# ==============================
# BENCHMARK
# ==============================
df['Benchmark'] = df['Close'].pct_change()
benchmark_curve = (1 + df['Benchmark']).cumprod().iloc[2:]

benchmark_return = benchmark_curve.iloc[-1] - 1

# ==============================
# WIN RATE
# ==============================
def return_based_win_rate(returns):
    if returns is None or len(returns) == 0:
        return 0

    total_positive = returns[returns > 0].sum()
    total_negative = -returns[returns < 0].sum()

    total = total_positive + total_negative
    return total_positive / total if total != 0 else 0

# ==============================
# RESULTS
# ==============================
print("\n===== RESULTS =====")
print(f"Benchmark Return: {benchmark_return:.2%}")
print(f"Total Return: {total_return:.2%}")
print(f"Final Capital: {equity.iloc[-1]:.2f}")
print(f"Max Drawdown: {max_dd:.2%}")
print(f"Sharpe Ratio: {sharpe:.2f}")
print(f"Win Rate: {return_based_win_rate(returns):.2%}")
print(f"Total Trades: {len(trade_pnls)}")
print("Total Trading Cost Paid:", round(trades_df["Cost"].sum(), 2))

print("\n===== LAST 10 BUY TRADES =====")
print(buy_trades)

print("\n===== LAST 10 SELL TRADES =====")
print(sell_trades)

# ==============================
# PLOT
# ==============================
plt.figure(figsize=(12, 6))

plt.plot(equity.index, equity, label="Strategy", linewidth=2)
plt.plot(benchmark_curve.index, benchmark_curve * initial_capital, label="Benchmark", linewidth=2)

plt.title("Strategy vs Benchmark")
plt.xlabel("Date")
plt.ylabel("Portfolio Value")

plt.legend()
plt.grid()

plt.show()

