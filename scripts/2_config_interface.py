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
    cmds = [
        "configure terminal",
        "interface Management0",
        "ip address 172.20.20.11/24",
        "no shutdown",
        "exit",
        "end",
        "write memory",
    ]
    node.execute(cmds)
    print("Configured Management0 on access1")


if __name__ == "__main__":
    main()


