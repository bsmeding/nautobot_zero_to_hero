#!/usr/bin/env bash
set -euo pipefail

# Detect if running in WSL
IS_WSL=false
if grep -qi microsoft /proc/version 2>/dev/null; then
    IS_WSL=true
fi

# Configuration options
# In WSL: Desktop disabled by default (requires explicit INSTALL_DESKTOP=true)
# In native Linux: Desktop disabled by default (requires explicit INSTALL_DESKTOP=true)
INSTALL_DESKTOP="${INSTALL_DESKTOP:-false}"

echo "=========================================="
echo " Nautobot Lab Installation Script"
echo "=========================================="
echo ""
echo "Environment:"
if [ "$IS_WSL" = "true" ]; then
    echo "  Running in: WSL (Windows Subsystem for Linux)"
else
    echo "  Running in: Native Linux"
fi
echo ""
echo "Options:"
echo "  INSTALL_DESKTOP=${INSTALL_DESKTOP}"
echo ""
if [ "$IS_WSL" = "true" ]; then
    echo "⚠️  WSL DETECTED: Desktop environment disabled by default"
    echo "  - WSL works best without a desktop environment"
    echo "  - Use WSL to run Docker/Containerlab, access via Windows browser"
    echo "  - To force desktop install: INSTALL_DESKTOP=true bash install.sh"
    echo ""
fi
echo "Usage:"
echo "  bash install.sh                          # Standard installation (no desktop)"
echo "  INSTALL_DESKTOP=true bash install.sh     # Force install desktop + VS Code"
echo ""
echo "=========================================="
echo ""

# Safety check: Confirm desktop installation in WSL
if [ "$IS_WSL" = "true" ] && [ "$INSTALL_DESKTOP" = "true" ]; then
    echo "⚠️  WARNING: You are about to install desktop environment in WSL"
    echo "  This is not recommended and may cause login issues!"
    echo ""
    read -p "Are you sure you want to continue? [y/N]: " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    echo ""
fi

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

echo "[INFO] Checking if Docker is already installed..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo "  ✅ Docker already installed: $DOCKER_VERSION"
    
    # Check if docker compose is available
    if docker compose version &> /dev/null; then
        COMPOSE_VERSION=$(docker compose version)
        echo "  ✅ Docker Compose already installed: $COMPOSE_VERSION"
        SKIP_DOCKER_INSTALL=true
    else
        echo "  ⚠️  Docker installed but Docker Compose plugin missing"
        SKIP_DOCKER_INSTALL=false
    fi
else
    echo "  Docker not found - will install"
    SKIP_DOCKER_INSTALL=false
fi

if [ "$SKIP_DOCKER_INSTALL" = "true" ]; then
    echo "[INFO] Skipping Docker installation (already installed)"
    echo ""
else
    echo "[INFO] Detecting OS distribution..."
    # Detect if running Ubuntu or Debian
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VERSION_CODENAME=$VERSION_CODENAME
        echo "  Detected: $OS $VERSION_CODENAME"
    else
        echo "[ERROR] Cannot detect OS version"
        exit 1
    fi

# Set Docker repo based on OS
if [ "$OS" = "ubuntu" ]; then
    DOCKER_REPO_URL="https://download.docker.com/linux/ubuntu"
    DOCKER_GPG_URL="https://download.docker.com/linux/ubuntu/gpg"
    
    # Handle newer Ubuntu versions that might not have Docker packages yet
    # If noble (24.04) or newer, fall back to jammy (22.04)
    case "$VERSION_CODENAME" in
        noble|oracular)
            echo "  [WARNING] $VERSION_CODENAME may not have Docker packages yet"
            echo "  Falling back to Ubuntu 22.04 LTS (jammy) repository"
            VERSION_CODENAME="jammy"
            ;;
        *)
            echo "  Using native codename: $VERSION_CODENAME"
            ;;
    esac
    
elif [ "$OS" = "debian" ]; then
    DOCKER_REPO_URL="https://download.docker.com/linux/debian"
    DOCKER_GPG_URL="https://download.docker.com/linux/debian/gpg"
