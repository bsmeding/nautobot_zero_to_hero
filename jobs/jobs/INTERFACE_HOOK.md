# Interface Configuration JobHook

## Overview

The **Interface Configuration Hook** is a Nautobot JobHook that automatically configures network device interfaces when they are created or updated in Nautobot. This provides real-time synchronization between Nautobot's Source of Truth and the actual network device configurations.

## Features

- **Automatic Configuration**: Pushes interface config to devices when interfaces are created/updated in Nautobot
- **Dry-Run Support**: Test changes without committing to devices
- **Platform Support**: Currently supports Arista EOS devices via pyeapi
- **Selective Sync**: Only syncs physical interfaces (Ethernet), skips virtual/management interfaces
- **Change Detection**: Only pushes config when relevant fields change (description, enabled, MTU, etc.)

## How It Works

### Trigger Events

The hook triggers on three Interface model events:

1. **Created**: When a new interface is added to a device in Nautobot
2. **Updated**: When an interface's properties are modified
3. **Deleted**: Logged but not synced (interface no longer exists)

### Configuration Flow

```
┌─────────────────────────────────────────────────┐
│ User creates/updates Interface in Nautobot UI  │
└────────────────┬────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────┐
│ Nautobot triggers InterfaceJobHookReceiver      │
└────────────────┬────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────┐
│ Hook validates:                                 │
│ - Device exists and has primary IP              │
│ - Interface is physical (Ethernet)              │
│ - Platform is supported (Arista EOS)            │
└────────────────┬────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────┐
│ Build configuration commands:                   │
│ - interface <name>                              │
│ - description <desc>                            │
│ - [no] shutdown                                 │
│ - mtu <value>                                   │
└────────────────┬────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────┐
│ Connect to device via pyeapi and push config    │
└────────────────┬────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────┐
│ Save configuration (write memory)               │
└─────────────────────────────────────────────────┘
```

## Configuration Fields

The hook syncs the following interface fields to devices:

| Field | Description | EOS Command |
|-------|-------------|-------------|
| `name` | Interface name | `interface <name>` |
| `description` | Interface description | `description <text>` |
| `enabled` | Interface status | `[no] shutdown` |
| `mtu` | MTU size | `mtu <size>` |

## Enabling the Hook

### 1. Ensure pyeapi is Available

The hook requires `pyeapi` to be installed in the Nautobot environment:

```bash
# If using the containerlab setup, pyeapi should already be installed
# Otherwise, install it:
pip install pyeapi
```

### 2. Enable the Hook in Nautobot UI

1. Navigate to **Jobs** → **Job Hooks**
2. Find **Interface Configuration Hook**
3. Click **"Enable"** if not already enabled
4. Configure trigger events:
   - ✅ On Create
   - ✅ On Update
   - ❌ On Delete (logged only, not synced)

### 3. Test with Dry-Run Mode

When running manually, you can test without committing:

1. Go to **Jobs** → **Interface Configuration Hook**
2. Uncheck **"Commit"** checkbox
3. The hook will log what it would do without actually configuring devices

## Usage Examples

### Example 1: Create New Interface

1. In Nautobot UI, navigate to **Devices** → Select `access1`
2. Go to **Interfaces** tab → **Add Interface**
3. Fill in:
   - **Name**: `Ethernet4`
   - **Type**: `1000BASE-T (1GE)`
   - **Description**: `Server connection`
   - **Enabled**: ✅
4. Click **Create**

**Result**: Hook automatically pushes this config to access1:
```
interface Ethernet4
  description Server connection
  no shutdown
```

### Example 2: Update Interface Description

1. Navigate to an existing interface (e.g., `Ethernet1` on `access1`)
2. Change **Description** to `Updated uplink to core`
3. Click **Update**

**Result**: Hook pushes the updated description:
```
interface Ethernet1
  description Updated uplink to core
  no shutdown
```

### Example 3: Disable Interface

1. Navigate to interface `Ethernet2` on `access2`
2. Uncheck **Enabled**
3. Click **Update**

**Result**: Hook disables the interface:
```
interface Ethernet2
  description Access port VLAN 10
  shutdown
```

## Monitoring Hook Execution

### View Hook Logs

1. Navigate to **Jobs** → **Job Results**
2. Filter by **Job**: `Interface Configuration Hook`
3. Click on a result to view detailed logs

