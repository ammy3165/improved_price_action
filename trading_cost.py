# ==============================
# TRADING COST MODULE (INDIA)
# ==============================
def calculate_cost(entry_price, exit_price, qty):
    buy_turnover  = entry_price * qty
    sell_turnover = exit_price  * qty
    turnover      = buy_turnover + sell_turnover

    # Brokerage: ₹20 cap per leg
    brokerage = min(20, 0.0003 * buy_turnover) + min(20, 0.0003 * sell_turnover)

    # STT: 0.025% on sell side only
    stt = sell_turnover * 0.00025

    # Exchange transaction charges
    exchange = turnover * 0.00000305

    # GST: 18% on brokerage + exchange
    gst = (brokerage + exchange) * 0.18

    # SEBI charges
    sebi = turnover * 0.000001

    # Stamp duty: 0.003% on buy side only
    stamp = buy_turnover * 0.00003

    total_cost = brokerage + stt + exchange + gst + sebi + stamp
    return round(total_cost, 2)