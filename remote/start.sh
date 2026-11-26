#!/data/data/com.termux/files/usr/bin/bash
# Start the home remote in Termux, keeping the CPU awake while it runs.
cd "$(dirname "$0")"
termux-wake-lock 2>/dev/null
exec python server.py
