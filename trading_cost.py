def calculate_cost(entry_price, exit_price, qty):
    buy_turnover  = entry_price * qty
    sell_turnover = exit_price  * qty
    turnover      = buy_turnover + sell_turnover

    # Brokerage
    brokerage = min(20, 0.0003 * buy_turnover) + min(20, 0.0003 * sell_turnover)

    # STT (index futures)
    stt = sell_turnover * 0.0001

    # Exchange (NSE futures)
    exchange = turnover * 0.000019

    # SEBI
    sebi = turnover * 0.000001

    # GST
    gst = (brokerage + exchange + sebi) * 0.18

    # Stamp duty (futures)
    stamp = buy_turnover * 0.00002

    total_cost = brokerage + stt + exchange + gst + sebi + stamp
    return round(total_cost, 2)