else
    echo "[WARNING] Unsupported OS: $OS, trying Ubuntu repository..."
    DOCKER_REPO_URL="https://download.docker.com/linux/ubuntu"
    DOCKER_GPG_URL="https://download.docker.com/linux/ubuntu/gpg"
    VERSION_CODENAME="jammy"  # Use LTS version as fallback
fi

echo "  Using repository: $DOCKER_REPO_URL"
echo "  Using codename: $VERSION_CODENAME"

echo "[INFO] Adding Docker's official GPG key..."
sudo mkdir -p /usr/share/keyrings

# Remove old key if exists to avoid overwrite warnings
if [ -f /usr/share/keyrings/docker.gpg ]; then
    echo "  Removing existing Docker GPG key..."
    sudo rm -f /usr/share/keyrings/docker.gpg
fi

curl -fsSL $DOCKER_GPG_URL | sudo gpg --dearmor -o /usr/share/keyrings/docker.gpg
sudo chmod a+r /usr/share/keyrings/docker.gpg
echo "  Docker GPG key added successfully"

echo "[INFO] Setting up Docker repository..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker.gpg] $DOCKER_REPO_URL \
  $VERSION_CODENAME stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

echo "  Created: /etc/apt/sources.list.d/docker.list"

echo "[INFO] Updating package lists..."
sudo apt-get update -y

# Check if packages are available
echo "  Checking package availability..."
if ! apt-cache policy docker-ce | grep -q "Candidate:" 2>/dev/null; then
    echo "[WARNING] Docker packages not found in apt repository!"
    echo "  Repository: $DOCKER_REPO_URL"
    echo "  Codename: $VERSION_CODENAME"
    echo ""
    echo "[INFO] Falling back to Docker's convenience script..."
    echo "  This will install the latest Docker version"
    
    # Use Docker's official convenience script
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
    
    echo "  ✅ Docker installed via convenience script"
else
    echo "  ✅ Docker packages found in repository"
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    echo "  Installed:"
    echo "    ✅ docker-ce (Docker Engine)"
    echo "    ✅ docker-ce-cli (Docker CLI)"
    echo "    ✅ containerd.io (Container runtime)"
    echo "    ✅ docker-buildx-plugin (Build plugin)"
    echo "    ✅ docker-compose-plugin (Compose V2 plugin)"
fi

    echo "[INFO] Verifying Docker installation..."
    docker --version
    docker compose version
fi  # End of SKIP_DOCKER_INSTALL check

echo "[INFO] Checking if Containerlab is already installed..."
if command -v containerlab &> /dev/null; then
    CLAB_VERSION=$(containerlab version | head -1)
    echo "  ✅ Containerlab already installed: $CLAB_VERSION"
    echo "[INFO] Skipping Containerlab installation"
else
    echo "  Containerlab not found - will install"
    echo "[INFO] Installing Containerlab..."
    bash -c "$(curl -sL https://get.containerlab.dev)"
    
    echo "[INFO] Verifying Containerlab installation..."
    containerlab version
fi

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

