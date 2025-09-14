from util import fit_text

# Layout tuned for Pico Display 2 (320x240)
COLS = [("Zeit", 35), ("", 55), ("Über", 95), ("Ziel", 95), ("Gleis", 35)]  # widths sum to 320
HEADER_H = 22
ROW_H = 18
MARGIN_Y = 4
SCALE = 1  # bitmap8 @ scale 1


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
    if max_chars <= 1:
        return t[:max_chars]
    return t[:max_chars - 1] + "…"


def render_board(display, timetable, fg_pen, bg_pen):
    # background
    display.set_pen(bg_pen)
    display.clear()

    # header bar
    display.set_pen(fg_pen)
    display.set_font("bitmap8")
    x = 0
    y = MARGIN_Y
    for name, w in COLS:
        # header text
        txt = _truncate_to_width(name, w - 4)
        display.text(txt, x + 2, y + 3, scale=SCALE)
        # column separator line under header (simple rule)
        # draw a 1px horizontal line
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
        # draw each cell
        for (wdef, cell) in zip(COLS, cells):
            w = wdef[1]
            txt = _truncate_to_width(cell, w - 4)
            display.text(txt, x + 2, y + 2, scale=SCALE)
            x += w
        # row underline
        display.line(0, y + ROW_H - 1, 319, y + ROW_H - 1)
        y += ROW_H

    display.update()


