def check_gap_exit(position, row, sl, tp):
    
    """
    Gap-aware exit logic
    Returns exit_price or None
    """

    open_price = row['Open']

    # LONG position
    if position == 1:
        # gap down stop
        if open_price <= sl:
            return open_price

        # gap up profit
        if open_price >= tp:
            return open_price

    # SHORT position
    elif position == -1:
        # gap up stop
        if open_price >= sl:
            return open_price

        # gap down profit
        if open_price <= tp:
            return open_price

    return None