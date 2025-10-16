#!/usr/bin/env python3

"""
USE NAUTOBOT FOR DEVICE INVENTORY: Fetch device list from Nautobot instead of static code.

This script demonstrates the transition from static inventory to Nautobot inventory:
- Device list comes from Nautobot (dynamic)
- Configuration template is still static (same as script 4b)
- Next step (script 6): Get interface states from Nautobot too

This is the bridge between hardcoded devices and full Nautobot-driven automation.
"""

import os
import requests
import pyeapi
from jinja2 import Environment, BaseLoader


# Static template (same as script 4b)
TEMPLATE = """
!
! === FIX: Enable Ethernet2 interfaces ===
!
interface Ethernet2
  description Connected to data plane
  switchport mode access
  switchport access vlan 10
  no shutdown
!
! === Add Loopback interface ===
!
interface Loopback0
  description {{ device_name }} Loopback
  ip address {{ loopback_ip }}/32
  no shutdown
!
end
"""


def get_devices_from_nautobot(nb_url: str, token: str):
    """Fetch device inventory from Nautobot.
    
    Returns list of devices with name, host (primary IP), and role.
    """
    headers = {"Authorization": f"Token {token}"}
    
    # Fetch all devices with depth=1 to include related objects
    resp = requests.get(
        f"{nb_url}/api/dcim/devices/?depth=1",
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()
    all_devices = resp.json().get("results", [])
    
    # Convert to simple inventory format
    inventory = []
    for device in all_devices:
        # Get primary IP
        primary = device.get("primary_ip4") or device.get("primary_ip")
        if not primary:
            continue  # Skip devices without management IP
        
        host = primary.get("address", "").split("/")[0]
        if not host:
            continue
        
        # Extract role name
        role = "Unknown"
        if isinstance(device.get("role"), dict):
            role = device["role"].get("display") or device["role"].get("name", "Unknown")
        
        inventory.append({
            "name": device.get("name"),
            "host": host,
            "role": role
        })
    
    return inventory


def push_config(host: str, hostname: str, rendered_cfg: str) -> None:
    """Push rendered configuration to device via eAPI."""
    connection = pyeapi.connect(
        transport="https",
        host=host,
        username="admin",
        password="admin",
        port=443,
    )
    node = pyeapi.client.Node(connection)
    
    # Use config() method for configuration commands
    config_cmds = [
        line for line in rendered_cfg.splitlines() 
        if line.strip() and not line.strip().startswith("!")
    ]
    if config_cmds:
        node.config(config_cmds)
        node.enable("write memory")
    print(f"✅ Pushed config to {hostname} ({host})")


def main() -> None:
    """Fetch device inventory from Nautobot and configure Ethernet2 interfaces."""
    print("\n" + "=" * 80)
    print("🔧 FIX NETWORK CONNECTIVITY - Using Nautobot Inventory")
    print("=" * 80)
    print("\nWhat's different from script 4b:")
    print("  - Device list comes from NAUTOBOT (not hardcoded)")
    print("  - Configuration template is still static")
    print("  - Next step (script 6): Get interface states from Nautobot too")
    print("=" * 80)
    print()
    
    # Nautobot connection
    nb_url = os.environ.get("NB_URL", "http://localhost:8080")
    token = os.environ.get("NB_TOKEN", "1234567890abcde0987654321")
    
    # Fetch device inventory from Nautobot
    print(f"📡 Fetching device inventory from Nautobot at {nb_url}...")
    inventory = get_devices_from_nautobot(nb_url, token)
    
    print(f"✅ Found {len(inventory)} devices in Nautobot:")
    for dev in inventory:
        print(f"   • {dev['name']} ({dev['host']}) - Role: {dev['role']}")
    print()
    
    # Filter for access1 and rtr1 (the devices we need to fix)
    target_devices = [d for d in inventory if d['name'] in ['access1', 'rtr1']]
    
    if not target_devices:
        print("❌ Error: Could not find access1 or rtr1 in Nautobot")
        print("   Make sure devices exist and have primary IPs assigned")
        return
    
    print(f"🔧 Configuring {len(target_devices)} devices: {', '.join(d['name'] for d in target_devices)}")
    print("=" * 80)
    print()
    
    # Initialize Jinja2
    env = Environment(loader=BaseLoader(), trim_blocks=True, lstrip_blocks=True)
    tmpl = env.from_string(TEMPLATE)
    
    # Configure each device
    for device in target_devices:
        # Derive loopback IP from management IP's last octet
        last_octet = device['host'].split('.')[-1]
        loopback_ip = f"10.99.1.{last_octet}"
        
        # Render configuration
        rendered = tmpl.render(
            device_name=device['name'],
            loopback_ip=loopback_ip
        )
        
        print(f">>> Configuring {device['name']} >>>")
        print(rendered)
        print("=" * 80)
        
        # Push to device
        push_config(device['host'], device['name'], rendered)
        print()
    
    print("=" * 80)
    print("✅ All devices configured successfully!")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Test connectivity with Nautobot Job")
    print("  2. Try script 6 for full Nautobot-driven automation")
    print("     (fetches interface states from Nautobot too)")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()

