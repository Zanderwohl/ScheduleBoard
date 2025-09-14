from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2
import uasyncio as asyncio
import network
import time
from settings import SSID, PASS
from config import WEB_ADMIN, TIME_FACTOR
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

    # virtual clock starting at midnight
    start_ms = time.ticks_ms()

    def current_minutes():
        elapsed_ms = time.ticks_diff(time.ticks_ms(), start_ms)
        sim_minutes = int((elapsed_ms / 1000.0) * (TIME_FACTOR / 60.0))
        return sim_minutes % (24 * 60)

    # initial render
    render_board(display, tt.generate_timetable(tt.ROUTES, current_minutes(), 20), fg, bg)

    if WEB_ADMIN:
        # Bonjour announce (no bind)
        ip_bytes = bytes(int(p) for p in MY_IP.split("."))
        asyncio.create_task(announce_http("Trainboard", f"{MY_NAME}.local", ip_bytes, port=80))

        # HTTP server
        handle = create_handler(display, fg, bg)
        server = await asyncio.start_server(handle, "0.0.0.0", 80, backlog=2)
        print("Serving on", MY_IP, "as", f"{MY_NAME}.local")
        # periodic update of board based on virtual time
        async def updater():
            last_min = -1
            while True:
                now_min = current_minutes()
                if now_min != last_min:
                    last_min = now_min
                    render_board(display, tt.generate_timetable(tt.ROUTES, now_min, 20), fg, bg)
                await asyncio.sleep_ms(200)

        asyncio.create_task(updater())
        await asyncio.Event().wait()
    else:
        # No web admin: just idle
        # periodic update even without web UI
        async def updater():
            last_min = -1
            while True:
                now_min = current_minutes()
                if now_min != last_min:
                    last_min = now_min
                    render_board(display, tt.generate_timetable(tt.ROUTES, now_min, 20), fg, bg)
                await asyncio.sleep_ms(200)
        await updater()


if __name__ == "__main__":
    asyncio.run(main())

