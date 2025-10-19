# Automatic Device Provisioning Hook

This document describes the Device Configuration Hook that automatically provisions devices when they are created or updated in Nautobot.

## Overview

The Device Configuration Hook integrates with the Provision Device job to automatically keep device configurations synchronized with Nautobot as the source of truth. When a device is created or updated in Nautobot, the hook can automatically:

1. Detect configuration-relevant changes
2. Regenerate the intended configuration
3. Deploy the configuration to the device
4. Ensure the device always has the correct configuration

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   User Action                                │
│  • Create new device in Nautobot                            │
│  • Update device (hostname, IP, platform, role, location)   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Device Configuration Hook                       │
│              (DeviceJobHookReceiver)                        │
│                                                              │
│  1. Triggered on device create/update                       │
│  2. Checks if configuration-relevant fields changed         │
│  3. Validates device is ready for provisioning              │
│  4. Calls ProvisionDevice job                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Provision Device Job                            │
│                                                              │
│  1. Gets intended config from Golden Config                 │
│  2. Connects to device via NAPALM                           │
│  3. Loads configuration (merge mode)                        │
│  4. Shows diff and commits changes                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Network Device                              │
│  • Configuration automatically updated                       │
│  • Always in sync with Nautobot                             │
└─────────────────────────────────────────────────────────────┘
```

## Features

### Smart Triggering

The hook only triggers provisioning when **configuration-relevant fields** are changed:

- ✅ **name** - Hostname change
- ✅ **primary_ip4** - Management IP address change
- ✅ **platform** - Platform change (affects template selection)
- ✅ **role** - Device role change (affects template selection)
- ✅ **location** - Location change (may affect config context)
- ✅ **status** - Status change

Changes to other fields (like comments, asset tags, etc.) will NOT trigger provisioning.

### Safety Features

1. **Validation Checks**
   - Device must have a platform configured
   - Platform must have NAPALM driver
   - Device must have primary IPv4 address
   - Device status must be Active, Planned, or Staged

2. **Dry Run Mode**
   - Default: Enabled
   - Shows what would change without actually deploying
   - Safe for testing the hook

3. **Merge Mode Only**
   - Auto-provisioning always uses merge mode
   - Never replaces entire configuration
   - Reduces risk of breaking connectivity

4. **Comprehensive Logging**
   - All actions logged
   - Easy to track what happened
   - Troubleshooting information included

## Configuration Options

The hook has three configuration parameters:

### 1. auto_provision_on_create

**Type:** Boolean  
**Default:** `False`  
**Description:** Automatically provision device when created in Nautobot

**Use Case:** Zero-touch provisioning for new devices

**Example Workflow:**
```
1. Add new device to Nautobot
2. Set hostname, IP, platform, role
3. Device is automatically provisioned
4. Device ready for production
```

### 2. auto_provision_on_update

**Type:** Boolean  
**Default:** `True`  
**Description:** Automatically provision device when configuration-relevant fields are updated

**Use Case:** Maintain configuration compliance

**Example Workflow:**
```
1. Update device hostname in Nautobot
2. Hook detects hostname change
3. Golden Config regenerates intended config
4. Device is automatically updated
5. Device hostname matches Nautobot
```

### 3. dry_run

**Type:** Boolean  
**Default:** `True`  
**Description:** Run provisioning in dry-run mode (preview only)

**Use Case:** Safe testing before live deployment

**Example Workflow:**
```
1. Update device in Nautobot
2. Hook triggers with dry_run=True
3. See what would change in logs
4. No actual changes made to device
5. Once confident, set dry_run=False
```

## Setup Instructions

### Step 1: Enable the Hook

1. Navigate to **Jobs → Jobs**
2. Find **"Device Configuration Hook"**
3. Click **Edit Job**
4. Check **"Enabled"** checkbox
5. Click **Update**

### Step 2: Configure Job Hook

1. Navigate to **Extensibility → Job Hooks**
2. Click **+ Add**
3. Configure the Job Hook:

| Field | Value |
|-------|-------|
| **Name** | `Auto Provision Devices` |
| **Content Types** | `dcim \| device` |
| **Job** | `Device Configuration Hook` |
| **Enabled** | ✅ Checked |
| **Type Choices** | Select: `create`, `update` |

### Step 3: Configure Parameters

When creating the Job Hook, set parameters:

**For Testing (Recommended First):**
```json
{
  "auto_provision_on_create": false,
  "auto_provision_on_update": true,
  "dry_run": true
}
```

**For Production (After Testing):**
```json
{
  "auto_provision_on_create": true,
  "auto_provision_on_update": true,
  "dry_run": false
}
```

### Step 4: Test the Hook

1. **Edit a test device:**
   ```
   Devices → Devices → access1 → Edit
   Change hostname from "access1" to "access1-new"
   Save
   ```

2. **Check Job Results:**
   ```
   Jobs → Job Results
   Look for "Device Configuration Hook" execution
   Review logs
   ```

3. **Verify Behavior:**
   - Hook should trigger
   - Should detect hostname change
   - Should show config diff (if dry_run=True)
   - Should NOT deploy (if dry_run=True)

## Usage Examples

### Example 1: Update Device Hostname

**Scenario:** You need to rename a device

**Steps:**
1. Navigate to device page
2. Edit device
3. Change **Name** from `access1` to `access-switch-1`
4. Save

**What Happens:**
```
Hook Triggered: UPDATE
Device: access-switch-1
Changed fields: ['name']
Configuration-relevant fields changed: ['name']
Auto-provision on update is enabled
Triggering Device Provisioning Job...
Device access-switch-1 is ready for provisioning
Running provision job (dry_run=True)...
[... provision job output ...]
Configuration changes:
--------------------------------------------------------------------------------
-hostname access1
+hostname access-switch-1
--------------------------------------------------------------------------------
DRY RUN mode: Discarding configuration changes
```

### Example 2: Change Device IP Address

**Scenario:** Device management IP changed

**Steps:**
1. Navigate to **IP Addresses**
2. Find device's primary IP
3. Edit IP address
4. Or assign different IP as primary
5. Save

**What Happens:**
```
Hook Triggered: UPDATE
Device: access1
Changed fields: ['primary_ip4']
Configuration-relevant fields changed: ['primary_ip4']
Auto-provision on update is enabled
Triggering Device Provisioning Job...
Device access1 is ready for provisioning
Running provision job (dry_run=True)...
[... provision job output ...]
Configuration changes:
--------------------------------------------------------------------------------
-   ip address 172.20.20.11/24
+   ip address 172.20.20.21/24
--------------------------------------------------------------------------------
DRY RUN mode: Discarding configuration changes
```

### Example 3: Change Device Role

**Scenario:** Device role changes from Access to Distribution

**Steps:**
1. Navigate to device page
2. Edit device
3. Change **Role** from `Access Switch` to `Distribution Switch`
4. Save

**What Happens:**
```
Hook Triggered: UPDATE
Device: access1
Changed fields: ['role']
Configuration-relevant fields changed: ['role']
Auto-provision on update is enabled
Triggering Device Provisioning Job...
Device access1 is ready for provisioning
Running provision job (dry_run=True)...
[... provision job output ...]
Note: New template assigned based on role
[... different configuration due to different template ...]
```

### Example 4: Non-Relevant Change

**Scenario:** You update device comments (not configuration-relevant)

**Steps:**
1. Navigate to device page
2. Edit device
3. Change **Comments** field
4. Save

**What Happens:**
```
Hook Triggered: UPDATE
Device: access1
Changed fields: ['comments']
No configuration-relevant fields changed. Skipping provisioning.
```

Device is NOT provisioned - hook is smart enough to skip.

## Monitoring and Logs

### Viewing Hook Executions

1. Navigate to **Jobs → Job Results**
2. Filter by:
   - **Job**: `Device Configuration Hook`
   - **Status**: All statuses
3. Click on any result to view detailed logs

### Log Output Example

**Successful Execution:**
```
================================================================================
Device Hook Triggered: UPDATED
Device: access1 (12345678-1234-1234-1234-123456789abc)
================================================================================
✅ Device updated: access1
ℹ️  Changed fields: ['name', 'primary_ip4']
ℹ️  Configuration-relevant fields changed: ['name', 'primary_ip4']
ℹ️  Auto-provision on update is enabled
--------------------------------------------------------------------------------
ℹ️  Triggering Device Provisioning Job...
✅ Device access1 is ready for provisioning
ℹ️  Running provision job for access1 (dry_run=True)...
================================================================================
Starting provisioning for device: access1
================================================================================
ℹ️  Validating device configuration...
✅ Device validation passed
⚠️  No secrets group configured. Using default credentials (admin/admin)
--------------------------------------------------------------------------------
ℹ️  Generating intended configuration from Golden Config...
✅ Found existing intended config (last updated: 2025-10-19 10:30:00)
--------------------------------------------------------------------------------
ℹ️  Connecting to device and deploying configuration...
✅ Connected to access1
✅ Configuration loaded successfully
ℹ️  Configuration changes:
--------------------------------------------------------------------------------
[... diff output ...]
--------------------------------------------------------------------------------
⚠️  DRY RUN mode: Discarding configuration changes
✅ Provision job completed for access1
```

### Common Log Messages

| Message | Meaning |
|---------|---------|
| `Auto-provision on update is enabled` | Hook will trigger provisioning |
| `Auto-provision on update is disabled` | Hook will NOT trigger provisioning |
| `No configuration-relevant fields changed` | No provisioning needed |
| `Device is not ready for provisioning` | Device validation failed |
| `Device ... is ready for provisioning` | Validation passed, provisioning will run |
| `DRY RUN mode: Discarding configuration changes` | Preview only, no actual changes |
| `Configuration committed successfully` | Changes deployed to device |

## Troubleshooting

### Hook Doesn't Trigger

**Issue:** Hook not running when device is updated

**Solutions:**
1. Check if hook is enabled:
   ```
   Jobs → Jobs → Device Configuration Hook → Ensure "Enabled" is checked
   ```

2. Check Job Hook configuration:
   ```
   Extensibility → Job Hooks
   Ensure hook exists and is enabled
   Ensure "update" is in Type Choices
   ```

3. Check if field is configuration-relevant:
   ```
   Only these fields trigger provisioning:
   - name
   - primary_ip4
   - platform
   - role
   - location
   - status
   ```

### Hook Triggers But Skips Provisioning

**Issue:** Hook runs but says "Device is not ready for provisioning"

**Solutions:**
1. Check device has platform:
   ```
   Device → Platform field must be set
   ```

2. Check platform has NAPALM driver:
   ```
   Devices → Platforms → [Your Platform]
   NAPALM Driver field must be set
   ```

3. Check device has primary IP:
   ```
   Device → Primary IPv4 field must be set
   ```

4. Check device status:
   ```
   Device → Status must be Active, Planned, or Staged
   ```

### Hook Runs But Provisioning Fails

**Issue:** Hook triggers and validation passes but provisioning fails

**Solutions:**
1. Review provision job logs in Job Results
2. Check device connectivity (ping test)
3. Verify credentials are correct
4. Ensure Golden Config has generated intended config
5. Check NAPALM driver is correct for platform

### Dry Run Mode Stuck

**Issue:** Hook always runs in dry run mode even when set to False

**Solution:**
1. Check Job Hook parameters:
   ```
   Extensibility → Job Hooks → [Your Hook] → Edit
   Verify parameters JSON has "dry_run": false
   ```

2. Update Job Hook:
   ```json
   {
     "auto_provision_on_create": true,
     "auto_provision_on_update": true,
     "dry_run": false
   }
   ```

## Best Practices

### 1. Start with Dry Run Enabled

Always test with `dry_run=true` first:
- Verify hook triggers correctly
- Review configuration diffs
- Ensure no unexpected changes
- Switch to `dry_run=false` only after thorough testing

### 2. Use Selective Auto-Provision

Consider different strategies:

**Conservative:**
```json
{
  "auto_provision_on_create": false,
  "auto_provision_on_update": false,
  "dry_run": true
}
```
Use manual provisioning via Job Button

**Moderate (Recommended):**
```json
{
  "auto_provision_on_create": false,
  "auto_provision_on_update": true,
  "dry_run": true
}
```
Auto-provision on updates, manual for new devices

**Aggressive:**
```json
{
  "auto_provision_on_create": true,
  "auto_provision_on_update": true,
  "dry_run": false
}
```
Full automation for both creates and updates

### 3. Monitor Job Results

Regularly review Job Results:
- Check for failures
- Review configuration changes
- Identify patterns
- Optimize templates

### 4. Maintain Golden Config

Ensure Golden Config is up to date:
- Run "Generate Intended Configurations" regularly
- Or set up scheduled job
- Hook relies on intended config being current

### 5. Test in Lab First

Before enabling in production:
1. Test with lab devices
2. Verify behavior with dry run
3. Test actual provisioning on one device
4. Gradually roll out to more devices
5. Enable for production only after confidence

## Advanced Configuration

### Custom Field Triggers

To add more fields that trigger provisioning, edit the hook:

```python
# In device_hook.py, line 75
config_relevant_fields = [
    'name',
    'primary_ip4',
    'platform',
    'role',
    'location',
    'status',
    'serial',        # Add serial number
    'asset_tag',     # Add asset tag
    # Add more fields as needed
]
```

### Conditional Provisioning

Add custom logic to control when provisioning happens:

```python
# In device_hook.py, in run() method
if action == "updated":
    # Only provision if device is in production location
    if device.location and device.location.name == "Production":
        if auto_provision_on_update:
            self._provision_device(device, dry_run)
    else:
        self.logger.info("Device not in production. Skipping provisioning.")
