# Provisioning System Architecture

This document explains how the provisioning system works and the three ways to trigger device provisioning.

## Architecture Overview

The provisioning system consists of two main components:

1. **Provision Device Job** (`provision_device.py`) - The core provisioning logic
2. **Device Configuration Hook** (`device_hook.py`) - Automatic trigger on device changes

## Three Ways to Trigger Provisioning

### Method 1: Manual Job Execution (On Demand)

**Use Case:** Manually provision a device when needed

**How to Trigger:**
```
Jobs → Jobs → Provision Device → Run Job
Select device → Configure options → Run
```

**Flow:**
```
User manually runs job
    ↓
ProvisionDevice Job
    ↓
Get intended config from Golden Config
    ↓
Deploy to device via NAPALM
    ↓
Device provisioned
```

**When to Use:**
- Initial device setup
- Manual configuration updates
- Testing and troubleshooting
- One-off provisioning tasks

---

### Method 2: Job Button (One-Click)

**Use Case:** Quick provisioning directly from device page

**How to Trigger:**
```
Device Page → Click "Provision Device" button
Job form opens with device pre-selected → Run
```

**Flow:**
```
User clicks button on device page
    ↓
Redirects to ProvisionDevice Job with device parameter
    ↓
Get intended config from Golden Config
    ↓
Deploy to device via NAPALM
    ↓
Device provisioned
```

**When to Use:**
- Quick device provisioning from device page
- After updating device details
- Regular maintenance tasks
- When working on a specific device

**Setup Required:**
- Custom Link configured (see [JOB_BUTTON_SETUP.md](./JOB_BUTTON_SETUP.md))

---

### Method 3: Automatic Hook (On Device Update)

**Use Case:** Automatically provision when device is changed

**How to Trigger:**
```
Edit device in Nautobot → Save
Hook automatically detects change → Triggers provisioning
```

**Flow:**
```
User updates device (name, IP, platform, role, location, status)
    ↓
Device Hook (JobHookReceiver) triggered
    ↓
Hook validates change is configuration-relevant
    ↓
Hook imports and calls ProvisionDevice Job
    ↓
Get intended config from Golden Config
    ↓
Deploy to device via NAPALM
    ↓
Device provisioned automatically
```

**When to Use:**
- Maintain continuous compliance
- Automatic configuration drift correction
- Zero-touch provisioning
- Hands-off operations

**Setup Required:**
- Job Hook configured (see [AUTO_PROVISIONING_HOOK.md](./AUTO_PROVISIONING_HOOK.md))

---

## Component Details

### Component 1: Provision Device Job

**File:** `/jobs/jobs/provision_device.py`

**Type:** Standard Nautobot Job

**Purpose:** Core provisioning logic that can be called multiple ways

**Key Features:**
- Can be run standalone (Method 1)
- Can be called via URL parameter (Method 2)
- Can be imported and called by other jobs (Method 3)
- Self-contained with all provisioning logic
- Handles NAPALM connection and deployment
- Manages credentials and validation

**Class:**
```python
class ProvisionDevice(Job):
    """Provision a device with Golden Config."""
    
    def run(self, device, dry_run=True, replace_config=False, commit_changes=True):
        # Core provisioning logic
        pass
```

**Can be Called:**
1. **Directly via Jobs UI**
   ```python
   # Nautobot runs it automatically
   ```

2. **Via URL (Job Button)**
   ```
   /extras/jobs/provision_device.ProvisionDevice/run/?device={{ obj.pk }}
   ```

3. **Via Import (Other Jobs)**
   ```python
   from .provision_device import ProvisionDevice
   
   provision_job = ProvisionDevice()
   provision_job.logger = self.logger  # Share logger
   provision_job.run(device=device, dry_run=True)
   ```

---

### Component 2: Device Configuration Hook

**File:** `/jobs/jobs/device_hook.py`

**Type:** JobHookReceiver

**Purpose:** Automatically trigger provisioning on device changes

**Key Features:**
- Detects device create/update events
- Filters for configuration-relevant changes
- Validates device readiness
- Imports and calls ProvisionDevice Job
- Configurable triggers (on create, on update)
- Safety checks and logging

