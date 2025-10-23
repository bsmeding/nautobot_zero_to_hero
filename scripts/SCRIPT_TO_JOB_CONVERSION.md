# Converting Python Scripts to Nautobot Jobs

This guide demonstrates how to convert a standalone Python script to a Nautobot Job using a real example from this repository.

## Example: Fix Network Connectivity Script

We'll convert `4b_config_arista_template_fix.py` to a Nautobot Job.

### Original Script (100 lines)
**File:** `4b_config_arista_template_fix.py`

### Converted Job (250 lines with docs)
**File:** `nautobot_job_fix_connectivity.py`

---

## Side-by-Side Comparison

### 1. Imports

**Script (Before):**
```python
import pyeapi
from jinja2 import Environment, BaseLoader
```

**Job (After):**
```python
from nautobot.apps.jobs import Job, MultiObjectVar, BooleanVar, register_jobs
from nautobot.dcim.models import Device
from jinja2 import Environment, BaseLoader

try:
    import pyeapi
    PYEAPI_AVAILABLE = True
except ImportError:
    PYEAPI_AVAILABLE = False
```

**Changes:**
- ✅ Added Nautobot job imports
- ✅ Added Nautobot model imports
- ✅ Added graceful pyeapi import handling

---

### 2. Device Inventory

**Script (Before):**
```python
# Static hardcoded inventory
ARISTA_DEVICES = [
    {
        "name": "access1",
        "host": "172.20.20.11",
        "loopback_ip": "10.99.1.1",
        "interfaces": [
            {"name": "Ethernet2", "description": "Connected to workstation1", 
             "mode": "access", "vlan": "10"},
        ],
    },
    {
        "name": "rtr1",
        "host": "172.20.20.14",
        "loopback_ip": "10.0.0.254",
        "interfaces": [
            {"name": "Ethernet2", "description": "Connected to mgmt server", 
             "mode": "access", "vlan": "10"},
        ],
    },
]
```

**Job (After):**
```python
# Dynamic database query
devices = Device.objects.filter(
    platform__name__icontains="Arista",
    interfaces__name="Ethernet2"
).distinct()

# Then for each device, get data from database
device_data = {
    "name": device.name,
    "host": str(device.primary_ip4.address.ip),
    "loopback_ip": self._get_loopback_ip(device),
    "interfaces": [
        {
            "name": eth2.name,
            "description": eth2.description or "Data interface",
            "mode": "access",
            "vlan": str(eth2.untagged_vlan.vid) if eth2.untagged_vlan else "10",
        }
    ],
}
```

**Changes:**
- ✅ No hardcoding - pulls from Nautobot database
- ✅ Automatically discovers devices
- ✅ Uses actual interface descriptions from Nautobot
- ✅ Uses actual VLAN assignments from Nautobot
- ✅ Scalable - works with any number of devices

---

### 3. Output/Logging

**Script (Before):**
```python
print(f"\n>>> Rendered config for {device['name']} >>>")
print(rendered)
print("=" * 70)
print(f"Pushed rendered config to {hostname} ({host})")
```

**Job (After):**
```python
self.logger.info(f"Processing device: {device.name}")
self.logger.info("Rendered configuration:")
self.logger.info("-" * 80)
self.logger.info(rendered_config)
self.logger.info("-" * 80)
self.logger.success(f"Configuration pushed to {device.name}")
```

**Changes:**
- ✅ Structured logging with levels (info, success, error, warning)
- ✅ Logs stored in Nautobot (Jobs → Job Results)
- ✅ Better formatting and organization
- ✅ Searchable and trackable

---

### 4. Error Handling

**Script (Before):**
```python
def push_config(host: str, hostname: str, rendered_cfg: str) -> None:
    """Push rendered configuration to device via eAPI."""
    connection = pyeapi.connect(...)
    node = pyeapi.client.Node(connection)
    node.config(config_cmds)
    node.enable("write memory")
    # No error handling!
```

**Job (After):**
```python
def _push_config_to_device(self, device, rendered_config, commit_changes):
    """Push configuration to device via eAPI."""
    try:
        connection = pyeapi.connect(...)
        node = pyeapi.client.Node(connection)
        node.config(config_cmds)
        
        if commit_changes:
            node.enable("write memory")
            self.logger.success(f"Configuration saved on {device.name}")
        
    except Exception as e:
        self.logger.error(f"Failed to configure {device.name}: {e}")
        import traceback
        self.logger.debug(traceback.format_exc())
```

