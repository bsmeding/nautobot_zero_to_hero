# Job Button Setup - Quick Guide

This guide provides step-by-step instructions for creating a "Provision Device" button on device pages in Nautobot.

## What is a Job Button?

A Job Button is a Custom Link in Nautobot that appears as a button on object detail pages (like Device pages). When clicked, it triggers a Job with pre-filled parameters, enabling one-click automation.

## Setup Steps

### Step 1: Access Custom Links

1. Log into Nautobot
2. Navigate to **Extensibility → Custom Links**
3. Click **+ Add** button (top right)

### Step 2: Configure Basic Settings

Fill in the following fields:

| Field | Value |
|-------|-------|
| **Name** | `Provision Device` |
| **Content Type** | Select `dcim \| device` |
| **Enabled** | ✅ Checked |
| **New Window** | ✅ Checked (optional - opens job in new tab) |

### Step 3: Configure Link Settings

| Field | Value |
|-------|-------|
| **Link Text** | `Provision Device` |
| **Link URL** | `/extras/jobs/provision_device.ProvisionDevice/run/?device={{ obj.pk }}` |
| **Link Button Class** | `primary` (for blue button) or `success` (for green button) |

### Step 4: Configure Grouping (Optional but Recommended)

| Field | Value |
|-------|-------|
| **Group Name** | `Actions` |
| **Weight** | `100` |

This groups the button with other action buttons and controls display order.

### Step 5: Add Conditional Display (Optional but Recommended)

To only show the button for devices that can be provisioned, add this Jinja2 filter:

**Jinja2 Template Filter:**
```jinja2
{{ obj.platform and obj.platform.napalm_driver and obj.primary_ip4 }}
```

This ensures the button only appears when:
- Device has a platform assigned
- Platform has a NAPALM driver configured
- Device has a primary IPv4 address

### Step 6: Save

Click **Create** button at the bottom

## Verification

### Test the Button

1. Navigate to **Devices → Devices**
2. Click on any device (e.g., `access1`)
3. Look for the **"Provision Device"** button in the top right area
4. Click the button
5. You should be redirected to the Job form with the device pre-selected

### Troubleshooting

**Button doesn't appear:**
- Check if device meets conditional filter requirements
- Verify Custom Link is enabled
- Check Content Type is set to `dcim | device`
- Clear browser cache and refresh

**Button appears but doesn't work:**
- Verify Link URL is correct
- Check job name matches exactly: `provision_device.ProvisionDevice`
- Ensure job is registered in `/jobs/jobs/__init__.py`

## Creating Multiple Job Buttons

You can create additional Job Buttons for other workflows:

### Example: "Sync Device" Button

```
Name: Sync Device
Content Type: dcim | device
Link URL: /extras/jobs/device_sync_napalm.DeviceSyncNAPALM/run/?device={{ obj.pk }}
Button Class: info
Group Name: Actions
```

### Example: "Run Compliance Check" Button

```
Name: Check Compliance
Content Type: dcim | device
Link URL: /plugins/golden-config/golden-config/?device={{ obj.pk }}
Button Class: warning
Group Name: Golden Config
```

## Advanced Configuration

### Custom Button Icons

If your Nautobot version supports it, you can add icons:

**Link Text:**
```html
<i class="mdi mdi-cog"></i> Provision Device
```

### Conditional Styling

Show different button colors based on device status:

**Link Button Class:**
```jinja2
{% if obj.status.name == "Active" %}success{% else %}secondary{% endif %}
```

### Multiple Parameters

Pass multiple parameters to the job:

**Link URL:**
```
/extras/jobs/provision_device.ProvisionDevice/run/?device={{ obj.pk }}&dry_run=true&commit_changes=true
```

## Button Classes Reference

| Class | Color | Use Case |
|-------|-------|----------|
| `primary` | Blue | Main actions |
| `success` | Green | Safe/positive actions |
| `info` | Light Blue | Informational actions |
| `warning` | Orange | Actions requiring attention |
| `danger` | Red | Destructive actions |
| `secondary` | Gray | Secondary actions |
| `default` | White | Default styling |

## Example: Complete Custom Link Configuration

Here's a complete example with all recommended settings:

```json
{
  "name": "Provision Device",
  "content_type": "dcim.device",
  "enabled": true,
  "new_window": true,
  "link_text": "Provision Device",
  "link_url": "/extras/jobs/provision_device.ProvisionDevice/run/?device={{ obj.pk }}",
  "button_class": "primary",
  "group_name": "Actions",
  "weight": 100,
  "text": "{{ obj.platform and obj.platform.napalm_driver and obj.primary_ip4 }}"
}
```

## Using Job Buttons in Your Workflow

### Standard Provisioning Workflow

1. **Navigate to device page**
   - Go to Devices → Devices
   - Click on device to provision

2. **Click "Provision Device" button**
   - Button is in top right area
   - Opens job form in new window

3. **Configure job parameters**
   - Device is pre-selected
   - Set Dry Run (on for testing)
   - Set other options as needed

4. **Review and execute**
   - Click "Run Job"
   - Monitor execution
   - Review configuration diff

5. **Deploy if satisfied**
   - Run again with Dry Run off
   - Verify deployment success

### Bulk Operations

For bulk provisioning, use the main Jobs interface:

1. Navigate to **Jobs → Jobs**
2. Select "Provision Device"
3. Click "Run Job"
4. Select multiple devices
5. Configure options
6. Execute

## Security Considerations

### Permission Requirements

Users need the following permissions to use Job Buttons:

- `extras.run_job` - Execute jobs
- `dcim.view_device` - View devices
- `extras.view_customlink` - See custom links

### Restrict to Specific Users/Groups

You can limit who sees the button by using more complex Jinja2 filters:

```jinja2
{{ obj.platform and obj.platform.napalm_driver and obj.primary_ip4 and request.user.groups.filter(name='Network Admins').exists() }}
```

### Audit Trail

All job executions are logged in Nautobot:

1. Navigate to **Jobs → Job Results**
2. Filter by job name "Provision Device"
3. Review execution history, user, timestamp, and results

## Related Documentation

- [Device Provisioning Guide](./DEVICE_PROVISIONING.md) - Detailed provisioning documentation
- [Golden Config Templates](../templates/README_GOLDEN_CONFIG_TEMPLATES.md) - Template documentation
- [Nautobot Custom Links Documentation](https://docs.nautobot.com/projects/core/en/stable/user-guide/platform-functionality/customlink/)

## Support

If you encounter issues:

1. Check Nautobot logs: `/opt/nautobot/nautobot.log`
2. Verify job is registered: Check Jobs interface
3. Test job manually: Jobs → Jobs → Provision Device
4. Check permissions: Ensure user has required permissions
5. Review Custom Link configuration: Extensibility → Custom Links

## Examples from This Lab

For the Nautobot Zero to Hero lab, create these Job Buttons:

### 1. Provision Device (Primary)
- **For**: Deploying Golden Config configurations
- **Color**: Blue (primary)
- **Group**: Actions

### 2. Sync Device
- **For**: Syncing device facts and interfaces
- **Color**: Light Blue (info)
- **Group**: Actions

### 3. Connectivity Test
- **For**: Testing containerlab connectivity
- **Color**: Green (success)
- **Group**: Diagnostics

This gives you a complete device management interface directly from the device page!

