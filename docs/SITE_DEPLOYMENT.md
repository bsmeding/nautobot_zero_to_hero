# Dynamic Site Deployment

This guide explains how to use the Deploy Site job to quickly create complete network sites with minimal input.

## Overview

The **Deploy Site** job allows you to create a complete network site infrastructure with just 4 parameters:

1. **Site Name** - Human-readable name (e.g., "Chicago Lab")
2. **Site Shortcode** - 3 letters + 2 digits (e.g., "CHI01")
3. **Site Prefix** - IP prefix for the site (e.g., "172.21.0.0/16")
4. **Region** - Region name (e.g., "US-Central")

From these 4 inputs, the job automatically creates:
- ✅ Region and Site locations
- ✅ 2 Racks with site-specific names
- ✅ 4 VLANs with site naming
- ✅ IP prefix and management subnet
- ✅ 4 Network devices (access1, access2, dist1, rtr1)
- ✅ 2 Virtual machines (workstation1, management)
- ✅ All IP addresses with DNS names
- ✅ All interfaces with VLAN configurations
- ✅ All cable connections
- ✅ Site-specific config context

## Architecture

```
Input: 4 Parameters
    ↓
┌─────────────────────────────────────────┐
│        Deploy Site Job                  │
│  • Validates inputs                     │
│  • Calculates derived values            │
│  • Renders YAML template                │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│    Design Builder Engine                │
│  • Creates locations                    │
│  • Creates racks                        │
│  • Creates VLANs                        │
│  • Creates prefixes                     │
│  • Creates devices                      │
│  • Creates IPs                          │
│  • Creates interfaces                   │
│  • Creates cables                       │
│  • Creates config contexts              │
└──────────────┬──────────────────────────┘
               ↓
Complete Site Infrastructure Created! ✅
```

## Usage

The `site_deployment.yaml` is a Design Builder design file. You use it with the **Design Builder job** by providing context variables.

### Method 1: Via Design Builder Job (Recommended)

1. Navigate to **Jobs → Jobs → Design Builder**
2. Click **Run Job**
3. **Design Files**: Select or upload `site_deployment.yaml`
4. **Context**: Provide JSON with variables:

```json
{
  "site_name": "Chicago Lab",
  "site_shortcode": "CHI01",
  "site_prefix": "172.21.0.0/16",
  "region": "US-Central"
}
```

5. Click **Run Job**

### Method 2: Via API

```python
import requests

response = requests.post(
    "http://localhost:8080/api/extras/jobs/design_builder.DesignJob/run/",
    headers={"Authorization": "Token YOUR_TOKEN"},
    json={
        "data": {
            "design_file": "site_deployment.yaml",
            "context": {
                "site_name": "Chicago Lab",
                "site_shortcode": "CHI01",
                "site_prefix": "172.21.0.0/16",
                "region": "US-Central"
            }
        }
    }
)
```

### Basic Example

**Input Context:**
```json
{
  "site_name": "Chicago Lab",
  "site_shortcode": "CHI01",
  "site_prefix": "172.21.0.0/16",
  "region": "US-Central"
}
```

**Output Creates:**
```
Region: US-Central
Site: Chicago Lab
Racks:
  - CHI01-RACK-01
  - CHI01-RACK-02
VLANs:
  - VLAN 10: CHI01-Management
  - VLAN 20: CHI01-Data
  - VLAN 30: CHI01-Voice
  - VLAN 100: CHI01-LabNetwork
Prefixes:
  - 172.21.0.0/16 (container)
  - 172.21.20.0/24 (management subnet)
Devices:
  - CHI01-access1 (172.21.20.11/24)
  - CHI01-access2 (172.21.20.12/24)
  - CHI01-dist1 (172.21.20.13/24)
  - CHI01-rtr1 (172.21.20.14/24)
Virtual Machines:
  - CHI01-workstation1 (172.21.20.15/24)
  - CHI01-management (172.21.20.16/24)
Cables:
  - All devices interconnected per topology
Config Context:
  - Site-specific NTP, DNS, SNMP, etc.
```

## Input Parameters

### Site Name

