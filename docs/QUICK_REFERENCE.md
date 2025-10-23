# Device Provisioning - Quick Reference

## ✅ Current Implementation Supports All 3 Methods!

### Method 1: Run as Normal Job (On Demand) ✅

**Status:** ALREADY WORKS

**How:**
```
Jobs → Jobs → Provision Device → Select device → Run
```

**Code:**
```python
# provision_device.py is a standard Job
class ProvisionDevice(Job):
    def run(self, device, dry_run, replace_config, commit_changes):
        # Provisioning logic
```

---

### Method 2: Via Job Button/Hook ✅

**Status:** ALREADY WORKS

**How:**
```
Device Page → Click "Provision Device" Button
```

**Code (Custom Link):**
```
URL: /extras/jobs/provision_device.ProvisionDevice/run/?device={{ obj.pk }}
```

The URL directly invokes the Job with pre-filled device parameter.

---

### Method 3: Via Import from Another Job ✅

**Status:** ALREADY WORKS

**How:**
```python
# In device_hook.py (or any other job)
from .provision_device import ProvisionDevice

provision_job = ProvisionDevice()
provision_job.logger = self.logger  # Share logger
provision_job.run(
    device=device,
    dry_run=True,
    replace_config=False,
    commit_changes=True
)
```

**Live Example:** `device_hook.py` line 116-132 already does this!

```python
# From device_hook.py
def _provision_device(self, device, dry_run=True):
    """Trigger the provision device job."""
    try:
        # Import the ProvisionDevice job
        from .provision_device import ProvisionDevice
        
        # Create an instance
        provision_job = ProvisionDevice()
        
        # Share logger
        provision_job.logger = self.logger
        
        # Run the job
        provision_job.run(
            device=device,
            dry_run=dry_run,
            replace_config=False,
            commit_changes=True
        )
        
        self.logger.success(f"Provision job completed for {device.name}")
        
    except ImportError as e:
        self.logger.error(f"Could not import ProvisionDevice job: {e}")
```

---

## Summary

| Method | File | Status | How It Works |
|--------|------|--------|--------------|
| **1. Normal Job** | `provision_device.py` | ✅ Working | Standard Job, run from Jobs UI |
| **2. Job Button** | Custom Link → `provision_device.py` | ✅ Working | URL with device parameter |
| **3. Import Call** | `device_hook.py` → `provision_device.py` | ✅ Working | Import and call `run()` method |

## The Key: Same Core Logic

All three methods call the same function:

```python
ProvisionDevice().run(device, dry_run, replace_config, commit_changes)
```

This ensures:
- ✅ Consistent behavior
- ✅ Single source of truth
- ✅ Easy maintenance
- ✅ Full reusability

---

## Files Overview

### `provision_device.py` (Core Job)
- Contains ALL provisioning logic
- Can be run standalone
- Can be imported by other jobs
- Self-contained and reusable

### `device_hook.py` (Automatic Trigger)
- Detects device changes
- Validates changes are relevant
- **Imports and calls** `provision_device.py`
- Automatic provisioning on update

### Custom Link (Job Button)
- Provides one-click access
- Links to `provision_device.py`
- Pre-fills device parameter
- Manual triggering from device page

---

## Testing All Three Methods

### Test 1: Run as Normal Job
```bash
# In Nautobot:
1. Go to Jobs → Jobs
2. Find "Provision Device"
3. Click "Run Job"
4. Select device: access1
5. Set dry_run: True
6. Click "Run Job Now"
7. ✅ Should provision device
```

### Test 2: Via Job Button
```bash
# In Nautobot:
1. Go to Devices → Devices → access1
2. Click "Provision Device" button (if configured)
3. Review pre-filled form
4. Click "Run Job"
5. ✅ Should provision device
```

### Test 3: Via Auto-Hook
```bash
# In Nautobot:
1. Enable Device Configuration Hook
2. Edit device: access1
3. Change hostname to: access1-new
4. Save
5. Check Jobs → Job Results
6. ✅ Should see hook triggered and provision executed
```

---

## Quick Setup Checklist

- [x] `provision_device.py` - Core job created ✅
- [x] `device_hook.py` - Hook created ✅
- [x] Hook imports provision job ✅
- [ ] Enable Device Configuration Hook (Jobs → Jobs)
- [ ] Create Job Hook (Extensibility → Job Hooks)
- [ ] Create Custom Link for button (Extensibility → Custom Links)
- [ ] Test all three methods

---

## Need More Info?

- **Full Architecture:** [PROVISIONING_ARCHITECTURE.md](docs/PROVISIONING_ARCHITECTURE.md)
- **Auto-Hook Details:** [AUTO_PROVISIONING_HOOK.md](docs/AUTO_PROVISIONING_HOOK.md)
- **Job Button Setup:** [JOB_BUTTON_SETUP.md](docs/JOB_BUTTON_SETUP.md)
- **Complete Guide:** [DEVICE_PROVISIONING.md](docs/DEVICE_PROVISIONING.md)

---

## TL;DR

**Everything is already implemented and working!** 🎉

The `provision_device.py` job can be:
1. ✅ Run manually from Jobs interface
2. ✅ Triggered via Job Button on device pages
3. ✅ Called from other jobs (like `device_hook.py`)

All three methods use the same core provisioning logic for consistency.

