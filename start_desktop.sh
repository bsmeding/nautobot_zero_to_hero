#!/usr/bin/env bash
# Start XFCE Desktop in WSL
# Workaround for "Failed to start session" issues

echo "=========================================="
echo " Start Desktop Environment (WSL)"
echo "=========================================="
echo ""

# Check if in WSL
if ! grep -qi microsoft /proc/version; then
    echo "[INFO] Not running in WSL - you can start desktop normally"
    echo "  Run: startxfce4"
    exit 0
fi

echo "[INFO] Detected WSL environment"
echo ""

# Check if XFCE is installed
if ! command -v startxfce4 &> /dev/null; then
    echo "[ERROR] XFCE not installed!"
    echo "  Install with: INSTALL_DESKTOP=true bash install.sh"
    exit 1
fi

# Method 1: WSLg (Windows 11 / Updated Windows 10)
echo "Choose startup method:"
echo ""
echo "1) WSLg (Recommended - Windows 11 or updated Windows 10)"
echo "   - Native GUI support, no X server needed"
echo "   - Best performance and integration"
echo ""
echo "2) VcXsrv/X410 (X Server on Windows)"
echo "   - Requires X server installed on Windows"
echo "   - Full desktop environment"
echo ""
echo "3) Individual GUI Apps (No full desktop)"
echo "   - Launch apps directly (VS Code, Firefox, Terminal)"
echo "   - Works with WSLg"
echo ""
read -p "Select method [1/2/3]: " METHOD

case $METHOD in
    1)
        echo ""
        echo "[INFO] Starting with WSLg..."
        echo "  Checking WSLg support..."
        
        if [ -z "$DISPLAY" ]; then
            export DISPLAY=:0
            echo "  Set DISPLAY=:0"
        fi
        
        # Start dbus if not running
        if ! pgrep -x dbus-daemon > /dev/null; then
            echo "  Starting dbus..."
            sudo service dbus start 2>/dev/null || sudo /etc/init.d/dbus start 2>/dev/null
        fi
        
        echo ""
        echo "Starting XFCE4..."
        echo "  Note: If it fails, you may need to update Windows and WSL"
        echo ""
        startxfce4 &
        
        echo ""
        echo "Desktop starting in background..."
        echo "  To stop: pkill -f xfce4"
        ;;
        
    2)
        echo ""
        echo "[INFO] Starting with external X Server..."
        echo ""
        echo "Prerequisites:"
        echo "  1. Install VcXsrv or X410 on Windows"
        echo "  2. Start the X server"
        echo "  3. Configure to allow connections"
        echo ""
        read -p "Press Enter when X server is running..."
        
        # Get Windows host IP
        WINDOWS_IP=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')
        export DISPLAY=$WINDOWS_IP:0
        
        echo "  Set DISPLAY=$DISPLAY"
        
        # Start dbus
        if ! pgrep -x dbus-daemon > /dev/null; then
            echo "  Starting dbus..."
            sudo service dbus start 2>/dev/null || sudo /etc/init.d/dbus start 2>/dev/null
        fi
        
        echo "  Starting XFCE4..."
        startxfce4 &
        
        echo ""
        echo "Desktop starting..."
        ;;
        
    3)
        echo ""
        echo "[INFO] Starting individual GUI applications..."
        echo ""
        
        if [ -z "$DISPLAY" ]; then
            export DISPLAY=:0
        fi
        
        # Start dbus if needed
        if ! pgrep -x dbus-daemon > /dev/null; then
            sudo service dbus start 2>/dev/null || sudo /etc/init.d/dbus start 2>/dev/null
        fi
        
        echo "Available commands:"
        echo "  code .                 # VS Code in current directory"
        echo "  firefox &              # Firefox browser"
        echo "  xfce4-terminal &       # Terminal"
        echo "  thunar &               # File manager"
        echo ""
        echo "Example - Open Nautobot in Firefox:"
        echo "  firefox http://nautobotlab.dev:8080 &"
        echo ""
        echo "Example - Open VS Code:"
        echo "  code /mnt/c/Users/BartSmeding/NetDevOps/Workspace &"
        echo ""
        ;;
        
    *)
        echo "[ERROR] Invalid selection"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "[INFO] Desktop environment ready!"
echo "=========================================="
echo ""
echo "Useful commands:"
echo "  pkill -f xfce4              # Stop desktop"
echo "  code .                      # Open VS Code"
echo "  firefox <url> &             # Open browser"
echo "  xdg-open ssh://admin@access1  # Open SSH connection"
echo ""




