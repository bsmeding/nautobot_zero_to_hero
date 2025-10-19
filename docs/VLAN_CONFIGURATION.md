# VLAN Configuration Reference

This document describes the VLAN configuration for all devices in the Nautobot Zero to Hero lab, based on the containerlab bootstrap configurations.

## VLAN Definitions

| VLAN ID | Name | Description | Purpose |
|---------|------|-------------|---------|
| 10 | Management | Management VLAN | Management and data traffic |
| 20 | Data | Data VLAN | Data traffic |
| 30 | Voice | Voice VLAN | Voice traffic |
| 100 | Lab-Network | Lab network VLAN | General lab network |
| 200 | Automation | Network automation VLAN | Automation tools |
| 300 | Testing | Testing and validation VLAN | Testing purposes |

## Device Interface Configurations

### dist1 (Distribution Switch)

| Interface | Description | Mode | Tagged VLANs | Untagged VLAN |
|-----------|-------------|------|--------------|---------------|
| Management0 | Management interface | - | - | - |
| Ethernet1 | Connected to access1 | Trunk | 10 | - |
| Ethernet2 | Connected to access2 | Trunk | 10 | - |
| Ethernet3 | Connected to rtr1 | Trunk | 10 | - |
| Ethernet4 | Available for connections | - | - | - |

### access1 (Access Switch)

| Interface | Description | Mode | Tagged VLANs | Untagged VLAN |
|-----------|-------------|------|--------------|---------------|
| Management0 | Management interface | - | - | - |
| Ethernet1 | Uplink to dist1 | Trunk | 10 | - |
| Ethernet2 | Connected to workstation1 | Access | - | 10 |
| Ethernet3 | Available for connections | - | - | - |

### access2 (Access Switch)

| Interface | Description | Mode | Tagged VLANs | Untagged VLAN |
|-----------|-------------|------|--------------|---------------|
| Management0 | Management interface | - | - | - |
| Ethernet1 | Connected to dist1 | Trunk | All | - |
| Ethernet2 | Available for connections | Access | - | 20 |
| Ethernet3 | Available for connections | Access | - | 30 |

### rtr1 (Router)

| Interface | Description | Mode | Tagged VLANs | Untagged VLAN |
|-----------|-------------|------|--------------|---------------|
| Management0 | Management interface | - | - | - |
| Ethernet1 | Uplink to dist1 | Trunk | 10 | - |
| Ethernet2 | Connected to mgmt server | Access | - | 10 |
| Ethernet3 | Available for connections | - | - | - |

## Nautobot Interface Configuration

The Preflight Lab Setup job now automatically configures:

### Interface Attributes

1. **Name** - Interface name (e.g., Ethernet1, Management0)
2. **Description** - Interface description
3. **Type** - Interface type (1000base-t)
4. **Mode** - Interface mode:
   - `tagged` - Trunk mode with specific VLANs
   - `tagged-all` - Trunk mode allowing all VLANs
   - `access` - Access mode with single VLAN
   - Empty - No L2 configuration

5. **Tagged VLANs** - List of VLANs for trunk ports
6. **Untagged VLAN** - Single VLAN for access ports

### Configuration Flow

When you run the **Pre-flight Lab Setup** job:

```
1. Create VLANs (10, 20, 30, 100, 200, 300)
2. Create devices (access1, access2, dist1, rtr1)
3. Create interfaces with proper types
4. Set interface modes (tagged/access/tagged-all)
5. Assign VLANs to interfaces:
   - Tagged VLANs for trunk ports
   - Untagged VLAN for access ports
6. Create IP addresses
7. Create cable connections
```

## Verification

After running the Preflight job, you can verify VLAN configurations:

### Via Nautobot UI

1. Navigate to **Devices → Devices → access1**
2. Click **Interfaces** tab
3. Check each interface:
   - **Mode** column shows access/tagged/tagged-all
   - Click interface to see VLAN assignments

### Via GraphQL

```graphql
query {
  device(name: "access1") {
    interfaces {
      name
      mode
      tagged_vlans {
        vid
        name
      }
      untagged_vlan {
        vid
        name
      }
    }
  }
}
```

