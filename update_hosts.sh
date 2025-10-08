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
    ["172.20.20.15"]="ztp.lab ztp"
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

echo "You can now use hostnames to access devices:"
echo "  - Nautobot UI: http://nautobotlab.dev:8080"
echo "  - SSH to access1: ssh admin@access1.lab (or just: ssh admin@access1)"
echo "  - SSH to dist1: ssh admin@dist1.lab"
echo "  - Ping device: ping access1"
echo ""
echo "To restore original /etc/hosts, run:"
echo "  sudo cp $BACKUP_FILE /etc/hosts"
echo ""

