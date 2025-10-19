# GraphQL Query Setup - GoldenConfig

This document describes the GoldenConfig GraphQL query that has been added to both the preflight job and design_builder.

## Overview

The GoldenConfig GraphQL query retrieves all necessary device information for rendering Jinja2 templates in the Golden Config plugin. This query is now automatically created when running either:

1. **Preflight Lab Setup Job** - Creates the query programmatically
2. **Design Builder Job** - Creates the query from YAML definition

## What Was Added

### 1. Design Builder GraphQL Query

**File:** `/jobs/jobs/design_builder/initial_data/designs/1102_graphql_queries.j2`

Added the GoldenConfig query definition to the Design Builder YAML file. This ensures the query is created when running the Design Builder job.

### 2. Preflight Job Method

**File:** `/jobs/jobs/preflight_lab_setup.py`

Added a new method `_create_graphql_queries()` that:
- Creates or updates the GoldenConfig GraphQL query
- Runs automatically as part of the preflight setup
- Ensures the query is available for Golden Config plugin

## GoldenConfig Query Details

### Query Name
`GoldenConfig`

### Purpose
Retrieves comprehensive device data for rendering configuration templates including:
- Device hostname, serial, position
- Primary IPv4 address with DNS name
- Platform and manufacturer details
- NAPALM driver configuration
- Location hierarchy
- All interfaces with:
  - IP addresses
  - VLANs (tagged and untagged)
  - Cable connections
  - MAC addresses
  - Enable status
- Configuration context (custom data)
- Tags and tenant information
- Device role

### Query Structure

```graphql
query ($device_id: ID!) {
  device(id: $device_id) {
    hostname:name
    position
    serial
    primary_ip4 {
      id
      address
      dns_name
      description
      interface_assignments {
        id
        interface {
          id
          name
          enabled
        }
      }
      primary_ip4_for {
        id
        name
      }
    }
    tenant {
      name
    }
    tags {
      name
    }
    role {
      name
    }
    platform {
      name
      manufacturer {
        name
      }
      network_driver
      napalm_driver
    }
    location {
      name
      parent {
        name
      }
    }
    interfaces {
      description
      mac_address
      enabled
      name
      ip_addresses {
        address
        tags {
          id
        }
      }
      connected_circuit_termination {
        circuit {
          cid
          commit_rate
          provider {
            name
          }
        }
      }
      tagged_vlans {
        id
      }
      untagged_vlan {
        id
      }
      cable {
        termination_a_type
        status {
          name
        }
        color
      }
      tags {
        id
      }
    }
    config_context
  }
}
```

### Query Variables

The query expects a single variable:
- `device_id` (ID, required) - The UUID of the device to query

### Example Usage

```graphql
# Variables
{
  "device_id": "12345678-1234-1234-1234-123456789abc"
}
```

## How It Works

### Automatic Creation

When you run either of these jobs:

1. **Preflight Lab Setup**
   ```
   Jobs → Jobs → Pre-flight Lab Setup → Run Job
   ```
   - Creates/updates the GoldenConfig query
   - Logs: "Created GraphQL query: GoldenConfig" or "Updated GraphQL query: GoldenConfig"

2. **Design Builder**
   ```
   Jobs → Jobs → Design Builder → Run Job
   ```
   - Processes the 1102_graphql_queries.j2 file
   - Creates/updates all defined GraphQL queries including GoldenConfig

### Manual Verification

To verify the query was created:

1. Navigate to **Extensibility → GraphQL Queries**
2. Look for a query named `GoldenConfig`
3. Click to view the query details
4. You should see the full query structure

### Using the Query

The Golden Config plugin automatically uses this query when:

1. **Generating Intended Configurations**
   - Plugin looks for the `GoldenConfig` query by name
   - Executes the query for each device
   - Passes results to Jinja2 templates as variables

2. **Template Rendering**
   - All fields from the query are available in templates
   - Access via `{{ hostname }}`, `{{ primary_ip4.address }}`, etc.
   - See [Template README](../templates/README_GOLDEN_CONFIG_TEMPLATES.md) for full variable list

## Integration with Golden Config

### Configuration Steps

1. **Ensure Query Exists**
   ```
   Run Preflight Job or Design Builder Job
   ```

2. **Configure Golden Config Plugin**
   ```
   Plugins → Golden Config → Settings
   - Set GraphQL Query: GoldenConfig
   ```

3. **Create Templates**
   ```
   Plugins → Golden Config → Configuration Templates
   - Upload your Jinja2 templates from /templates/
   - Assign to platforms/roles
   ```

4. **Generate Configs**
   ```
   Jobs → Jobs → Generate Intended Configurations
   - Select devices
   - Run job
   - Query executes automatically
   ```

## Available Variables in Templates

Based on the GraphQL query, these variables are available:

### Device Information
- `{{ hostname }}` - Device name (aliased from `name`)
- `{{ position }}` - Rack position
- `{{ serial }}` - Serial number

### Primary IP
- `{{ primary_ip4.address }}` - IP with CIDR (e.g., `172.20.20.11/24`)
- `{{ primary_ip4.dns_name }}` - DNS name
- `{{ primary_ip4.description }}` - IP description

