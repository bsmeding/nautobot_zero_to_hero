#!/usr/bin/env python3

"""
Static example: configure hostname on access1 via Arista eAPI.
Requires pyeapi in the environment and HTTPS eAPI enabled on the device.
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
        "hostname access1",
        "end",
        "write memory",
    ]
    result = node.execute(cmds)
    print("Completed hostname configuration on access1")
    if "error" in str(result).lower():
        print(result)


if __name__ == "__main__":
    main()


