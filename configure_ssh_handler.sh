#!/usr/bin/env bash
# Configure ssh:// protocol handler for WSL/Linux
# This allows clicking ssh://user@host links to open in terminal

set -euo pipefail

echo "=========================================="
echo " Configure SSH Protocol Handler"
echo "=========================================="
echo ""

# Check if running in WSL
if grep -qi microsoft /proc/version; then
    echo "[INFO] Detected WSL environment"
    IN_WSL=true
else
    echo "[INFO] Detected native Linux environment"
    IN_WSL=false
fi

# Check if a terminal emulator is installed
TERMINAL=""
if command -v xfce4-terminal &> /dev/null; then
    TERMINAL="xfce4-terminal"
elif command -v gnome-terminal &> /dev/null; then
    TERMINAL="gnome-terminal"
elif command -v konsole &> /dev/null; then
    TERMINAL="konsole"
elif command -v x-terminal-emulator &> /dev/null; then
    TERMINAL="x-terminal-emulator"
fi

if [ -z "$TERMINAL" ]; then
    echo "[ERROR] No terminal emulator found!"
    echo ""
    echo "Please install a terminal emulator first:"
    echo "  For XFCE: sudo apt-get install -y xfce4-terminal"
    echo "  For GNOME: sudo apt-get install -y gnome-terminal"
    echo "  For KDE: sudo apt-get install -y konsole"
    echo ""
    echo "Or install a desktop environment:"
    echo "  INSTALL_DESKTOP=true bash install.sh"
    exit 1
fi

echo "[INFO] Using terminal emulator: $TERMINAL"
echo ""

# Install xdg-utils if not present
if ! command -v xdg-mime &> /dev/null; then
    echo "[INFO] Installing xdg-utils..."
    sudo apt-get install -y xdg-utils
fi

# Create desktop file for ssh:// protocol handler
echo "[INFO] Creating ssh:// protocol handler..."
mkdir -p ~/.local/share/applications

# Create handler based on detected terminal
if [ "$TERMINAL" = "xfce4-terminal" ]; then
    cat > ~/.local/share/applications/ssh-handler.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=SSH Protocol Handler
Exec=xfce4-terminal -e "bash -c 'ssh %u; exec bash'"
Terminal=false
MimeType=x-scheme-handler/ssh
NoDisplay=true
EOF
elif [ "$TERMINAL" = "gnome-terminal" ]; then
    cat > ~/.local/share/applications/ssh-handler.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=SSH Protocol Handler
Exec=gnome-terminal -- bash -c 'ssh %u; exec bash'
Terminal=false
MimeType=x-scheme-handler/ssh
NoDisplay=true
EOF
elif [ "$TERMINAL" = "konsole" ]; then
    cat > ~/.local/share/applications/ssh-handler.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=SSH Protocol Handler
Exec=konsole -e bash -c 'ssh %u; exec bash'
Terminal=false
MimeType=x-scheme-handler/ssh
NoDisplay=true
EOF
else
    cat > ~/.local/share/applications/ssh-handler.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=SSH Protocol Handler
Exec=x-terminal-emulator -e bash -c 'ssh %u; exec bash'
Terminal=false
MimeType=x-scheme-handler/ssh
NoDisplay=true
EOF
fi

# Update desktop database
update-desktop-database ~/.local/share/applications/ 2>/dev/null || true

# Set as default handler for ssh:// links
xdg-mime default ssh-handler.desktop x-scheme-handler/ssh

# Verify configuration
DEFAULT_HANDLER=$(xdg-mime query default x-scheme-handler/ssh)

echo ""
echo "=========================================="
echo "[SUCCESS] SSH protocol handler configured!"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  Terminal: $TERMINAL"
echo "  Handler: $DEFAULT_HANDLER"
echo "  Protocol: ssh://"
echo ""
echo "Usage examples:"
echo "  - Click links like: ssh://admin@access1"
echo "  - Click links like: ssh://admin@172.20.20.11"
echo "  - Open from terminal: xdg-open ssh://admin@access1.lab"
echo ""
if [ "$IN_WSL" = true ]; then
    echo "WSL Note:"
    echo "  - Links will open in WSL terminal"
    echo "  - Works best with WSLg (GUI support in WSL2)"
    echo "  - Or use Windows Terminal with WSL integration"
fi
echo ""

