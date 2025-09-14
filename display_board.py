from util import fit_text

# Layout tuned for Pico Display 2 (320x240)
# Each column: (header_label, width_px, reverse_colors)
COLS = [("Zeit", 35, False), ("", 55, True), ("Über", 105, False), ("Ziel", 95, False), ("Gleis", 35, False)]  # widths sum to 320
HEADER_H = 22
ROW_H = 18
MARGIN_Y = 4
SCALE = 1  # bitmap8 @ scale 1
GLYPH_H = 8 * SCALE  # bitmap8 glyph height in pixels
HIGHLIGHT_MARGIN = 2


def safe_text(display, s, x, y, w, scale=1):
    if w <= 0 or x >= 320 or y >= 240:
        return
    s = fit_text(display, s, min(w - 2, 320 - x - 1), scale)
    display.text(s, x + 2, y + 2, scale=scale)


def _truncate_to_width(text, px_w):
    # bitmap8 is ~6 px per glyph at scale=1 (tight); use ~6 to be safe
    max_chars = max(0, px_w // 6)
    t = str(text or "")
    if len(t) <= max_chars:
        return t
    # Use a single ASCII dot to save space
    ell = "."
    if max_chars <= len(ell):
        return t[:max_chars]
    return t[:max_chars - len(ell)] + ell


def render_board(display, timetable, fg_pen, bg_pen):
    # background
    display.set_pen(bg_pen)
    display.clear()

    # header bar
    display.set_pen(fg_pen)
    display.set_font("bitmap8")
    x = 0
    y = MARGIN_Y
    for name, w, rev in COLS:
        # base header background (ensure consistent color)
        display.set_pen(bg_pen)
        display.rectangle(x, y, w, HEADER_H)
        # header text
        avail = w - (3 if name in ("Über", "Ziel") else 4)
        txt = _truncate_to_width(name, avail)
        tx = x + 2
        ty = y + 3
        # draw small highlight for reversed columns
        if rev and txt:
            txt_px = min(avail, len(txt) * 6 * SCALE)
            display.set_pen(fg_pen)
            display.rectangle(tx - HIGHLIGHT_MARGIN, ty - HIGHLIGHT_MARGIN,
                              txt_px + 2 * HIGHLIGHT_MARGIN, GLYPH_H + 2 * HIGHLIGHT_MARGIN)
            display.set_pen(bg_pen)
        else:
            display.set_pen(fg_pen)
        display.text(txt, tx, ty, scale=SCALE)
        # column separator line under header (simple rule)
        # draw a 1px horizontal line
        display.set_pen(fg_pen)
        display.line(0, y + HEADER_H, 319, y + HEADER_H)
        x += w

    # rows
    y = MARGIN_Y + HEADER_H + 2

    # how many rows fit?
    max_rows = max(0, (240 - y - 2) // ROW_H)
    rows = timetable[:max_rows]

    for row in rows:
        x = 0
        cells = [
            row.get("time", ""),
            row.get("train", ""),
            row.get("via", ""),
            row.get("dest", ""),
            row.get("track", ""),
        ]
        # vertically center text within the row cell (leave header unchanged)
        row_text_y = y + max(0, (ROW_H - GLYPH_H) // 2)
        # draw each cell
        for ((name, w, rev), cell) in zip(COLS, cells):
            # base cell background
            display.set_pen(bg_pen)
            display.rectangle(x, y, w, ROW_H)
            # text and optional highlight
            avail = w - 3
            txt = _truncate_to_width(cell, avail)
            tx = x + 2
            ty = row_text_y
            if rev and txt:
                txt_px = min(avail, len(txt) * 6 * SCALE)
                display.set_pen(fg_pen)
                display.rectangle(tx - HIGHLIGHT_MARGIN, ty - HIGHLIGHT_MARGIN,
                                  txt_px + 2 * HIGHLIGHT_MARGIN, GLYPH_H + 2 * HIGHLIGHT_MARGIN)
                display.set_pen(bg_pen)
            else:
                display.set_pen(fg_pen)
            display.text(txt, tx, ty, scale=SCALE)
            x += w
        # row underline
        display.set_pen(fg_pen)
        display.line(0, y + ROW_H - 1, 319, y + ROW_H - 1)
        y += ROW_H

    display.update()