```

### Async Provisioning

For better performance with many devices, consider running provisioning asynchronously:

```python
# Use Celery or similar for background processing
from django_rq import enqueue
enqueue(self._provision_device, device, dry_run)
```

## Integration with CI/CD

### GitOps Workflow

1. **Update Nautobot via API**
   ```python
   import requests
   
   response = requests.patch(
       f"{nautobot_url}/api/dcim/devices/{device_id}/",
       headers={"Authorization": f"Token {token}"},
       json={"name": "new-hostname"}
   )
   ```

2. **Hook Automatically Triggers**
   - Detects change
   - Provisions device
   - Logs results

3. **Verify Results**
   ```python
   job_results = requests.get(
       f"{nautobot_url}/api/extras/job-results/",
       headers={"Authorization": f"Token {token}"},
       params={"job__name": "Device Configuration Hook"}
   )
   ```

## Security Considerations

### 1. Credentials

- Store credentials in Secrets Groups
- Use least-privilege accounts
- Rotate credentials regularly
- Never hardcode credentials

### 2. Change Control

- Dry run mode for change review
- Approval workflows before enabling
- Audit logs for all changes
- Rollback procedures

### 3. Access Control

- Limit who can enable/disable hook
- Limit who can modify hook parameters
- Review permissions regularly

### 4. Network Security

- Ensure management network is secure
- Use encrypted protocols (SSH/HTTPS)
- Implement firewall rules
- Monitor for unauthorized access

## Related Documentation

- [Device Provisioning Guide](./DEVICE_PROVISIONING.md)
- [Provisioning Quick Start](./PROVISIONING_QUICKSTART.md)
- [Job Button Setup](./JOB_BUTTON_SETUP.md)
- [Golden Config Templates](../templates/README_GOLDEN_CONFIG_TEMPLATES.md)

## Summary

The Device Configuration Hook provides:

✅ **Automatic provisioning** when devices are created/updated  
✅ **Smart triggering** - only on configuration-relevant changes  
✅ **Safety features** - validation, dry run, merge-only  
✅ **Comprehensive logging** - track all actions  
✅ **Flexible configuration** - enable/disable per scenario  
✅ **Integration with Golden Config** - seamless workflow  
✅ **Production-ready** - tested and documented  

With this hook enabled, Nautobot becomes the true **source of truth** for your network, automatically keeping device configurations in sync! 🚀

