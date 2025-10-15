# Config Contexts in Nautobot Zero to Hero Lab

This document explains the config contexts created by both the **Preflight Lab Setup** and **Design Builder Lab Setup** jobs.

## Overview

Config contexts in Nautobot provide a hierarchical way to store configuration data that can be applied to devices based on various criteria (location, platform, role, etc.). This data is then available in Jinja2 templates for generating device configurations.

## Config Contexts Created

Both jobs create identical config contexts with the following hierarchy:

### 1. Lab Common Configuration (Weight: 1000)
**Scope:** All devices in the `netdevops.it_lab` location

Common configuration applicable to all lab devices:

```yaml
ntp_servers:
  - "192.168.1.1"
  - "192.168.1.2"
  - "time.google.com"

dns_servers:
  - "8.8.8.8"       # Google DNS
  - "8.8.4.4"       # Google DNS
  - "1.1.1.1"       # Cloudflare DNS

syslog_hosts:
  - host: "192.168.1.100"
    port: 514
  - host: "192.168.1.101"
    port: 514

snmp:
  community: "nautobot_lab_ro"
  location: "NetDevOps Lab"

timezone: "UTC"
domain_name: "netdevops.lab"
```

### 2. Arista Platform Configuration (Weight: 2000)
**Scope:** Devices with platform `Arista EOS` in `netdevops.it_lab`

Platform-specific configuration for Arista devices:

```yaml
platform_specific:
  cli_commands:
    save_config: "write memory"
    show_version: "show version"
  
  management_interface: "Management0"
  ntp_source_interface: "Management0"
  
  logging:
    buffer_size: 16384
    source_interface: "Management0"
  
  banner:
    motd: "Arista Device - NetDevOps Lab - Unauthorized access prohibited"

features:
  lldp: true
  stp: "rapid-pvst"
```

**Applies to devices:**
- access1
- access2

### 3. Nokia Platform Configuration (Weight: 2000)
**Scope:** Devices with platform `Nokia SR Linux` in `netdevops.it_lab`

Platform-specific configuration for Nokia devices:

```yaml
platform_specific:
  cli_commands:
    save_config: "tools system configuration save"
    show_version: "info system version"
  
  management_interface: "mgmt0"
  ntp_source_interface: "mgmt0"
  
  logging:
    buffer_size: 10000
    source_interface: "mgmt0"
  
  banner:
    motd: "Nokia SR Linux Device - NetDevOps Lab - Unauthorized access prohibited"

features:
  lldp: true
  spanning_tree: "mstp"
```

**Applies to devices:**
- dist1
- rtr1

### 4. Access Switch Role Configuration (Weight: 3000)
**Scope:** Devices with role `Access Switch` in `netdevops.it_lab`

Role-specific configuration for access layer switches:

```yaml
role_specific:
  port_security:
    enabled: true
    max_mac_addresses: 2
  
  default_vlan: 100
  allowed_vlans: [10, 20, 30, 100, 200, 300]
  stp_portfast: true
```

**Applies to devices:**
- access1
- access2

## Config Context Hierarchy & Weight

Config contexts are applied in order of **weight** (lower to higher):

1. **Weight 1000** - Lab Common Configuration (base settings)
2. **Weight 2000** - Platform-specific Configuration (Arista or Nokia)
3. **Weight 3000** - Role-specific Configuration (Access Switch, etc.)

Higher weight values **override** lower weight values for the same keys.

## Viewing Config Contexts in Nautobot

### Via Web UI
1. Navigate to a device (e.g., `access1`)
2. Click on the **Config Context** tab
3. View the **Rendered Context** showing the merged data from all applicable contexts

### Via API
```bash
# Get rendered config context for a device
curl -H "Authorization: Token YOUR_API_TOKEN" \
     http://localhost:8080/api/dcim/devices/<device-id>/?include=config_context
```

