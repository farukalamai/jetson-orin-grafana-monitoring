#!/bin/bash
# Prometheus Installation Script for Jetson Devices
# Compatible with ARM64 architecture

set -e

echo "=========================================="
echo "Prometheus Installation for Jetson"
echo "=========================================="

# Variables
PROMETHEUS_VERSION="2.47.0"
PROMETHEUS_URL="https://github.com/prometheus/prometheus/releases/download/v${PROMETHEUS_VERSION}/prometheus-${PROMETHEUS_VERSION}.linux-arm64.tar.gz"
INSTALL_DIR="/opt/prometheus"
CONFIG_DIR="/etc/prometheus"
DATA_DIR="/var/lib/prometheus"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 
   exit 1
fi

echo "[1/7] Downloading Prometheus ${PROMETHEUS_VERSION}..."
cd /tmp
wget -q --show-progress ${PROMETHEUS_URL}

echo "[2/7] Extracting archive..."
tar xvfz prometheus-${PROMETHEUS_VERSION}.linux-arm64.tar.gz

echo "[3/7] Installing to ${INSTALL_DIR}..."
mv prometheus-${PROMETHEUS_VERSION}.linux-arm64 ${INSTALL_DIR}

echo "[4/7] Creating Prometheus user..."
useradd --no-create-home --shell /bin/false prometheus || true

echo "[5/7] Creating directories..."
mkdir -p ${CONFIG_DIR}
mkdir -p ${DATA_DIR}
chown prometheus:prometheus ${DATA_DIR}

echo "[6/7] Creating configuration file..."
cat > ${CONFIG_DIR}/prometheus.yml <<EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'jetson-orin-nx'
    static_configs:
      - targets: ['localhost:8000']
        labels:
          instance: 'jetson-orin-nx'
          job: 'jetson-stats'
EOF

chown prometheus:prometheus ${CONFIG_DIR}/prometheus.yml

echo "[7/7] Creating systemd service..."
cat > /etc/systemd/system/prometheus.service <<EOF
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=${INSTALL_DIR}/prometheus \\
    --config.file=${CONFIG_DIR}/prometheus.yml \\
    --storage.tsdb.path=${DATA_DIR}/ \\
    --web.console.templates=${INSTALL_DIR}/consoles \\
    --web.console.libraries=${INSTALL_DIR}/console_libraries

Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "Enabling and starting Prometheus service..."
systemctl daemon-reload
systemctl enable prometheus
systemctl start prometheus

echo ""
echo "=========================================="
echo "✅ Prometheus installation complete!"
echo "=========================================="
echo ""
echo "Service status:"
systemctl status prometheus --no-pager -l
echo ""
echo "Access Prometheus at: http://localhost:9090"
echo "Check metrics: curl http://localhost:9090/-/healthy"
echo ""
echo "To view logs: sudo journalctl -u prometheus -f"
echo "=========================================="