### Platform and Location
- `{{ platform.name }}` - Platform name (e.g., "Arista EOS")
- `{{ platform.manufacturer.name }}` - Manufacturer
- `{{ platform.napalm_driver }}` - NAPALM driver (e.g., "eos")
- `{{ platform.network_driver }}` - Network driver
- `{{ location.name }}` - Location name
- `{{ location.parent.name }}` - Parent location

### Role and Organization
- `{{ role.name }}` - Device role
- `{{ tenant.name }}` - Tenant name
- `{{ tags }}` - List of tags (iterate with `{% for tag in tags %}`)

### Interfaces
- `{{ interfaces }}` - List of all interfaces

For each interface:
```jinja2
{% for interface in interfaces %}
  {{ interface.name }}
  {{ interface.description }}
  {{ interface.mac_address }}
  {{ interface.enabled }}
  {{ interface.ip_addresses }}
  {{ interface.tagged_vlans }}
  {{ interface.untagged_vlan }}
{% endfor %}
```

### Configuration Context
- `{{ config_context }}` - Custom JSON data

Access nested values:
```jinja2
{{ config_context.ntp_servers }}
{{ config_context.vlans }}
{{ config_context.snmp.community }}
```

## Testing the Query

### Via GraphQL Interface

1. Navigate to **Extensibility → GraphQL**
2. Paste the query
3. Add variables:
   ```json
   {
     "device_id": "your-device-uuid-here"
   }
   ```
4. Click **Execute**
5. Review the results

### Via Golden Config

1. **Generate Intended Config**
   ```
   Jobs → Jobs → Generate Intended Configurations
   Select a device
   Run job
   ```

2. **Review Results**
   ```
   Plugins → Golden Config → Golden Configs
   Click on device
   View "Intended Configuration" tab
   ```

3. **Verify Variables**
   - Hostname should match device name
   - IP address should match primary IP
   - All template variables should be populated

## Troubleshooting

### Query Not Found

**Error:** "GraphQL query 'GoldenConfig' not found"

**Solution:**
1. Run Preflight Lab Setup job
2. Or run Design Builder job
3. Verify query exists in Extensibility → GraphQL Queries

### Query Syntax Error

**Error:** GraphQL syntax errors when executing

**Solution:**
1. Check query syntax in Extensibility → GraphQL Queries
2. Test query manually in GraphQL interface
3. Ensure device_id variable is valid UUID

### Missing Variables in Templates

**Error:** Template variables are undefined

**Solution:**
1. Verify query includes all required fields
2. Check device has data populated (IP, platform, etc.)
3. Test query execution manually
4. Review Golden Config logs for errors

### Permission Issues

**Error:** Cannot create or execute query

**Solution:**
1. Ensure user has `extras.add_graphqlquery` permission
2. Ensure user has `extras.run_graphqlquery` permission
3. Check job execution permissions

## Advanced Usage

### Modifying the Query

To add more fields to the query:

1. **Edit the query in Nautobot:**
   ```
   Extensibility → GraphQL Queries → GoldenConfig → Edit
   ```

2. **Add fields:**
   ```graphql
   device(id: $device_id) {
     # ... existing fields ...
     custom_field_data
     device_type {
       model
     }
   }
   ```

3. **Test the query:**
   ```
   Extensibility → GraphQL → Test with sample device_id
   ```

4. **Update template to use new fields:**
   ```jinja2
   Model: {{ device_type.model }}
   Custom Data: {{ custom_field_data }}
   ```

### Multiple Queries

You can create additional queries for different purposes:

```yaml
# In 1102_graphql_queries.j2

  - "!create_or_update:name": "DeviceInventory"
    query: |
      query {
        devices {
          name
          serial
          asset_tag
        }
      }
    variables: {}
```

## Files Modified

1. **`/jobs/jobs/preflight_lab_setup.py`**
   - Added `_create_graphql_queries()` method
   - Calls method in main `run()` function
   - Creates/updates GoldenConfig query programmatically

2. **`/jobs/jobs/design_builder/initial_data/designs/1102_graphql_queries.j2`**
   - Added GoldenConfig query definition
   - Uses Design Builder YAML format
   - Creates query when Design Builder runs

## Related Documentation

- [Golden Config Templates README](../templates/README_GOLDEN_CONFIG_TEMPLATES.md)
- [Device Provisioning Guide](./DEVICE_PROVISIONING.md)
- [Provisioning Quick Start](./PROVISIONING_QUICKSTART.md)
- [Nautobot GraphQL Documentation](https://docs.nautobot.com/projects/core/en/stable/user-guide/platform-functionality/graphql/)
- [Golden Config Plugin Documentation](https://docs.nautobot.com/projects/golden-config/)

## Summary

The GoldenConfig GraphQL query is now automatically created by both the preflight job and design_builder, ensuring that:

✅ Query is available for Golden Config plugin  
✅ All necessary device data is retrieved  
✅ Templates have access to required variables  
✅ Configuration generation works seamlessly  
✅ Query is version controlled in your repository  

You no longer need to manually create this query - it's handled automatically!

