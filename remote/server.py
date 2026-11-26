#!/usr/bin/env python3
"""Moto E home remote: a tiny local web server for Tinxy lights and a Samsung TV.

Runs inside Termux on the phone. Open http://127.0.0.1:8765 in the phone's browser.

Only the Python standard library is required, plus `websocket-client`
(pip install websocket-client) for the Samsung TV.
"""
import base64
import json
import os
import socket
import ssl
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "config.json")
TOKEN_PATH = os.path.join(HERE, "tv_token.txt")
STATIC_DIR = os.path.join(HERE, "static")

TINXY_API = "https://backend.tinxy.in/"
APP_NAME = "MotoE Remote"


def load_config():
    if not os.path.exists(CONFIG_PATH):
        sys.exit("config.json missing: copy config.example.json to config.json and fill it in.")
    with open(CONFIG_PATH) as f:
        return json.load(f)


CONFIG = load_config()


# ---------------------------------------------------------------- Tinxy (cloud API)

def tinxy_request(path, payload=None, method="GET"):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        TINXY_API + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Bearer " + CONFIG["tinxy_api_key"],
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode() or "null"
        return json.loads(body)


def tinxy_list():
    """Flatten Tinxy devices into one entry per switch (node)."""
    raw = tinxy_request("v2/devices/")
    hidden = set(CONFIG.get("hide_tinxy", []))
    out = []
    for dev in raw:
        nodes = dev.get("devices") or [dev.get("name", "Switch")]
        for i, node_name in enumerate(nodes):
            key = "%s:%d" % (dev["_id"], i + 1)
            if key in hidden:
                continue
            label = node_name if len(nodes) > 1 else dev.get("name", node_name)
            out.append({"id": dev["_id"], "number": i + 1, "name": label, "room": dev.get("name", "")})
    return out


def tinxy_state(dev_id, number):
    """True/False for one switch, or None if Tinxy doesn't say. Best effort."""
    try:
        st = tinxy_request("v2/devices/%s/state?deviceNumber=%d" % (dev_id, int(number)))
        if isinstance(st, list) and st:
            st = st[0]
        if isinstance(st, dict) and "state" in st:
            return st["state"] in ("ON", 1, True)
    except Exception as exc:  # state is optional; buttons still work without it
        print("tinxy state error:", exc)
    return None


def tinxy_set(dev_id, number, on):
    payload = {"request": {"state": 1 if on else 0}, "deviceNumber": int(number)}
    return tinxy_request("v2/devices/%s/toggle" % dev_id, payload=payload, method="POST")


# ---------------------------------------------------------------- Samsung TV (Tizen 2016+)

def _tv_token():
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH) as f:
            return f.read().strip()
    return ""


def tv_send_key(key):
    """Send one remote key, e.g. KEY_VOLUP. First use shows an Allow prompt on the TV."""
    import websocket  # from websocket-client

    ip = CONFIG["tv_ip"]
    name = base64.b64encode(APP_NAME.encode()).decode()
    attempts = [
        ("wss://%s:8002/api/v2/channels/samsung.remote.control?name=%s" % (ip, name), True),
        ("ws://%s:8001/api/v2/channels/samsung.remote.control?name=%s" % (ip, name), False),
    ]
    last_err = None
    for url, secure in attempts:
        token = _tv_token()
        if secure and token:
            url += "&token=" + token
        try:
            ws = websocket.create_connection(
                url,
                timeout=8,
                # The TV uses a self-signed certificate; this only talks to the TV on the home LAN.
                sslopt={"cert_reqs": ssl.CERT_NONE, "check_hostname": False} if secure else None,
            )
            # First connection shows an Allow prompt on the TV; give the user time to accept it.
            ws.settimeout(30)
            try:
                hello = json.loads(ws.recv())
            except websocket.WebSocketProtocolException:
                # The TV closes with code 1005 / "notack" when this remote is not allowed.
                raise RuntimeError("TV rejected the connection (Allow prompt denied or missed)")
            if hello.get("event") != "ms.channel.connect":
                raise RuntimeError("TV refused: %s" % hello.get("event"))
            new_token = (hello.get("data") or {}).get("token")
            if new_token:
                with open(TOKEN_PATH, "w") as f:
                    f.write(str(new_token))
            ws.send(json.dumps({
                "method": "ms.remote.control",
                "params": {"Cmd": "Click", "DataOfCmd": key, "Option": "false",
                           "TypeOfRemote": "SendRemoteKey"},
            }))
            ws.close()
            return {"ok": True, "via": "8002" if secure else "8001"}
        except Exception as exc:
            last_err = exc
    raise RuntimeError("TV not reachable: %s" % last_err)


def tv_power_on():
    """Wake-on-LAN magic packet. Needs the TV setting 'Power On with Mobile' enabled."""
    mac = CONFIG["tv_mac"].replace(":", "").replace("-", "")
    packet = bytes.fromhex("FF" * 6 + mac * 16)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.sendto(packet, (CONFIG.get("broadcast_ip", "255.255.255.255"), 9))
    s.close()
    return {"ok": True}


def tv_is_on():
    try:
        urllib.request.urlopen("http://%s:8001/api/v2/" % CONFIG["tv_ip"], timeout=2).read()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------- HTTP server

ALLOWED_KEYS = {
    "KEY_POWER", "KEY_VOLUP", "KEY_VOLDOWN", "KEY_MUTE", "KEY_CHUP", "KEY_CHDOWN",
    "KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT", "KEY_ENTER", "KEY_RETURN",
    "KEY_HOME", "KEY_SOURCE", "KEY_PLAY", "KEY_PAUSE", "KEY_MENU",
}


class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            with open(os.path.join(STATIC_DIR, "index.html"), "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/state":
            try:
                lights = tinxy_list()
                for l in lights:
                    l["on"] = tinxy_state(l["id"], l["number"])
                tinxy_err = None
            except Exception as exc:
                lights, tinxy_err = [], str(exc)
            self._json({"lights": lights, "tinxy_error": tinxy_err, "tv_on": tv_is_on()})
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        try:
            data = self._body()
            if self.path == "/api/light":
                self._json(tinxy_set(data["id"], data["number"], bool(data["on"])))
            elif self.path == "/api/tv/key":
                if data.get("key") not in ALLOWED_KEYS:
                    return self._json({"error": "unknown key"}, 400)
                self._json(tv_send_key(data["key"]))
            elif self.path == "/api/tv/on":
                self._json(tv_power_on())
            else:
                self._json({"error": "not found"}, 404)
        except urllib.error.HTTPError as exc:
            self._json({"error": "Tinxy HTTP %s" % exc.code}, 502)
        except Exception as exc:
            self._json({"error": str(exc)}, 502)

    def log_message(self, fmt, *args):
        pass  # keep Termux quiet


def main():
    host = CONFIG.get("listen", "127.0.0.1")  # phone-only by default
    port = int(CONFIG.get("port", 8765))
    print("Moto E remote on http://%s:%d" % (host, port))
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
