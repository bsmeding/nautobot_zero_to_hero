#!/usr/bin/env python3

"""
Template Nautobot Job equivalent of script #5.
Copy this into your Nautobot jobs tree (e.g. /opt/nautobot/jobs/) as a Job module
and adjust imports per your environment.
"""

from ipaddress import ip_network
from nautobot.apps.jobs import Job, StringVar


class ConfigureAccessLoopbacks(Job):
    class Meta:
        name = "Configure Access Loopbacks"
        description = "Create Loopback0/1 on all Access Switches with IPs from subnet"

    ACCESS_LOOPBACK_SUBNET = StringVar(
        description="IPv4 /24 to allocate loopback IPs from (e.g., 10.99.1.0/24)",
        default="10.99.1.0/24",
    )

    def run(self, ACCESS_LOOPBACK_SUBNET):
        from nautobot.dcim.models import Device
        import pyeapi

        net = ip_network(ACCESS_LOOPBACK_SUBNET)
        hosts = list(net.hosts())

        # Target devices: Role = Access Switch, active
        targets = Device.objects.filter(role__name="Access Switch", status__name="Active").order_by("name")
        for idx, dev in enumerate(targets):
            if not dev.primary_ip4 and not dev.primary_ip:
                self.log_warning(f"Skip {dev.name}: no primary IP")
                continue
            host = (dev.primary_ip4 or dev.primary_ip).address.ip.exploded
            lo0 = hosts[idx].exploded
            lo1 = hosts[idx + 1].exploded if idx + 1 < len(hosts) else hosts[idx].exploded

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
            self.log_success(f"Configured loopbacks on {dev.name} ({host})")


# When copied into Nautobot jobs, include register_jobs(ConfigureAccessLoopbacks)


