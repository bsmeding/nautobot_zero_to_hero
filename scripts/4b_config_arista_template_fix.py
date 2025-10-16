#!/usr/bin/env python3

"""
FIX NETWORK CONNECTIVITY: Enable shutdown interfaces on Arista switches.

This script demonstrates how to use Jinja2 templates to fix network connectivity issues.
The problem: Ethernet2 ports are administratively shutdown
The solution: Enable (no shutdown) Ethernet2 interfaces to restore connectivity
"""

import pyeapi
from jinja2 import Environment, BaseLoader


# Static device inventory - focusing on Ethernet2 interfaces
ARISTA_DEVICES = [
    {
        "name": "access1",
        "host": "172.20.20.11",
        "loopback_ip": "10.99.1.1",
        "interfaces": [
            {"name": "Ethernet2", "description": "Connected to workstation1", "mode": "access", "vlan": "10"},
        ],
    },
    {
        "name": "rtr1",
        "host": "172.20.20.14",
        "loopback_ip": "10.0.0.254",  # In same subnet as workstation1/mgmt for easy testing
        "interfaces": [
            {"name": "Ethernet2", "description": "Connected to mgmt server", "mode": "access", "vlan": "10"},
        ],
    },
]

# Template to enable Ethernet2 interfaces and add loopback
TEMPLATE = """
!
! === FIX: Enable Ethernet2 interfaces ===
!
{% for iface in device.interfaces %}
interface {{ iface.name }}
  description {{ iface.description }}
  switchport mode access
  switchport access vlan {{ iface.vlan }}
  no shutdown
!
{% endfor %}
!
! === Add Loopback interface (for {{ device.name }}) ===
!
interface Loopback0
  description {{ device.name }} Loopback - Reachable from data plane
  ip address {{ device.loopback_ip }}/32
  no shutdown
!
end
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
    print("\n" + "=" * 70)
    print("🔧 FIXING NETWORK CONNECTIVITY ISSUE")
    print("=" * 70)
    print("\nPROBLEM: Ethernet2 ports are administratively shutdown")
    print("         (Run '4a_diagnose_connectivity_issue.py' to verify)")
    print("\nSOLUTION: Enable interfaces with 'no shutdown' command")
    print("\nDevices to fix: access1, rtr1")
    print("=" * 70)
    
    env = Environment(loader=BaseLoader(), trim_blocks=True, lstrip_blocks=True)
    tmpl = env.from_string(TEMPLATE)

    for device in ARISTA_DEVICES:
        rendered = tmpl.render(device=device)
        print(f"\n>>> Rendered config for {device['name']} >>>")
        print(rendered)
        print("=" * 70)
        push_config(device["host"], device["name"], rendered)
    
    print("\n" + "=" * 70)
    print("✅ Configuration applied successfully!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Run diagnostic script again to verify fix:")
    print("     $ python3 4a_diagnose_connectivity_issue.py")
    print()
    print("  2. Test connectivity using Nautobot Job:")
    print("     - Navigate to Jobs > 'Containerlab Connectivity Test'")
    print("     - Select: workstation1 → management")
    print("     - Should now PASS ✅")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
