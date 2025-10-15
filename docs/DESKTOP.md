# Desktop Environment Guide

## Overview

This lab supports an optional desktop environment (XFCE) with VS Code and Firefox **for native Linux installations only**. 

⚠️ **Desktop installation is NOT recommended for WSL** - the install script will warn you and require confirmation.

## WSL vs Native Linux

### WSL (Windows Subsystem for Linux)
- **Recommendation**: DO NOT install desktop environment
- **Why**: WSL is designed to run headless services
- **Best Practice**: 
  - Run Docker/Containerlab/Nautobot in WSL
  - Access Nautobot from Windows browser at `http://localhost:8080`
  - Use VS Code on Windows with WSL extension
  
### Native Linux (Bare Metal / VM)
- **Recommendation**: Desktop is optional but supported
- **Use Case**: When you need an all-in-one Linux environment
- **Note**: System always boots to text console (no graphical login)

## Installation

### Standard Installation (No Desktop) - RECOMMENDED for WSL

```bash
bash install.sh
```

### With Desktop (Not recommended for WSL)

```bash
INSTALL_DESKTOP=true bash install.sh
```

**WSL Warning**: If installing desktop in WSL, the script will:
1. Warn you it's not recommended
2. Ask for confirmation
3. Configure console-only boot (no graphical login)

## Desktop Configuration

When desktop IS installed:
- ✅ System configured for **console login only**
- ✅ No graphical login screen (prevents "Failed to start session" errors)
- ✅ All display managers disabled (lightdm, gdm, etc.)
- ✅ Boot target set to `multi-user.target` (text mode)

## Usage After Installation

### Starting GUI Applications

After logging in via text console:

```bash
# Individual apps (recommended)
code .                                  # VS Code
firefox http://nautobotlab.dev:8080 &   # Browser
xfce4-terminal &                        # Terminal

# Or use helper script for full desktop
bash start_desktop.sh
```

### WSL-Specific Tips

```bash
# Access Nautobot from Windows
# Open in Windows browser: http://localhost:8080

# Use VS Code on Windows with WSL extension
# This is better than running Code in WSL
```

## Troubleshooting

### "Failed to start session" Error

This happens when a display manager (graphical login) is enabled. Fix:

```bash
# Run the recovery script
bash /tmp/fix_desktop_login.sh
sudo reboot

# Or manually
sudo systemctl set-default multi-user.target
sudo systemctl disable lightdm gdm gdm3
sudo reboot
```

### Remove Desktop Environment

```bash
bash uninstall_desktop.sh
```

This will:
- Remove XFCE, VS Code, Firefox
- Remove all display managers
- Restore text-only mode
- Free up disk space

### WSL Desktop Not Working

**Don't use desktop in WSL!** Instead:
1. Remove desktop: `bash uninstall_desktop.sh`
2. Access Nautobot from Windows browser
3. Use VS Code on Windows with WSL Remote extension

## Architecture Decisions

### Why Console Boot Only?

1. **Prevents Login Issues**: Graphical login often fails in lab/WSL environments
2. **Resource Efficient**: No resources wasted on login screen
3. **Flexibility**: Start only the GUI apps you need
4. **Lab Friendly**: Better for headless/remote environments

### Why Not Desktop in WSL?

1. **WSLg Available**: Windows 11+ has native GUI support
2. **Performance**: Windows apps perform better than X11 in WSL
3. **Complexity**: Desktop in WSL adds unnecessary complexity
4. **Login Problems**: Graphical login doesn't work well in WSL

## Best Practices

### For WSL Users
```bash
# ✅ DO: Run services in WSL
docker compose up -d
sudo containerlab deploy -t lab.yml

# ✅ DO: Access from Windows
# Browser: http://localhost:8080
# VS Code: Use WSL Remote extension

# ❌ DON'T: Install desktop in WSL
INSTALL_DESKTOP=true bash install.sh  # Not recommended!
```

### For Native Linux Users
```bash
# ✅ DO: Install desktop if you want an all-in-one environment
INSTALL_DESKTOP=true bash install.sh

# ✅ DO: Login via text console
# Then: bash start_desktop.sh

# ❌ DON'T: Expect graphical login
# System always boots to console
```

## Files

- `install.sh` - Main installation script (with WSL detection)
- `start_desktop.sh` - Helper to start desktop apps (WSL-aware)
- `uninstall_desktop.sh` - Remove desktop environment
- `/tmp/fix_desktop_login.sh` - Emergency recovery script

## Summary

| Environment | Desktop? | Access Method |
|-------------|----------|---------------|
| **WSL** | ❌ No (not recommended) | Windows browser + VS Code WSL Remote |
| **Native Linux** | ✔️ Optional | Console login → start desktop apps |
| **Both** | Console boot only | Never graphical login screen |