**Format:** Any string  
**Example:** `"Chicago Lab"`, `"New York Office"`, `"Tokyo Datacenter"`  
**Used For:**
- Location name in Nautobot
- Config context descriptions
- DNS domain names (sanitized)

### Site Shortcode

**Format:** 3 uppercase letters + 2 digits  
**Regex:** `^[A-Z]{3}\d{2}$`  
**Examples:**
- `CHI01` - Chicago site 1
- `NYC02` - New York site 2
- `LON01` - London site 1
- `TKY01` - Tokyo site 1

**Used For:**
- Device hostname prefixes (e.g., `CHI01-access1`)
- Rack names (e.g., `CHI01-RACK-01`)
- VLAN names (e.g., `CHI01-Management`)
- Resource identification

**Validation:**
- Must be exactly 5 characters
- First 3 must be uppercase letters
- Last 2 must be digits

### Site Prefix

**Format:** CIDR notation  
**Regex:** `^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$`  
**Examples:**
- `172.21.0.0/16` - 65,536 addresses
- `172.22.0.0/16` - Another /16 block
- `192.168.10.0/24` - Small site (256 addresses)
- `10.100.0.0/16` - Large site

**Used For:**
- Container prefix in Nautobot
- Calculating management subnet (.20.0/24)
- Device IP addresses (.20.11, .20.12, etc.)
- VM IP addresses (.20.15, .20.16)

**Automatic Calculations:**
From `172.21.0.0/16`:
- Management subnet: `172.21.20.0/24`
- Device IPs: `172.21.20.11-14`
- VM IPs: `172.21.20.15-16`

### Region

**Format:** Any string  
**Example:** `"US-Central"`, `"Europe"`, `"Asia-Pacific"`  
**Used For:**
- Parent location for site
- Organizational hierarchy
- Grouping sites

## What Gets Created

### 1. Location Hierarchy

```
Region (e.g., US-Central)
  └── Site (e.g., Chicago Lab)
```

### 2. Racks (2)

```
CHI01-RACK-01 (42U) - Distribution and router
CHI01-RACK-02 (42U) - Access switches
```

### 3. VLANs (4)

```
VLAN 10  - CHI01-Management
VLAN 20  - CHI01-Data
VLAN 30  - CHI01-Voice
VLAN 100 - CHI01-LabNetwork
```

### 4. IP Prefixes

```
172.21.0.0/16    - Container prefix
172.21.20.0/24   - Management subnet
```

### 5. Network Devices (4)

| Device | Hostname | IP | Location | Rack | Position |
|--------|----------|-----|----------|------|----------|
| Access 1 | CHI01-access1 | 172.21.20.11/24 | Chicago Lab | RACK-02 | U11 |
| Access 2 | CHI01-access2 | 172.21.20.12/24 | Chicago Lab | RACK-02 | U12 |
| Distribution | CHI01-dist1 | 172.21.20.13/24 | Chicago Lab | RACK-01 | U15 |
| Router | CHI01-rtr1 | 172.21.20.14/24 | Chicago Lab | RACK-01 | U20 |

### 6. Virtual Machines (2)

| VM | Hostname | IP | Cluster | Role |
|----|----------|-----|---------|------|
| Workstation | CHI01-workstation1 | 172.21.20.15/24 | Lab-Cluster | Workstation |
| Management | CHI01-management | 172.21.20.16/24 | Lab-Cluster | Management |

### 7. Interfaces

All devices get standard interfaces:
- **Management0** - Management interface
- **Ethernet1-3** - Data interfaces
- **Proper modes** - Tagged (trunk) or access
- **VLAN assignments** - Per topology

### 8. Cable Connections

```
access1:Ethernet1 ←→ dist1:Ethernet1
access2:Ethernet1 ←→ dist1:Ethernet2
dist1:Ethernet3   ←→ rtr1:Ethernet1
```

### 9. Config Context

Site-specific configuration with:
- NTP servers using site gateway (.20.1)
- SNMP community with site shortcode
- Syslog servers
- DNS domain: `{site_name}.local`

## Step-by-Step Usage

### Step 1: Navigate to Design Builder

