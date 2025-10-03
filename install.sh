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

echo "[DONE] Installation complete: Docker, Docker Compose, and Containerlab are installed."
