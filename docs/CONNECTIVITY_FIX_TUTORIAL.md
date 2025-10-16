# Tutorial: Fixing Network Connectivity with Automation

## Overview

This tutorial demonstrates a real-world network troubleshooting scenario where automation is used to identify and fix connectivity issues.

## The Problem

After initial containerlab deployment, connectivity tests show that:
- **workstation1** (10.0.0.15) cannot communicate with **mgmt** (10.0.0.16)
- Both devices are in the same subnet (10.0.0.0/24), so they should communicate at Layer 2
- The issue is caused by **shutdown interfaces** on the switches

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
   shutdown    ← PROBLEM! Interface is disabled
   description "Connected to workstation1 - DISABLED"
```

**rtr1 (Ethernet2 - connected to mgmt):**
```
interface Ethernet2
   shutdown    ← PROBLEM! Interface is disabled
   description "Connected to mgmt server - DISABLED"
```

**Root Cause**: Both Ethernet2 interfaces are administratively shutdown, preventing any communication.

### Step 3: Diagnose the Problem

Run the diagnostic script to identify the root cause:

```bash
cd /home/bsmeding/nautobot_zero_to_hero/scripts
python3 4a_diagnose_connectivity_issue.py
```

This will connect to the switches and check Ethernet2 interface status.

**Expected Output**: Shows that Ethernet2 is SHUTDOWN on both access1 and rtr1

### Step 4: Fix with Automation

Run the fix script that uses Jinja2 templates and pyeapi:

```bash
cd /home/bsmeding/nautobot_zero_to_hero/scripts
python3 4b_config_arista_template_fix.py
```

**What the script does:**
1. Connects to access1 and rtr1 via eAPI
2. Renders configuration from Jinja2 template
3. Enables Ethernet2 interfaces with "no shutdown" command
4. Ensures correct VLAN 10 assignment
5. Adds loopback interfaces for management
6. Saves the configuration

### Step 5: Verify the Fix

Run the connectivity test again:

1. Navigate to **Jobs** in Nautobot
2. Run **"Containerlab Connectivity Test"**
3. Test both **Workstation 1** and **mgmt**

**Expected Result**: ✅ All tests PASS

## What You Learned

1. **Problem Identification**: Using automated tests to identify connectivity issues
2. **Root Cause Analysis**: Understanding interface shutdown issues
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

- access1 Eth2: **shutdown** ❌
- rtr1 Eth2: **shutdown** ❌
- Result: No physical connectivity to workstation1 and mgmt

### After Fix (Working)

- access1 Eth2: **no shutdown** + VLAN 10 ✅
- rtr1 Eth2: **no shutdown** + VLAN 10 ✅
- Result: Interfaces enabled, Layer 2 connectivity restored

## Files Involved

- `containerlab/bootstrap/access1.cfg` - Initial broken config
- `containerlab/bootstrap/rtr1.cfg` - Initial broken config  
- `scripts/4a_diagnose_connectivity_issue.py` - Diagnostic script
- `scripts/4b_config_arista_template_fix.py` - Fix script (static inventory)
- `scripts/5_config_arista_nautobot_inventory.py` - Fix script (Nautobot inventory)
- `scripts/6_config_arista_template_nautobot_full.py` - Full Nautobot-driven (inventory + state)
- `jobs/jobs/containerlab_connectivity_test.py` - Test job
- `jobs/jobs/interface_hook.py` - Automatic sync hook

## Automation Journey

This tutorial demonstrates the evolution of network automation:

1. **Script 4a**: Manual diagnosis (connect and check)
2. **Script 4b**: Hardcoded fix (static device list)
3. **Script 5**: Nautobot inventory (dynamic device list, static config)
4. **Script 6**: Full Nautobot SoT (dynamic devices + interface states)
5. **Interface Hook**: Automatic real-time sync (ultimate automation)

## Next Steps

- Progress through scripts 5 and 6 to see automation evolution
- Enable Interface Hook for automatic sync
- Modify interface in Nautobot → Watch it sync to device automatically!

