# Device Provisioning Quick Start Guide

This guide walks you through the complete workflow from creating Jinja2 templates to provisioning devices with one-click buttons.

## Overview

The complete provisioning workflow consists of:

```
1. Create Jinja2 Templates ────┐
2. Upload to Golden Config     │
3. Configure Template Mapping  │──► Source of Truth
4. Assign Config Context       │
                               │
5. Generate Intended Config ───┘
                               │
6. Create Job Button ──────────┤
7. Provision Device ───────────┴──► Device Configuration
8. Verify Deployment
```

## Prerequisites

✅ Nautobot installed and running  
✅ Golden Config plugin installed  
✅ NAPALM installed  
✅ Devices added to Nautobot  
✅ Network connectivity to devices  

## Part 1: Template Setup (One-Time)

### Step 1: Jinja2 Templates (Already Created)

The templates are already created in `/templates/` directory:

- `arista_generic.j2` - Generic Arista device
- `arista_dist_switch.j2` - Distribution switches
- `arista_access_switch1.j2` - Access switches (type 1)
- `arista_access_switch2.j2` - Access switches (type 2)
- `arista_router.j2` - Routers
- `alpine_mgmt_server.j2` - Management servers
- `alpine_workstation.j2` - Workstations

### Step 2: Upload Templates to Golden Config

1. Navigate to **Plugins → Golden Config → Configuration Templates**
2. Click **+ Add**
3. For each template:

**Example: Arista Access Switch Template**

| Field | Value |
|-------|-------|
| **Name** | `Arista Access Switch` |
| **Platform** | Select `Arista EOS` |
| **Content** | Copy content from `arista_access_switch1.j2` |

4. Click **Create**

Repeat for all templates.

### Step 3: Assign Templates to Platforms/Roles

Golden Config uses template mapping to determine which template to use for each device.

**Option A: By Platform + Role**

1. Navigate to **Plugins → Golden Config → Template Mappings**
2. Click **+ Add**
3. Configure:
   - **Platform**: `Arista EOS`
   - **Role**: `access-switch`
   - **Template**: `Arista Access Switch`
4. Repeat for other platform/role combinations

**Option B: By Tags**

Add tags to devices and map templates to tags:
- Tag: `provision-type-dist` → Template: `Arista Dist Switch`
- Tag: `provision-type-access` → Template: `Arista Access Switch`

## Part 2: Device Configuration

### Step 4: Configure Devices in Nautobot

For each device, ensure the following are set:

#### Required Fields

| Field | Example | Notes |
|-------|---------|-------|
| **Name** | `access1` | Will be used as hostname |
| **Status** | `Active` | Device operational status |
| **Role** | `access-switch` | For template mapping |
| **Platform** | `Arista EOS` | Must have NAPALM driver |
| **Location** | `Lab` | Physical location |
| **Primary IPv4** | `172.20.20.11/24` | Management IP |

#### Optional but Recommended

- **Serial Number** - Device serial
- **Asset Tag** - Asset tracking
- **Tenant** - Multi-tenancy
- **Tags** - Additional categorization

#### Platform Configuration

Ensure each platform has:

1. Navigate to **Devices → Platforms**
2. Edit platform (e.g., `Arista EOS`)
3. Set:
   - **NAPALM Driver**: `eos` (for Arista)
   - **Network Driver**: `arista_eos` (optional)
   - **NAPALM Args**: `{}` (or custom JSON)

### Step 5: Configure Config Context (Optional but Powerful)

Config Context allows you to add custom variables to devices.

1. Navigate to **Extensibility → Config Contexts**
2. Click **+ Add**
3. Create context:

**Example: Lab-wide Config Context**

```json
{
  "domain_name": "lab.local",
  "ntp_servers": [
    "172.20.20.1",
    "pool.ntp.org"
  ],
  "syslog_servers": [
    "172.20.20.1"
  ],
  "snmp": {
    "community": "public",
    "location": "Network Lab",
    "contact": "netadmin@lab.local"
  }
}
```

**Assignment:**
- **Name**: `Lab Global Settings`
- **Weight**: `1000` (lower weight = higher priority)
- **Is Active**: ✅ Checked
- **Locations**: Select `Lab` (applies to all devices in Lab)

**Example: Role-specific Config Context**

```json
{
  "vlans": {
    "10": "DATA_VLAN",
    "20": "VOICE_VLAN",
    "30": "MGMT_VLAN"
  },
  "spanning_tree_mode": "rapid-pvst"
}
```

**Assignment:**
- **Name**: `Access Switch VLANs`
- **Weight**: `500`
- **Roles**: Select `access-switch`

### Step 6: Configure Secrets (For Authentication)

