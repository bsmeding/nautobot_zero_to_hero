# Config Context Implementation Summary

## What Was Added

Config contexts have been added to **both** the Preflight Lab Setup and Design Builder Lab Setup jobs to provide identical hierarchical configuration data.

## Files Modified/Created

### 1. Preflight Lab Setup (`jobs/jobs/preflight_lab_setup.py`)
- ✅ Added `_create_config_contexts()` method
- ✅ Called in the main `run()` method after devices are created
- ✅ Creates 4 config contexts with proper associations

### 2. Design Builder Lab Setup (`jobs/jobs/test_design_builder.py`)
- ✅ Renamed to `DesignBuilderLabSetup` 
- ✅ Updated to use `lab_setup.yaml` design file
- ✅ Includes config contexts from YAML

### 3. Design Builder YAML (`jobs/jobs/design_builder/lab_setup/lab_setup.yaml`)
- ✅ Added `config_contexts` section at the end
- ✅ Defines same 4 contexts as Preflight job

### 4. Example Template (`templates/base_config_from_context.j2`)
- ✅ New Jinja2 template demonstrating config context usage
- ✅ Shows platform-specific logic (Arista vs Nokia)
- ✅ Shows role-specific logic (Access Switch)

### 5. Render Config Job (`jobs/jobs/render_config_template.py`)
- ✅ New job that uses the template
- ✅ Renders device configuration using config context data
- ✅ Can be run from Nautobot UI for any device

### 6. Configure Network Services Job (`jobs/jobs/configure_network_services.py`)
- ✅ **NEW** - Practical job that configures devices using config context
- ✅ Configurable options: NTP, DNS, Syslog, SNMP
- ✅ Multi-device selection
- ✅ Dry-run mode to preview commands
- ✅ Platform-aware (Arista vs Nokia)
- ✅ Actually pushes config to devices

