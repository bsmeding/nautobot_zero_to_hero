# Network Connectivity Setup - MGMT to Workstation1

## Overview
This document describes the network configuration that enables ping connectivity from the management server (mgmt) to workstation1 through the Data VLAN (VLAN 10).

## Network Topology

```
mgmt (10.0.0.16/24) --- eth1 --- rtr1:eth1-2 (untagged → VLAN 10)
                                      |
                                 (bridged via data-vlan10)
                                      |
                                 rtr1:eth1-1 (VLAN 10 tagged)
                                      |
                                 dist1:eth1-3 (VLAN 10 tagged)
                                      |
                                 (bridged via data-vlan10)
                                      |
                                 dist1:eth1-1 (VLAN 10 tagged)
                                      |
                                 access1:eth1 (trunk, all VLANs)
                                      |
                                 (switched to VLAN 10)
                                      |
                                 access1:eth2 (access port, VLAN 10)
                                      |
                              workstation1:eth1 (10.0.0.15/24)
```

## Configuration Changes Made

### 1. Workstation1 (`bootstrap/workstation1.cfg`)
- **eth0**: Management network (172.20.20.15/24) - unchanged
- **eth1**: Configured with IP 10.0.0.15/24 (Data VLAN)
- Both interfaces are now brought up at boot

### 2. Access Switch 1 (`bootstrap/access1.cfg`)
- **Ethernet2**: Changed from VLAN 20 to VLAN 10 (access mode)
- Connected to workstation1:eth1
- Added VLAN definitions (10, 20, 30)

### 3. Distribution Switch (`bootstrap/dist1.cfg`)
- Created MAC-VRF bridge `data-vlan10`
- Bridges ethernet-1/1.0, ethernet-1/2.0, and ethernet-1/3.0
- All interfaces configured for VLAN 10 tagged traffic

### 4. Router 1 (`bootstrap/rtr1.cfg`)
- **ethernet-1/2**: Changed to accept untagged traffic from mgmt
- Created MAC-VRF bridge `data-vlan10`
- Bridges ethernet-1/1.0 (tagged VLAN 10) and ethernet-1/2.0 (untagged)
- Fixed description for ethernet-1/3

## IP Address Summary

### Management Network (172.20.20.0/24)
- access1: 172.20.20.11
- access2: 172.20.20.12
- dist1: 172.20.20.13
- rtr1: 172.20.20.14
- workstation1: 172.20.20.15
- mgmt: 172.20.20.16

### Data VLAN Network (10.0.0.0/24)
- workstation1:eth1: 10.0.0.15
- mgmt:eth1: 10.0.0.16

## Testing Connectivity

After deploying the lab with `sudo containerlab deploy -t nautobot-lab.clab.yml`, you can test:

### 1. Access the management server:
```bash
docker exec -it clab-nautobot-lab-mgmt sh
```

### 2. Verify network configuration:
```bash
ip addr show
# Should show:
# - eth0: 172.20.20.16/24
# - eth1: 10.0.0.16/24
```

### 3. Ping workstation1 via Data VLAN:
```bash
ping 10.0.0.15
```

### 4. Access workstation1:
```bash
docker exec -it clab-nautobot-lab-workstation1 sh
```

### 5. Verify workstation1 network configuration:
```bash
ip addr show
# Should show:
# - eth0: 172.20.20.15/24
# - eth1: 10.0.0.15/24
```

### 6. Ping mgmt from workstation1:
```bash
ping 10.0.0.16
```

## VLAN 10 Path
The traffic flow from mgmt to workstation1:
1. mgmt sends untagged packet from 10.0.0.16 to 10.0.0.15
2. rtr1:ethernet-1/2 receives untagged traffic, bridges it to VLAN 10
3. rtr1 MAC-VRF forwards to rtr1:ethernet-1/1 with VLAN 10 tag
4. dist1:ethernet-1/3 receives VLAN 10 tagged traffic
5. dist1 MAC-VRF bridges to dist1:ethernet-1/1 with VLAN 10 tag
6. access1:eth1 (trunk) receives VLAN 10 tagged traffic
7. access1 switches VLAN 10 to access1:eth2 (access port)
8. workstation1:eth1 receives untagged packet

## Notes
- Both mgmt and workstation1 have dual connectivity:
  - Management network via eth0 (172.20.20.0/24)
  - Data network via eth1 (10.0.0.0/24)
- The Data VLAN uses Layer 2 switching/bridging (no routing required)
- All Nokia SR Linux switches use MAC-VRF for Layer 2 bridging

