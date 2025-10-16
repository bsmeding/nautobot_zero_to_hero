#!/usr/bin/env python3

"""
DIAGNOSE CONNECTIVITY ISSUE: Check interface status on Arista switches.

This script connects to the switches and checks if Ethernet2 interfaces are enabled.
Run this BEFORE the fix script to identify the problem.
"""

import pyeapi
from tabulate import tabulate


# Device inventory
ARISTA_DEVICES = [
    {"name": "access1", "host": "172.20.20.11", "connected_to": "workstation1"},
    {"name": "rtr1", "host": "172.20.20.14", "connected_to": "mgmt server"},
]


def check_interface_status(host: str, hostname: str, interface: str) -> dict:
    """Check if an interface is enabled or disabled on a device.
    
    Args:
        host: Device IP address
        hostname: Device hostname
        interface: Interface name (e.g., "Ethernet2")
        
    Returns:
        Dictionary with status information
    """
    try:
        # Connect to device via eAPI
        connection = pyeapi.connect(
            transport="https",
            host=host,
            username="admin",
            password="admin",
            port=443,
        )
        node = pyeapi.client.Node(connection)
        
        # Get interface status
        result = node.enable(f"show interfaces {interface} status")
        
        # Parse the output
        output = result[0]["result"]
        
        # Check if interface is in output and get status
        if "interfaceStatuses" in output and interface in output["interfaceStatuses"]:
            status_info = output["interfaceStatuses"][interface]
            line_protocol = status_info.get("lineProtocolStatus", "unknown")
            link_status = status_info.get("linkStatus", "unknown")
            vlan = status_info.get("vlanInformation", {}).get("vlanId", "N/A")
            
            # Determine if shutdown
            is_shutdown = link_status == "disabled"
            
            return {
                "device": hostname,
                "interface": interface,
                "status": "SHUTDOWN" if is_shutdown else "ENABLED",
                "link": link_status,
                "vlan": vlan,
                "problem": "❌ YES" if is_shutdown else "✅ NO"
            }
        else:
            return {
                "device": hostname,
                "interface": interface,
                "status": "NOT FOUND",
                "link": "N/A",
                "vlan": "N/A",
                "problem": "⚠️  UNKNOWN"
            }
            
    except Exception as e:
        return {
            "device": hostname,
            "interface": interface,
            "status": "ERROR",
            "link": str(e)[:30],
            "vlan": "N/A",
            "problem": "⚠️  ERROR"
        }


def main() -> None:
    """Check Ethernet2 status on all devices."""
    print("\n" + "=" * 80)
    print("🔍 DIAGNOSTIC: Checking Interface Status")
    print("=" * 80)
    print("\nProblem: workstation1 (10.0.0.15) cannot ping mgmt (10.0.0.16)")
    print("Diagnosis: Checking if Ethernet2 interfaces are enabled...")
    print("=" * 80)
    print()
    
    # Collect status from all devices
    results = []
    
    for device in ARISTA_DEVICES:
        print(f"Checking {device['name']} (connected to {device['connected_to']})...")
        status = check_interface_status(device["host"], device["name"], "Ethernet2")
        results.append(status)
    
    # Display results in a table
    print("\n" + "=" * 80)
    print("DIAGNOSTIC RESULTS")
    print("=" * 80)
    print()
    
    headers = ["Device", "Interface", "Status", "Link State", "VLAN", "Is Problem?"]
    table_data = [
        [r["device"], r["interface"], r["status"], r["link"], r["vlan"], r["problem"]]
        for r in results
    ]
    
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    problems = [r for r in results if r["status"] == "SHUTDOWN"]
    
    if problems:
        print(f"\n❌ Found {len(problems)} PROBLEM(S):")
        for p in problems:
            print(f"   • {p['device']} Ethernet2 is SHUTDOWN")
        
        print("\n💡 ROOT CAUSE:")
        print("   Ethernet2 interfaces are administratively shutdown,")
        print("   preventing Layer 2 connectivity between workstation1 and mgmt server.")
        
        print("\n🔧 SOLUTION:")
        print("   Run the fix script to enable these interfaces:")
        print("   $ python3 4_config_arista_template.py")
    else:
        print("\n✅ No problems found - all Ethernet2 interfaces are enabled")
        print("   If connectivity still fails, check:")
        print("   • VLAN configuration")
        print("   • Routing between networks")
        print("   • Firewall rules")
    
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()

