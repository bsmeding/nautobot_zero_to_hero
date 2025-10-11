#!/usr/bin/env python3

"""
Static example with Jinja2 template: render a config template for access1/access2 and push via eAPI.
Demonstrates using Jinja2 templates with static inventory (no Nautobot dependency).
"""

import pyeapi
from jinja2 import Environment, BaseLoader


# Static device inventory
ARISTA_DEVICES = [
    {
        "name": "access1",
        "host": "172.20.20.11",
        "loopback_ip": "10.99.1.1",
        "interfaces": [
            {"name": "Ethernet1", "description": "Uplink to core"},
            {"name": "Ethernet2", "description": "Access port VLAN 10"},
            {"name": "Ethernet3", "description": "Access port VLAN 20"},
        ],
    },
    {
        "name": "access2",
        "host": "172.20.20.12",
        "loopback_ip": "10.99.1.2",
        "interfaces": [
            {"name": "Ethernet1", "description": "Uplink to core"},
            {"name": "Ethernet2", "description": "Access port VLAN 10"},
            {"name": "Ethernet3", "description": "Access port VLAN 20"},
        ],
    },
]

# For simplicity, we are using a static template instead of loading jinja file
TEMPLATE = """
hostname {{ device.name }}
!
interface Loopback0
  description Management Loopback
  ip address {{ device.loopback_ip }}/32
  no shutdown
!
{% for iface in device.interfaces %}
interface {{ iface.name }}
  description {{ iface.description }}
  no shutdown
!
{% endfor %}
"""


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
    """Render Jinja2 template for each device and push configuration."""
    env = Environment(loader=BaseLoader(), trim_blocks=True, lstrip_blocks=True)
    tmpl = env.from_string(TEMPLATE)

    for device in ARISTA_DEVICES:
        rendered = tmpl.render(device=device)
        print(f"\n=== Rendered config for {device['name']} ===")
        print(rendered)
        print("=" * 50)
        push_config(device["host"], device["name"], rendered)


if __name__ == "__main__":
    main()
