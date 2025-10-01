# Lab Setup - Two Approaches

This document explains how to populate Nautobot with the lab topology data from the [Containerlab lab setup](https://netdevops.it/blog/building-a-reusable-network-automation-lab-with-containerlab/) using two different approaches.

## 🎯 **Lab Topology Overview**

Based on the Containerlab topology from the blog post, this creates:

- **2x Access Switches** (`access1`, `access2`) - Arista cEOS
- **1x Distribution Switch** (`dist1`) - Nokia SR Linux  
- **1x Core Router** (`rtr1`) - Nokia SR Linux
- **Management Network**: 172.20.20.0/24
- **VLANs**: Data (10), Voice (20), Management (30), Native (100)

## 🚀 **Approach 1: Custom Job (Imperative)**

### **What it does:**
- Programmatically creates Nautobot objects using Python code
- Provides interactive variables for customization
- Offers detailed logging and error handling
- Demonstrates the imperative/programmatic approach

### **How to use:**

1. **Access the Job**:
   - Go to Nautobot UI: http://localhost:8081
   - Navigate to: Admin → Jobs
   - Find: "Pre-flight Lab Setup"

2. **Run the Job**:
   - Click on "Pre-flight Lab Setup"
   - Configure variables (or use defaults):
     - **Site Name**: "Main Lab" (default)
     - **Management Subnet**: "172.20.20.0/24" (default)
     - **Create VLANs**: ✓ (default)
     - **Create Tags**: ✓ (default)
   - Click "Run Job"

3. **Monitor Progress**:
   - Watch the job logs in real-time
   - See detailed information about what's being created
   - Check for any errors or warnings

### **Job Features:**
- ✅ Creates site, device roles, platforms
- ✅ Creates organizational tags
- ✅ Creates VLANs and IP prefixes
- ✅ Creates devices with proper roles and platforms
- ✅ Creates interfaces with IP addresses
- ✅ Handles existing objects gracefully
- ✅ Provides detailed logging

## 🎨 **Approach 2: Design Builder (Declarative)**

### **What it does:**
- Uses YAML configuration to define the desired state
- Declarative approach - describes what you want, not how to create it
- Version-controlled configuration
- Demonstrates the declarative approach

### **How to use:**

1. **Access Design Builder**:
   - Go to Nautobot UI: http://localhost:8081
   - Navigate to: Admin → Design Builder
   - Click "Create Design"

2. **Import Configuration**:
   - Click "Import from YAML"
   - Copy the contents of `design_builder/lab_setup.yaml`
   - Paste into the import field
   - Click "Import"

3. **Review and Deploy**:
   - Review the design preview
   - Verify all objects are correctly defined
   - Click "Deploy Design"

### **Design Builder Features:**
- ✅ Declarative YAML configuration
- ✅ Visual preview of objects to be created
- ✅ Version control friendly
- ✅ Easy to modify and redeploy
- ✅ Handles dependencies automatically

## 📊 **Comparison**

| Feature | Custom Job | Design Builder |
|---------|------------|----------------|
| **Approach** | Imperative (how) | Declarative (what) |
| **Customization** | Interactive variables | YAML configuration |
| **Logging** | Detailed real-time logs | Basic deployment status |
| **Error Handling** | Programmatic control | Automatic rollback |
| **Version Control** | Code in Git | YAML in Git |
| **Learning Curve** | Python knowledge needed | YAML knowledge needed |
| **Flexibility** | High (full programming) | Medium (configuration) |

## 🔧 **Lab Topology Details**

### **Devices Created:**

#### **Access Layer (Arista cEOS)**
- **access1**: 172.20.20.11
  - Management1: 172.20.20.11/24
  - Ethernet1: Link to dist1
  - Ethernet2: Access port
  - Ethernet3: Access port

- **access2**: 172.20.20.12
  - Management1: 172.20.20.12/24
  - Ethernet1: Link to dist1
  - Ethernet2: Access port
  - Ethernet3: Access port

#### **Distribution Layer (Nokia SR Linux)**
- **dist1**: 172.20.20.13
  - ethernet-1/1: Link to access1
  - ethernet-1/2: Link to access2
  - ethernet-1/3: Link to rtr1
  - ethernet-1/4: 172.20.20.13/24

#### **Core Layer (Nokia SR Linux)**
- **rtr1**: 172.20.20.14
  - ethernet-1/1: Link to dist1
  - ethernet-1/2: 172.20.20.14/24

### **Network Objects:**
- **Site**: Main Lab
- **Prefix**: 172.20.20.0/24 (Management)
- **VLANs**: Data (10), Voice (20), Management (30), Native (100)
- **Tags**: lab, access, distribution, core, management, data

## 🎯 **Next Steps**

After populating the lab data:

1. **Verify the setup**:
   - Check Devices page for all 4 devices
   - Verify IP addresses are assigned
   - Confirm VLANs and prefixes exist

2. **Use with Containerlab**:
   - Deploy the Containerlab lab: `containerlab deploy -t containerlab/nautobot-lab.clab.yml`
   - The devices in Nautobot should match your Containerlab topology

3. **Continue with the blog series**:
   - Use this populated data for Device Onboarding (Part 2)
   - Use for Golden Config compliance (Part 3)
   - Use for automation workflows (Parts 4-6)

## 🚨 **Troubleshooting**

### **Custom Job Issues:**
- **Permission errors**: Ensure you have proper permissions to create objects
- **Validation errors**: Check that required fields are properly set
- **Duplicate objects**: The job handles existing objects gracefully

### **Design Builder Issues:**
- **Import errors**: Verify YAML syntax is correct
- **Deployment failures**: Check that referenced objects exist
- **Partial deployments**: Use rollback feature if needed

### **General Issues:**
- **Database connection**: Ensure Nautobot is running and database is accessible
- **Plugin issues**: Verify all required plugins are installed and configured
- **Network connectivity**: Check that management IPs are reachable

---

*Both approaches will create the same lab topology data. Choose the approach that best fits your workflow and expertise level!* 🎯
