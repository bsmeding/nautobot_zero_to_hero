# Device Provisioning with Golden Config

This guide explains how to use the Device Provisioning job to automatically configure network devices using Golden Config templates and NAPALM.

## Overview

The Device Provisioning job automates the process of:
1. **Generating** intended configuration from Golden Config templates
2. **Deploying** the configuration to the device
3. **Committing** changes to startup-config
4. **Verifying** the deployment was successful

This job can be triggered:
- **Manually** from the Jobs interface
- **Via Job Button** on device detail pages (one-click provisioning)
- **Via API** for automation workflows

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Nautobot Database                        │
│  • Device Info (hostname, IP, platform, role)               │
│  • Config Context (VLANs, NTP, SNMP, etc.)                  │
│  • Golden Config Templates (Jinja2)                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Golden Config Plugin                            │
│  • Renders Jinja2 templates with device data                │
│  • Stores intended configuration                             │
│  • GraphQL queries for device variables                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            Provision Device Job                              │
│  • Retrieves intended config from Golden Config             │
│  • Connects to device via NAPALM                             │
│  • Loads configuration (merge or replace)                    │
│  • Shows diff of changes                                     │
│  • Commits to startup-config                                 │
│  • Verifies deployment                                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Network Device                              │
│  • Configuration applied via NAPALM                          │
│  • Saved to startup-config                                   │
│  • Running in production                                     │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### 1. Install Required Plugins

Ensure you have the following installed:

```bash
pip install nautobot-golden-config napalm
```

### 2. Device Requirements

Each device must have:
- ✅ **Platform** configured with NAPALM driver (e.g., "eos" for Arista)
- ✅ **Primary IPv4 address** assigned
- ✅ **Device role** assigned (for template matching)
- ✅ **Reachable** via management network
- ✅ **SSH/API enabled** on the device

### 3. Golden Config Setup

1. **Create Jinja2 Templates** (already done in `/templates/` directory)
2. **Upload templates to Golden Config** plugin
3. **Assign templates** to platforms/roles
4. **Run "Generate Intended Configurations"** job for your devices

## Job Parameters

### Device (Required)
- **Type**: Device object
- **Description**: The device to provision
- **Usage**: Select from dropdown or passed via Job Button

### Dry Run (Optional)
- **Type**: Boolean
- **Default**: `True` (enabled)
- **Description**: When enabled, shows what would change without applying
- **Usage**: 
  - ✅ Enable for testing and previewing changes
  - ❌ Disable to actually deploy configuration

### Replace Config (Optional)
- **Type**: Boolean
- **Default**: `False` (disabled)
- **Description**: Replace entire configuration instead of merging
- **Warning**: ⚠️ Use with extreme caution! This will wipe the existing config
- **Usage**:
  - ✅ Enable for new device provisioning (zero-touch)
  - ❌ Disable for configuration updates/changes

### Commit Changes (Optional)
- **Type**: Boolean
- **Default**: `True` (enabled)
- **Description**: Save configuration to startup-config
- **Usage**:
  - ✅ Enable to make changes persistent across reboots
  - ❌ Disable to only load to running-config (testing)

## Setting Up Job Button

A Job Button provides one-click device provisioning directly from the device detail page.

### Step 1: Create Custom Link (Job Button)

1. Navigate to **Extensibility → Custom Links**
2. Click **Add**
3. Configure the custom link:

**Basic Settings:**
- **Name**: `Provision Device`
- **Content Type**: `dcim | device`
- **Enabled**: ✅ Checked
- **New Window**: ✅ Checked (optional)

**Link Settings:**
- **Link Text**: `Provision Device`
- **Link URL**:
  ```django
  /extras/jobs/provision_device.ProvisionDevice/run/?device={{ obj.pk }}
  ```

- **Link Button Class**: `primary` (blue button) or `success` (green button)

**Visibility:**
- **Group Name**: `Actions` (groups with other action buttons)
- **Weight**: `100` (display order)

**Conditional Display (Optional):**

To only show the button for devices with platforms that support NAPALM:

- **Jinja2 Template Filter**:
  ```jinja2
  {{ obj.platform and obj.platform.napalm_driver and obj.primary_ip4 }}
  ```

### Step 2: Verify Button Appears

1. Navigate to any **Device** detail page
2. Look for the **"Provision Device"** button in the top right
3. Button should only appear if device meets requirements (if filter is set)

### Step 3: Using the Job Button

1. Click **"Provision Device"** button on device page
2. Review pre-filled device parameter
3. Configure job options:
   - ✅ **Dry Run**: Check to preview changes
   - ❌ **Replace Config**: Leave unchecked (unless new device)
   - ✅ **Commit Changes**: Check to save to startup-config
