#!/usr/bin/env python3

"""
Dynamic example: render a Jinja2 template using Nautobot inventory and push to access1/access2.
Reads Nautobot API (token env NB_TOKEN, base URL NB_URL), collects devices with role 'Access Switch',
then renders template and pushes via eAPI.
"""

import os
import requests
import pyeapi
from jinja2 import Environment, BaseLoader


# For simplicity, we are using a static template instead of loading jinja file
TEMPLATE = """
hostname {{ device.name }}
!
interface Management0
  no shutdown
!
{% for iface in interfaces %}
interface {{ iface.name }}
  description {{ iface.description or 'configured by automation' }}
  no shutdown
!
{% endfor %}
end
write memory
"""


def get_access_devices(nb_url: str, token: str):
    headers = {"Authorization": f"Token {token}"}
    resp = requests.get(
        f"{nb_url}/api/dcim/devices/?role=Access%20Switch&status=active", headers=headers, timeout=10
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


def get_device_interfaces(nb_url: str, token: str, device_id: str):
    headers = {"Authorization": f"Token {token}"}
    resp = requests.get(
        f"{nb_url}/api/dcim/interfaces/?device_id={device_id}", headers=headers, timeout=10
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


def push_config(host: str, rendered_cfg: str) -> None:
    node = pyeapi.connect(
        transport="https",
        host=host,
        username="admin",
        password="admin",
        port=443,
    )
    # Split into commands; template already includes end/write mem, but eAPI needs cmd list
    cmds = ["configure terminal"] + [line for line in rendered_cfg.splitlines() if line.strip()] 
    node.execute(cmds)
    print(f"Pushed rendered config to {host}")


def main() -> None:
    nb_url = os.environ.get("NB_URL", "http://localhost:8081")
    token = os.environ.get("NB_TOKEN")
    if not token:
        raise SystemExit("NB_TOKEN env var required")

    devices = get_access_devices(nb_url, token)
    env = Environment(loader=BaseLoader(), trim_blocks=True, lstrip_blocks=True)
    tmpl = env.from_string(TEMPLATE)

    for dev in devices:
        name = dev["name"]
        primary = dev.get("primary_ip4") or dev.get("primary_ip")
        if not primary:
            print(f"Skip {name}: no primary IP")
            continue
        host = primary.get("address", "").split("/")[0]
        if not host:
            print(f"Skip {name}: invalid primary IP")
            continue
        ifaces = get_device_interfaces(nb_url, token, dev["id"]) or []
        rendered = tmpl.render(device=dev, interfaces=ifaces)
        push_config(host, rendered)


if __name__ == "__main__":
    main()