1. Go to **Jobs → Jobs**
2. Find **"Design Builder"** job
3. Click **Run Job**

### Step 2: Select Design File

**Design Files:** 
- Upload `site_deployment.yaml` or
- If already available, select it from the list

### Step 3: Provide Context (JSON)

In the **Context** field, enter JSON with your site parameters:

```json
{
  "site_name": "Chicago Lab",
  "site_shortcode": "CHI01",
  "site_prefix": "172.21.0.0/16",
  "region": "US-Central"
}
```

### Step 4: Run and Monitor

1. Click **Run Job Now**
2. Monitor execution in real-time
3. Review created resources in the logs

### Step 4: Verify Results

**Check Locations:**
```
Organization → Locations
└── US-Central (Region)
    └── Chicago Lab (Site)
```

**Check Devices:**
```
Devices → Devices
Filter by Location: Chicago Lab
Should see: CHI01-access1, CHI01-access2, CHI01-dist1, CHI01-rtr1
```

**Check IP Addresses:**
```
IPAM → IP Addresses
Filter by Prefix: 172.21.20.0/24
Should see: .11, .12, .13, .14, .15, .16
```

## Multiple Sites Example

Deploy multiple sites quickly:

### Site 1: Chicago
```
Site Name: Chicago Lab
Site Shortcode: CHI01
Site Prefix: 172.21.0.0/16
Region: US-Central
```

### Site 2: New York
```
Site Name: New York Lab
Site Shortcode: NYC01
Site Prefix: 172.22.0.0/16
Region: US-East
```

### Site 3: Los Angeles
```
Site Name: Los Angeles Lab
Site Shortcode: LAX01
Site Prefix: 172.23.0.0/16
Region: US-West
```

Each creates a complete, independent site!

## Network Topology Created

```
                  CHI01-dist1
                 (172.21.20.13)
                       │
        ┌──────────────┼──────────────┐
        │              │              │
    Ethernet1      Ethernet2      Ethernet3
   (Trunk VLAN10)(Trunk VLAN10)(Trunk VLAN10)
        │              │              │
        │              │              │
    Ethernet1      Ethernet1      Ethernet1
        │              │              │
   CHI01-access1  CHI01-access2   CHI01-rtr1
  (172.21.20.11) (172.21.20.12) (172.21.20.14)
        │              │              │
    Ethernet2      Ethernet2      Ethernet2
   (Access       (Access        (Access
    VLAN 10)      VLAN 20)       VLAN 10)
        │              │              │
        │              │              │
CHI01-workstation1     │      CHI01-management
  (172.21.20.15)   Ethernet3    (172.21.20.16)
                  (Access
                   VLAN 30)
```

## Advanced Features

### Automatic IP Calculation

The job automatically calculates all IPs from the site prefix:

**For site_prefix = `172.21.0.0/16`:**
- Management subnet: `172.21.20.0/24`
- Access1 IP: `172.21.20.11/24`
- Access2 IP: `172.21.20.12/24`
- Dist1 IP: `172.21.20.13/24`
- Rtr1 IP: `172.21.20.14/24`
- Workstation1 IP: `172.21.20.15/24`
- Management IP: `172.21.20.16/24`

### DNS Name Generation

DNS names are automatically generated:
```
CHI01-access1.chicago-lab
CHI01-access2.chicago-lab
CHI01-dist1.chicago-lab
etc.
```

### Config Context Integration

Site-specific config context created with:
```json
{
  "site_shortcode": "CHI01",
  "ntp_servers": ["172.21.20.1", "time.google.com"],
  "dns_servers": ["8.8.8.8", "8.8.4.4"],
  "syslog_hosts": [{"host": "172.21.20.1", "port": 514}],
  "snmp": {
    "community": "CHI01_ro",
    "location": "Chicago Lab"
  },
  "timezone": "UTC",
  "domain_name": "chicago-lab.local"
}
```

## Validation

The job validates all inputs:

### Site Shortcode Validation

✅ Valid:
- `CHI01`, `NYC02`, `LAX01`, `LON01`

❌ Invalid:
- `chi01` (lowercase)
- `CH101` (too many digits)
- `CHI1` (too few digits)
- `CHICAGO` (no digits)
- `C01` (too few letters)