4. Click **Run Job**
5. Monitor job execution in real-time
6. Review output and configuration diff

## Usage Workflows

### Workflow 1: Test Device Provisioning (Safe)

```
1. Generate Golden Config intended configuration
   → Plugins → Golden Config → Generate Intended Configurations
   → Select device(s)
   → Run job

2. Preview the intended config
   → Navigate to device page
   → Click "Config" tab
   → Review "Intended Config"

3. Test provision with dry run
   → Click "Provision Device" button
   → ✅ Dry Run: Enabled
   → ❌ Replace Config: Disabled
   → ✅ Commit Changes: Enabled
   → Run Job
   → Review configuration diff

4. If diff looks good, provision for real
   → Run job again
   → ❌ Dry Run: Disabled
   → ❌ Replace Config: Disabled
   → ✅ Commit Changes: Enabled
   → Run Job
```

### Workflow 2: New Device Provisioning (Zero-Touch)

```
1. Add device to Nautobot
   → Set hostname, IP, platform, role

2. Generate intended configuration
   → Run Golden Config job

3. Provision with replace
   → Click "Provision Device" button
   → ✅ Dry Run: Enabled (first time)
   → ✅ Replace Config: Enabled
   → ✅ Commit Changes: Enabled
   → Review diff

4. Deploy if satisfied
   → Run again with Dry Run disabled
   → Device will be fully configured from scratch
```

### Workflow 3: Configuration Update

```
1. Update device data in Nautobot
   → Change interfaces, VLANs, IP addresses, etc.
   → Or update Config Context

2. Regenerate intended configuration
   → Run Golden Config job for affected devices

3. Deploy updates
   → Click "Provision Device" button
   → ❌ Dry Run: Disabled
   → ❌ Replace Config: Disabled (merge changes)
   → ✅ Commit Changes: Enabled
   → Run Job
```

### Workflow 4: Bulk Provisioning via API

```python
import requests

nautobot_url = "https://nautobot.example.com"
api_token = "your-api-token"

headers = {
    "Authorization": f"Token {api_token}",
    "Content-Type": "application/json"
}

# Get devices to provision
devices = requests.get(
    f"{nautobot_url}/api/dcim/devices/?role=access-switch&status=active",
    headers=headers
).json()["results"]

# Provision each device
for device in devices:
    job_data = {
        "device": device["id"],
        "dry_run": False,
        "replace_config": False,
        "commit_changes": True
    }
    
    response = requests.post(
        f"{nautobot_url}/api/extras/jobs/provision_device.ProvisionDevice/run/",
        headers=headers,
        json={"data": job_data}
    )
    
    print(f"Provisioning {device['name']}: {response.status_code}")
```

## Job Output Explanation

### Successful Dry Run Output

```
================================================================================
Starting provisioning for device: access1
================================================================================
Validating device configuration...
✅ Device validation passed
⚠️  No secrets group configured. Using default credentials (admin/admin)
--------------------------------------------------------------------------------
Generating intended configuration from Golden Config...
✅ Found existing intended config (last updated: 2025-10-18 10:30:00)
ℹ️  Config preview:
!
! Bootstrap configuration for access1 (Arista EOS)
! Management interface and SSH configuration
...
--------------------------------------------------------------------------------
Connecting to device and deploying configuration...
ℹ️  Device IP: 172.20.20.11
ℹ️  NAPALM Driver: eos
ℹ️  Mode: DRY RUN
ℹ️  Method: MERGE
ℹ️  Opening connection to 172.20.20.11...
✅ Connected to access1
ℹ️  Loading configuration to device...
ℹ️  MERGE mode: Configuration will be merged with existing
✅ Configuration loaded successfully
ℹ️  Generating configuration diff...
ℹ️  Configuration changes:
--------------------------------------------------------------------------------
+interface Ethernet2
+   no shutdown
+   description Connected to workstation1
--------------------------------------------------------------------------------
⚠️  DRY RUN mode: Discarding configuration changes
ℹ️  To apply these changes, run again with 'Dry run mode' unchecked
ℹ️  Connection closed
================================================================================
✅ Provisioning completed for access1
================================================================================
```

### Successful Live Deployment Output

