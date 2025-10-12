#!/usr/bin/env bash
# Update /etc/hosts file with Nautobot lab devices
# Run this script to add lab device hostnames to your /etc/hosts file

set -euo pipefail

echo "=========================================="
echo " Update /etc/hosts for Nautobot Lab"
echo "=========================================="
echo ""

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "[ERROR] This script must be run with sudo"
    echo "Usage: sudo bash update_hosts.sh"
    exit 1
fi

# Backup /etc/hosts
BACKUP_FILE="/etc/hosts.backup.$(date +%Y%m%d_%H%M%S)"
echo "[INFO] Creating backup of /etc/hosts..."
cp /etc/hosts "$BACKUP_FILE"
echo "  Backup saved to: $BACKUP_FILE"
echo ""

echo "[INFO] Adding Nautobot lab entries to /etc/hosts..."
echo ""

# Add Nautobot lab domain
if ! grep -q "nautobotlab.dev" /etc/hosts; then
    echo "127.0.0.1    nautobotlab.dev" | tee -a /etc/hosts > /dev/null
    echo "  ✅ Added: nautobotlab.dev -> 127.0.0.1"
else
    echo "  ℹ️  nautobotlab.dev already exists in /etc/hosts"
fi

# Add lab devices
declare -A LAB_DEVICES=(
    ["172.20.20.11"]="access1.lab access1"
    ["172.20.20.12"]="access2.lab access2"
    ["172.20.20.13"]="dist1.lab dist1"
    ["172.20.20.14"]="rtr1.lab rtr1"
    ["172.20.20.15"]="workstation1.lab workstation1"
    ["172.20.20.16"]="mgmt.lab mgmt"
)

echo ""
echo "Lab Devices:"
for ip in "${!LAB_DEVICES[@]}"; do
    hostname="${LAB_DEVICES[$ip]}"
    if ! grep -q "$ip.*$hostname" /etc/hosts; then
        echo "$ip    $hostname" | tee -a /etc/hosts > /dev/null
        echo "  ✅ Added: $hostname -> $ip"
    else
        echo "  ℹ️  $hostname already exists in /etc/hosts"
    fi
done

echo ""
echo "=========================================="
echo "[SUCCESS] /etc/hosts updated successfully!"
echo "=========================================="
echo ""

echo "Current lab entries in /etc/hosts:"
echo "---"
grep -E "(nautobotlab\.dev|\.lab|172\.20\.20\.)" /etc/hosts || echo "No lab entries found"
echo "---"
echo ""

# Update SSH config for easier access
echo "[INFO] Updating SSH config for lab devices..."

# Get the actual user's home directory (not root when using sudo)
if [ -n "$SUDO_USER" ]; then
    USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
    ACTUAL_USER="$SUDO_USER"
else
    USER_HOME="$HOME"
    ACTUAL_USER="$USER"
fi

SSH_CONFIG="${USER_HOME}/.ssh/config"
SSH_CONFIG_BAK="${SSH_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"

# Create .ssh directory if it doesn't exist
mkdir -p "${USER_HOME}/.ssh"
chmod 700 "${USER_HOME}/.ssh"
chown "${ACTUAL_USER}:${ACTUAL_USER}" "${USER_HOME}/.ssh"

# Backup existing SSH config if it exists
if [ -f "$SSH_CONFIG" ]; then
    cp "$SSH_CONFIG" "$SSH_CONFIG_BAK"
    chown "${ACTUAL_USER}:${ACTUAL_USER}" "$SSH_CONFIG_BAK"
    echo "  Backup saved to: $SSH_CONFIG_BAK"
fi

# Remove old lab entries if they exist
if [ -f "$SSH_CONFIG" ]; then
    sed -i.tmp '/# Nautobot Lab SSH Config - START/,/# Nautobot Lab SSH Config - END/d' "$SSH_CONFIG"
    rm -f "${SSH_CONFIG}.tmp"
fi

# Add new SSH config entries
cat >> "$SSH_CONFIG" << 'EOF'

# Nautobot Lab SSH Config - START
# Network devices (Arista/Nokia)
Host access1 access1.lab
    HostName 172.20.20.11
    User admin
    Port 22
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null

Host access2 access2.lab
    HostName 172.20.20.12
    User admin
    Port 22
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null

Host dist1 dist1.lab
    HostName 172.20.20.13
    User admin
    Port 22
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null

Host rtr1 rtr1.lab
    HostName 172.20.20.14
    User admin
    Port 22
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null

# Linux containers (Alpine)
Host workstation1 workstation1.lab
    HostName 172.20.20.15
    User root
    Port 22
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null

Host mgmt mgmt.lab
    HostName 172.20.20.16
    User root
    Port 22
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
# Nautobot Lab SSH Config - END
EOF

chmod 600 "$SSH_CONFIG"
chown "${ACTUAL_USER}:${ACTUAL_USER}" "$SSH_CONFIG"
echo "  ✅ SSH config updated successfully!"
echo "  Config file: $SSH_CONFIG"
echo ""

echo "You can now use hostnames to access devices:"
echo "  - Nautobot UI: http://nautobotlab.dev:8080"
echo "  - SSH to access1: ssh access1 (or: ssh access1.lab)"
echo "  - SSH to dist1: ssh dist1"
echo "  - SSH to workstation1: ssh workstation1"
echo "  - Ping device: ping access1"
echo ""
echo "To restore original files, run:"
echo "  sudo cp $BACKUP_FILE /etc/hosts"
echo "  cp $SSH_CONFIG_BAK ~/.ssh/config"
echo ""