1. Navigate to **Secrets → Secrets Groups**
2. Click **+ Add Secret Group**
3. Create group:
   - **Name**: `Device Admin Credentials`
   - **Description**: `Standard device admin credentials`

4. Add secrets:
   - Click **Add Secret**
   - **Access Type**: `Generic`
   - **Secret Type**: `Username`
   - **Secret Value**: `admin`

   - Click **Add Secret**
   - **Access Type**: `Generic`
   - **Secret Type**: `Password`
   - **Secret Value**: `admin`

5. Assign to devices:
   - Go to each device
   - Edit device
   - Set **Secrets Group**: `Device Admin Credentials`

## Part 3: Generate Intended Configurations

### Step 7: Run Golden Config Job

1. Navigate to **Jobs → Jobs**
2. Find **"Generate Intended Configurations"** (Golden Config plugin)
3. Click **Run Job**
4. Select devices:
   - Select all devices you want to provision
   - Or select specific roles/locations
5. Click **Run Job Now**
6. Monitor execution

### Step 8: Verify Intended Configs

1. Navigate to **Plugins → Golden Config → Golden Configs**
2. Click on a device (e.g., `access1`)
3. View **Intended Configuration** tab
4. Verify configuration looks correct

**Example output for access1:**

```
!
! Bootstrap configuration for access1 (Arista EOS)
!
hostname access1
!
interface Management0
   ip address 172.20.20.11/24
   no shutdown
   description "Management interface"
!
...
```

## Part 4: Create Provision Button (One-Time)

### Step 9: Create Custom Link (Job Button)

1. Navigate to **Extensibility → Custom Links**
2. Click **+ Add**
3. Configure:

| Field | Value |
|-------|-------|
| **Name** | `Provision Device` |
| **Content Type** | `dcim \| device` |
| **Enabled** | ✅ Checked |
| **New Window** | ✅ Checked |
| **Link Text** | `Provision Device` |
| **Link URL** | `/extras/jobs/provision_device.ProvisionDevice/run/?device={{ obj.pk }}` |
| **Button Class** | `primary` |
| **Group Name** | `Actions` |
| **Weight** | `100` |
| **Jinja2 Filter** | `{{ obj.platform and obj.platform.napalm_driver and obj.primary_ip4 }}` |

4. Click **Create**

### Step 10: Verify Button

1. Navigate to any device (e.g., **Devices → Devices → access1**)
2. Look for **"Provision Device"** button in top right
3. Button should be visible and clickable

## Part 5: Provision Devices

### Step 11: Test Provision (Dry Run)

1. Navigate to device page (e.g., `access1`)
2. Click **"Provision Device"** button
3. Configure job:
   - **Device**: `access1` (pre-selected)
   - **Dry Run**: ✅ **Enabled** (important for testing!)
   - **Replace Config**: ❌ Disabled
   - **Commit Changes**: ✅ Enabled
4. Click **Run Job**
5. Review output:
   - Configuration diff
   - What would change
   - Any errors

**Expected output:**

```
✅ Device validation passed
✅ Found existing intended config
✅ Connected to access1
ℹ️  Configuration changes:
--------------------------------------------------------------------------------
+interface Ethernet2
+   no shutdown
--------------------------------------------------------------------------------
⚠️  DRY RUN mode: Discarding configuration changes
```

### Step 12: Deploy Configuration (Live)

If dry run looks good:

1. Run job again
2. Configure:
   - **Device**: `access1` (pre-selected)
   - **Dry Run**: ❌ **Disabled** (deploy for real)
   - **Replace Config**: ❌ Disabled
   - **Commit Changes**: ✅ Enabled
3. Click **Run Job**
4. Monitor deployment

**Expected output:**

```
✅ Device validation passed
✅ Found existing intended config
✅ Connected to access1
✅ Configuration loaded successfully
ℹ️  Configuration changes:
--------------------------------------------------------------------------------
+interface Ethernet2
+   no shutdown
--------------------------------------------------------------------------------
✅ Configuration committed successfully and saved to startup-config
✅ Device access1 is running with new configuration
```

### Step 13: Verify Device Configuration

1. **Via Nautobot Job:**
   - Review job output
   - Check for success messages
   - Verify no errors

2. **Via Device CLI:**
   ```bash
   ssh admin@172.20.20.11
   show running-config
   ```

3. **Via Golden Config Compliance:**
   - Navigate to **Plugins → Golden Config**
   - Run **"Perform Configuration Compliance"** job
   - Check device compliance status

## Part 6: Bulk Provisioning

### Step 14: Provision Multiple Devices

**Option A: Via Web Interface**

1. Navigate to **Jobs → Jobs**
2. Select **"Provision Device"**
3. Click **Run Job**
4. Do NOT select a device (to enable bulk selection)
5. Configure options
6. Click **Run Job**

