
GAP_THRESHOLD = 0.005    # 0.5%

gap = (today_open - prev_close) / prev_close

# Long position
if position == 1:
    if gap <= -GAP_THRESHOLD:
        # Gap down > 0.5% → wait, reset trail to open
        trail_sl = today_open - ATR_TRAIL_MULT * atr

    else:
        # Gap down < 0.5% → normal ATR trail continues
        pass

# ── SHORT position ──
elif position == -1:
    if gap >= GAP_THRESHOLD:
        # Gap up > 0.5% → wait, reset trail to open
        trail_sl = today_open + ATR_TRAIL_MULT * atr

    else:
        # Gap up < 0.5% → normal ATR trail continues
        pass