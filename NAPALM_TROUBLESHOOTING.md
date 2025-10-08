# NAPALM Connection Troubleshooting Guide

## Issue: Cannot connect to Containerlab devices from Nautobot GUI via NAPALM

## Root Causes Identified

### 1. NAPALM Configuration Not Enabled
**FIXED**: The NAPALM_USERNAME and NAPALM_PASSWORD were commented out in `config/nautobot_config.py`
- **Solution**: Uncommented the NAPALM configuration lines
- **Status**: ✅ COMPLETED

### 2. Potential Network Connectivity Issues
The Containerlab devices and Nautobot need to be on the same network.

## Troubleshooting Steps

### Step 1: Verify Nautobot is Running
```bash
cd /mnt/c/Users/BartSmeding/NetDevOps/Workspace/NAUTOBOT_JOBS/nautobot_zero_to_hero
docker compose up -d
docker compose ps
```

### Step 2: Verify Containerlab Lab is Deployed
```bash
cd /mnt/c/Users/BartSmeding/NetDevOps/Workspace/NAUTOBOT_JOBS/nautobot_zero_to_hero/containerlab
containerlab deploy -t nautobot-lab.clab.yml
containerlab inspect -t nautobot-lab.clab.yml
```

### Step 3: Check Network Connectivity
```bash
# Check if clab network exists
docker network ls | grep clab

# Test connectivity from Nautobot container to devices
docker exec -it nzth-nautobot ping -c 3 172.20.20.11
docker exec -it nzth-nautobot ping -c 3 172.20.20.12
docker exec -it nzth-nautobot ping -c 3 172.20.20.13
docker exec -it nzth-nautobot ping -c 3 172.20.20.14
```

### Step 4: Test SSH Connectivity
```bash
# Test SSH from Nautobot container
docker exec -it nzth-nautobot ssh -o StrictHostKeyChecking=no admin@172.20.20.11
docker exec -it nzth-nautobot ssh -o StrictHostKeyChecking=no admin@172.20.20.13
```

### Step 5: Test NAPALM Directly
```bash
# Install NAPALM in Nautobot container if not present
docker exec -it nzth-nautobot pip install napalm napalm-eos napalm-srl

# Test NAPALM connection
docker exec -it nzth-nautobot napalm --user admin --password admin --vendor eos 172.20.20.11 get_facts
docker exec -it nzth-nautobot napalm --user admin --password admin --vendor nokia_srl 172.20.20.13 get_facts
```

## Device Configuration Verification

### Arista EOS Devices (access1, access2)
- **IP**: 172.20.20.11, 172.20.20.12
- **Username**: admin
- **Password**: admin
- **NAPALM Driver**: eos

### Nokia SR Linux Devices (dist1, rtr1)
- **IP**: 172.20.20.13, 172.20.20.14
- **Username**: admin
- **Password**: admin
- **NAPALM Driver**: nokia_srl

## Nautobot GUI Testing

### 1. Verify Platform Configuration
1. Go to **Devices > Platforms**
2. Check that platforms have correct NAPALM drivers:
   - Arista EOS: `eos`
   - Nokia SR Linux: `nokia_srl`

### 2. Verify Device Configuration
1. Go to **Devices > Devices**
2. For each device, verify:
   - Platform is set correctly
   - Primary IP is set (172.20.20.11-14)
   - Device is in "Active" status

### 3. Test NAPALM Connection
1. Go to **Devices > Devices**
2. Click on a device (e.g., access1)
3. Go to **Connect > NAPALM**
4. Try to run `get_facts` or `get_interfaces`

## Common Issues and Solutions

### Issue: "Connection refused" or "Timeout"
**Cause**: Network connectivity problem
**Solution**: 
- Verify both Nautobot and Containerlab are using the `clab` network
- Check if devices are actually running: `docker ps | grep clab`

### Issue: "Authentication failed"
**Cause**: Wrong credentials
**Solution**:
- Verify credentials in Containerlab config match Nautobot config
- Test SSH manually first

### Issue: "NAPALM driver not supported"
**Cause**: Missing NAPALM driver packages
**Solution**:
```bash
docker exec -it nzth-nautobot pip install napalm-eos napalm-srl
docker compose restart nautobot
```

### Issue: "Device not found" in Nautobot GUI
**Cause**: Device not properly configured in Nautobot
**Solution**:
- Run the preflight setup job to populate devices
- Verify device has primary IP assigned

## Restart Procedure

If issues persist, restart everything:

```bash
# Stop everything
docker compose down
containerlab destroy -t nautobot-lab.clab.yml

# Start fresh
docker compose up -d
containerlab deploy -t nautobot-lab.clab.yml

# Wait for devices to fully boot (30-60 seconds)
sleep 60

# Test connectivity
docker exec -it nzth-nautobot ping -c 3 172.20.20.11
```

## Verification Commands

```bash
# Check all services are running
docker compose ps

# Check containerlab devices
containerlab inspect -t nautobot-lab.clab.yml

# Check network connectivity
docker exec -it nzth-nautobot ping -c 1 172.20.20.11

# Test NAPALM directly
docker exec -it nzth-nautobot napalm --user admin --password admin --vendor eos 172.20.20.11 get_facts
```
