#!/bin/bash

echo "Configuring containerlab devices for SSH access..."

# Function to configure Arista device
configure_arista() {
    local device=$1
    local ip=$2
    echo "Configuring $device with IP $ip"
    
    # Wait for device to be ready
    sleep 5
    
    # Configure via FastCli
    docker exec $device FastCli -c "enable" -c "configure" -c "interface Management1" -c "ip address $ip/24" -c "no shutdown" -c "exit" -c "management ssh" -c "no shutdown" -c "exit" -c "exit" || echo "Failed to configure $device"
}

# Function to configure Nokia device
configure_nokia() {
    local device=$1
    local ip=$2
    echo "Configuring $device with IP $ip"
    
    # Wait for device to be ready
    sleep 5
    
    # Configure via sr_cli
    docker exec $device sr_cli -c "enter candidate" -c "/system network-instance mgmt interface ethernet-1/1" -c "ipv4 address $ip/24" -c "admin-state enable" -c "commit stay" || echo "Failed to configure $device"
}

# Configure all devices
echo "Configuring Arista devices..."
configure_arista "clab-nautobot-lab-access1" "172.20.20.11"
configure_arista "clab-nautobot-lab-access2" "172.20.20.12"

echo "Configuring Nokia devices..."
configure_nokia "clab-nautobot-lab-dist1" "172.20.20.13"
configure_nokia "clab-nautobot-lab-rtr1" "172.20.20.14"

echo "Configuration complete!"
echo "Testing connectivity..."

# Test connectivity
for ip in 172.20.20.11 172.20.20.12 172.20.20.13 172.20.20.14; do
    echo "Testing $ip..."
    ping -c 1 $ip && echo "✓ $ip is reachable" || echo "✗ $ip is not reachable"
done

echo "SSH test:"
echo "ssh admin@172.20.20.11  # access1"
echo "ssh admin@172.20.20.12  # access2"
echo "ssh admin@172.20.20.13  # dist1"
echo "ssh admin@172.20.20.14  # rtr1"
