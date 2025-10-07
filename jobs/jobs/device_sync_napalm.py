#!/usr/bin/env python3
"""Custom Device Sync Job using NAPALM instead of netmiko."""

from nautobot.apps.jobs import Job, ObjectVar, register_jobs
from nautobot.dcim.models import Device, Interface
from nautobot.ipam.models import IPAddress
from napalm import get_network_driver
from napalm.base.exceptions import ConnectionException


class DeviceSyncNAPALM(Job):
    """
    Custom Device Sync Job using NAPALM.
    
    This job connects to a device using NAPALM and syncs:
    - Device facts (hostname, model, serial, OS version)
    - Interfaces (name, type, description, MAC address, MTU, enabled status)
    - IP addresses on interfaces
    """

    class Meta:
        name = "Device Sync (NAPALM)"
        description = "Sync device data using NAPALM instead of netmiko"
        has_sensitive_variables = False

    device = ObjectVar(
        description="Device to sync",
        model=Device,
        required=True,
    )

    def run(self, device):
        """Main execution method."""
        self.logger.info(f"Starting sync for device: {device.name}")

        # Get device credentials from secrets or use defaults
        username = "admin"
        password = "admin"
        
        # Try to get credentials from secrets group
        if device.secrets_group:
            try:
                secrets = device.secrets_group.get_secret_value(
                    access_type="generic",
                    secret_type="username",
                )
                if secrets:
                    username = secrets
                secrets = device.secrets_group.get_secret_value(
                    access_type="generic",
                    secret_type="password",
                )
                if secrets:
                    password = secrets
            except Exception as e:
                self.logger.warning(f"Could not retrieve secrets: {e}. Using defaults.")
        
        # Get NAPALM driver
        if not device.platform or not device.platform.napalm_driver:
            self.logger.error(f"Device {device.name} has no platform or NAPALM driver configured")
            return

        driver_name = device.platform.napalm_driver
        self.logger.info(f"Using NAPALM driver: {driver_name}")

        # Get device IP
        if not device.primary_ip4:
            self.logger.error(f"Device {device.name} has no primary IPv4 address")
            return

        device_ip = str(device.primary_ip4.address.ip)
        self.logger.info(f"Connecting to {device_ip}...")

        # Parse NAPALM optional args
        optional_args = device.platform.napalm_args or {}
        if isinstance(optional_args, str):
            import json
            optional_args = json.loads(optional_args)

        try:
            # Connect to device
            driver = get_network_driver(driver_name)
            napalm_device = driver(
                hostname=device_ip,
                username=username,
                password=password,
                optional_args=optional_args
            )
            
            napalm_device.open()
            self.logger.success(f"Connected to {device.name}")

            # Get device facts
            self.logger.info("Fetching device facts...")
            facts = napalm_device.get_facts()
            self.logger.info(f"Device facts: {facts}")

            # Update device fields
            if facts.get("hostname"):
                device.name = facts["hostname"]
            if facts.get("serial_number"):
                device.serial = facts["serial_number"]
            if facts.get("model"):
                # You might want to map this to a DeviceType
                self.logger.info(f"Model: {facts['model']}")
            if facts.get("os_version"):
                # You might want to map this to a SoftwareVersion
                self.logger.info(f"OS Version: {facts['os_version']}")
            
            device.save()
            self.logger.success(f"Updated device {device.name}")

            # Get interfaces
            self.logger.info("Fetching interfaces...")
            interfaces = napalm_device.get_interfaces()
            self.logger.info(f"Found {len(interfaces)} interfaces")

            for intf_name, intf_data in interfaces.items():
                self.logger.debug(f"Processing interface: {intf_name}")
                
                # Get or create interface
                interface, created = Interface.objects.get_or_create(
                    device=device,
                    name=intf_name,
                    defaults={
                        "type": "other",
                        "status": device.status,
                    }
                )

                # Update interface fields
                interface.description = intf_data.get("description", "")
                interface.mac_address = intf_data.get("mac_address", "")
                interface.mtu = intf_data.get("mtu", 1500)
                interface.enabled = intf_data.get("is_enabled", False)
                
                # Determine interface type
                if "Management" in intf_name:
                    interface.type = "1000base-t"
                elif "Ethernet" in intf_name:
                    interface.type = "1000base-t"
                elif "Loopback" in intf_name:
                    interface.type = "virtual"
                
                interface.save()
                
                if created:
                    self.logger.info(f"Created interface: {intf_name}")
                else:
                    self.logger.debug(f"Updated interface: {intf_name}")

            # Get interface IPs
            self.logger.info("Fetching interface IP addresses...")
            try:
                interface_ips = napalm_device.get_interfaces_ip()
                
                for intf_name, ip_data in interface_ips.items():
                    # Get interface
                    try:
                        interface = Interface.objects.get(device=device, name=intf_name)
                    except Interface.DoesNotExist:
                        self.logger.warning(f"Interface {intf_name} not found for IP assignment")
                        continue

                    # Process IPv4 addresses
                    for ip_addr, ip_info in ip_data.get("ipv4", {}).items():
                        prefix_length = ip_info.get("prefix_length", 24)
                        ip_with_prefix = f"{ip_addr}/{prefix_length}"
                        
                        # Get or create IP address
                        ip_address, created = IPAddress.objects.get_or_create(
                            address=ip_with_prefix,
                            defaults={
                                "status": device.status,
                            }
                        )
                        
                        # Assign to interface
                        ip_address.assigned_object = interface
                        ip_address.save()
                        
                        if created:
                            self.logger.info(f"Created IP {ip_with_prefix} on {intf_name}")
                        else:
                            self.logger.debug(f"Updated IP {ip_with_prefix} on {intf_name}")

            except Exception as e:
                self.logger.warning(f"Could not fetch interface IPs: {e}")

            # Close connection
            napalm_device.close()
            self.logger.success(f"Device sync completed for {device.name}")

        except ConnectionException as e:
            self.logger.error(f"Connection error: {e}")
        except Exception as e:
            self.logger.error(f"Error syncing device: {e}")
            import traceback
            self.logger.error(traceback.format_exc())


register_jobs(DeviceSyncNAPALM)

