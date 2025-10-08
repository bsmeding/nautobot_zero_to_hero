#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Updating system..."
sudo apt-get update -y
sudo apt-get upgrade -y

echo "[INFO] Installing required packages..."
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common \
    iputils-ping \
    lsb-release \
    git

echo "[INFO] Adding Docker’s official GPG key..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker.gpg

echo "[INFO] Setting up Docker repository..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

echo "[INFO] Installing Docker Engine..."
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "[INFO] Verifying Docker installation..."
docker --version
docker compose version

echo "[INFO] Installing Containerlab..."
bash -c "$(curl -sL https://get.containerlab.dev)"

echo "[INFO] Verifying Containerlab installation..."
containerlab version

echo "[INFO] Adding current user to docker group..."
sudo usermod -aG docker $USER
echo ">>> You need to log out and back in (or run 'newgrp docker') for group changes to take effect."

echo "[INFO] Updating /etc/hosts file with lab devices..."
# Backup /etc/hosts
sudo cp /etc/hosts /etc/hosts.backup.$(date +%Y%m%d_%H%M%S)

# Add Nautobot lab domain
if ! grep -q "nautobotlab.dev" /etc/hosts; then
    echo "127.0.0.1    nautobotlab.dev" | sudo tee -a /etc/hosts > /dev/null
    echo "  Added: nautobotlab.dev -> 127.0.0.1"
else
    echo "  nautobotlab.dev already in /etc/hosts"
fi

# Add lab devices
declare -A LAB_DEVICES=(
    ["172.20.20.11"]="access1.lab access1"
    ["172.20.20.12"]="access2.lab access2"
    ["172.20.20.13"]="dist1.lab dist1"
    ["172.20.20.14"]="rtr1.lab rtr1"
    ["172.20.20.15"]="ztp.lab ztp"
    ["172.20.20.16"]="mgmt.lab mgmt"
)

for ip in "${!LAB_DEVICES[@]}"; do
    hostname="${LAB_DEVICES[$ip]}"
    if ! grep -q "$ip.*$hostname" /etc/hosts; then
        echo "$ip    $hostname" | sudo tee -a /etc/hosts > /dev/null
        echo "  Added: $hostname -> $ip"
    else
        echo "  $hostname already in /etc/hosts"
    fi
done

echo "[INFO] /etc/hosts updated successfully!"

echo "[DONE] Installation complete: Docker, Docker Compose, and Containerlab are installed."
