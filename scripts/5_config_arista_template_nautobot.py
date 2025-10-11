#!/usr/bin/env python3

"""
Transition example: fetch devices from Nautobot and render Jinja2 template.
This demonstrates moving from static inventory (script 4) to Nautobot-driven automation.
Fetches Access Switch devices from Nautobot and configures hostname, Loopback0, and interfaces.
"""

import os
import requests
import pyeapi
from jinja2 import Environment, BaseLoader


# For simplicity, we are using a static template instead of loading jinja file
TEMPLATE = """
hostname {{ device.name }}
!
interface Loopback0
  description Management Loopback
  ip address {{ loopback_ip }}/32
  no shutdown
!
{% for iface in interfaces %}
interface {{ iface.name }}
  description {{ iface.description or 'configured by automation' }}
  no shutdown
!
{% endfor %}
"""


def get_access_devices(nb_url: str, token: str):
    """Fetch devices with role 'Access Switch' from Nautobot."""
    headers = {"Authorization": f"Token {token}"}
    resp = requests.get(
        f"{nb_url}/api/dcim/devices/?role=Access%20Switch&status=active&ordering=name",
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


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
    nb_url = os.environ.get("NB_URL", "http://localhost:8081")
    token = os.environ.get("NB_TOKEN")
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
        
        # Simple loopback IP assignment based on device order (10.99.1.1, 10.99.1.2, etc.)
        loopback_ip = f"10.99.1.{idx}"
        
        # Render template with Nautobot data
        rendered = tmpl.render(
            device=device,
            interfaces=interfaces,
            loopback_ip=loopback_ip
        )
        
        print(f"=== Rendered config for {name} ===")
        print(rendered)
        print("=" * 50)
        
        # Push configuration to device
        push_config(host, name, rendered)
        print()


if __name__ == "__main__":
    main()