### Via API

```bash
curl -H "Authorization: Token YOUR_TOKEN" \
  "http://localhost:8080/api/dcim/interfaces/?device=access1" | jq '.results[] | {name, mode, tagged_vlans, untagged_vlan}'
```

## VLAN Configuration Matrix

### Trunk Ports (Tagged VLANs)

| Device | Interface | Tagged VLANs |
|--------|-----------|--------------|
| dist1 | Ethernet1 | 10 |
| dist1 | Ethernet2 | 10 |
| dist1 | Ethernet3 | 10 |
| access1 | Ethernet1 | 10 |
| access2 | Ethernet1 | All VLANs |
| rtr1 | Ethernet1 | 10 |

### Access Ports (Untagged VLAN)

| Device | Interface | Untagged VLAN |
|--------|-----------|---------------|
| access1 | Ethernet2 | 10 |
| access2 | Ethernet2 | 20 |
| access2 | Ethernet3 | 30 |
| rtr1 | Ethernet2 | 10 |

## Topology Diagram

```
                    dist1
                     │
        ┌────────────┼────────────┐
        │            │            │
    Ethernet1    Ethernet2    Ethernet3
    (Trunk       (Trunk       (Trunk
     VLAN 10)     VLAN 10)     VLAN 10)
        │            │            │
        │            │            │
    Ethernet1    Ethernet1    Ethernet1
    (Trunk       (Trunk All)  (Trunk
     VLAN 10)                  VLAN 10)
        │            │            │
    access1      access2        rtr1
        │            │            │
    Ethernet2    Ethernet2    Ethernet2
    (Access      (Access      (Access
     VLAN 10)     VLAN 20)     VLAN 10)
        │            │            │
        │            │            │
  workstation1       │        management
                Ethernet3
                (Access
                 VLAN 30)
```

## Using VLANs in Templates

In your Jinja2 templates, you can now access VLAN information:

```jinja2
{# Example: Configure interfaces dynamically #}
{% for interface in interfaces %}
interface {{ interface.name }}
   description {{ interface.description }}
   {% if interface.mode == 'tagged' %}
   switchport mode trunk
   switchport trunk allowed vlan {% for vlan in interface.tagged_vlans %}{{ vlan.id }}{% if not loop.last %},{% endif %}{% endfor %}
   {% elif interface.mode == 'tagged-all' %}
   switchport mode trunk
   switchport trunk allowed vlan all
   {% elif interface.mode == 'access' and interface.untagged_vlan %}
   switchport mode access
   switchport access vlan {{ interface.untagged_vlan.id }}
   {% endif %}
{% endfor %}
```

## Troubleshooting

### VLANs Not Showing on Interfaces

**Check:**
1. VLANs exist: **IPAM → VLANs**
2. Preflight job ran successfully
3. Interface mode is set (tagged/access/tagged-all)
4. VLAN objects are valid

### VLAN Configuration Not in Golden Config

**Update templates to use VLAN data:**

```jinja2
{% if interfaces %}
! Configure VLANs on interfaces
{% for interface in interfaces %}
{% if interface.tagged_vlans or interface.untagged_vlan %}
interface {{ interface.name }}
   {% if interface.mode == 'tagged' and interface.tagged_vlans %}
   switchport mode trunk
   switchport trunk allowed vlan {% for vlan in interface.tagged_vlans %}{{ vlan.id }}{% if not loop.last %},{% endif %}{% endfor %}
   {% elif interface.mode == 'access' and interface.untagged_vlan %}
   switchport mode access
   switchport access vlan {{ interface.untagged_vlan.id }}
   {% endif %}
{% endif %}
{% endfor %}
{% endif %}
```

## Summary

The Preflight Lab Setup job now properly configures:

✅ **VLAN definitions** - All VLANs (10, 20, 30, 100, 200, 300)  
✅ **Interface modes** - Tagged (trunk), Access, Tagged-All  
✅ **Tagged VLANs** - For trunk ports  
✅ **Untagged VLANs** - For access ports  
✅ **Based on containerlab** - Matches bootstrap configurations  

This ensures Nautobot accurately reflects your actual network topology! 🎯

