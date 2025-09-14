def fit_text(display, s, max_px, scale=1):
    # ASCII-safe ellipsis
    ELL = "..."
    s = s or ""
    # Fast path
    try:
        w = display.measure_text(s, scale)
    except AttributeError:
        # crude fallback if measure_text isn't present
        w = len(s) * 6 * scale
    if w <= max_px:
        return s

    # Reserve space for ellipsis
    try:
        ell_w = display.measure_text(ELL, scale)
    except AttributeError:
        ell_w = 3 * 6 * scale
    max_px = max(0, max_px - ell_w)

    # Binary chop to fit
    lo, hi = 0, len(s)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        try:
            mw = display.measure_text(s[:mid], scale)
        except AttributeError:
            mw = mid * 6 * scale
        if mw <= max_px:
            lo = mid
        else:
            hi = mid - 1
    return (s[:lo] + ELL) if lo < len(s) else s


