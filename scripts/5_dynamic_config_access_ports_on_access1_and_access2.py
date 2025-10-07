#!/usr/bin/env python3

"""
Dynamic example: select devices by Role 'Access Switch' from Nautobot and configure Loopback0/1
with IPs from ACCESS_LOOPBACK_SUBNET (default 10.99.1.0/24). access1 gets .1, access2 gets .2.
"""

import ipaddress
import os
import requests
import pyeapi

ACCESS_LOOPBACK_SUBNET = os.environ.get("ACCESS_LOOPBACK_SUBNET", "10.99.1.0/24")


def get_access_devices(nb_url: str, token: str):
    headers = {"Authorization": f"Token {token}"}
    resp = requests.get(
        f"{nb_url}/api/dcim/devices/?role=Access%20Switch&status=active&ordering=name",
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


def device_ip(dev):
    primary = dev.get("primary_ip4") or dev.get("primary_ip")
    return (primary or {}).get("address", "").split("/")[0]


def assign_loopback_ips(subnet: str, device_names: list[str]) -> dict[str, str]:
    net = ipaddress.ip_network(subnet)
    # Simple mapping: first host (.1) for first device, second host (.2) for second device
    hosts = list(net.hosts())
    mapping: dict[str, str] = {}
    for idx, name in enumerate(device_names):
        mapping[name] = str(hosts[idx])
    return mapping


def push_loopbacks(host: str, lo0: str, lo1: str) -> None:
    node = pyeapi.connect(
        transport="https",
        host=host,
        username="admin",
        password="admin",
        port=443,
    )
    cmds = [
        "configure terminal",
        "interface Loopback0",
        f" ip address {lo0}/32",
        " no shutdown",
        "exit",
        "interface Loopback1",
        f" ip address {lo1}/32",
        " no shutdown",
        "exit",
        "end",
        "write memory",
    ]
    node.execute(cmds)
    print(f"Configured Loopbacks on {host}")


def main() -> None:
    nb_url = os.environ.get("NB_URL", "http://localhost:8081")
    token = os.environ.get("NB_TOKEN")
    if not token:
        raise SystemExit("NB_TOKEN env var required")

    devices = get_access_devices(nb_url, token)
    names = [d["name"] for d in devices]
    mapping = assign_loopback_ips(ACCESS_LOOPBACK_SUBNET, names)
    for dev in devices:
        name = dev["name"]
        host = device_ip(dev)
        if not host:
            print(f"Skip {name}: no primary IP")
            continue
        base = mapping[name]
        # Example: derive second IP by incrementing last octet (safe within /24)
        last = int(base.split(".")[-1])
        lo0 = base
        lo1 = ".".join(base.split(".")[:-1] + [str(last + 1)])
        push_loopbacks(host, lo0, lo1)


if __name__ == "__main__":
    main()


