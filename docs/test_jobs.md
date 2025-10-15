# Testing the Jobs

## ✅ **Jobs Should Now Be Available**

After restarting Nautobot, you should now see these jobs in the Admin → Jobs section:

1. **Simple Input Job** (original test job)
2. **Simple Lab Setup** (basic test job)
3. **Pre-flight Lab Setup** (full lab topology job)

## 🧪 **Testing the Jobs**

### **1. Test Simple Lab Setup First**
1. Go to **Admin → Jobs**
2. Click on **"Simple Lab Setup"**
3. Use default values or customize:
   - **Site Name**: "Main Lab" (default)
   - **Create Site**: ✓ (default)
4. Click **"Run Job"**
5. Watch the logs - should complete successfully

### **2. Test Pre-flight Lab Setup**
1. Go to **Admin → Jobs**
2. Click on **"Pre-flight Lab Setup"**
3. Configure variables:
   - **Site Name**: "Main Lab" (default)
   - **Management Subnet**: "172.20.20.0/24" (default)
   - **Create VLANs**: ✓ (default)
   - **Create Tags**: ✓ (default)
4. Click **"Run Job"**
5. Watch the detailed logs

## 🔍 **What the Pre-flight Job Creates**

### **Network Objects:**
- **Site**: "Main Lab" (Location of type Site)
- **Prefix**: 172.20.20.0/24 (Management network)
- **VLANs**: Data (10), Voice (20), Management (30), Native (100)
- **Tags**: lab, access, distribution, core, management, data

### **Devices:**
- **access1**: 172.20.20.11 (Arista cEOS)
- **access2**: 172.20.20.12 (Arista cEOS)
- **dist1**: 172.20.20.13 (Nokia SR Linux)
- **rtr1**: 172.20.20.14 (Nokia SR Linux)

### **Device Roles:**
- Access Switch (green)
- Distribution Switch (orange)
- Core Router (red)

### **Platforms:**
- Arista EOS
- Nokia SR Linux

## 🎯 **Expected Results**

After running the Pre-flight Lab Setup job, you should see:

1. **In Locations**: "Main Lab" site
2. **In Devices**: 4 devices with proper roles and platforms
3. **In IP Addresses**: Management IPs assigned to devices
4. **In Interfaces**: Device interfaces with descriptions
5. **In VLANs**: 4 VLANs (Data, Voice, Management, Native)
6. **In Prefixes**: Management network 172.20.20.0/24
7. **In Tags**: 6 organizational tags

## 🚨 **Troubleshooting**

### **If you get Location validation errors:**
- The job now properly handles Location types
- It creates a Site location type if needed
- It ensures proper parent-child relationships

### **If jobs don't appear:**
- Check that Nautobot restarted successfully
- Look for import errors in the logs
- Verify the job files are in the correct location

### **If job fails:**
- Check the job logs for specific error messages
- Verify that all required plugins are installed
- Ensure you have proper permissions

## 🎉 **Success Indicators**

✅ Jobs appear in Admin → Jobs  
✅ Jobs run without errors  
✅ Objects are created in Nautobot  
✅ No validation errors in logs  
✅ Job completes with success message  

---

*Once the jobs are working, you can proceed with the blog series using this populated data!* 🚀
