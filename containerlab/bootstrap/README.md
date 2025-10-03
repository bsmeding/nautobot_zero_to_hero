# Bootstrap Configurations for Containerlab Lab

This directory contains bootstrap configuration files that automatically configure the network devices when the containerlab lab starts up.

## Files

- **`access1.cfg`** - Bootstrap config for access1 (Arista EOS)
- **`access2.cfg`** - Bootstrap config for access2 (Arista EOS)  
- **`dist1.cfg`** - Bootstrap config for dist1 (Nokia SR Linux)
- **`rtr1.cfg`** - Bootstrap config for rtr1 (Nokia SR Linux)

## What Each Config Does

### Arista EOS (access1, access2)
- Sets management IP: `172.20.20.11/24` and `172.20.20.12/24`
- Enables SSH service
- Enables HTTP API for automation
- Creates admin user with password "admin"
- Enables logging to management host

### Nokia SR Linux (dist1, rtr1)
- Sets management IP: `172.20.20.13/24` and `172.20.20.14/24`
- Enables gNMI server on port 57400
- Enables JSON-RPC server on port 80
- Creates admin user with password "admin"
- Commits configuration

## Usage

1. **Deploy the lab:**
   ```bash
   containerlab deploy -t nautobot-lab.clab.yml
   ```

2. **Verify SSH access:**
   ```bash
   ssh admin@172.20.20.11  # access1
   ssh admin@172.20.20.12  # access2
   ssh admin@172.20.20.13  # dist1
   ssh admin@172.20.20.14  # rtr1
   ```

3. **Test NAPALM connectivity:**
   ```bash
   # From Nautobot or management host
   napalm --user admin --password admin --vendor eos 172.20.20.11 get_facts
   napalm --user admin --password admin --vendor nokia_srl 172.20.20.13 get_facts
   ```

## Management Network

All devices are configured on the management network:
- **Subnet:** `172.20.20.0/24`
- **Access1:** `172.20.20.11`
- **Access2:** `172.20.20.12`
- **Dist1:** `172.20.20.13`
- **Rtr1:** `172.20.20.14`

## Credentials

- **Username:** `admin`
- **Password:** `admin`
- **Privilege:** 15 (for Arista), admin (for Nokia)

## Automation APIs

- **Arista:** HTTP API enabled on port 80
- **Nokia:** gNMI on port 57400, JSON-RPC on port 80
- **NAPALM:** All devices support NAPALM for automation
