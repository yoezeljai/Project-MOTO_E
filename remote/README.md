# Moto E home remote

A one-screen remote for **Tinxy** Wi‑Fi switches and a **Samsung Tizen TV** (tested design target: UA50MU6100, 2017).
It runs inside **Termux** on the phone (LineageOS 14.1 / Android 7.1) and is opened in the phone's browser.

```
browser on the phone ──► http://127.0.0.1:8765 ──► server.py (Termux)
                                                     ├─► Tinxy cloud API (lights)
                                                     └─► TV on home Wi‑Fi (WebSocket 8002/8001, Wake‑on‑LAN)
```

## One-time setup (in Termux)

```bash
pkg install -y python git
pip install websocket-client
git clone -b claude/project-thread-0k36jx https://github.com/yoezeljai/project-moto_e.git
cd project-moto_e/remote
cp config.example.json config.json
nano config.json        # paste the Tinxy API key, TV IP and TV MAC
```

`config.json` and `tv_token.txt` are git-ignored, so the key never leaves the phone.

- **Tinxy API key:** in the Tinxy app's settings (the same key the Home Assistant integration uses).
- **TV IP:** TV › Settings › General › Network › Network Status › IP Settings. Reserving it in the router stops it changing.
- **TV MAC:** same screen. Needed only for "Power on".
- **Turn TV on from the phone:** TV › Settings › General › Network › Expert Settings › **Power On with Mobile** → On.

## Run

```bash
./start.sh
```

Then open **http://127.0.0.1:8765** in the browser. The first TV button press shows an **Allow** prompt on the TV; accept it with the normal remote once.

## Notes

- Lights go through Tinxy's cloud, so they need internet. The TV is controlled locally.
- The server listens on `127.0.0.1` only (this phone). Set `"listen": "0.0.0.0"` to reach it from other devices on the LAN; there is no login, so only do that on a trusted network.
- Hide a switch from the screen by adding `"<deviceId>:<number>"` to `hide_tinxy`.
