# Troubleshooting Guide

This guide covers common issues and their solutions when setting up Jetson Grafana Monitoring.

## Table of Contents
- [Service Issues](#service-issues)
- [Metrics Not Appearing](#metrics-not-appearing)
- [Grafana Connection Issues](#grafana-connection-issues)
- [ZeroTier Issues](#zerotier-issues)
- [Performance Issues](#performance-issues)

---

## Service Issues

### Jetson Stats Collector Not Starting

**Symptom**: Service fails to start or crashes immediately.

**Check logs**:
```bash
sudo journalctl -u jetson_stats_prometheus_collector -n 50
```

**Common causes**:

1. **jetson-stats not installed or not activated**
   ```bash
   # Install jetson-stats
   sudo pip3 install -U jetson-stats
   
   # Reboot to activate
   sudo reboot
   ```

2. **Permission issues with jtop socket**
   ```bash
   # Check socket exists
   ls -la /run/jtop.sock
   
   # Restart jtop service
   sudo systemctl restart jtop.service
   ```

3. **Port 8000 already in use**
   ```bash
   # Check what's using port 8000
   sudo lsof -i :8000
   
   # Change port in service file
   sudo nano /etc/systemd/system/jetson_stats_prometheus_collector.service
   # Modify: --port 8001
   
   # Reload and restart
   sudo systemctl daemon-reload
   sudo systemctl restart jetson_stats_prometheus_collector
   ```

### Prometheus Not Starting

**Check logs**:
```bash
sudo journalctl -u prometheus -n 50
```

**Common causes**:

1. **Configuration syntax error**
   ```bash
   # Validate config
   /opt/prometheus/promtool check config /etc/prometheus/prometheus.yml
   ```

2. **Permission issues**
   ```bash
   # Fix permissions
   sudo chown -R prometheus:prometheus /var/lib/prometheus
   sudo chown prometheus:prometheus /etc/prometheus/prometheus.yml
   ```

3. **Port 9090 already in use**
   ```bash
   sudo lsof -i :9090
   ```

### Grafana Not Starting

**Check logs**:
```bash
sudo journalctl -u grafana-server -n 50
```

**Common causes**:

1. **Port 3000 already in use**
   ```bash
   sudo lsof -i :3000
   ```

2. **Database corruption**
   ```bash
   # Backup and reset Grafana database
   sudo systemctl stop grafana-server
   sudo mv /var/lib/grafana/grafana.db /var/lib/grafana/grafana.db.backup
   sudo systemctl start grafana-server
   ```

---

## Metrics Not Appearing

### Prometheus Not Scraping Metrics

**Check Prometheus targets**:
1. Open: `http://localhost:9090/targets`
2. Look for your Jetson target - should show **UP** in green

**If target shows DOWN**:

```bash
# Test metrics endpoint manually
curl http://localhost:8000/metrics | head -n 20

# Check if collector is running
sudo systemctl status jetson_stats_prometheus_collector

# Test Prometheus can reach the endpoint
curl -v http://localhost:8000/metrics
```

### No Data in Grafana

**Verify Prometheus data source**:
1. In Grafana: **Configuration** → **Data Sources** → **Prometheus**
2. Click **Save & test**
3. Should see: ✅ "Successfully queried the Prometheus API"

**Test query manually**:
```bash
# Query Prometheus API directly
curl 'http://localhost:9090/api/v1/query?query=jetson_usage_gpu' | jq

# Should return data like:
# {"status":"success","data":{"resultType":"vector","result":[...]}}
```

**If query returns no data**:
```bash
# Check if metrics are being collected
curl http://localhost:8000/metrics | grep jetson_usage_gpu

# Check Prometheus scrape interval
grep scrape_interval /etc/prometheus/prometheus.yml

# Wait for at least one scrape cycle (default 15s)
```

### Partial Data Missing

**Some metrics showing, others not**:

1. Check which metrics are available:
   ```bash
   curl http://localhost:8000/metrics | grep "^jetson_" | cut -d'{' -f1 | sort -u
   ```

2. Verify jetson-stats is providing the data:
   ```bash
   python3 -c "from jtop import jtop; j = jtop(); j.start(); print(j.gpu); j.close()"
   ```

---

## Grafana Connection Issues

### Can't Access Grafana Web UI

**From local machine**:
```bash
# Test if Grafana is listening
curl http://localhost:3000/api/health

# Check Grafana is bound to correct interface
sudo netstat -tlnp | grep 3000

# Should show: 0.0.0.0:3000 (all interfaces)
```

**From remote machine via ZeroTier**:
```bash
# On Jetson, get ZeroTier IP
sudo zerotier-cli listnetworks

# From remote machine, test connectivity
ping JETSON_ZEROTIER_IP

# Test Grafana port
telnet JETSON_ZEROTIER_IP 3000
# or
nc -zv JETSON_ZEROTIER_IP 3000
```

### Firewall Blocking Access

```bash
# Check if UFW is active
sudo ufw status

# If active, allow Grafana
sudo ufw allow 3000/tcp

# For Prometheus
sudo ufw allow 9090/tcp

# For metrics collector
sudo ufw allow 8000/tcp

# Check iptables rules
sudo iptables -L -n | grep -E "3000|9090|8000"
```

### Can't Login to Grafana

**Forgot admin password**:
```bash
# Reset admin password
sudo grafana-cli admin reset-admin-password newpassword

# Restart Grafana
sudo systemctl restart grafana-server
```

---

## ZeroTier Issues

### Can't Connect to ZeroTier Network

```bash
# Check ZeroTier service status
sudo systemctl status zerotier-one

# Restart ZeroTier
sudo systemctl restart zerotier-one

# List networks
sudo zerotier-cli listnetworks

# Leave and rejoin network
sudo zerotier-cli leave NETWORK_ID
sudo zerotier-cli join NETWORK_ID
```

### ZeroTier Connected but Can't Access Services

1. **Check authorization**: Go to ZeroTier Central, ensure device is authorized
2. **Check managed IP is assigned**: `sudo zerotier-cli listnetworks` should show IP
3. **Test connectivity from another device**:
   ```bash
   ping JETSON_ZEROTIER_IP
   ```

---

## Performance Issues

### High CPU Usage

**Prometheus using too much CPU**:
```bash
# Check Prometheus metrics
curl http://localhost:9090/metrics | grep process_cpu

# Reduce scrape frequency in /etc/prometheus/prometheus.yml
# Change: scrape_interval: 30s (instead of 15s)

# Restart Prometheus
sudo systemctl restart prometheus
```

**Metrics collector using too much CPU**:
```bash
# Check collector process
top -p $(pgrep -f jetson_stats_prometheus_collector)

# Reduce collection frequency by modifying scrape interval in Prometheus config
```

### High Memory Usage

```bash
# Check Grafana memory usage
ps aux | grep grafana-server

# Check Prometheus memory usage  
ps aux | grep prometheus

# Configure Prometheus retention (in service file)
sudo nano /etc/systemd/system/prometheus.service

# Add to ExecStart:
--storage.tsdb.retention.time=7d \
--storage.tsdb.retention.size=1GB

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart prometheus
```

### Disk Space Issues

```bash
# Check Prometheus data size
du -sh /var/lib/prometheus

# Clean old Prometheus data
sudo systemctl stop prometheus
sudo rm -rf /var/lib/prometheus/*
sudo systemctl start prometheus

# Check Grafana data size
du -sh /var/lib/grafana
```

---

## Debug Commands Reference

### Service Status
```bash
# Check all services
sudo systemctl status jetson_stats_prometheus_collector
sudo systemctl status prometheus
sudo systemctl status grafana-server
sudo systemctl status zerotier-one
```

### View Logs
```bash
# Follow logs in real-time
sudo journalctl -u jetson_stats_prometheus_collector -f
sudo journalctl -u prometheus -f
sudo journalctl -u grafana-server -f

# View last 100 lines
sudo journalctl -u SERVICE_NAME -n 100
```

### Test Endpoints
```bash
# Metrics endpoint
curl http://localhost:8000/metrics

# Prometheus health
curl http://localhost:9090/-/healthy

# Prometheus targets
curl http://localhost:9090/api/v1/targets | jq

# Grafana health
curl http://localhost:3000/api/health

# Query Prometheus
curl 'http://localhost:9090/api/v1/query?query=jetson_usage_gpu'
```

### Network Diagnostics
```bash
# Check listening ports
sudo netstat -tlnp | grep -E "3000|8000|9090"

# Check if port is reachable
nc -zv localhost 8000
nc -zv localhost 9090
nc -zv localhost 3000

# Test from remote via ZeroTier
nc -zv JETSON_ZEROTIER_IP 3000
```

---

## Still Having Issues?

1. **Enable debug logging**:
   ```bash
   # For Prometheus
   sudo nano /etc/systemd/system/prometheus.service
   # Add: --log.level=debug
   
   # For Grafana
   sudo nano /etc/grafana/grafana.ini
   # Set: log_level = debug
   ```

2. **Collect diagnostic information**:
   ```bash
   # Create diagnostic report
   echo "=== System Info ===" > diagnostic.txt
   uname -a >> diagnostic.txt
   echo "" >> diagnostic.txt
   
   echo "=== Services Status ===" >> diagnostic.txt
   sudo systemctl status jetson_stats_prometheus_collector >> diagnostic.txt
   sudo systemctl status prometheus >> diagnostic.txt
   sudo systemctl status grafana-server >> diagnostic.txt
   echo "" >> diagnostic.txt
   
   echo "=== Listening Ports ===" >> diagnostic.txt
   sudo netstat -tlnp >> diagnostic.txt
   echo "" >> diagnostic.txt
   
   echo "=== Metrics Sample ===" >> diagnostic.txt
   curl -s http://localhost:8000/metrics | head -n 50 >> diagnostic.txt
   ```

3. **Open a GitHub issue** with your diagnostic information and specific error messages.

---

**Need more help?** Check the [GitHub Discussions](https://github.com/YOUR_USERNAME/jetson-grafana-monitoring/discussions) or open an [Issue](https://github.com/YOUR_USERNAME/jetson-grafana-monitoring/issues).