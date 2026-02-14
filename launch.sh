#!/bin/bash
killall -9 Xorg 2>/dev/null
rm -f /tmp/.X0-lock

# Start X normally (No rotation requested)
Xorg :0 vt7 -nolisten tcp -nocursor &
sleep 5
export DISPLAY=:0

# Switch to the graphical terminal
chvt 7

# Run the app
cd /root/retro-adsb-radar
source venv/bin/activate
python3 main.py
