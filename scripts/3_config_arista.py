#!/usr/bin/env python3

"""
Static example: full basic config on access1 and access2 via Arista eAPI.
"""

import pyeapi

ARISTA_DEVICES = [
    {"host": "172.20.20.11", "hostname": "access1"},
    {"host": "172.20.20.12", "hostname": "access2"},
]


def configure_device(host: str, hostname: str) -> None:
    node = pyeapi.connect(
        transport="https",
        host=host,
        username="admin",
        password="admin",
        port=443,
    )
    cmds = [
        "configure terminal",
        f"hostname {hostname}",
        "interface Management0",
        "no shutdown",
        "exit",
        "interface Ethernet1",
        "no shutdown",
        "exit",
        "end",
        "write memory",
    ]
    node.execute(cmds)
    print(f"Configured {hostname} ({host})")


def main() -> None:
    for dev in ARISTA_DEVICES:
        configure_device(dev["host"], dev["hostname"])


if __name__ == "__main__":
    main()


