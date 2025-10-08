#!/bin/bash

# Script to get nautobot_config.py and jobs from container if they don't exist locally

CONFIG_DIR="./config"
CONFIG_FILE="$CONFIG_DIR/nautobot_config.py"
JOBS_DIR="./jobs"

echo "Setting up Nautobot configuration and jobs..."

# Create directories
mkdir -p "$CONFIG_DIR"
mkdir -p "$JOBS_DIR"

# Check if config file exists locally
if [ ! -f "$CONFIG_FILE" ]; then
    echo "nautobot_config.py not found locally."
    echo "Creating a minimal docker compose file to get config..."
    
    # Create a minimal docker compose file for getting config
    cat > docker compose.temp.yml << 'EOF'
services:
  nautobot:
    container_name: nautobot_temp
    image: bsmeding/nautobot:stable-py3.11
    environment:
      - NAUTOBOT_DEBUG=True
      - NAUTOBOT_DB_HOST=postgres
      - NAUTOBOT_DB_PORT=5432
      - NAUTOBOT_DB_NAME=nautobot
      - NAUTOBOT_DB_USER=nautobot
      - NAUTOBOT_DB_PASSWORD=nautobotpassword
      - NAUTOBOT_ALLOWED_HOSTS=*
      - NAUTOBOT_REDIS_HOST=redis
      - NAUTOBOT_REDIS_PORT=6379
      - NAUTOBOT_SUPERUSER_NAME=admin
      - NAUTOBOT_SUPERUSER_PASSWORD=admin
      - NAUTOBOT_SUPERUSER_API_TOKEN=1234567890abcde0987654321
      - NAUTOBOT_CREATE_SUPERUSER=true
      - NAUTOBOT_INSTALLATION_METRICS_ENABLED=false
      - NAUTOBOT_CONFIG=/opt/nautobot/nautobot_config.py
      - NAUTOBOT_CELERY_BROKER_URL=redis://redis:6379/0
    command: ["sleep", "infinity"]
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:13-alpine
    container_name: postgres_temp
    environment:
      POSTGRES_USER: nautobot
      POSTGRES_PASSWORD: nautobotpassword
      POSTGRES_DB: nautobot
    command: ["sleep", "infinity"]

  redis:
    image: redis:6
    container_name: redis_temp
    command: ["sleep", "infinity"]
EOF
    
    echo "Starting temporary containers..."
    docker compose -f docker compose.temp.yml up -d
    
    echo "Waiting for containers to be ready..."
    sleep 10
    
    # Check if nautobot container is running
    if docker ps --format "table {{.Names}}" | grep -q "nautobot_temp"; then
        echo "Copying nautobot_config.py from container..."
        docker cp nautobot_temp:/opt/nautobot/nautobot_config.py "$CONFIG_FILE"
        
        if [ -f "$CONFIG_FILE" ]; then
            echo "Successfully copied nautobot_config.py to $CONFIG_FILE"
        else
            echo "Error: Failed to copy nautobot_config.py from container"
            docker compose -f docker compose.temp.yml down
            rm -f docker compose.temp.yml
            exit 1
        fi
        
        echo "Copying jobs directory from container..."
        docker cp nautobot_temp:/opt/nautobot/jobs/ "$JOBS_DIR/"
        
        echo "Stopping temporary containers..."
        docker compose -f docker compose.temp.yml down
        
        echo "Removing temporary docker compose file..."
        rm -f docker compose.temp.yml
        
        echo "Configuration and jobs copied successfully!"
    else
        echo "Error: nautobot container is not running."
        docker compose -f docker compose.temp.yml down
        rm -f docker compose.temp.yml
        exit 1
    fi
else
    echo "nautobot_config.py already exists locally at $CONFIG_FILE"
fi

# Check if jobs directory is empty
if [ -z "$(ls -A $JOBS_DIR 2>/dev/null)" ]; then
    echo "Jobs directory is empty. Please run the script again to copy jobs."
else
    echo "Jobs directory already exists locally at $JOBS_DIR"
fi

echo "Setup complete! You can now start Nautobot with: docker compose up -d"
