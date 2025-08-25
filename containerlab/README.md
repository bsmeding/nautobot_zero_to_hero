# Containerlab Integration with Nautobot

This directory contains Containerlab testbed configurations that can be integrated with your Nautobot instance.

⚠️ **WSL Limitation**: Containerlab has known networking issues in WSL environments (error: "Failed to lookup link"). The topology files are provided for reference and testing in native Linux environments or Docker Desktop for Windows.

## Quick Start

### 1. Install Containerlab (if not already installed)
```bash
# Install Containerlab
bash -c "$(curl -sL https://get.containerlab.dev)"

# Verify installation
containerlab version
```

### 2. Start a Testbed
```bash
# Start your default testbed (recommended)
cd /mnt/c/Users/BartSmeding/NetDevOps/Workspace/DOCKER-COMPOSE_Projects/customer1/containerlab
containerlab deploy -t nautobot-lab.clab.yml

# Or start the simple testbed (Linux-based routers)
containerlab deploy -t simple-testbed.clab.yml


```

### 3. Discover Devices in Nautobot
1. Go to Nautobot UI: http://localhost:8081
2. Navigate to **Jobs** → **Containerlab Device Discovery**
3. Fill in the form:
   - **Testbed Name**: `nautobot-lab` (or your testbed name)
   - **Site Name**: `Testbed` (or your preferred site name)
   - **Device Type**: `Auto-detect from Containerlab`
   - **Platform**: `Auto-detect from Containerlab`
   - **Dry Run**: Check first to see what would be discovered
4. Click **Run Job**

### 4. Verify Devices
- Go to **Devices** in Nautobot
- You should see your Containerlab devices listed
- Each device will have the management IP from Containerlab

## Testbed Configurations

### Default Testbed (`nautobot-lab.yml`) - **RECOMMENDED**
- **2 Arista cEOS switches** (access1, access2)
- **2 Nokia SR Linux routers** (dist1, rtr1)
- **2 Linux servers** (ztp, mgmt)
- **Management IPs**: 172.20.20.10-15
- **SSH Ports**: 50001-50010
- **Realistic network topology** with access, distribution, and core layers

### Simple Testbed (`simple-testbed.yml`)
- **3 Linux routers** (Alpine, Ubuntu, Debian)
- **Management IPs**: 192.168.1.10, 192.168.1.11, 192.168.1.12
- **SSH Ports**: 50001, 50002, 50003
- **Easy to start** - uses standard Linux images



## Management Access

### SSH Access
```bash
# Connect to devices via SSH (Default Testbed)
ssh admin@localhost -p 50001  # access1 (Arista cEOS)
ssh admin@localhost -p 50003  # access2 (Arista cEOS)
ssh admin@localhost -p 50005  # dist1 (Nokia SR Linux)
ssh admin@localhost -p 50007  # rtr1 (Nokia SR Linux)
ssh root@localhost -p 50009   # ztp (Linux)
ssh root@localhost -p 50010   # mgmt (Linux)

# Default credentials:
# - Arista cEOS: admin/admin
# - Nokia SR Linux: admin/admin
# - Linux: root/root
```

### Network Configuration
```bash
# View network interfaces
ip addr show

# Configure network interfaces
ip addr add 10.0.1.1/24 dev eth1
ip route add 10.0.2.0/24 via 10.0.1.2
```

## Nautobot Integration

### Automatic Discovery
The **Containerlab Device Discovery** job will:
1. ✅ **Discover** all devices in your testbed
2. ✅ **Create** a site for the devices
3. ✅ **Add** devices to Nautobot with proper device types/platforms
4. ✅ **Set** management IPs and descriptions

### Manual Device Addition
You can also manually add devices:
1. Go to **Devices** → **Add Device**
2. Fill in device details:
   - **Name**: `access1`, `access2`, `dist1`, `rtr1`, `ztp`, `mgmt`
   - **Site**: `Testbed`
   - **Device Type**: `Auto-detect` (arista_ceos, nokia_srlinux, linux)
   - **Platform**: `Auto-detect` (eos, srl, linux)
   - **Management IP**: `172.20.20.10-15`

## Useful Commands

### Containerlab Commands
```bash
# List running testbeds
containerlab list

# Inspect a testbed
containerlab inspect nautobot-lab

# Stop a testbed
containerlab destroy nautobot-lab

# View logs
containerlab logs nautobot-lab
```

### Network Testing
```bash
# Test connectivity between devices
docker exec clab-nautobot-lab-access1 ping 172.20.20.11
docker exec clab-nautobot-lab-dist1 ping 172.20.20.13
```

## Troubleshooting

### WSL Network Issues
If you encounter "Failed to lookup link" errors in WSL, this is a known issue with Containerlab in WSL environments. Try these workarounds:

#### Option 1: Use Docker Desktop for Windows
1. Install Docker Desktop for Windows
2. Enable WSL 2 integration
3. Use Windows Terminal or PowerShell instead of WSL

#### Option 2: Use Linux Native Environment
1. Use a native Linux machine or VM
2. Install Containerlab directly on Linux

#### Option 3: Manual Network Creation
```bash
# Create the network manually
docker network create clab --subnet=192.168.1.0/24
docker network create mgmt-net --subnet=172.20.20.0/24

# Then try deploying again
containerlab deploy -t nautobot-lab.clab.yml
```

### Containerlab Issues
```bash
# Check if Containerlab is running
containerlab version

# Check Docker daemon
docker ps

# View Containerlab logs
containerlab logs nautobot-lab
```

### Nautobot Integration Issues
1. **Job not found**: Restart Nautobot to pick up new jobs
2. **Permission denied**: Ensure Containerlab has access to Docker
3. **No devices discovered**: Check if testbed is running and accessible

### Network Issues
```bash
# Check if management network exists
docker network ls | grep mgmt-net

# Recreate management network
docker network create mgmt-net --subnet=172.20.20.0/24
```

## Next Steps

1. **Configure devices** with proper network interfaces
2. **Add interfaces** to Nautobot devices
3. **Create IP addresses** and assign to interfaces
4. **Test connectivity** between devices
5. **Use Nautobot jobs** to configure devices automatically

## Files Structure
```
containerlab/
├── README.md              # This file
├── nautobot-lab.clab.yml      # Default testbed (RECOMMENDED)
├── simple-testbed.clab.yml    # Simple Linux testbed
└── configs/              # Device configurations (optional)
    ├── access1/
    ├── access2/
    ├── dist1/
    ├── rtr1/
    ├── ztp/
    └── mgmt/
```