**Class:**
```python
class DeviceJobHookReceiver(JobHookReceiver):
    """Hook that triggers provisioning on device changes."""
    
    def run(self, auto_provision_on_create=False, auto_provision_on_update=True, dry_run=True, **kwargs):
        # Detect changes
        # Validate device
        # Call ProvisionDevice Job
        pass
```

**How It Calls ProvisionDevice:**
```python
# Import the job
from .provision_device import ProvisionDevice

# Create instance
provision_job = ProvisionDevice()

# Share logger for unified logging
provision_job.logger = self.logger

# Call the job
provision_job.run(
    device=device,
    dry_run=dry_run,
    replace_config=False,  # Always merge for auto-provisioning
    commit_changes=True
)
```

---

## Detailed Flow Diagrams

### Flow 1: Manual Execution

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface                            │
│  Jobs → Jobs → Provision Device                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              User Input                                      │
│  • Select Device: access1                                   │
│  • Dry Run: True/False                                      │
│  • Replace Config: False                                    │
│  • Commit Changes: True                                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         ProvisionDevice.run()                                │
│         provision_device.py                                  │
│                                                              │
│  1. Validate device (platform, IP, NAPALM driver)          │
│  2. Get credentials (from secrets or defaults)              │
│  3. Get intended config (from Golden Config)                │
│  4. Deploy via NAPALM (load, diff, commit)                  │
│  5. Verify deployment                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Job Results                                 │
│  • Configuration diff shown                                  │
│  • Success/failure logged                                    │
│  • Device provisioned                                        │
└─────────────────────────────────────────────────────────────┘
```

### Flow 2: Job Button

```
┌─────────────────────────────────────────────────────────────┐
│                  Device Detail Page                          │
│  Device: access1                                            │
│  [Provision Device] ← User clicks button                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               Custom Link Redirect                           │
│  URL: /extras/jobs/provision_device.ProvisionDevice/run/    │
│  Parameter: ?device={{ obj.pk }}                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                Job Form Pre-filled                           │
│  • Device: access1 (pre-selected)                           │
│  • User configures other options                            │
│  • User clicks "Run Job"                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         ProvisionDevice.run()                                │
│         provision_device.py                                  │
│         (Same as Flow 1)                                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Job Results                                 │
│  Device provisioned                                          │
└─────────────────────────────────────────────────────────────┘
```

### Flow 3: Automatic Hook

```
┌─────────────────────────────────────────────────────────────┐
│                    User Action                               │
│  Edit Device → Change hostname → Save                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Nautobot Signal                                 │
│  post_save signal triggered for Device model                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│        DeviceJobHookReceiver.run()                           │
│        device_hook.py                                        │
│                                                              │
│  1. Detect action (created/updated/deleted)                 │
│  2. Check if configuration-relevant fields changed          │
│     • name ✓ (changed)                                      │
│     • primary_ip4, platform, role, location, status         │
│  3. Validate device is ready                                │
│     • Has platform? ✓                                       │
│     • Has NAPALM driver? ✓                                  │
│     • Has primary IP? ✓                                     │
│     • Status is Active/Planned/Staged? ✓                    │
│  4. Import ProvisionDevice job                              │
│  5. Call provision_job.run()                                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         ProvisionDevice.run()                                │
│         provision_device.py                                  │
│                                                              │
│  Called by hook with:                                       │
│  • device=device                                            │
│  • dry_run=True (from hook config)                         │
│  • replace_config=False (always merge for auto)            │
│  • commit_changes=True                                      │
│                                                              │
│  (Same provisioning logic as Flows 1 & 2)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Job Results                                 │
│  • Hook execution logged                                     │
│  • Provision job execution logged                            │
│  • Device automatically provisioned                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Design Principles

### 1. Single Source of Logic

**Provision Device Job** (`provision_device.py`) contains ALL provisioning logic:
- ✅ One place to maintain
- ✅ Consistent behavior across all trigger methods
- ✅ Easy to test and debug
- ✅ Reusable by other jobs

### 2. Separation of Concerns

**Device Hook** (`device_hook.py`) only handles:
- Event detection (device created/updated)
- Change filtering (configuration-relevant fields)
- Device validation (readiness checks)
- Triggering the provision job