### Log Levels

The hook uses different log levels:

- **SUCCESS**: Configuration pushed successfully
- **INFO**: Normal operation messages (validation, skips)
- **WARNING**: Non-critical issues (unsupported platform, no IP)
- **ERROR**: Configuration failures
- **DEBUG**: Detailed connection/command information

## Limitations and Considerations

### Current Limitations

1. **Platform Support**: Only Arista EOS devices are currently supported
2. **Authentication**: Uses hardcoded credentials (admin/admin) - should be moved to Secrets
3. **Delete Actions**: Interface deletions are logged but not synced to devices
4. **Physical Interfaces Only**: Virtual interfaces, LAGs, and management interfaces are skipped
5. **No Rollback**: Failed configurations don't automatically rollback

### Future Enhancements

- [ ] Support for additional platforms (Cisco IOS, Juniper, etc.)
- [ ] Integration with Nautobot Secrets for credentials
- [ ] Configurable interface filtering (which interfaces to sync)
- [ ] Configuration rollback on failure
- [ ] Batch interface updates
- [ ] Support for interface deletion cleanup
- [ ] VLAN and IP address configuration

## Troubleshooting

### Hook Not Triggering

**Check:**
1. Hook is enabled in Jobs → Job Hooks
2. Trigger events are configured correctly
3. Interface being modified is physical (Ethernet)
4. Device has a primary IP address

### Configuration Not Pushed

**Check:**
1. Device has `primary_ip4` or `primary_ip` set
2. Device platform contains "arista" or "eos"
3. Device is reachable from Nautobot container
4. Credentials are correct (default: admin/admin)
5. Review job logs for detailed error messages

### Connection Failures

```python
# Error: Failed to connect/configure access1: Connection refused
```

**Solutions:**
- Verify device IP is correct in Nautobot
- Check network connectivity: `docker exec -it nautobot ping <device_ip>`
- Verify eAPI is enabled on device
- Check firewall rules

### Permission Errors

```python
# Error: Failed to connect/configure access1: Authentication failed
```

**Solutions:**
- Verify device credentials
- Check user has privilege level 15 or equivalent
- Verify eAPI authentication is configured

## Security Considerations

### Credentials

⚠️ **Current Implementation**: Credentials are hardcoded in the hook code

**Recommended**: Use Nautobot Secrets for storing device credentials:

```python
# Future implementation
from nautobot.extras.models import Secret

secret = Secret.objects.get(name="device_credentials")
username = secret.get_value()["username"]
password = secret.get_value()["password"]
```

### Network Access

- Hook runs within Nautobot container
- Requires network access to management interfaces
- Consider using management VLANs/VRFs
- Implement firewall rules to restrict access

## Development and Testing

### Testing the Hook Locally

```bash
# 1. Make changes to interface_hook.py

# 2. Restart Nautobot to reload the job
docker compose restart nautobot

# 3. Test by creating/updating an interface in Nautobot UI

# 4. Check logs
docker compose logs -f nautobot | grep "Interface Configuration"
```

### Adding Support for Other Platforms

To add support for a new platform, modify `_push_config_to_device()`:

```python
def _push_config_to_device(self, device, config_commands):
    platform_name = device.platform.name.lower() if device.platform else ""
    
    if 'cisco' in platform_name:
        # Cisco implementation using netmiko
        self._push_config_cisco(device, host, config_commands)
    elif 'juniper' in platform_name:
        # Juniper implementation
        self._push_config_juniper(device, host, config_commands)
    # ... etc
```

## Related Documentation

- [Device JobHook](device_hook.py) - Similar hook for device-level changes
- [Scripts README](../../scripts/README.md) - Standalone scripts that inspired this hook
- [Nautobot Jobs Documentation](https://docs.nautobot.com/projects/core/en/stable/user-guide/platform-functionality/jobs/)
- [Nautobot Job Hooks](https://docs.nautobot.com/projects/core/en/stable/user-guide/platform-functionality/jobs/job-hooks/)

## Questions or Issues?

If you encounter issues or have questions:

1. Check the job logs in Nautobot UI
2. Review device connectivity and credentials
3. Check containerlab device status: `sudo containerlab inspect`
4. Review Nautobot logs: `docker compose logs nautobot`