**Changes:**
- ✅ Try/except blocks
- ✅ Detailed error messages
- ✅ Traceback logging for debugging
- ✅ Job continues even if one device fails

---

### 5. Execution Flow

**Script (Before):**
```python
def main() -> None:
    """Render Jinja2 template for each device and push configuration."""
    env = Environment(loader=BaseLoader(), trim_blocks=True, lstrip_blocks=True)
    tmpl = env.from_string(TEMPLATE)

    for device in ARISTA_DEVICES:
        rendered = tmpl.render(device=device)
        print(f"\n>>> Rendered config for {device['name']} >>>")
        print(rendered)
        push_config(device["host"], device["name"], rendered)

if __name__ == "__main__":
    main()
```

**Job (After):**
```python
def run(self, devices=None, dry_run=True, commit_changes=True):
    """Main execution method."""
    # Check dependencies
    if not PYEAPI_AVAILABLE:
        self.logger.error("pyeapi library is not installed")
        return

    # Auto-discover devices if not specified
    if not devices:
        devices = self._discover_devices()
    
    # Process each device
    for device in devices:
        self._process_device(device, dry_run, commit_changes)
```

**Changes:**
- ✅ Job framework instead of `if __name__ == "__main__"`
- ✅ Parameters for configuration (dry_run, commit_changes)
- ✅ Better organization with helper methods
- ✅ Dependency checking

---

### 6. New Features Added

**Script Had:** Basic configuration push

**Job Has:**
- ✅ **Dry run mode** - Preview before applying
- ✅ **Device selection** - Choose specific devices or auto-discover
- ✅ **Database integration** - Pulls data from Nautobot
- ✅ **Commit control** - Choose whether to save config
- ✅ **Error handling** - Graceful failure handling
- ✅ **Logging** - Structured, searchable logs
- ✅ **UI integration** - Run from Nautobot web interface
- ✅ **API access** - Can be triggered via API
- ✅ **Scheduling** - Can be scheduled to run automatically
- ✅ **Audit trail** - All executions logged

---

## Conversion Process

### Step 1: Create Job Class

```python
from nautobot.apps.jobs import Job, register_jobs

class FixNetworkConnectivity(Job):
    class Meta:
        name = "Fix Network Connectivity"
        description = "Enable Ethernet2 interfaces"
    
    def run(self):
        # Your code here
        pass

register_jobs(FixNetworkConnectivity)
```

### Step 2: Add Parameters

Convert script arguments to Job parameters:

```python
devices = MultiObjectVar(
    description="Devices to configure",
    model=Device,
    required=False,
)

dry_run = BooleanVar(
    description="Preview without applying",
    default=True,
)
```

### Step 3: Replace Hardcoded Data

**Before:**
```python
ARISTA_DEVICES = [{"name": "access1", "host": "172.20.20.11"}]
```

**After:**
```python
devices = Device.objects.filter(
    platform__name__icontains="Arista"
)
```

### Step 4: Replace print() with Logger

**Before:**
```python
print(f"Processing {device_name}")
print(f"Error: {error}")
```

**After:**
```python
self.logger.info(f"Processing {device.name}")
self.logger.error(f"Error: {error}")
```

### Step 5: Add Error Handling

Wrap risky operations in try/except:

```python
try:
    connection = pyeapi.connect(...)
    node.config(commands)
except Exception as e:
    self.logger.error(f"Failed: {e}")
```

### Step 6: Register the Job

```python
register_jobs(FixNetworkConnectivity)
```

---

## Benefits of Conversion

| Feature | Script | Job |
|---------|--------|-----|
| **Data Source** | Hardcoded | Nautobot database |
| **Scalability** | Fixed list | Any number of devices |
| **UI Access** | Command line only | Web interface |
| **Logging** | stdout | Structured database logs |
| **Error Handling** | None/basic | Comprehensive |
| **Parameters** | Edit code | UI form/API |
| **Scheduling** | Manual/cron | Nautobot scheduler |
| **Audit Trail** | None | Full execution history |
| **Permissions** | OS-level | Nautobot RBAC |
| **Integration** | Standalone | Part of Nautobot ecosystem |
| **Testing** | Edit and run | Dry-run mode |
| **Monitoring** | Manual | Job Results page |

