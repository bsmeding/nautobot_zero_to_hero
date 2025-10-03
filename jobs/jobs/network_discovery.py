"""
Network Discovery Job

This job discovers network topology and device information from the containerlab lab.
It uses NAPALM to gather detailed information about each device.
"""

from nautobot.apps.jobs import Job, StringVar, BooleanVar, register_jobs
from nautobot.dcim.models import Device, Interface
from nautobot.ipam.models import IPAddress
import napalm

name = "LAB Setup"

class NetworkDiscovery(Job):
    """Discover network topology and device information."""
    
    class Meta:
        name = "Network Discovery"
        description = "Discover containerlab network topology using NAPALM"
        has_sensitive_variables = False

    device_name = StringVar(
        description="Device name to discover (leave empty for all devices)",
        default="",
        required=False
    )
    
    discover_interfaces = BooleanVar(
        description="Discover interface information",
        default=True
    )
    
    discover_neighbors = BooleanVar(
        description="Discover LLDP neighbors",
        default=True
    )

    def run(self, device_name, discover_interfaces, discover_neighbors):
        self.logger.info("Starting network discovery...")
        
        # Get devices to discover
        if device_name:
            devices = Device.objects.filter(name=device_name)
        else:
            devices = Device.objects.filter(
                name__in=['access1', 'access2', 'dist1', 'rtr1']
            )
        
        if not devices.exists():
            self.logger.warning("No devices found to discover")
            return
        
        # Device mapping
        device_drivers = {
            'access1': 'eos',
            'access2': 'eos', 
            'dist1': 'nokia_srl',
            'rtr1': 'nokia_srl'
        }
        
        device_ips = {
            'access1': '172.20.20.11',
            'access2': '172.20.20.12',
            'dist1': '172.20.20.13',
            'rtr1': '172.20.20.14'
        }
        
        discovery_results = {}
        
        for device in devices:
            device_name = device.name
            self.logger.info(f"Discovering device: {device_name}")
            
            if device_name not in device_drivers:
                self.logger.warning(f"Unknown device type for {device_name}")
                continue
                
            driver = device_drivers[device_name]
            ip = device_ips[device_name]
            
            try:
                driver_obj = napalm.get_network_driver(driver)
                
                with driver_obj(
                    hostname=ip,
                    username='admin',
                    password='admin',
                    timeout=10
                ) as conn:
                    self.logger.info(f"Connected to {device_name} ({ip})")
                    
                    # Get device facts
                    facts = conn.get_facts()
                    self.logger.info(f"Device: {facts.get('hostname')} - {facts.get('model')} - {facts.get('os_version')}")
                    
                    discovery_results[device_name] = {
                        'facts': facts,
                        'interfaces': {},
                        'neighbors': {}
                    }
                    
                    # Discover interfaces
                    if discover_interfaces:
                        interfaces = conn.get_interfaces()
                        self.logger.info(f"Found {len(interfaces)} interfaces")
                        
                        for iface_name, iface_data in interfaces.items():
                            self.logger.info(f"Interface {iface_name}: {iface_data.get('is_up', False)} - {iface_data.get('speed', 'Unknown')}")
                            
                            # Update interface in Nautobot
                            try:
                                nautobot_interface = Interface.objects.get(
                                    device=device,
                                    name=iface_name
                                )
                                
                                # Update interface status
                                if iface_data.get('is_up', False):
                                    nautobot_interface.enabled = True
                                else:
                                    nautobot_interface.enabled = False
                                    
                                nautobot_interface.save()
                                
                            except Interface.DoesNotExist:
                                self.logger.warning(f"Interface {iface_name} not found in Nautobot for {device_name}")
                        
                        discovery_results[device_name]['interfaces'] = interfaces
                    
                    # Discover LLDP neighbors
                    if discover_neighbors:
                        try:
                            neighbors = conn.get_lldp_neighbors()
                            self.logger.info(f"Found {len(neighbors)} LLDP neighbors")
                            
                            for local_port, neighbor_list in neighbors.items():
                                for neighbor in neighbor_list:
                                    self.logger.info(f"Port {local_port} -> {neighbor.get('hostname', 'Unknown')} ({neighbor.get('port', 'Unknown')})")
                            
                            discovery_results[device_name]['neighbors'] = neighbors
                            
                        except Exception as e:
                            self.logger.warning(f"LLDP discovery failed for {device_name}: {str(e)}")
                    
            except Exception as e:
                self.logger.error(f"Discovery failed for {device_name}: {str(e)}")
                discovery_results[device_name] = {'error': str(e)}
        
        # Summary
        self.logger.info("Network discovery complete!")
        self.logger.info(f"Discovered {len(discovery_results)} devices")
        
        return discovery_results


register_jobs(NetworkDiscovery)
