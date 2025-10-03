#!/bin/bash

echo "🔍 Validating Containerlab Lab Setup..."
echo "========================================"

# Check if containerlab is running
if ! containerlab inspect > /dev/null 2>&1; then
    echo "❌ Containerlab lab is not running"
    echo "   Run: containerlab deploy -t nautobot-lab.clab.yml"
    exit 1
fi

echo "✅ Containerlab lab is running"

# Test device connectivity
devices=("172.20.20.11:access1" "172.20.20.12:access2" "172.20.20.13:dist1" "172.20.20.14:rtr1")

echo ""
echo "🔗 Testing device connectivity..."
for device in "${devices[@]}"; do
    ip=$(echo $device | cut -d: -f1)
    name=$(echo $device | cut -d: -f2)
    
    if ping -c 1 -W 2 $ip > /dev/null 2>&1; then
        echo "✅ $name ($ip) is reachable"
    else
        echo "❌ $name ($ip) is not reachable"
    fi
done

echo ""
echo "🔑 Testing SSH access..."
for device in "${devices[@]}"; do
    ip=$(echo $device | cut -d: -f1)
    name=$(echo $device | cut -d: -f2)
    
    if timeout 5 ssh -o ConnectTimeout=3 -o StrictHostKeyChecking=no admin@$ip "show version" > /dev/null 2>&1; then
        echo "✅ $name SSH is working"
    else
        echo "❌ $name SSH is not working (use: docker exec -it clab-nautobot-lab-$name FastCli)"
    fi
done

echo ""
echo "🎯 Lab validation complete!"
echo ""
echo "📋 Quick access commands:"
echo "   docker exec -it clab-nautobot-lab-access1 FastCli"
echo "   docker exec -it clab-nautobot-lab-access2 FastCli"
echo "   docker exec -it clab-nautobot-lab-dist1 sr_cli"
echo "   docker exec -it clab-nautobot-lab-rtr1 sr_cli"
