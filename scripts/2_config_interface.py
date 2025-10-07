#!/usr/bin/env python3

"""
Static example: configure Management0 on access1 via Arista eAPI.
Sets IP 172.20.20.11/24 and enables interface; commits to startup-config.
"""

import pyeapi


def main() -> None:
    node = pyeapi.connect(
        transport="https",
        host="172.20.20.11",
        username="admin",
        password="admin",
        port=443,
    )
    # Use config() method for configuration commands (pyeapi handles config mode automatically)
    config_cmds = [
        "interface Management0",
        "ip address 172.20.20.11/24",
        "no shutdown",
    ]
    node.config(config_cmds)
    
    # Save configuration
    node.enable("write memory")
    print("Configured Management0 on access1")


if __name__ == "__main__":
    main()


