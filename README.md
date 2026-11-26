# Project Moto E

Repurposing a 2014 Moto E (XT1022, LineageOS 14.1) as a home remote, QR box tracker and cycling GPS logger.

- `remote/`: home remote for Tinxy lights and a Samsung TV (runs in Termux).
- `android/`: two tiny launcher apps, "Lights" and "TV", that open the remote pages full-screen (`build.sh`, no Gradle).
- `termux/start-remote`: Termux:Boot script that starts the server when the phone boots.
- `remote/static/clock.html`, `frame.html`, `stand.html`: minimal clock + Bangalore weather (Open-Meteo, no key), 60 s photo frame from `Pictures/Frame`, and stand mode (tap to choose clock or frame).
- `wallpapers/`: calm home and lock screen wallpapers (generated, no licence issues).
