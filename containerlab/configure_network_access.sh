#!/bin/bash
# Configure network access for Nautobot to reach Containerlab devices

echo "Configuring network access for Nautobot to Containerlab devices..."

# Check if containerlab network exists
if docker network ls | grep -q "clab"; then
    echo "Containerlab network 'clab' found"
    
    # Get the containerlab network details
    CLAB_NETWORK=$(docker network ls | grep clab | awk '{print $1}')
    echo "Containerlab network ID: $CLAB_NETWORK"
    
    # Check if Nautobot is running in Docker
    if docker ps | grep -q nautobot; then
        echo "Nautobot container found"
        
        # Get Nautobot container name/ID
        NAUTOBOT_CONTAINER=$(docker ps | grep nautobot | awk '{print $1}')
        echo "Nautobot container: $NAUTOBOT_CONTAINER"
        
        # Connect Nautobot to containerlab network
        echo "Connecting Nautobot to containerlab network..."
        docker network connect clab $NAUTOBOT_CONTAINER
        
        echo "✅ Nautobot connected to containerlab network"
        echo "Nautobot should now be able to reach devices at 172.20.20.x"
        
    else
        echo "❌ Nautobot container not found"
        echo "Make sure Nautobot is running in Docker"
    fi
    
else
    echo "❌ Containerlab network 'clab' not found"
    echo "Please start the containerlab topology first:"
    echo "  cd /mnt/c/Users/BartSmeding/NetDevOps/Workspace/NAUTOBOT_JOBS/nautobot_zero_to_hero/containerlab"
    echo "  containerlab deploy -t nautobot-lab.clab.yml"
fi

echo ""
echo "To test connectivity, you can run:"
echo "  docker exec -it <nautobot-container> ping 172.20.20.11"