```
================================================================================
Starting provisioning for device: access1
================================================================================
Validating device configuration...
✅ Device validation passed
ℹ️  Using username from secrets group
ℹ️  Using password from secrets group
--------------------------------------------------------------------------------
Generating intended configuration from Golden Config...
✅ Found existing intended config (last updated: 2025-10-18 10:30:00)
--------------------------------------------------------------------------------
Connecting to device and deploying configuration...
ℹ️  Device IP: 172.20.20.11
ℹ️  NAPALM Driver: eos
ℹ️  Mode: LIVE DEPLOYMENT
ℹ️  Method: MERGE
ℹ️  Opening connection to 172.20.20.11...
✅ Connected to access1
ℹ️  Loading configuration to device...
ℹ️  MERGE mode: Configuration will be merged with existing
✅ Configuration loaded successfully
ℹ️  Generating configuration diff...
ℹ️  Configuration changes:
--------------------------------------------------------------------------------
+interface Ethernet2
+   no shutdown
+   description Connected to workstation1
--------------------------------------------------------------------------------
ℹ️  Committing configuration changes...
✅ Configuration committed successfully and saved to startup-config
ℹ️  Verifying configuration...
✅ Device access1 is running with new configuration
ℹ️  Connection closed
================================================================================
✅ Provisioning completed for access1
================================================================================
```

## Troubleshooting

### Error: "Device has no platform configured"

**Solution:**
1. Navigate to device page
2. Edit device
3. Set **Platform** field (e.g., "Arista EOS")
4. Ensure platform has **NAPALM driver** configured

### Error: "Device has no primary IPv4 address"

**Solution:**
1. Navigate to device page
2. Click **IP Addresses** tab
3. Add IP address to management interface
4. Set as **Primary IPv4** address

### Error: "No Golden Config record found"

**Solution:**
1. Navigate to **Plugins → Golden Config**
2. Click **Generate Intended Configurations**
3. Select your device(s)
4. Run the job
5. Try provisioning again

### Error: "Connection error"

**Possible causes:**
- Device is not reachable (check network connectivity)
- Wrong IP address configured
- SSH/API not enabled on device
- Firewall blocking connection
- Incorrect credentials

**Solutions:**
1. Verify device is reachable: `ping <device-ip>`
2. Verify SSH is accessible: `ssh admin@<device-ip>`
3. Check device management interface is up
4. Verify credentials in Secrets Group
5. Check NAPALM driver is correct for platform

### Error: "Configuration deployment error"

**Possible causes:**
- Syntax error in generated configuration
- Configuration conflict
- Device rejected configuration

**Solutions:**
1. Review the configuration diff
2. Test configuration syntax on device manually
3. Check template for syntax errors
4. Verify device supports commands in template

## Security Considerations

### Credentials Management

**Best Practice:** Use Nautobot Secrets Groups

1. Navigate to **Secrets → Secrets Groups**
2. Create a secrets group (e.g., "Device Admin Credentials")
3. Add secrets:
   - **Username** secret
   - **Password** secret
4. Assign secrets group to devices

**Avoid:** Hardcoded credentials in job code

### Dry Run First

**Always test with dry run enabled** before deploying to production devices:
- ✅ Review configuration diff
- ✅ Verify no unexpected changes
- ✅ Confirm syntax is correct
- ✅ Check for breaking changes

### Replace Config Warning

**⚠️ DANGER:** Replace config mode will **completely wipe** the existing configuration.

Only use when:
- Provisioning a new device
- Performing disaster recovery
- You have a complete backup
- You've tested in lab environment

**Never use on production devices** without thorough testing!

## Advanced Configuration

### Custom NAPALM Arguments

Some devices require additional NAPALM connection arguments. Configure these in the Platform settings:

1. Navigate to **Devices → Platforms**
2. Edit platform (e.g., "Arista EOS")
3. Set **NAPALM Args** (JSON format):

```json
{
  "timeout": 60,
  "optional_args": {
    "port": 22,
    "transport": "ssh",
    "enable_password": "enablepass"
  }
}
```

### Extending the Job

The provision job can be extended with additional functionality:

```python
# jobs/jobs/provision_device.py

def _post_deployment_tasks(self, device):
    """Run additional tasks after deployment."""
    # Examples:
    # - Send notification
    # - Update device status
    # - Trigger compliance check
    # - Log to external system
    pass
```

## Integration with CI/CD

### GitLab CI Example

```yaml
provision-devices:
  stage: deploy
  script:
    - |
      for device in $(cat devices.txt); do
        curl -X POST "${NAUTOBOT_URL}/api/extras/jobs/provision_device.ProvisionDevice/run/" \
          -H "Authorization: Token ${NAUTOBOT_TOKEN}" \
          -H "Content-Type: application/json" \
          -d "{\"data\": {\"device\": \"${device}\", \"dry_run\": false}}"
      done
  only:
    - main
```

## Related Documentation

- [Golden Config Templates](../templates/README_GOLDEN_CONFIG_TEMPLATES.md)
- [Template Mapping](../templates/TEMPLATE_MAPPING.md)
- [NAPALM Documentation](https://napalm.readthedocs.io/)
- [Nautobot Golden Config Plugin](https://docs.nautobot.com/projects/golden-config/)

