# Download Prometheus (ARM64 version for Jetson)
cd /tmp
wget https://github.com/prometheus/prometheus/releases/download/v2.47.0/prometheus-2.47.0.linux-arm64.tar.gz

# Extract
tar xvfz prometheus-2.47.0.linux-arm64.tar.gz

# Move to /opt
sudo mv prometheus-2.47.0.linux-arm64 /opt/prometheus

# Create Prometheus user
sudo useradd --no-create-home --shell /bin/false prometheus

# Create directories
sudo mkdir -p /etc/prometheus
sudo mkdir -p /var/lib/prometheus

# Set ownership
sudo chown prometheus:prometheus /var/lib/prometheus