# Optional: Install desktop environment
if [ "$INSTALL_DESKTOP" = "true" ]; then
    echo ""
    echo "[INFO] Installing desktop environment..."
    echo "  This will install XFCE desktop environment (lightweight)"
    
    sudo apt-get install -y \
        xfce4 \
        xfce4-terminal \
        dbus-x11 \
        xdg-utils \
        x11-apps \
        firefox
    
    echo "[INFO] Desktop environment installed!"
    echo ""
    
    echo "[INFO] Configuring desktop for console boot (NEVER use graphical login)..."
    # Set system to boot to console (multi-user.target) instead of graphical login
    # This avoids "Failed to start session" issues and is better for lab environments
    sudo systemctl set-default multi-user.target
    
    # Stop and disable ALL display managers to prevent graphical login
    for dm in lightdm gdm gdm3 sddm xdm; do
        if systemctl list-unit-files | grep -q "^${dm}.service"; then
            if systemctl is-active $dm &>/dev/null; then
                sudo systemctl stop $dm
                echo "  Stopped $dm"
            fi
            if systemctl is-enabled $dm &>/dev/null; then
                sudo systemctl disable $dm
                echo "  Disabled $dm"
            fi
        fi
    done
    
    # Remove display manager packages to be absolutely sure
    sudo apt-get remove -y lightdm lightdm-gtk-greeter gdm3 2>/dev/null || true
    
    echo ""
    echo "  ✅ System configured for CONSOLE BOOT ONLY"
    echo "  ✅ No graphical login screen will appear"
    echo "  ✅ Login via text console, then start GUI apps manually"
    echo ""
    
    echo "[INFO] Installing Visual Studio Code..."
    # Install VS Code dependencies
    sudo apt-get install -y wget gpg apt-transport-https
    
    # Remove old Microsoft GPG key if exists
    if [ -f /etc/apt/keyrings/packages.microsoft.gpg ]; then
        echo "  Removing existing Microsoft GPG key..."
        sudo rm -f /etc/apt/keyrings/packages.microsoft.gpg
    fi
    
    # Download and install Microsoft GPG key
    sudo mkdir -p /etc/apt/keyrings
    wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
    sudo install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg
    rm packages.microsoft.gpg
    echo "  Microsoft GPG key added successfully"
    
    # Add VS Code repository
    echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" | sudo tee /etc/apt/sources.list.d/vscode.list > /dev/null
    
    # Update and install VS Code
    sudo apt-get update -y
    sudo apt-get install -y code
    
    echo "[INFO] Visual Studio Code installed!"
    echo ""
    echo "[INFO] Configuring ssh:// protocol handler..."
    
    # Create desktop file for ssh:// protocol handler
    mkdir -p ~/.local/share/applications
    
    cat > ~/.local/share/applications/ssh-handler.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=SSH Protocol Handler
Exec=xfce4-terminal -e "bash -c 'ssh %u; exec bash'"
Terminal=false
MimeType=x-scheme-handler/ssh
NoDisplay=true
EOF
    
    # Update desktop database
    update-desktop-database ~/.local/share/applications/
    
    # Set as default handler for ssh:// links
    xdg-mime default ssh-handler.desktop x-scheme-handler/ssh
    
    echo "[INFO] ssh:// protocol handler configured!"
    echo "  You can now click ssh://admin@access1 links to open SSH in terminal"
    echo ""
    echo "[INFO] Desktop Environment Usage:"
    echo "  System configured to boot to CONSOLE (no graphical login screen)"
    echo "  This avoids login issues and is better for lab environments"
    echo ""
    echo "  After reboot/login via console, launch GUI apps:"
    echo "    code .                              # VS Code"
    echo "    firefox http://nautobotlab.dev:8080 &  # Browser"
    echo "    xfce4-terminal &                    # Terminal"
    echo ""
    echo "  Or use the helper script:"
    echo "    bash start_desktop.sh"
    echo ""
else
    echo ""
    echo "[INFO] Desktop environment not installed (INSTALL_DESKTOP=false)"
    echo "  To install later, run: INSTALL_DESKTOP=true bash install.sh"
    echo ""
fi

echo "[DONE] Installation complete!"
echo ""
echo "Summary:"
echo "  ✅ Docker and Docker Compose installed"
echo "  ✅ Containerlab installed"
echo "  ✅ /etc/hosts updated with lab devices"
if [ "$INSTALL_DESKTOP" = "true" ]; then
    echo "  ✅ Desktop environment (XFCE) installed"
    echo "  ✅ Visual Studio Code installed"
    echo "  ✅ Firefox browser installed"
    echo "  ✅ ssh:// protocol handler configured"
fi
echo ""
echo "Next steps:"
echo "  1. Log out and back in (or run: newgrp docker)"
echo "  2. Deploy containerlab: cd containerlab && sudo containerlab deploy -t nautobot-lab.clab.yml"
echo "  3. Start Nautobot: docker compose up -d"
if [ "$INSTALL_DESKTOP" = "true" ]; then
    echo "  4. Open VS Code: code ."
    echo "  5. Open Nautobot: firefox http://nautobotlab.dev:8080"
fi
echo ""
