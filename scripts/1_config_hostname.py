#!/usr/bin/env python3

"""
Static example: configure hostname on access1 via Arista eAPI.
Requires pyeapi in the environment and HTTPS eAPI enabled on the device.
"""

import pyeapi


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
    
    # Use config() method for configuration commands (pyeapi handles config mode automatically)
    config_cmds = [
        "hostname access1",
    ]
    node.config(config_cmds)
    
    # Save configuration
    node.enable("write memory")
    print("Completed hostname configuration on access1")


if __name__ == "__main__":
    main()


