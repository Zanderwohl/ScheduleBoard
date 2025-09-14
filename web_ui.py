import uasyncio as asyncio

import timetable as tt
from display_board import render_board


# ---------- Minimal HTTP helpers ----------
async def read_request(reader):
    """Return (method, path, headers_dict, body_bytes)"""
    # Read request line + headers
    raw = b""
    try:
        raw = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), 2)
    except Exception:
        # fallback: read whatever is there
        chunk = await asyncio.wait_for(reader.read(1024), 1)
        raw += chunk
    parts = raw.split(b"\r\n\r\n", 1)
    head = parts[0].decode("utf-8", "ignore")
    body = parts[1] if len(parts) == 2 else b""

    lines = head.split("\r\n")
    req = lines[0].split()
    method = req[0] if len(req) > 0 else ""
    path = req[1] if len(req) > 1 else "/"
    # headers
    hdrs = {}
    for ln in lines[1:]:
        if ":" in ln:
            k, v = ln.split(":", 1)
            hdrs[k.strip().lower()] = v.strip()

    # read remaining body if Content-Length indicates more
    clen = int(hdrs.get("content-length", "0") or "0")
    if clen > len(body):
        remaining = clen - len(body)
        while remaining > 0:
            chunk = await reader.read(remaining)
            if not chunk:
                break
            body += chunk
            remaining -= len(chunk)
    return method, path, hdrs, body


def _urldecode(s):
    s = s.replace("+", " ")
    out = bytearray()
    i = 0
    bs = s.encode() if isinstance(s, str) else s
    while i < len(bs):
        c = bs[i]
        if c == 37 and i + 2 < len(bs):  # '%'
            try:
                out.append(int(bs[i + 1:i + 3].decode(), 16))
                i += 3
                continue
            except Exception:
                pass
        out.append(c)
        i += 1
    return out.decode("utf-8", "ignore")


def parse_form(body_bytes):
    """Return dict[str, list[str]] supporting repeated keys like time[], train[]"""
    qs = body_bytes.decode("utf-8", "ignore")
    out = {}
    if not qs:
        return out
    for pair in qs.split("&"):
        if not pair:
            continue
        if "=" in pair:
            k, v = pair.split("=", 1)
        else:
            k, v = pair, ""
            
        k = _urldecode(k)
        v = _urldecode(v)
        out.setdefault(k, []).append(v)
    return out


def http_response(status, headers, body_bytes):
    head = [status]
    for k, v in headers.items():
        head.append(f"{k}: {v}")
    head.append("")  # blank line
    head_joined = "\r\n".join(head).encode()
    return head_joined + b"\r\n" + body_bytes


