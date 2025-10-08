# Installation Guide - Nautobot Zero to Hero Lab

## Quick Installation Options

### 🚀 Option 1: Full Automated Install (Recommended)

Install everything including Docker, Containerlab, and desktop environment:

```bash
INSTALL_DESKTOP=true bash install.sh
```

**Installs:**
- ✅ Docker & Docker Compose
- ✅ Containerlab
- ✅ XFCE Desktop Environment
- ✅ Visual Studio Code
- ✅ Firefox browser
- ✅ Terminal emulator (xfce4-terminal)
- ✅ ssh:// protocol handler
- ✅ Updates /etc/hosts with lab devices

**Best for:**
- WSL users who want GUI support
- Users who want clickable ssh:// links
- Developers who want VS Code in WSL
- First-time setup

---

### ⚡ Option 2: Headless Install (No Desktop)

Install just Docker and Containerlab without GUI:

```bash
bash install.sh
```

**Installs:**
- ✅ Docker & Docker Compose
- ✅ Containerlab
- ✅ Updates /etc/hosts with lab devices
- ❌ No desktop environment
- ❌ No ssh:// link handler

**Best for:**
- Server installations
- Users who prefer command-line only
- Minimal installations

---

### 🔧 Option 3: Add Desktop Later

If you already ran the headless install and want to add desktop:

```bash
INSTALL_DESKTOP=true bash install.sh
```

The script is idempotent - it will skip already installed components.

---

### 🎯 Option 4: Standalone Components

Install individual components separately:

#### Update /etc/hosts Only
```bash
sudo bash update_hosts.sh
```

#### Configure ssh:// Handler Only
```bash
bash configure_ssh_handler.sh
```
*Requires terminal emulator already installed*

---

## Installation Details

### What Gets Installed

#### Core Components (Always)
- **Docker Engine** - Container runtime
- **Docker Compose** - Multi-container orchestration
- **Containerlab** - Network lab platform
- **Git** - Version control
- **System utilities** - curl, ca-certificates, etc.

#### Desktop Environment (Optional)
- **XFCE4** - Lightweight desktop environment
- **xfce4-terminal** - Terminal emulator
- **Visual Studio Code** - Code editor/IDE
- **Firefox** - Web browser
- **dbus-x11** - Desktop communication
- **xdg-utils** - Desktop integration
- **x11-apps** - X11 utilities

#### Configuration Updates
- **/etc/hosts** - Lab device hostname mappings
- **ssh:// handler** - Protocol handler for clickable SSH links
- **Docker group** - Current user added for non-sudo access

### System Requirements

**Minimum:**
- Ubuntu 20.04+ or Debian 11+ (or WSL2 with these)
- 4 GB RAM
- 20 GB disk space
- Internet connection

**Recommended:**
- Ubuntu 22.04+ or Debian 12+ (or WSL2)
- 8 GB RAM
- 50 GB disk space
- Fast internet connection

### Installation Time

| Component | Time |
|-----------|------|
| System update | 2-5 minutes |
| Docker installation | 3-5 minutes |
| Containerlab installation | 1-2 minutes |
| Desktop environment (XFCE) | 5-10 minutes |
| Visual Studio Code | 2-3 minutes |
| /etc/hosts update | < 1 minute |
| ssh:// handler config | < 1 minute |
| **Total (headless)** | **~10 minutes** |
| **Total (with desktop)** | **~25 minutes** |

## Post-Installation

### 1. Verify Installation

```bash
# Check Docker
docker --version
docker compose version

# Check Containerlab  
containerlab version

# Check Docker group membership
groups | grep docker

# Check /etc/hosts
grep "\.lab" /etc/hosts

# If desktop was installed, check:
code --version              # VS Code
firefox --version           # Firefox
which xfce4-terminal        # Terminal
xdg-mime query default x-scheme-handler/ssh  # ssh:// handler
```

### 2. Log Out and Back In

**Important:** After installation, you must log out and back in for Docker group changes to take effect.

```bash
# Option 1: Log out and back in
exit
# ... log back in to WSL/Linux

# Option 2: Quick refresh (temporary)
newgrp docker
```

### 3. Start Desktop and Applications (if installed)

**For WSL with WSLg (Recommended - Windows 11 or updated Windows 10):**
```bash
# GUI apps work automatically with WSLg
code .                                      # Open VS Code in current directory
firefox http://nautobotlab.dev:8080 &       # Open Nautobot in browser
xfce4-terminal &                            # Open terminal
```

**For WSL with Windows Terminal (Alternative):**
```bash
# VS Code Remote-WSL extension (recommended)
code .   # Opens VS Code on Windows connecting to WSL

# Or launch GUI apps with WSLg
firefox http://nautobotlab.dev:8080 &
```

**For WSL without WSLg (VcXsrv/X Server):**
```bash
# Install VcXsrv on Windows, then:
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
startxfce4
```

**For native Linux:**
```bash
startxfce4
code .
```

### 4. Test ssh:// Links

```bash
# From command line
xdg-open ssh://admin@access1

# In browser, create a bookmark:
# Name: Access1 SSH
# URL: ssh://admin@access1.lab
# Click it to open terminal with SSH connection
```

## Troubleshooting

### "Docker daemon is not running"
```bash
sudo service docker start
# or
sudo systemctl start docker
```

### "Permission denied" when running docker
```bash
# You need to log out and back in after install
exit
# ... log back in

# Or temporarily:
newgrp docker
```

### Desktop won't start
```bash
# For WSL, ensure WSLg is enabled (Windows 11 or updated Windows 10)
wsl --version

# Or install X server on Windows (VcXsrv)
```

### ssh:// links don't work
```bash
# Ensure terminal is installed
which xfce4-terminal gnome-terminal konsole

# Reconfigure handler
bash configure_ssh_handler.sh

# Test manually
xdg-open ssh://admin@access1
```

### Containerlab installation fails
```bash
# Manual installation:
bash -c "$(curl -sL https://get.containerlab.dev)"
```

## Uninstallation

### Remove Components

```bash
# Remove Docker
sudo apt-get purge -y docker-ce docker-ce-cli containerd.io
sudo rm -rf /var/lib/docker

# Remove desktop environment
sudo apt-get purge -y xfce4*
sudo apt-get autoremove -y

# Remove containerlab
sudo containerlab uninstall

# Restore /etc/hosts
sudo cp /etc/hosts.backup.* /etc/hosts  # Use your backup file
```

## Security Notes

⚠️ **This is a LAB environment** - Not for production use!

- Default credentials: admin/admin
- No SSL/TLS on Nautobot (uses HTTP)
- Default SNMP communities
- No firewall rules

For production deployment, follow security best practices:
- Change all default passwords
- Enable HTTPS/SSL
- Configure proper authentication (LDAP/SAML)
- Set up firewall rules
- Use secrets management

## Next Steps

After successful installation:

1. ✅ Deploy Containerlab lab
2. ✅ Start Nautobot with Docker Compose
3. ✅ Run Pre-flight or Design Builder Lab Setup job
4. ✅ Access Nautobot UI at http://nautobotlab.dev:8080
5. ✅ Start automating!

See main [README.md](README.md) for detailed usage instructions.

---

**Questions?** Check the main README or the blog series at netdevops.it!