### 7. Documentation
- ✅ `jobs/jobs/CONFIG_CONTEXTS.md` - Complete config context documentation
- ✅ `CONFIG_CONTEXT_SUMMARY.md` - This summary (you're reading it!)
- ✅ Updated `README.md` with config context section

## Config Contexts Created

Both jobs create these **identical** config contexts:

### 1. Lab Common Configuration (Weight 1000)
**Applied to:** All devices in `netdevops.it_lab`

Contains:
- `ntp_servers` - List of NTP servers
- `dns_servers` - List of DNS servers  
- `syslog_hosts` - List of syslog destinations
- `snmp` - SNMP community and location
- `timezone` - Timezone setting
- `domain_name` - Domain name

### 2. Arista Platform Configuration (Weight 2000)
**Applied to:** Devices with platform `Arista EOS`

Contains:
- `platform_specific.cli_commands` - Save/show commands
- `platform_specific.management_interface` - "Management0"
- `platform_specific.ntp_source_interface` - NTP source
- `platform_specific.logging` - Buffer size and source
- `platform_specific.banner` - MOTD banner
- `features.lldp` - LLDP enabled
- `features.stp` - "rapid-pvst"

**Devices:** access1, access2

### 3. Nokia Platform Configuration (Weight 2000)
**Applied to:** Devices with platform `Nokia SR Linux`

Contains:
- `platform_specific.cli_commands` - Save/show commands (Nokia syntax)
- `platform_specific.management_interface` - "mgmt0"
- `platform_specific.ntp_source_interface` - NTP source
- `platform_specific.logging` - Buffer size and source
- `platform_specific.banner` - MOTD banner
- `features.lldp` - LLDP enabled
- `features.spanning_tree` - "mstp"

**Devices:** dist1, rtr1

### 4. Access Switch Role Configuration (Weight 3000)
**Applied to:** Devices with role `Access Switch`

Contains:
- `role_specific.port_security` - Settings
- `role_specific.default_vlan` - Default VLAN ID
- `role_specific.allowed_vlans` - List of allowed VLANs
- `role_specific.stp_portfast` - Portfast enabled

**Devices:** access1, access2

## Key Differences: Arista vs Nokia

| Feature | Arista EOS | Nokia SR Linux |
|---------|-----------|----------------|
| **Management Interface** | `Management0` | `mgmt0` |
| **Save Command** | `write memory` | `tools system configuration save` |
| **Show Version** | `show version` | `info system version` |
| **Spanning Tree** | `rapid-pvst` | `mstp` |
| **Log Buffer** | 16384 | 10000 |

## How to Use Config Contexts

### In Jinja2 Templates

Config context data is automatically available:

```jinja2
{# Access common data #}
hostname {{ device.name }}
domain-name {{ domain_name }}

{# Loop through lists #}
{% for ntp in ntp_servers %}
ntp server {{ ntp }}
{% endfor %}

{# Platform-specific logic #}
{% if platform_specific.management_interface == 'Management0' %}
  {# Arista commands #}
  logging source-interface {{ platform_specific.logging.source_interface }}
  logging buffered {{ platform_specific.logging.buffer_size }}
{% elif platform_specific.management_interface == 'mgmt0' %}
  {# Nokia commands #}
  / system logging buffer-size {{ platform_specific.logging.buffer_size }}
{% endif %}

{# Role-specific logic #}
{% if role_specific and device.role.name == "Access Switch" %}
vlan {{ role_specific.default_vlan }}
{% endif %}
```

### Via Python/Job

```python
from nautobot.dcim.models import Device

device = Device.objects.get(name="access1")
context = device.get_config_context()

# Access the data
ntp_servers = context['ntp_servers']
mgmt_interface = context['platform_specific']['management_interface']
```

### Via API

```bash
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8080/api/dcim/devices/?name=access1&include=config_context
```

## Testing the Config Contexts

### 1. Run Either Job

```bash
# Option 1: Preflight Job (Python)
# Go to: Jobs → LAB Setup → Pre-flight Lab Setup → Run

# Option 2: Design Builder (YAML)  
# Go to: Jobs → Design Builder Lab Setup → Run
```

### 2. View Config Context

1. Navigate to **Devices → access1**
2. Click **Config Context** tab
3. See the merged/rendered context

### 3. Test in Template

1. Go to **Extensibility → Computed Fields** or **Jobs**
2. Create a test job that renders `templates/base_config_from_context.j2`
3. Verify platform-specific output

## Example Rendered Context for access1

```json
{
  "ntp_servers": ["192.168.1.1", "192.168.1.2", "time.google.com"],
  "dns_servers": ["8.8.8.8", "8.8.4.4", "1.1.1.1"],
  "syslog_hosts": [
    {"host": "192.168.1.100", "port": 514},
    {"host": "192.168.1.101", "port": 514}
  ],
  "snmp": {
    "community": "nautobot_lab_ro",
    "location": "NetDevOps Lab"
  },
  "timezone": "UTC",
  "domain_name": "netdevops.lab",
  "platform_specific": {
    "cli_commands": {
      "save_config": "write memory",
      "show_version": "show version"
    },
    "management_interface": "Management0",
    "ntp_source_interface": "Management0",
    "logging": {
      "buffer_size": 16384,
      "source_interface": "Management0"
    },
    "banner": {
      "motd": "Arista Device - NetDevOps Lab - Unauthorized access prohibited"
    }
  },
  "features": {
    "lldp": true,
    "stp": "rapid-pvst"
  },
  "role_specific": {
    "port_security": {
      "enabled": true,
      "max_mac_addresses": 2
    },
    "default_vlan": 100,
    "allowed_vlans": [10, 20, 30, 100, 200, 300],
    "stp_portfast": true
  }
}
```

## Benefits

✅ **DRY Principle** - Define data once, use in all templates  
✅ **Platform Agnostic** - Same structure for multi-vendor  
✅ **Hierarchical** - Override with specific contexts  
✅ **Maintainable** - Update context, all devices get new data  
✅ **Testable** - Easy to validate via API or Python

## Using the Configure Network Services Job

This job demonstrates practical use of config contexts:

### 1. Restart Nautobot
```bash
cd /mnt/c/Users/BartSmeding/NetDevOps/Workspace/NAUTOBOT_JOBS/nautobot_zero_to_hero
docker-compose restart nautobot
```

### 2. Run the Job
1. Go to **Jobs → Network Services → Configure Network Services**
2. **Select devices** (e.g., access1, access2, dist1)
3. **Choose services to configure:**
   - ✅ Configure NTP servers
   - ✅ Configure DNS servers  
   - ✅ Configure Syslog hosts
   - ✅ Configure SNMP
4. **Enable Dry Run** (recommended first time) ✅
5. Click **Run Job**

### 3. Review Output

**Dry Run Mode** shows commands that will be applied:

**For Arista (access1):**
```
dns domain netdevops.lab
ntp server 192.168.1.1
ntp server 192.168.1.2
ntp server time.google.com
ntp local-interface Management0
ip name-server 8.8.8.8
ip name-server 8.8.4.4
ip name-server 1.1.1.1
logging host 192.168.1.100
logging host 192.168.1.101
logging source-interface Management0
logging buffered 16384
snmp-server community nautobot_lab_ro ro
snmp-server location NetDevOps Lab
```

**For Nokia (dist1):**
```
/ system name domain-name netdevops.lab
/ system ntp server 192.168.1.1
/ system ntp server 192.168.1.2
/ system ntp server time.google.com
/ system dns server-list [ 8.8.8.8 ]
/ system dns server-list [ 8.8.4.4 ]
/ system dns server-list [ 1.1.1.1 ]
/ system logging remote-server 192.168.1.100 port 514
/ system logging remote-server 192.168.1.101 port 514
/ system snmp community nautobot_lab_ro access-permissions ro
/ system snmp location NetDevOps Lab
```

### 4. Apply Configuration

Once satisfied with dry run:
1. **Uncheck "Dry run"** ❌
2. **Run Job** again
3. Configuration will be pushed to devices via eAPI (Arista)

## Next Steps

1. Run either the Preflight or Design Builder job to create config contexts
2. Check created config contexts in **Extensibility → Config Contexts**
3. View rendered context on devices
4. **Run Configure Network Services job** to apply configs
5. Use `templates/base_config_from_context.j2` as a reference
6. Create your own templates using the config context data

## Documentation

📖 **Full Documentation:** [`jobs/jobs/CONFIG_CONTEXTS.md`](jobs/jobs/CONFIG_CONTEXTS.md)  
🔧 **Example Template:** [`templates/base_config_from_context.j2`](templates/base_config_from_context.j2)  
📘 **Main README:** Updated with config context section

---

**Both jobs now create identical config contexts - use whichever approach you prefer!** 🚀