# ---------- HTML rendering ----------
def render_page():
    # Build table rows from ROUTES (backing structure)
    def esc(x):
        return (x or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    rows_html = []
    for i, row in enumerate(tt.ROUTES):
        rows_html.append(f"""
<tr>
  <td><input name="train[]"  value="{esc(row.get('train', ''))}"  required></td>
  <td><input name="via[]"    value="{esc(row.get('via', ''))}"></td>
  <td><input name="dest[]"   value="{esc(row.get('dest', ''))}"></td>
  <td><input name="frequency[]"  value="{esc(str(row.get('frequency', '')))}" style="width:6em" required></td>
  <td><input name="track[]"  value="{esc(str(row.get('track', '')))}" style="width:4em"></td>
  <td><input name="offset[]"  value="{esc(str(row.get('offset', '')))}" style="width:6em"></td>
  <td><button type="button" class="del">Delete</button></td>
</tr>""")
    rows = "\n".join(rows_html) or """
<tr>
  <td><input name="train[]" required></td>
  <td><input name="via[]"></td>
  <td><input name="dest[]"></td>
  <td><input name="frequency[]" style="width:6em" required></td>
  <td><input name="track[]" style="width:4em"></td>
  <td><button type="button" class="del">Delete</button></td>
</tr>
"""
    html = f"""<!doctype html><meta charset="utf-8"><title>Train Board</title>
<style>
  body{{font:16px/1.4 system-ui;margin:2rem;}}
  table{{border-collapse:collapse;width:100%;max-width:900px}}
  th,td{{border:1px solid #ccc;padding:.4rem;vertical-align:top}}
  thead th{{background:#f5f5f5}}
  input{{width:100%}}
  .actions{{margin-top:1rem;display:flex;gap:1rem}}
</style>
<h1>Train Board Routes</h1>
<form method="POST" action="/save">
  <table id="tt">
    <thead><tr>
      <th>Train</th><th>Via</th><th>Destination</th><th>Frequency (min)</th><th>Track</th><th>Offset (min)</th><th></th>
    </tr></thead>
    <tbody>
      {rows}
    </tbody>
  </table>
  <div class="actions">
    <button type="button" id="add">Add row</button>
    <button type="submit">Save</button>
  </div>
</form>
<script>
  const tbody = document.querySelector('#tt tbody');
  function mkRow() {{
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><input name="train[]" required></td>
      <td><input name="via[]"></td>
      <td><input name="dest[]"></td>
      <td><input name="frequency[]" style="width:6em" required></td>
      <td><input name="track[]" style="width:4em"></td>
      <td><input name="offset[]" style="width:6em"></td>
      <td><button type="button" class="del">Delete</button></td>`;
    return tr;
  }}
  document.getElementById('add').addEventListener('click', () => {{
    tbody.appendChild(mkRow());
  }});
  tbody.addEventListener('click', (e) => {{
    if (e.target.classList.contains('del')) {{
      const tr = e.target.closest('tr');
      tr.parentNode.removeChild(tr);
    }}
  }});
</script>"""
    return html.encode()


def create_handler(display, fg_pen, bg_pen):
    async def handle(reader, writer):
        try:
            method, path, headers, body = await read_request(reader)

            if method == "GET" and (path == "/" or path.startswith("/index")):
                body_bytes = render_page()
                resp = http_response(
                    "HTTP/1.1 200 OK",
                    {
                        "Content-Type": "text/html; charset=utf-8",
                        "Connection": "close",
                        "Content-Length": str(len(body_bytes)),
                    },
                    body_bytes,
                )
                await writer.awrite(resp)

            elif method == "POST" and path.startswith("/save"):
                # Parse and update routes, then regenerate timetable
                form = parse_form(body)
                trains = form.get("train[]", [])
                vias = form.get("via[]", [])
                dests = form.get("dest[]", [])
                freqs = form.get("frequency[]", [])
                tracks = form.get("track[]", [])
                offsets = form.get("offset[]", [])
                n = min(len(trains), len(vias), len(dests), len(freqs), len(tracks), len(offsets))
                routes = []
                for i in range(n):
                    tr = trains[i].strip()
                    vi = vias[i].strip()
                    de = dests[i].strip()
                    fr_raw = freqs[i].strip()
                    tk = tracks[i].strip()
                    off_raw = offsets[i].strip()
                    if not (tr or vi or de or fr_raw):
                        continue
                    try:
                        fr = int(fr_raw)
                    except Exception:
                        fr = 60
                    if fr <= 0:
                        fr = 60
                    try:
                        off = int(off_raw)
                    except Exception:
                        off = 0
                    if off < 0:
                        off = 0
                    routes.append({
                        "train": tr,
                        "via": vi,
                        "dest": de,
                        "frequency": fr,
                        "track": tk,
                        "offset": off,
                    })
                # Update globals
                tt.ROUTES = routes
                # Regenerate a small upcoming window from midnight for preview
                tt.TIMETABLE = tt.generate_timetable(tt.ROUTES, 0, 20)
                render_board(display, tt.TIMETABLE, fg_pen, bg_pen)

                # 303 redirect back to GET /
                resp = http_response(
                    "HTTP/1.1 303 See Other",
                    {
                        "Location": "/",
                        "Connection": "close",
                        "Content-Length": "0",
                    },
                    b"",
                )
                await writer.awrite(resp)

            else:
                # 404
                body_bytes = b"Not Found"
                resp = http_response(
                    "HTTP/1.1 404 Not Found",
                    {"Content-Type": "text/plain; charset=utf-8", "Connection": "close",
                     "Content-Length": str(len(body_bytes))},
                    body_bytes,
                )
                await writer.awrite(resp)

        finally:
            try:
                await writer.aclose()
            except Exception:
                pass

    return handle


