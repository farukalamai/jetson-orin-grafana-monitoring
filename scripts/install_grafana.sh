#!/bin/bash
# Grafana Installation Script for Jetson Devices
# Compatible with ARM64 architecture

set -e

echo "=========================================="
echo "Grafana Installation for Jetson"
echo "=========================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 
   exit 1
fi

echo "[1/6] Adding Grafana GPG key..."
mkdir -p /etc/apt/keyrings/
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | tee /etc/apt/keyrings/grafana.gpg > /dev/null

echo "[2/6] Adding Grafana repository..."
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | tee /etc/apt/sources.list.d/grafana.list

echo "[3/6] Updating package list..."
apt-get update

echo "[4/6] Installing Grafana..."
apt-get install -y grafana

echo "[5/6] Installing required plugins..."
grafana-cli plugins install marcusolsson-dynamictext-panel

echo "[6/6] Configuring Grafana..."
# Backup original config
cp /etc/grafana/grafana.ini /etc/grafana/grafana.ini.backup

# Configure to listen on all interfaces
sed -i 's/;http_addr =/http_addr = 0.0.0.0/' /etc/grafana/grafana.ini
sed -i 's/;http_port = 3000/http_port = 3000/' /etc/grafana/grafana.ini

echo "Enabling and starting Grafana service..."
systemctl daemon-reload
systemctl enable grafana-server
systemctl start grafana-server

echo ""
echo "=========================================="
echo "✅ Grafana installation complete!"
echo "=========================================="
echo ""
echo "Service status:"
systemctl status grafana-server --no-pager -l
echo ""
echo "Access Grafana at: http://localhost:3000"
echo ""
echo "Default credentials:"
echo "  Username: admin"
echo "  Password: admin"
echo ""
echo "⚠️  IMPORTANT: Change the default password on first login!"
echo ""
echo "To view logs: sudo journalctl -u grafana-server -f"
echo "=========================================="