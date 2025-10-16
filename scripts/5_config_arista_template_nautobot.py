#!/usr/bin/env python3

"""
NAUTOBOT AS SOURCE OF TRUTH: Fetch devices and interface state from Nautobot.

This demonstrates using Nautobot as the single source of truth for network configuration.
The script:
1. Fetches devices and their interfaces from Nautobot
2. Configures hostname based on Nautobot device name
3. Configures interface status (enabled/disabled) based on Nautobot interface state
4. Pushes configuration to actual network devices via eAPI
"""

import os
import requests
import pyeapi
from jinja2 import Environment, BaseLoader


# Template that uses Nautobot data for hostname and interface configuration
TEMPLATE = """
!
! === Configure hostname from Nautobot ===
!
hostname {{ device.name }}
!
! === Configure Loopback interface ===
!
interface Loopback0
  description Management Loopback
  ip address {{ loopback_ip }}/32
  no shutdown
!
! === Configure interfaces based on Nautobot state ===
!
{% for iface in interfaces %}
interface {{ iface.name }}
  description {{ iface.description or 'Configured by Nautobot automation' }}
{% if iface.enabled %}
  no shutdown
{% else %}
  shutdown
{% endif %}
!
{% endfor %}
!
end
"""


def get_access_devices(nb_url: str, token: str):
    """Fetch all Arista devices from Nautobot (access switches and routers)."""
    headers = {"Authorization": f"Token {token}"}
    # Fetch all devices with depth=1 to get related objects
    resp = requests.get(
        f"{nb_url}/api/dcim/devices/?depth=1",
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()
    all_devices = resp.json().get("results", [])
    
    # Debug: show all device info
    print(f"   Debug: Found {len(all_devices)} total devices:")
    for d in all_devices[:10]:
        role_data = d.get("role")
        role_type = type(role_data).__name__
        
        # Extract role name based on what type it is
        if isinstance(role_data, dict):
            role_name = role_data.get("display") or role_data.get("name") or str(role_data)
        elif isinstance(role_data, str):
            role_name = f"URL: {role_data}"
        else:
            role_name = f"Unknown type: {role_type}"
        
        print(f"     - {d.get('name')}: role type={role_type}, value='{role_name}'")
    
    # Filter for Arista devices (access1, access2, rtr1) by platform or just get all
    # For simplicity, return all devices with primary IPs (likely the network devices)
    target_devices = [
        d for d in all_devices 
        if d.get("primary_ip4") or d.get("primary_ip")
    ]
    
    print(f"\n   Selected {len(target_devices)} devices with primary IPs\n")
    
    return target_devices


def get_device_interfaces(nb_url: str, token: str, device_id: str):
    """Fetch interfaces for a specific device from Nautobot."""
    headers = {"Authorization": f"Token {token}"}
    resp = requests.get(
        f"{nb_url}/api/dcim/interfaces/?device_id={device_id}",
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


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
    
    # Use config() method for configuration commands (pyeapi handles config mode automatically)
    # Filter out empty lines and comment lines
    config_cmds = [
        line for line in rendered_cfg.splitlines() 
        if line.strip() and not line.strip().startswith("!")
    ]
    if config_cmds:
        node.config(config_cmds)
        # Save configuration
        node.enable("write memory")
    print(f"Pushed rendered config to {hostname} ({host})")


def main() -> None:
    """Fetch devices from Nautobot, render template, and push configuration."""
    nb_url = os.environ.get("NB_URL", "http://localhost:8080")
    token = os.environ.get("NB_TOKEN", "1234567890abcde0987654321")  # Fallback token for demo
    if not token:
        raise SystemExit("NB_TOKEN env var required")

    # Initialize Jinja2 environment
    env = Environment(loader=BaseLoader(), trim_blocks=True, lstrip_blocks=True)
    tmpl = env.from_string(TEMPLATE)

    # Fetch devices from Nautobot
    devices = get_access_devices(nb_url, token)
    print(f"Found {len(devices)} Access Switch devices in Nautobot\n")

    for idx, device in enumerate(devices, start=1):
        name = device["name"]
        
        # Get primary IP for management connection
        primary = device.get("primary_ip4") or device.get("primary_ip")
        if not primary:
            print(f"Skip {name}: no primary IP")
            continue
        host = primary.get("address", "").split("/")[0]
        if not host:
            print(f"Skip {name}: invalid primary IP")
            continue

        # Fetch interfaces from Nautobot
        interfaces = get_device_interfaces(nb_url, token, device["id"])
        
        # Show interface states from Nautobot (what will be configured)
        print(f"   Found {len(interfaces)} interfaces - states from Nautobot:")
        for iface in interfaces[:5]:  # Show first 5
            status = "ENABLED" if iface.get("enabled") else "DISABLED"
            print(f"     • {iface['name']}: {status}")
        if len(interfaces) > 5:
            print(f"     ... and {len(interfaces) - 5} more")
        
        # Derive loopback IP from management IP's last octet
        # Example: 172.20.20.11 → 10.99.1.11
        last_octet = host.split('.')[-1]
        loopback_ip = f"10.99.1.{last_octet}"
        print(f"   Loopback IP (based on mgmt IP): {loopback_ip}")
        
        # Render template with Nautobot data
        rendered = tmpl.render(
            device=device,
            interfaces=interfaces,
            loopback_ip=loopback_ip
        )
        
        print(f"\n>>> Rendered config for {name} >>>")
        print(rendered)
        print("=" * 80)
        
        # Push configuration to device
        push_config(host, name, rendered)
        print(f"✅ Configuration applied to {name}\n")


if __name__ == "__main__":
    main()