### Site Prefix Validation

✅ Valid:
- `172.21.0.0/16`
- `192.168.10.0/24`
- `10.100.0.0/16`

❌ Invalid:
- `172.21.0.0` (no CIDR)
- `172.21.0/16` (incomplete IP)
- `256.1.1.1/24` (invalid octet)

⚠️ Warning (non-RFC 1918):
- `8.8.8.0/24` (public IP)
- `1.1.1.0/24` (public IP)

The job will warn but still allow non-private addresses.

## Use Cases

### Use Case 1: Lab Environment

Create identical lab environments for different purposes:

```
Development Lab:  DEV01, 172.30.0.0/16
Testing Lab:      TST01, 172.31.0.0/16
Staging Lab:      STG01, 172.32.0.0/16
Production Lab:   PRD01, 172.33.0.0/16
```

### Use Case 2: Multi-Site Deployment

Deploy to multiple geographic locations:

```
Chicago:      CHI01, 172.21.0.0/16, US-Central
New York:     NYC01, 172.22.0.0/16, US-East
Los Angeles:  LAX01, 172.23.0.0/16, US-West
London:       LON01, 172.24.0.0/16, Europe
```

### Use Case 3: Customer Sites

Deploy identical infrastructure per customer:

```
Customer A Site 1:  CTA01, 172.40.0.0/16
Customer A Site 2:  CTA02, 172.41.0.0/16
Customer B Site 1:  CTB01, 172.50.0.0/16
Customer B Site 2:  CTB02, 172.51.0.0/16
```

## Post-Deployment Steps

After the job completes:

### 1. Assign IP Addresses to Interfaces

The IPs are created but need to be assigned:

```
For each device:
1. Go to device page
2. Click "Interfaces" tab
3. Edit Management0
4. Add IP Address: {corresponding IP}
5. Set as Primary IPv4
```

Or run a script to automate this.

### 2. Configure Secrets Group

```
Devices → Devices → CHI01-access1 → Edit
Secrets Group: Arista NAPALM Secrets Group
Repeat for all devices
```

### 3. Generate Golden Config

```
Jobs → Jobs → Generate Intended Configurations
Select devices from site
Run job
```

### 4. Provision Devices

```
For each device:
Device Page → Click "Provision Device" button
Configure and run
```

## Customization

### Modify the Design

Edit `/jobs/jobs/design_builder/lab_setup/site_deployment.yaml` to customize:

**Add more devices:**
```yaml
- "!create_or_update:name": "{{ site_shortcode }}-firewall1"
  location__name: "{{ site_name }}"
  role__name: "Firewall"
  ...
```

**Change IP allocation:**
```yaml
# Use different third octet
{{ site_prefix.split('.')[0] }}.{{ site_prefix.split('.')[1] }}.30.11/24
```

**Add more VLANs:**
```yaml
- "!create_or_update:vid": 40
  "!create_or_update:name": "{{ site_shortcode }}-Guest"
  status__name: "Active"
```

### Extend the Job

Add more parameters in `/jobs/jobs/deploy_site.py`:

```python
num_access_switches = IntegerVar(
    description="Number of access switches to create",
    default=2,
    min_value=1,
    max_value=10,
)
```

## Naming Conventions

All resources use consistent naming:

| Resource Type | Naming Pattern | Example |
|---------------|----------------|---------|
| Devices | `{shortcode}-{type}{number}` | `CHI01-access1` |
| Racks | `{shortcode}-RACK-{number}` | `CHI01-RACK-01` |
| VLANs | `{shortcode}-{purpose}` | `CHI01-Management` |
| IP DNS Names | `{shortcode}-{device}.{site}` | `CHI01-access1.chicago-lab` |

## IP Address Scheme

Management subnet always uses `.20` third octet:

| Device | Fourth Octet | Full IP (for 172.21.x.x) |
|--------|--------------|--------------------------|
| Gateway | .1 | 172.21.20.1 |
| Access1 | .11 | 172.21.20.11 |
| Access2 | .12 | 172.21.20.12 |
| Dist1 | .13 | 172.21.20.13 |
| Rtr1 | .14 | 172.21.20.14 |
| Workstation1 | .15 | 172.21.20.15 |
| Management | .16 | 172.21.20.16 |