### Via Python
```python
from nautobot.dcim.models import Device

device = Device.objects.get(name="access1")
context_data = device.get_config_context()

print(f"NTP Servers: {context_data['ntp_servers']}")
print(f"Management Interface: {context_data['platform_specific']['management_interface']}")
```

## Using Config Contexts in Jinja2 Templates

Config context data is automatically available in Jinja2 templates as top-level variables:

### Example: Base Configuration Template

```jinja2
{# templates/base_config_from_context.j2 #}

hostname {{ device.name }}
!
ip domain-name {{ domain_name }}
!
{# NTP Configuration #}
{% for ntp_server in ntp_servers %}
ntp server {{ ntp_server }}
{% endfor %}
ntp source {{ platform_specific.ntp_source_interface }}
!
{# Syslog Configuration #}
{% for syslog in syslog_hosts %}
logging host {{ syslog.host }}
{% endfor %}
logging source-interface {{ platform_specific.logging.source_interface }}
!
{# SNMP Configuration #}
snmp-server community {{ snmp.community }} ro
snmp-server location {{ snmp.location }}
!
```

### Platform-Specific Logic in Templates

```jinja2
{# Differentiate between Arista and Nokia #}
{% if platform_specific.management_interface == 'Management0' %}
  {# Arista EOS commands #}
  ntp server {{ ntp_servers[0] }}
  {{ platform_specific.cli_commands.save_config }}
{% elif platform_specific.management_interface == 'mgmt0' %}
  {# Nokia SR Linux commands #}
  / system ntp server {{ ntp_servers[0] }}
  {{ platform_specific.cli_commands.save_config }}
{% endif %}
```

### Role-Specific Configuration

```jinja2
{# Access Switch specific config #}
{% if role_specific and device.role.name == "Access Switch" %}
!
! Access Switch Configuration
vlan {{ role_specific.default_vlan }}
   name Default-Access-VLAN
!
{% for vlan_id in role_specific.allowed_vlans %}
vlan {{ vlan_id }}
{% endfor %}
!
{% if role_specific.stp_portfast %}
! Portfast enabled for access ports
{% endif %}
{% endif %}
```

## Example: Rendered Context for access1

When you view the config context for `access1` (Arista EOS, Access Switch role), you'll see:

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

## Key Differences: Arista vs Nokia

| Configuration Item | Arista EOS | Nokia SR Linux |
|-------------------|------------|----------------|
| Management Interface | `Management0` | `mgmt0` |
| Save Config Command | `write memory` | `tools system configuration save` |
| Show Version Command | `show version` | `info system version` |
| Spanning Tree | `rapid-pvst` | `mstp` |
| Logging Buffer Size | 16384 | 10000 |

## Benefits of Config Contexts

1. **DRY Principle** - Define common data once, use everywhere
2. **Hierarchical** - Override values based on specific criteria
3. **Platform Agnostic** - Same data structure works across vendors
4. **Template Simplicity** - Templates focus on logic, not data
5. **Easy Updates** - Change config context, all devices get updated data
6. **API Integration** - Easily query and use context data programmatically

## Testing Config Contexts

### 1. Via Nautobot UI
- Go to **Extensibility → Config Contexts**
- View all created contexts
- Check their assignments (locations, platforms, roles)

### 2. Via GraphQL
```graphql
query {
  devices(name: "access1") {
    name
    config_context
  }
}
```

### 3. Via Job/Script
```python
from nautobot.dcim.models import Device

device = Device.objects.get(name="access1")
context = device.get_config_context()

# Test NTP servers
assert len(context['ntp_servers']) == 3
assert 'time.google.com' in context['ntp_servers']

# Test platform-specific
assert context['platform_specific']['management_interface'] == 'Management0'

print("✓ Config context validation passed!")
```

## Additional Resources

- [Nautobot Config Contexts Documentation](https://docs.nautobot.com/projects/core/en/stable/user-guide/platform-functionality/template-filters/#config-context)
- [Jinja2 Template Documentation](https://jinja.palletsprojects.com/)
- See `templates/base_config_from_context.j2` for a complete working example

