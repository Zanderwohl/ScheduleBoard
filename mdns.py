# Announce-only Bonjour for _http._tcp (no bind -> no EADDRINUSE)
import socket, uasyncio as asyncio

_MDNS_GRP = "224.0.0.251"
_MDNS_PORT = 5353

def _lab(s): return bytes([len(s)]) + s.encode()
def _q(name): return b"".join(_lab(p) for p in name.split(".")) + b"\x00"

def _fqdn(s):
    s = s if s.endswith(".") else s + "."
    return s

def build_http_announcement(instance, host_local, ip_bytes, port=80, ttl=120, txt_kv=None):
    """
    Returns one mDNS response containing:
      PTR: _http._tcp.local -> <instance>._http._tcp.local
      SRV: <instance>._http._tcp.local -> host_local:port
      TXT: (optional key=val list)
      A  : host_local -> ip_bytes
    """
    svc = "_http._tcp.local"
    inst = f"{instance}._http._tcp.local"
    host = _fqdn(host_local)

    # DNS header: QR=1, AA=1, 0 questions, 4 answers
    hdr = b"\x00\x00" + b"\x84\x00" + b"\x00\x00\x00\x04\x00\x00\x00\x00"

    # PTR (_http._tcp.local -> <instance>._http._tcp.local)
    ans = (
        _q(svc) + b"\x00\x0c\x00\x01" + ttl.to_bytes(4,"big") +
        len(_q(inst)).to_bytes(2,"big") + _q(inst)
    )

    # SRV (<instance> -> host:port), class IN|cache-flush (0x8001)
    srv_rdata = b"\x00\x00\x00\x00" + port.to_bytes(2,"big") + _q(host)
    ans += (
        _q(inst) + b"\x00\x21\x80\x01" + ttl.to_bytes(4,"big") +
        len(srv_rdata).to_bytes(2,"big") + srv_rdata
    )

    # TXT (optional), class IN|cache-flush
    txt = b""
    if txt_kv:
        for k, v in txt_kv.items():
            kv = f"{k}={v}".encode()
            txt += bytes([len(kv)]) + kv
    ans += _q(inst) + b"\x00\x10\x80\x01" + ttl.to_bytes(4,"big") + len(txt).to_bytes(2,"big") + txt

    # A (host_local -> ip), class IN|cache-flush
    a = _q(host) + b"\x00\x01\x80\x01" + ttl.to_bytes(4,"big") + b"\x00\x04" + bytes(ip_bytes)

    return hdr + ans + a

async def announce_http(instance, hostname_local, ip_bytes, port=80, interval=60, burst=3, burst_gap=1):
    """
    Periodically multicast the service announcement. Sends a small burst on startup
    for fast discovery, then every `interval` seconds.
    """
    pkt = build_http_announcement(instance, hostname_local, ip_bytes, port=port, txt_kv={"path": "/"})
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # no bind
    # startup burst
    for _ in range(burst):
        try: s.sendto(pkt, (_MDNS_GRP, _MDNS_PORT))
        except Exception: pass
        await asyncio.sleep(burst_gap)
    # steady-state announce
    while True:
        try: s.sendto(pkt, (_MDNS_GRP, _MDNS_PORT))
        except Exception: pass
        await asyncio.sleep(interval)