---

## When to Convert

### Convert to Job When:

✅ **Need database integration** - Pull data from Nautobot  
✅ **Multiple users** - Team needs access via UI  
✅ **Audit requirements** - Need execution logs  
✅ **Scheduling needed** - Run automatically  
✅ **Parameter flexibility** - Different options per run  
✅ **Error tracking** - Better error reporting  
✅ **Integration** - Use with webhooks, hooks, etc.  

### Keep as Script When:

✋ **One-time use** - Won't run again  
✋ **External tools only** - No Nautobot data needed  
✋ **Quick prototyping** - Testing concepts  
✋ **Simple tasks** - No parameters or error handling needed  

---

## Conversion Checklist

- [ ] Create Job class extending `Job`
- [ ] Add Meta class with name and description
- [ ] Convert function to `run()` method
- [ ] Add job parameters (ObjectVar, BooleanVar, etc.)
- [ ] Replace hardcoded data with database queries
- [ ] Replace print() with self.logger methods
- [ ] Add try/except blocks
- [ ] Add input validation
- [ ] Add helper methods for organization
- [ ] Call register_jobs()
- [ ] Test with dry-run mode
- [ ] Test with actual execution

---

## Testing the Converted Job

### 1. Add to __init__.py

```python
# In /jobs/jobs/__init__.py
from . import fix_network_connectivity
```

### 2. Restart Nautobot

```bash
docker compose restart nautobot
```

### 3. Test via UI

```
Jobs → Jobs → Fix Network Connectivity
Devices: (leave empty for auto-discovery)
Dry run: ✅ Enabled
Run Job
```

### 4. Review Logs

```
Jobs → Job Results
Click on latest execution
Review detailed logs
```

### 5. Run Live

```
Jobs → Jobs → Fix Network Connectivity
Devices: Select specific devices
Dry run: ❌ Disabled
Commit changes: ✅ Enabled
Run Job
```

---

## Advanced Enhancements

Once converted, you can add advanced features:

### 1. Use Secrets for Credentials

```python
username, password = self._get_credentials(device)

connection = pyeapi.connect(
    transport="https",
    host=host,
    username=username,  # From secrets
    password=password,  # From secrets
    port=443,
)
```

### 2. Use Config Context

```python
# Get site-specific settings from config context
loopback_subnet = device.config_context.get('loopback_subnet', '10.99.0.0/16')
```

### 3. Add Job Button

Create Custom Link for one-click access:
```
URL: /extras/jobs/fix_network_connectivity.FixNetworkConnectivity/run/?devices={{ obj.pk }}
```

### 4. Trigger from Hooks

Call from device hook:
```python
from .fix_network_connectivity import FixNetworkConnectivity

fix_job = FixNetworkConnectivity()
fix_job.run(devices=[device], dry_run=False)
```

---

## File Comparison

### Original Script Structure

```
4b_config_arista_template_fix.py (103 lines)
├── Imports (3 lines)
├── ARISTA_DEVICES list (33 lines)
├── TEMPLATE string (22 lines)
├── push_config() function (18 lines)
├── main() function (14 lines)
└── __main__ block (3 lines)
```

### Converted Job Structure

```
nautobot_job_fix_connectivity.py (270 lines)
├── Imports (10 lines)
├── Job class (250 lines)
│   ├── Meta class (5 lines)
│   ├── Parameters (20 lines)
│   ├── TEMPLATE (22 lines - same as original)
│   ├── run() method (25 lines)
│   ├── _discover_devices() (15 lines - NEW)
│   ├── _process_device() (25 lines)
│   ├── _validate_device() (20 lines - NEW)
│   ├── _get_device_data() (30 lines - replaces hardcoded dict)
│   ├── _get_loopback_ip() (20 lines)
│   ├── _render_config() (10 lines - same logic)
│   └── _push_config_to_device() (45 lines - enhanced)
└── register_jobs() (1 line)
```

---

## Key Conversion Patterns

### Pattern 1: Hardcoded List → Database Query

**Before:**
```python
DEVICES = [
    {"name": "switch1", "ip": "10.0.0.1"},
    {"name": "switch2", "ip": "10.0.0.2"},
]
```

**After:**
```python
devices = Device.objects.filter(role__name="Access Switch")
for device in devices:
    ip = str(device.primary_ip4.address.ip)
```

