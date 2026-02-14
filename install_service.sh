#!/bin/bash

echo "Installing Radar Service..."

# 1. Copy the service file to the system directory
cp /root/retro-adsb-radar/radar.service /etc/systemd/system/

# 2. Set correct permissions (root read/write, others read-only)
chmod 644 /etc/systemd/system/radar.service

# 3. Reload the systemd daemon so it sees the new file
systemctl daemon-reload

# 4. Enable the service to start on boot
systemctl enable radar.service

# 5. Start the service immediately
systemctl restart radar.service

echo "Done. Service is active."
systemctl status radar.service