**Option B: Via API**

```python
import requests

nautobot_url = "https://your-nautobot.example.com"
api_token = "your-api-token-here"

headers = {
    "Authorization": f"Token {api_token}",
    "Content-Type": "application/json"
}

# List of devices to provision
devices = ["access1", "access2", "dist1"]

for device_name in devices:
    # Get device ID
    device_response = requests.get(
        f"{nautobot_url}/api/dcim/devices/?name={device_name}",
        headers=headers
    )
    device_id = device_response.json()["results"][0]["id"]
    
    # Provision device
    job_data = {
        "device": device_id,
        "dry_run": False,
        "replace_config": False,
        "commit_changes": True
    }
    
    response = requests.post(
        f"{nautobot_url}/api/extras/jobs/provision_device.ProvisionDevice/run/",
        headers=headers,
        json={"data": job_data}
    )
    
    print(f"Provisioning {device_name}: HTTP {response.status_code}")
```

## Common Workflows

### Workflow 1: New Device Onboarding

```
1. Add device to Nautobot (name, IP, platform, role)
2. Assign secrets group for credentials
3. Generate intended config (Golden Config job)
4. Test provision (dry run = true)
5. Deploy provision (dry run = false, replace = true)
6. Verify compliance
```

### Workflow 2: Configuration Update

```
1. Update device data in Nautobot (interfaces, IPs, etc.)
2. Or update Config Context (VLANs, NTP, etc.)
3. Regenerate intended config
4. Test provision (dry run = true)
5. Deploy updates (dry run = false, replace = false)
6. Verify compliance
```

### Workflow 3: Disaster Recovery

```
1. Ensure device record exists in Nautobot
2. Ensure intended config is current
3. Deploy with replace (replace = true)
4. Device fully restored from Nautobot
```

## Troubleshooting

### Issue: Button Doesn't Appear

**Check:**
- Device has platform configured
- Platform has NAPALM driver set
- Device has primary IP address
- Custom Link is enabled
- Browser cache cleared

### Issue: "No intended configuration available"

**Solution:**
1. Run Golden Config "Generate Intended Configurations" job
2. Verify template is assigned to device platform/role
3. Check template for errors

### Issue: "Connection error"

**Check:**
- Device is reachable (ping test)
- SSH/API is enabled on device
- Credentials are correct (test manual SSH)
- Firewall allows connections
- Management interface is up

### Issue: Configuration syntax errors

**Check:**
- Template syntax is correct for device platform
- Variables are properly populated
- Review intended config manually
- Test commands on device CLI first

## Next Steps

After successful provisioning:

1. **Set up compliance checking:**
   - Schedule Golden Config compliance jobs
   - Monitor for configuration drift
   - Set up alerts for non-compliant devices

2. **Automate workflows:**
   - Create webhooks for automatic provisioning
   - Integrate with CI/CD pipelines
   - Build ChatOps integrations

3. **Expand templates:**
   - Add more device-specific templates
   - Enhance with conditional logic
   - Integrate with external data sources

4. **Create additional Job Buttons:**
   - Backup configuration
   - Restore configuration
   - Run show commands
   - Test connectivity

## Success Criteria

You'll know your provisioning workflow is successful when:

✅ Templates render correctly for all devices  
✅ Intended configs are generated automatically  
✅ Dry run shows expected configuration changes  
✅ Live deployment succeeds without errors  
✅ Device is accessible after provisioning  
✅ Configuration persists after device reload  
✅ Compliance checks show device is compliant  
✅ Provisioning button works from device pages  

## Resources

- [Device Provisioning Guide](./DEVICE_PROVISIONING.md)
- [Job Button Setup](./JOB_BUTTON_SETUP.md)
- [Golden Config Templates README](../templates/README_GOLDEN_CONFIG_TEMPLATES.md)
- [Template Mapping](../templates/TEMPLATE_MAPPING.md)
- [Nautobot Documentation](https://docs.nautobot.com/)
- [Golden Config Plugin](https://docs.nautobot.com/projects/golden-config/)
- [NAPALM Documentation](https://napalm.readthedocs.io/)

## Lab-Specific Quick Commands

For this Nautobot Zero to Hero lab:

### Verify Containerlab Devices

```bash
cd /home/bsmeding/nautobot_zero_to_hero/containerlab
sudo containerlab inspect -t nautobot-lab.clab.yml
```

### Test Device Connectivity

```bash
# Test ping
ping 172.20.20.11

# Test SSH
ssh admin@172.20.20.11
# Password: admin
```

### Check Nautobot Logs

```bash
docker logs nautobot
# Or if running locally:
tail -f /opt/nautobot/nautobot.log
```

Happy provisioning! 🚀