**Provision Job** (`provision_device.py`) only handles:
- Getting intended configuration
- NAPALM connection and deployment
- Configuration diff and commit
- Verification

### 3. Flexible Triggering

All three methods call the same core logic:
```python
ProvisionDevice().run(device, dry_run, replace_config, commit_changes)
```

### 4. Shared Logging

When hook calls provision job, it shares its logger:
```python
provision_job.logger = self.logger
```

This creates a single unified log showing:
1. Hook triggered
2. Hook validated device
3. Hook called provision job
4. Provision job executed
5. Result

---

## Configuration Summary

### For All Three Methods to Work

1. **Provision Device Job** - Must be enabled
   ```
   Jobs → Jobs → Provision Device
   Ensure it's registered and runnable
   ```

2. **Job Button (Optional)** - For Method 2
   ```
   Extensibility → Custom Links
   Create link to provision_device.ProvisionDevice
   ```

3. **Job Hook (Optional)** - For Method 3
   ```
   Jobs → Jobs → Device Configuration Hook
   Enable the job
   
   Extensibility → Job Hooks
   Create hook linking to DeviceJobHookReceiver
   Configure parameters
   ```

---

## Example: Using All Three Methods

### Scenario: Provision New Device

**Step 1: Create Device in Nautobot**
```
Devices → Devices → Add
Name: access3
Platform: Arista EOS
Primary IP: 172.20.20.23/24
Role: Access Switch
Save
```

**Step 2: Generate Intended Config**
```
Jobs → Jobs → Generate Intended Configurations
Select: access3
Run Job
```

**Now you have 3 ways to provision:**

**Method 1: Manual Job**
```
Jobs → Jobs → Provision Device
Device: access3
Dry Run: True
Run Job
```

**Method 2: Job Button**
```
Go to Device Page: access3
Click "Provision Device" button
Configure options
Run Job
```

**Method 3: Automatic (if hook enabled)**
```
Edit Device: access3
Change hostname to: access-switch-3
Save
→ Hook automatically triggers
→ Device automatically provisioned
```

---

## Comparison Matrix

| Feature | Manual Job | Job Button | Automatic Hook |
|---------|-----------|------------|----------------|
| **User Control** | Full | Full | Automatic |
| **When** | On demand | On demand | On change |
| **Setup Required** | None | Custom Link | Job Hook |
| **Parameters** | All configurable | All configurable | Pre-configured |
| **Dry Run** | User choice | User choice | Hook config |
| **Use Case** | Testing, bulk ops | Quick provisioning | Continuous compliance |
| **Safety** | Manual review | Manual review | Automatic (with dry run) |
| **Convenience** | Low (navigate to Jobs) | High (one click) | Very High (automatic) |

---

## Code Reusability Example

Here's how another job could also call ProvisionDevice:

```python
# In another job file, e.g., bulk_provision.py

from nautobot.apps.jobs import Job, register_jobs
from nautobot.dcim.models import Device
from .provision_device import ProvisionDevice

class BulkProvision(Job):
    """Provision multiple devices at once."""
    
    class Meta:
        name = "Bulk Provision Devices"
        description = "Provision all devices in a location"
    
    def run(self):
        # Get all devices in a location
        devices = Device.objects.filter(location__name="Lab")
        
        # Import the provision job
        provision_job = ProvisionDevice()
        provision_job.logger = self.logger
        
        # Provision each device
        for device in devices:
            self.logger.info(f"Provisioning {device.name}...")
            provision_job.run(
                device=device,
                dry_run=False,
                replace_config=False,
                commit_changes=True
            )

register_jobs(BulkProvision)
```

This demonstrates the reusability of the Provision Device Job!

---

## Summary

The provisioning system is designed with flexibility in mind:

✅ **One Core Job** - `provision_device.py` contains all provisioning logic  
✅ **Three Trigger Methods** - Manual, Button, Hook  
✅ **All Use Same Logic** - Consistent behavior  
✅ **Reusable by Other Jobs** - Import and call  
✅ **Shared Logging** - Unified execution logs  
✅ **Configurable** - Parameters for each method  
✅ **Safe** - Dry run, validation, error handling  

This architecture provides maximum flexibility while maintaining code simplicity and reusability! 🚀

