# Nautobot Integration with Containerlab Lab

This guide explains how to integrate the containerlab lab with Nautobot for status monitoring, automation, and network management.

## 🎯 **Integration Overview**

The lab is designed to work seamlessly with Nautobot through:
- **NAPALM Integration:** Device connectivity and automation
- **Status Monitoring:** Real-time device health checks
- **Network Discovery:** Automatic topology discovery
- **Configuration Management:** Device configuration tracking

## 🔧 **Prerequisites**

### **1. Nautobot Configuration**
The `docker compose.yml` already includes:
```yaml
environment:
  - NAUTOBOT_NAPALM_USERNAME=admin
  - NAUTOBOT_NAPALM_PASSWORD=admin
  - NAUTOBOT_NAPALM_TIMEOUT=5
```

### **2. Network Connectivity**
- Nautobot is on the `clab` network
- Containerlab devices have static IPs
- NAPALM drivers are configured

## 🚀 **Integration Steps**

### **Step 1: Deploy the Lab**
```bash
# Start Nautobot
docker compose up -d

# Deploy containerlab
cd containerlab
containerlab deploy -t nautobot-lab.clab.yml
```

### **Step 2: Populate Nautobot**
1. **Access Nautobot:** http://localhost:8081
2. **Login:** admin/admin
3. **Run Jobs:**
   - Go to **Jobs** → **Pre-flight Lab Setup**
   - Click **Run Job**
   - This populates Nautobot with lab topology

### **Step 3: Monitor Device Status**
1. **Run Device Status Monitor:**
   - Go to **Jobs** → **Device Status Monitor**
   - Click **Run Job**
   - This checks device connectivity and status

### **Step 4: Discover Network Topology**
1. **Run Network Discovery:**
   - Go to **Jobs** → **Network Discovery**
   - Click **Run Job**
   - This discovers interfaces and neighbors

## 📊 **Available Jobs**

### **1. Pre-flight Lab Setup**
- **Purpose:** Populate Nautobot with lab topology
- **Creates:** Sites, devices, interfaces, IPs, VLANs
- **Run:** Once after lab deployment

### **2. Device Status Monitor**
- **Purpose:** Monitor device health and status
- **Features:**
  - NAPALM connectivity checks
  - Interface status monitoring
  - System information gathering
  - Status updates in Nautobot
- **Run:** Regularly for monitoring

### **3. Network Discovery**
- **Purpose:** Discover network topology
- **Features:**
  - Interface discovery
  - LLDP neighbor discovery
  - Device facts gathering
  - Topology mapping
- **Run:** After topology changes

## 🔍 **NAPALM Integration Details**

### **Supported Devices:**
| Device | Driver | IP Address | Status |
|--------|--------|------------|--------|
| access1 | eos | 172.20.20.11 | ✅ Supported |
| access2 | eos | 172.20.20.12 | ✅ Supported |
| dist1 | nokia_srl | 172.20.20.13 | ✅ Supported |
| rtr1 | nokia_srl | 172.20.20.14 | ✅ Supported |

### **NAPALM Capabilities:**
- **Device Facts:** Hostname, model, OS version
- **Interface Status:** Up/down, speed, description
- **LLDP Neighbors:** Network topology discovery
- **Configuration:** Running config retrieval
- **Health Checks:** Connectivity and status monitoring

## 🔄 **Automation Workflows**

### **1. Daily Monitoring**
```bash
# Run device status check
curl -X POST http://localhost:8081/api/jobs/device-status-monitor/run/ \
  -H "Authorization: Token YOUR_TOKEN"
```

### **2. Topology Discovery**
```bash
# Run network discovery
curl -X POST http://localhost:8081/api/jobs/network-discovery/run/ \
  -H "Authorization: Token YOUR_TOKEN"
```

### **3. Configuration Backup**
```bash
# Backup device configs
curl -X POST http://localhost:8081/api/jobs/device-status-monitor/run/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{"backup_configs": true}'
```

## 📈 **Monitoring Dashboard**

### **Device Status:**
- **Active:** Device is reachable via NAPALM
- **Failed:** Device is unreachable
- **Maintenance:** Device is in maintenance mode

### **Interface Status:**
- **Up:** Interface is operational
- **Down:** Interface is not operational
- **Unknown:** Status cannot be determined

### **Network Topology:**
- **LLDP Neighbors:** Discovered via NAPALM
- **Interface Connections:** Mapped automatically
- **Device Relationships:** Parent-child relationships

## 🔧 **Troubleshooting**

### **NAPALM Connection Issues:**
```bash
# Test NAPALM connectivity
docker exec -it nzth-nautobot python -c "
import napalm
driver = napalm.get_network_driver('eos')
with driver('172.20.20.11', 'admin', 'admin') as conn:
    print(conn.get_facts())
"
```

### **Device Status Issues:**
1. **Check device connectivity:**
   ```bash
   ping 172.20.20.11
   ```

2. **Check NAPALM credentials:**
   - Username: admin
   - Password: admin

3. **Check device status:**
   ```bash
   docker exec -it clab-nautobot-lab-access1 FastCli -c "show version"
   ```

### **Job Execution Issues:**
1. **Check job logs** in Nautobot UI
2. **Verify device connectivity**
3. **Check NAPALM driver installation**
4. **Verify network connectivity**

## 🎯 **Best Practices**

### **1. Regular Monitoring**
- Run device status monitor every 5 minutes
- Run network discovery after topology changes
- Monitor job execution logs

### **2. Automation**
- Use Nautobot's REST API for automation
- Implement webhooks for real-time updates
- Set up alerting for device failures

### **3. Maintenance**
- Regular device configuration backups
- Interface status monitoring
- Topology change detection

## 📚 **Additional Resources**

- **NAPALM Documentation:** https://napalm.readthedocs.io/
- **Nautobot Jobs:** https://docs.nautobot.com/en/stable/plugins/development/jobs/
- **Containerlab Documentation:** https://containerlab.dev/

This integration provides a complete network automation and monitoring solution using Nautobot and containerlab!
