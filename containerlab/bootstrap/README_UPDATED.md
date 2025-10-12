# Bootstrap Configuration - Updated for Reproducibility

## Overview
This directory contains bootstrap configurations that are **automatically applied** when deploying the containerlab topology. This ensures complete reproducibility on any fresh machine.

## How It Works

### Network Devices (Arista cEOS & Nokia SR Linux)
These use the `startup-config` parameter in the containerlab YAML:
- **access1.cfg**, **access2.cfg** - Arista access switches
- **dist1.cfg** - Nokia distribution switch  
- **rtr1.cfg** - Nokia router

These configs are applied automatically during container startup.

### Linux Containers (Alpine)
These use the `binds` + `exec` parameters in the containerlab YAML:
- **workstation1.cfg** - Workstation for network testing
- **mgmt.cfg** - Management server

The bootstrap files are:
1. Mounted into the container via `binds`
2. Executed via `exec` command
3. Automatically configure networking, install tools, and start services

## What Gets Configured

### Workstation1 (172.20.20.15)
- ✅ Management interface (eth0) with static IP
- ✅ SSH server enabled
- ✅ Network testing tools (ping, curl, tcpdump, iperf3, mtr)
- ✅ Root password set (root:root)
- ✅ Data interface (eth1) ready for configuration exercises

### Management Server (172.20.20.16)
- ✅ Management interface (eth0) with static IP
- ✅ Data interface (eth1) configured
- ✅ SSH server enabled
- ✅ Network tools (tcpdump, nmap, iperf3)
- ✅ Directory structure for automation scripts
- ✅ Root password set (root:root)

## Testing Deployment

To test reproducibility on a fresh machine:

```bash
cd containerlab
containerlab deploy -t nautobot-lab.clab.yml
```

All configurations will be applied automatically!

## Accessing Containers

```bash
# SSH to workstation1
ssh -p 50009 root@localhost

# SSH to management server
ssh -p 50010 root@localhost

# Direct exec
docker exec -it clab-nautobot-lab-workstation1 sh
docker exec -it clab-nautobot-lab-mgmt sh
```

## Changes from Original

- **Removed:** ztp container (replaced with workstation1)
- **Added:** workstation1.cfg bootstrap configuration
- **Updated:** All bootstrap files now use `binds` for automatic application
- **Standardized:** All Linux containers use consistent bootstrap approach

## For Blog Series

The workstation1 is intentionally configured with:
- ✅ Management network access (eth0)
- ⏸️ Data network interface (eth1) - UP but not configured

This allows step-by-step demonstrations of:
1. Configuring VLANs on access switches
2. Setting up routing through the topology
3. Establishing end-to-end connectivity
4. Network automation with Nautobot

