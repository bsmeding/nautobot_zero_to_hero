# Tutorial: Fixing Network Connectivity with Automation

## Overview

This tutorial demonstrates a real-world network troubleshooting scenario where automation is used to identify and fix connectivity issues.

## The Problem

After initial containerlab deployment, connectivity tests show that:
- **workstation1** (10.0.0.15) cannot communicate with **mgmt** (10.0.0.16)
- Both devices are in the same subnet (10.0.0.0/24), so they should communicate at Layer 2
- The issue is caused by **incorrect VLAN assignments** on the switches

## Step-by-Step Tutorial

### Step 1: Verify the Problem

Run the Nautobot connectivity test job to confirm the issue:

1. Navigate to **Jobs** in Nautobot
2. Find **"Containerlab Connectivity Test"**
3. Select **Destination Node**: `Workstation 1 (172.20.20.4)`
4. Click **Run Job**

**Expected Result**: ❌ Ping test FAILS

### Step 2: Investigate the Issue

Looking at the bootstrap configurations:

**access1 (Ethernet2 - connected to workstation1):**
```
interface Ethernet2
   switchport access vlan 999    ← WRONG! Should be VLAN 10
```

**rtr1 (Ethernet2 - connected to mgmt):**
```
interface Ethernet2
   switchport access vlan 999    ← WRONG! Should be VLAN 10
```

**Root Cause**: Both Ethernet2 interfaces are in VLAN 999 instead of VLAN 10, preventing Layer 2 communication.

### Step 3: Fix with Automation

Run the fix script that uses Jinja2 templates and pyeapi:

```bash
cd /home/bsmeding/nautobot_zero_to_hero/scripts
python3 4_config_arista_template.py
```

**What the script does:**
1. Connects to access1 and rtr1 via eAPI
2. Renders configuration from Jinja2 template
3. Moves Ethernet2 interfaces from VLAN 999 to VLAN 10
4. Adds loopback interfaces for management
5. Saves the configuration

### Step 4: Verify the Fix

Run the connectivity test again:

1. Navigate to **Jobs** in Nautobot
2. Run **"Containerlab Connectivity Test"**
3. Test both **Workstation 1** and **mgmt**

**Expected Result**: ✅ All tests PASS

## What You Learned

1. **Problem Identification**: Using automated tests to identify connectivity issues
2. **Root Cause Analysis**: Understanding VLAN misconfigurations
3. **Automated Remediation**: Using Python + Jinja2 + pyeapi to fix configurations at scale
4. **Verification**: Re-testing to confirm the fix worked

## Technical Details

### Network Topology

```
┌─────────────┐                           ┌──────────┐
│ workstation1│                           │   mgmt   │
│  10.0.0.15  │                           │10.0.0.16 │
└──────┬──────┘                           └────┬─────┘
       │ eth1                                  │ eth1
       │ VLAN 10                               │ VLAN 10
       │                                       │
┌──────┴──────┐                         ┌─────┴──────┐
│   access1   │                         │    rtr1    │
│  Eth2       │                         │   Eth2     │
│  (VLAN 10)  │                         │  (VLAN 10) │
└──────┬──────┘                         └─────┬──────┘
       │ Eth1                                 │ Eth1
       │ Trunk                                │ Trunk
       │ VLAN 10                              │ VLAN 10
       │                                      │
       └──────────┬──────────────────────────┘
                  │
           ┌──────┴──────┐
           │    dist1    │
           │(Layer 2 SW) │
           └─────────────┘
```

### Before Fix (Broken)

- access1 Eth2: VLAN 999 ❌
- rtr1 Eth2: VLAN 999 ❌
- Result: workstation1 and mgmt in different broadcast domains

### After Fix (Working)

- access1 Eth2: VLAN 10 ✅
- rtr1 Eth2: VLAN 10 ✅
- Result: workstation1 and mgmt in same VLAN, Layer 2 connectivity restored

## Files Involved

- `containerlab/bootstrap/access1.cfg` - Initial broken config
- `containerlab/bootstrap/rtr1.cfg` - Initial broken config
- `scripts/4_config_arista_template.py` - Fix script
- `jobs/jobs/containerlab_connectivity_test.py` - Test job

## Next Steps

- Try the same fix using Nautobot as source of truth (script 5)
- Explore more advanced templating with variables
- Automate the entire workflow: test → detect → fix → verify

