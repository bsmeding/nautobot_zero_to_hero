"""
Device Status Monitor Job

This job monitors the status of containerlab devices using NAPALM.
It checks device connectivity, interface status, and system health.
"""

from nautobot.apps.jobs import Job, StringVar, BooleanVar, register_jobs
from nautobot.dcim.models import Device
from nautobot.extras.models import Status
import napalm
import time

name = "LAB Setup"

class DeviceStatusMonitor(Job):
    """Monitor device status using NAPALM."""
    
    class Meta:
        name = "Device Status Monitor"
        description = "Monitor containerlab device status using NAPALM"
        has_sensitive_variables = False

    device_name = StringVar(
        description="Device name to monitor (leave empty for all devices)",
        default="",
        required=False
    )
    
    check_interfaces = BooleanVar(
        description="Check interface status",
        default=True
    )
    
    check_system = BooleanVar(
        description="Check system information",
        default=True
    )

    def run(self, device_name, check_interfaces, check_system):
        self.logger.info("Starting device status monitoring...")
        
        # Get devices to monitor
        if device_name:
            devices = Device.objects.filter(name=device_name)
        else:
            # Monitor all containerlab devices
            devices = Device.objects.filter(
                name__in=['access1', 'access2', 'dist1', 'rtr1']
            )
        
        if not devices.exists():
            self.logger.warning("No devices found to monitor")
            return
        
        # Device mapping for NAPALM drivers
        device_drivers = {
            'access1': 'eos',
            'access2': 'eos', 
            'dist1': 'nokia_srl',
            'rtr1': 'nokia_srl'
        }
        
        # IP mapping
        device_ips = {
            'access1': '172.20.20.11',
            'access2': '172.20.20.12',
            'dist1': '172.20.20.13',
            'rtr1': '172.20.20.14'
        }
        
        results = {}
        
        for device in devices:
            device_name = device.name
            self.logger.info(f"Monitoring device: {device_name}")
            
            if device_name not in device_drivers:
                self.logger.warning(f"Unknown device type for {device_name}")
                continue
                
            driver = device_drivers[device_name]
            ip = device_ips[device_name]
            
            try:
                # Connect using NAPALM
                driver_obj = napalm.get_network_driver(driver)
                
                with driver_obj(
                    hostname=ip,
                    username='admin',
                    password='admin',
                    timeout=10
                ) as conn:
                    self.logger.info(f"Connected to {device_name} ({ip})")
                    
                    # Get device facts
                    if check_system:
                        facts = conn.get_facts()
                        self.logger.info(f"System: {facts.get('hostname', 'Unknown')} - {facts.get('os_version', 'Unknown')}")
                        results[device_name] = {
                            'status': 'connected',
                            'facts': facts
                        }
                    
                    # Get interface information
                    if check_interfaces:
                        interfaces = conn.get_interfaces()
                        up_interfaces = [name for name, data in interfaces.items() if data.get('is_up', False)]
                        self.logger.info(f"Interfaces up: {len(up_interfaces)}/{len(interfaces)}")
                        results[device_name]['interfaces'] = {
                            'total': len(interfaces),
                            'up': len(up_interfaces),
                            'up_list': up_interfaces
                        }
                    
                    # Update device status in Nautobot
                    active_status = Status.objects.get(name='Active')
                    device.status = active_status
                    device.save()
                    
            except Exception as e:
                self.logger.error(f"Failed to connect to {device_name}: {str(e)}")
                results[device_name] = {'status': 'failed', 'error': str(e)}
                
                # Update device status to failed
                try:
                    failed_status = Status.objects.get(name='Failed')
                    device.status = failed_status
                    device.save()
                except Status.DoesNotExist:
                    self.logger.warning("Failed status not found in Nautobot")
        
        # Summary
        self.logger.info("Device monitoring complete!")
        self.logger.info(f"Results: {results}")
        
        return results


register_jobs(DeviceStatusMonitor)
