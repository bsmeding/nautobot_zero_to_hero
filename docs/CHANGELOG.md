# Changelog

## Pre-flight Lab Setup Job Updates

### Fixed: Management Subnet Parameter
- **Issue:** The `preflight_lab_setup.py` job had a configurable `management_subnet` parameter that could cause conflicts with the containerlab topology
- **Solution:** Hardcoded the management subnet to `172.20.20.0/24` to match the containerlab topology exactly
- **Changes:**
  - Removed `management_subnet` StringVar parameter
  - Hardcoded `management_subnet = "172.20.20.0/24"` in the function
  - Updated job description to indicate fixed subnet
  - Updated site_name description for clarity

### Benefits:
- **Consistency:** Job always uses the same subnet as containerlab
- **Reliability:** No risk of subnet mismatch between Nautobot and containerlab
- **Simplicity:** Fewer parameters to configure
- **Compatibility:** Ensures NAPALM connectivity works correctly

### Usage:
The job now automatically uses the correct subnet (`172.20.20.0/24`) that matches the containerlab topology, ensuring:
- Device IPs are correctly assigned (172.20.20.11-14)
- NAPALM connectivity works
- Network discovery functions properly
- Status monitoring is accurate

This ensures the lab setup is robust and reusable across different environments.