## Comparison with Manual Setup

### Manual Setup (Old Way)

1. Create region ✋
2. Create site ✋
3. Create 2 racks ✋
4. Create 4 VLANs ✋
5. Create prefixes ✋
6. Create 4 devices ✋
7. Create 2 VMs ✋
8. Create ~20 interfaces ✋
9. Assign VLANs ✋
10. Create 6 IP addresses ✋
11. Assign IPs to interfaces ✋
12. Create 3 cables ✋
13. Create config context ✋

**Time: 30-45 minutes** ⏱️

### Deploy Site Job (New Way)

1. Run job ✅
2. Enter 4 parameters ✅
3. Click Run ✅

**Time: 2 minutes** ⚡

---

## Troubleshooting

### Invalid Site Shortcode Error

**Error:** "Invalid site shortcode 'chi01'"

**Solution:** Use uppercase: `CHI01`

### Invalid Prefix Error

**Error:** "Invalid site prefix '172.21.0.0'"

**Solution:** Add CIDR notation: `172.21.0.0/16`

### Objects Already Exist

**Behavior:** Job updates existing objects

The design uses `!create_or_update`, so:
- Existing objects are updated
- New objects are created
- Safe to run multiple times

### Design File Not Found

**Error:** "Design file not found"

**Solution:** Ensure `site_deployment.yaml` exists in:
```
/jobs/jobs/design_builder/lab_setup/site_deployment.yaml
```

## API Usage

Deploy sites programmatically:

```python
import requests

nautobot_url = "http://localhost:8080"
api_token = "your-api-token"

sites = [
    {"name": "Chicago Lab", "code": "CHI01", "prefix": "172.21.0.0/16", "region": "US-Central"},
    {"name": "New York Lab", "code": "NYC01", "prefix": "172.22.0.0/16", "region": "US-East"},
]

for site in sites:
    response = requests.post(
        f"{nautobot_url}/api/extras/jobs/deploy_site.DeploySite/run/",
        headers={
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json"
        },
        json={
            "data": {
                "site_name": site["name"],
                "site_shortcode": site["code"],
                "site_prefix": site["prefix"],
                "region": site["region"]
            }
        }
    )
    print(f"Deployed {site['name']}: HTTP {response.status_code}")
```

## Best Practices

### 1. Plan IP Address Space

Reserve /16 blocks for each site:
- `172.20.0.0/16` - Original lab
- `172.21.0.0/16` - Site 1
- `172.22.0.0/16` - Site 2
- etc.

### 2. Use Consistent Shortcodes

Create a naming convention:
- First 2 letters: Location (CH, NY, LA, LO)
- Third letter: Purpose (I=Internal, E=External, P=Production)
- Last 2 digits: Sequential (01, 02, 03)

### 3. Document Deployments

Keep a record of deployed sites:
```
CHI01 - Chicago Lab - 172.21.0.0/16
NYC01 - New York Lab - 172.22.0.0/16
LAX01 - Los Angeles Lab - 172.23.0.0/16
```

### 4. Test First

Test with a development site before production:
```
Site Name: Test Site
Site Shortcode: TST99
Site Prefix: 172.99.0.0/16
Region: Testing
```

## Related Documentation

- [Preflight Lab Setup](../jobs/jobs/preflight_lab_setup.py) - Original manual setup
- [Lab Setup YAML](../jobs/jobs/design_builder/lab_setup/lab_setup.yaml) - Template basis
- [Design Builder Documentation](https://docs.nautobot.com/projects/design-builder/)

## Summary

The Deploy Site job enables:

✅ **Rapid site deployment** - 2 minutes vs 45 minutes  
✅ **Consistency** - Same structure every time  
✅ **Scalability** - Deploy unlimited sites  
✅ **Flexibility** - Customize via parameters  
✅ **Standards compliance** - Enforced naming conventions  
✅ **Integration** - Works with provisioning system  

Deploy a complete network site with just 4 parameters! 🚀

