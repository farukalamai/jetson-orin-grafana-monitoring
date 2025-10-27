# Add Grafana GPG key
sudo mkdir -p /etc/apt/keyrings/
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null

# Add repository
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee /etc/apt/sources.list.d/grafana.list

# Update and install
sudo apt-get update
sudo apt-get install -y grafana

# Install required plugin
sudo grafana-cli plugins install marcusolsson-dynamictext-panel

# Configure Grafana
sudo nano /etc/grafana/grafana.ini

# Find and modify these lines (remove the ; to uncomment):
[server]
http_addr = 0.0.0.0
http_port = 3000