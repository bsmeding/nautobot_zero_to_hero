# Deterministic Containerlab Lab Setup

This lab is configured to ensure everyone gets the same devices and IP addresses.

## 🔧 **Static IP Configuration**

### **Management Network:**
- **Subnet:** `172.20.20.0/24`
- **Gateway:** `172.20.20.1`

### **Device IP Assignments:**
| Device | IP Address | Port Mapping | Description |
|--------|------------|--------------|-------------|
| **access1** | `172.20.20.11` | 50001:22, 50002:830 | Arista EOS Access Switch 1 |
| **access2** | `172.20.20.12` | 50003:22, 50004:830 | Arista EOS Access Switch 2 |
| **dist1** | `172.20.20.13` | 50005:22, 50006:830 | Nokia SR Linux Distribution Switch |
| **rtr1** | `172.20.20.14` | 50007:22, 50008:830 | Nokia SR Linux Router |
| **mgmt** | `172.20.20.16` | 50010:22 | Management Host |
| **workstation1** | `172.20.20.15` | 50009:22 | Network Testing Workstation |

## 🚀 **How to Deploy**

### **1. Prerequisites:**
```bash
# Install containerlab
curl -sL https://get.containerlab.dev | bash

# Pull required images
docker pull ceos:4.34.2F
docker pull ghcr.io/nokia/srlinux
docker pull alpine:latest
```

### **2. Deploy the Lab:**
```bash
# Navigate to containerlab directory
cd containerlab

# Deploy the lab
containerlab deploy -t nautobot-lab.clab.yml

# Verify deployment
containerlab inspect
```

### **3. Verify Static IPs:**
```bash
# Check that all devices have the expected IPs
containerlab inspect | grep "172.20.20"

# Test connectivity
ping 172.20.20.11  # access1
ping 172.20.20.12  # access2
ping 172.20.20.13  # dist1
ping 172.20.20.14  # rtr1
```

## 🔑 **SSH Access**

### **Network Devices:**
```bash
ssh admin@172.20.20.11  # access1
ssh admin@172.20.20.12  # access2
ssh admin@172.20.20.13  # dist1
ssh admin@172.20.20.14  # rtr1
```

### **Linux Containers:**
```bash
ssh root@172.20.20.16   # mgmt
ssh root@172.20.20.15   # workstation1
```

**Credentials:** `admin/admin` for network devices, `root/admin` for Linux containers

## 🔄 **Reset Lab**

```bash
# Destroy and recreate
containerlab destroy -t nautobot-lab.clab.yml
containerlab deploy -t nautobot-lab.clab.yml
```

## 📋 **Bootstrap Configuration**

The lab uses bootstrap configurations that automatically:
- Configure management IPs
- Enable SSH
- Set up authentication
- Enable automation APIs (gNMI, JSON-RPC, HTTP)

## 🎯 **Deterministic Features**

1. **Static IP Assignment:** Each device has a fixed IP via `mgmt-ipv4`
2. **Bootstrap Configs:** Automatic configuration on startup
3. **Consistent Naming:** All devices follow the same naming convention
4. **Port Mappings:** Fixed port mappings for external access

## 🔧 **Troubleshooting**

### **If IPs are different:**
```bash
# Check containerlab version
containerlab version

# Ensure you're using the latest topology
git pull origin main

# Redeploy
containerlab destroy -t nautobot-lab.clab.yml
containerlab deploy -t nautobot-lab.clab.yml
```

### **If SSH doesn't work:**
```bash
# Check if bootstrap configs are applied
docker exec -it clab-nautobot-lab-access1 Cli
show management ssh

# Manually configure if needed
docker exec -it clab-nautobot-lab-access1 Cli
enable
configure
management ssh
   no shutdown
exit
exit
```

This setup ensures that everyone using this lab gets exactly the same topology and IP addresses!