---

### Pattern 2: print() → self.logger

**Before:**
```python
print(f"Processing {name}")
print(f"Error: {error}")
```

**After:**
```python
self.logger.info(f"Processing {device.name}")
self.logger.error(f"Error: {error}")
```

---

### Pattern 3: main() → run()

**Before:**
```python
def main():
    for device in DEVICES:
        process(device)

if __name__ == "__main__":
    main()
```

**After:**
```python
class MyJob(Job):
    def run(self):
        devices = Device.objects.all()
        for device in devices:
            self._process(device)
```

---

### Pattern 4: Global Config → Job Parameters

**Before:**
```python
# At top of file
DRY_RUN = True
COMMIT = False

def main():
    if not DRY_RUN:
        commit_config()
```

**After:**
```python
class MyJob(Job):
    dry_run = BooleanVar(default=True)
    commit = BooleanVar(default=False)
    
    def run(self, dry_run, commit):
        if not dry_run:
            self._commit_config()
```

---

### Pattern 5: Direct Execution → Helper Methods

**Before:**
```python
def main():
    # 100 lines of code all in one function
    connect()
    get_data()
    process()
    push_config()
```

**After:**
```python
class MyJob(Job):
    def run(self):
        data = self._get_data()
        config = self._process_data(data)
        self._push_config(config)
    
    def _get_data(self):
        # 20 lines
    
    def _process_data(self, data):
        # 30 lines
    
    def _push_config(self, config):
        # 25 lines
```

---

## Common Pitfalls

### Pitfall 1: Forgetting to Register

```python
class MyJob(Job):
    def run(self):
        pass

# Don't forget this!
register_jobs(MyJob)
```

### Pitfall 2: Not Adding to __init__.py

```python
# In /jobs/jobs/__init__.py
from . import my_new_job  # Must import!
```

### Pitfall 3: Using print() Instead of Logger

```python
# ❌ Wrong
print("Processing device")

# ✅ Correct
self.logger.info("Processing device")
```

### Pitfall 4: Hardcoding Credentials

```python
# ❌ Wrong
username = "admin"
password = "admin"

# ✅ Better
username, password = self._get_credentials(device)
```

---

## Testing Strategy

### 1. Test Original Script

```bash
python 4b_config_arista_template_fix.py
```

Verify it works as expected.

### 2. Convert to Job

Follow conversion patterns above.

### 3. Test Job with Dry Run

```
Jobs → Jobs → Your Job
Dry run: ✅ Enabled
Run Job
```

Compare output with original script.

### 4. Test on One Device

```
Jobs → Jobs → Your Job
Devices: Select one test device
Dry run: ❌ Disabled
Run Job
```

Verify changes on device.

### 5. Test on All Devices

```
Jobs → Jobs → Your Job
Devices: Select all or leave empty
Dry run: ❌ Disabled
Run Job
```

---

## Real-World Example

Our conversion adds these capabilities:

**Original Script Capabilities:**
- Configure 2 hardcoded devices
- Enable Ethernet2 interfaces
- Add loopback interfaces
- Basic output

**Converted Job Capabilities:**
- Configure ANY Arista devices in Nautobot
- Auto-discover devices with Ethernet2
- Pull interface descriptions from Nautobot
- Pull VLAN assignments from Nautobot
- Dry-run preview mode
- Optional commit to startup
- Structured logging
- Error handling per device
- Web UI access
- API access
- Audit trail
- Can be scheduled
- Can be triggered by webhooks
- Integrates with other jobs

---

## Summary

Converting scripts to jobs provides:

✅ **Database integration** - Single source of truth  
✅ **Web interface** - No command line needed  
✅ **Better logging** - Searchable, persistent  
✅ **Error handling** - Production-ready  
✅ **Parameters** - Flexible configuration  
✅ **Audit trail** - Who ran what when  
✅ **Scalability** - Works with growing inventory  
✅ **Integration** - Part of Nautobot ecosystem  

---

## Files in This Example

- **`4b_config_arista_template_fix.py`** - Original script (103 lines)
- **`nautobot_job_fix_connectivity.py`** - Converted job (270 lines)
- **`SCRIPT_TO_JOB_CONVERSION.md`** - This guide

Use these files to demonstrate the migration path from standalone scripts to Nautobot Jobs!

---

**Happy converting!** 🚀

