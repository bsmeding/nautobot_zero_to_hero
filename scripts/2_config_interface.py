#!/usr/bin/env python3

"""
Static example: configure Management0 on access1 via Arista eAPI.
Sets IP 172.20.20.11/24 and enables interface; commits to startup-config.
"""

import pyeapi


def configure_interface(node: pyeapi.client.Node, interface_name: str, ip_address: str, 
    enabled: bool = True, save_config: bool = True) -> None:
    """

    Input:      node: pyeapi.client.Node, interface_name: str, ip_address: str,
                enabled: bool = True, save_config: bool = True
    Output: None
    Description: Configure an interface on an Arista device.
    Example:
    >>> configure_interface(node, "Management0", "172.20.20.11/24", True, True)
    Configured Management0 with IP 172.20.20.11/24 on device
    """

    config_cmds = [
        f"interface {interface_name}",
        f"ip address {ip_address}",
    ]
    
    if enabled:
        config_cmds.append("no shutdown")
    else:
        config_cmds.append("shutdown")
    
    node.config(config_cmds)
    
    if save_config:
        node.enable("write memory")
    
    print(f"Configured {interface_name} with IP {ip_address} on device")


def main() -> None:
    # Create a connection and get the node
    connection = pyeapi.connect(
        transport="https",
        host="172.20.20.11",
        username="admin",
        password="admin",
        port=443,
    )
    node = pyeapi.client.Node(connection)
    
    # Use the reusable function to configure the interface
    configure_interface(
        node=node,
        interface_name="Loopback0",
        ip_address="172.10.10.11/24",
        enabled=True,
        save_config=True,
    )


if __name__ == "__main__":
    main()


