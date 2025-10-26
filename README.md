# Jetson Orin NX Grafana Monitoring System

A complete monitoring solution for NVIDIA Jetson devices (Orin NX, Xavier, Nano) using Prometheus and Grafana. This system provides real-time monitoring of GPU, CPU, memory, temperature, power consumption, and more - accessible remotely via ZeroTier VPN.

[![Jetson Monitoring Dashboard](https://img.shields.io/badge/Jetson-Monitoring-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](https://www.jetson-ai-lab.com/)
[![Grafana](https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white)](https://github.com/grafana/grafana)
[![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)](https://github.com/prometheus/prometheus)


## 📊 Features

- **Real-time Monitoring**
  - GPU usage and frequency
  - CPU usage per core
  - RAM and SWAP memory
  - Temperature sensors (CPU, GPU, SOC)
  - Power consumption
  - Fan speed
  - Disk usage
  - System uptime

- **Remote Access**
  - Access dashboard from anywhere via ZeroTier VPN
  - No port forwarding required
  - Secure peer-to-peer connection

- **Auto-refresh Dashboard**
  - Configurable refresh intervals (5s, 10s, 30s, 1m)
  - Historical data visualization
  - Customizable time ranges

## 🛠️ System Requirements

- **Hardware**: NVIDIA Jetson Orin NX (also compatible with Xavier, Nano, TX series)
- **OS**: Ubuntu 20.04+ (JetPack 5.0+)
- **RAM**: At least 4GB available
- **Disk**: ~500MB for Prometheus, Grafana, and metrics storage
- **Network**: ZeroTier account (free for up to 100 devices)

## 📦 Components

1. **jetson-stats** - Python library for accessing Jetson metrics
2. **Prometheus Metrics Collector** - Custom exporter for jetson-stats
3. **Prometheus** - Time-series database for metrics storage
4. **Grafana** - Visualization and dashboard platform

## 🚀 Quick Start

### 1. Install Prerequisites

```bash
# Update system
sudo apt-get update

# Install Python dependencies
sudo pip3 install -U jetson-stats prometheus-client

# Reboot to activate jetson-stats
sudo reboot
```

### 2. Install Prometheus Metrics Collector

```bash
# Download the collector script
sudo curl -o /usr/local/bin/jetson_stats_prometheus_collector.py \
  https://raw.githubusercontent.com/YOUR_USERNAME/jetson-grafana-monitoring/main/jetson_stats_prometheus_collector.py

# Make it executable
sudo chmod +x /usr/local/bin/jetson_stats_prometheus_collector.py

# Create systemd service
sudo curl -o /etc/systemd/system/jetson_stats_prometheus_collector.service \
  https://raw.githubusercontent.com/YOUR_USERNAME/jetson-grafana-monitoring/main/jetson_stats_prometheus_collector.service

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable jetson_stats_prometheus_collector
sudo systemctl start jetson_stats_prometheus_collector
```

### 3. Install Prometheus

```bash
# Run the installation script
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/jetson-grafana-monitoring/main/install_prometheus.sh | bash
```

### 4. Install Grafana

```bash
# Run the installation script
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/jetson-grafana-monitoring/main/install_grafana.sh | bash
```

### 5. Configure ZeroTier (Optional but Recommended)

```bash
# Install ZeroTier
curl -s https://install.zerotier.com | sudo bash

# Join your network
sudo zerotier-cli join YOUR_NETWORK_ID

# Get your ZeroTier IP
sudo zerotier-cli listnetworks
```

### 6. Access Grafana

Open your browser and navigate to:
- **Local**: `http://localhost:3000`
- **ZeroTier**: `http://YOUR_ZEROTIER_IP:3000`

**Default credentials:**
- Username: `admin`
- Password: `admin`

### 7. Import Dashboard

1. In Grafana, go to **☰** → **Dashboards** → **Import**
2. Upload the `grafana-dashboard.json` file from this repository
3. Select your Prometheus data source
4. Click **Import**

## 📁 Repository Structure

```
jetson-grafana-monitoring/
├── README.md
├── LICENSE
├── .gitignore
├── docs/
│   ├── installation.md
│   ├── troubleshooting.md
│   └── screenshots/
├── scripts/
│   ├── jetson_stats_prometheus_collector.py
│   ├── install_prometheus.sh
│   ├── install_grafana.sh
│   └── uninstall.sh
├── config/
│   ├── prometheus.yml
│   ├── jetson_stats_prometheus_collector.service
│   └── prometheus.service
├── dashboards/
│   └── grafana-dashboard.json
└── examples/
    └── deepstream-integration/
```

## 🔧 Configuration

### Prometheus Configuration

Edit `/etc/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'jetson-orin-nx'
    static_configs:
      - targets: ['localhost:8000']
```

### Metrics Collector Configuration

The collector runs on port 8000 by default. To change:

```bash
sudo nano /etc/systemd/system/jetson_stats_prometheus_collector.service
```

Modify the `--port` argument in the `ExecStart` line.

## 📊 Metrics Exposed

| Metric Name | Description | Type |
|------------|-------------|------|
| `jetson_usage_cpu` | CPU usage percentage per core | Gauge |
| `jetson_usage_gpu` | GPU usage percentage | Gauge |
| `jetson_freq_gpu` | GPU frequency in MHz | Gauge |
| `jetson_usage_ram` | RAM usage in MB | Gauge |
| `jetson_usage_swap` | SWAP usage in MB | Gauge |
| `jetson_temperatures` | Temperature sensors in Celsius | Gauge |
| `jetson_power` | Power consumption in mW | Gauge |
| `jetson_fan_speed` | Fan speed percentage | Gauge |
| `jetson_disk_usage` | Disk usage in MB | Gauge |
| `jetson_uptime_seconds` | System uptime in seconds | Gauge |

## 🐛 Troubleshooting

### Service not starting

```bash
# Check service status
sudo systemctl status jetson_stats_prometheus_collector

# View logs
sudo journalctl -u jetson_stats_prometheus_collector -f

# Restart service
sudo systemctl restart jetson_stats_prometheus_collector
```

### Metrics not appearing in Grafana

```bash
# Test metrics endpoint
curl http://localhost:8000/metrics | grep jetson

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Verify Prometheus is scraping
curl 'http://localhost:9090/api/v1/query?query=jetson_usage_gpu'
```

### Firewall issues

```bash
# Check firewall status
sudo ufw status

# Allow necessary ports
sudo ufw allow 8000/tcp comment 'Jetson Metrics'
sudo ufw allow 9090/tcp comment 'Prometheus'
sudo ufw allow 3000/tcp comment 'Grafana'
```

See [docs/troubleshooting.md](docs/troubleshooting.md) for more details.

## 🔐 Security Considerations

1. **Change default Grafana password** immediately after first login
2. **Use ZeroTier** for remote access instead of exposing ports publicly
3. **Enable authentication** on Prometheus if exposed to network
4. **Keep services updated** regularly

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [jetson-stats](https://github.com/rbonghi/jetson_stats) by Raffaello Bonghi
- [Prometheus](https://prometheus.io/)
- [Grafana](https://grafana.com/)
- [ZeroTier](https://www.zerotier.com/)

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/jetson-grafana-monitoring/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YOUR_USERNAME/jetson-grafana-monitoring/discussions)

## ⭐ Star History

If you find this project useful, please consider giving it a star!

---

**Made with ❤️ for the Jetson Community**