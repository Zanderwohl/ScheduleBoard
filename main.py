from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2
import uasyncio as asyncio
import network
from settings import SSID, PASS
from config import WEB_ADMIN
from wifi import connect
from mdns_announce import announce_http
from display_board import render_board
import timetable as tt
from web_ui import create_handler

# ---------- Display (unchanged) ----------
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2)
bg = display.create_pen(30, 30, 255)
fg = display.create_pen(255, 255, 255)

MY_NAME = "trainboard"
MY_IP = None

# ---------- Main ----------
async def main():
    global MY_IP
    network.hostname(MY_NAME)
    if WEB_ADMIN:
        MY_IP = connect(SSID, PASS)

    # draw something so you see it's alive
    display.set_pen(bg);
    display.clear()
    display.set_pen(fg)
    display.set_font("bitmap8");
    display.text("Trainboard", 4, 4)
    display.set_font("bitmap8");
    display.text("Online", 4, 20, scale=3)
    display.update()

    render_board(display, sorted(tt.TIMETABLE, key=tt._time_key), fg, bg)

    if WEB_ADMIN:
        # Bonjour announce (no bind)
        ip_bytes = bytes(int(p) for p in MY_IP.split("."))
        asyncio.create_task(announce_http("Trainboard", f"{MY_NAME}.local", ip_bytes, port=80))

        # HTTP server
        handle = create_handler(display, fg, bg)
        server = await asyncio.start_server(handle, "0.0.0.0", 80, backlog=2)
        print("Serving on", MY_IP, "as", f"{MY_NAME}.local")
        await asyncio.Event().wait()
    else:
        # No web admin: just idle
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())

