"""
Pre-flight Lab Setup Job

This job populates Nautobot with the lab topology data from the Containerlab setup.
Based on the lab topology from: https://netdevops.it/blog/building-a-reusable-network-automation-lab-with-containerlab/

This demonstrates how to programmatically create Nautobot objects using Jobs.
"""

from nautobot.apps.jobs import Job, StringVar, BooleanVar, register_jobs


name = "LAB Setup"

class PreflightLabSetup(Job):
    """Pre-flight lab setup job to populate Nautobot with Containerlab lab topology."""
    
    class Meta:
        name = "Pre-flight Lab Setup"
        description = "Populate Nautobot with Containerlab lab topology data (uses fixed 172.20.20.0/24 subnet)"
        has_sensitive_variables = False

    # All parameters are now hardcoded with defaults - no user input required

    def run(self):
        self.logger.info("Starting pre-flight lab setup...")
        
        # Hardcoded values - no user input required
        site_name = "netdevops.it_lab"
        create_vlans = True
        create_tags = True
        management_subnet = "172.20.20.0/24"

        try:
            # Import models within the job to avoid import issues
            from nautobot.dcim.models import Location, LocationType, Device, Platform, Interface
            from nautobot.ipam.models import IPAddress, Prefix, VLAN
            from nautobot.extras.models import Tag, Role, Status
            import ipaddress

            # Get the active status
            try:
                active_status = Status.objects.get(name='Active')
            except Status.DoesNotExist:
                # If 'Active' doesn't exist, try to get the first available status
                active_status = Status.objects.first()
                if not active_status:
                    self.logger.error("No status objects found. Please create at least one status.")
                    return
                self.logger.info(f"Using status: {active_status.name}")

            # Create location type hierarchy with proper nesting
            location_types = {}
            hierarchy_config = [
                {'name': 'Region', 'description': 'Geographic regions', 'parent': None, 'nestable': True},
                {'name': 'Site', 'description': 'Physical sites and data centers', 'parent': 'Region', 'nestable': True},
                {'name': 'Building', 'description': 'Buildings within sites', 'parent': 'Site', 'nestable': True},
                {'name': 'Floor', 'description': 'Floors within buildings', 'parent': 'Building', 'nestable': True},
                {'name': 'Room', 'description': 'Rooms within floors', 'parent': 'Floor', 'nestable': True}
            ]
            
            # Create location types in hierarchy order with proper parent relationships
            for config in hierarchy_config:
                parent_type = None
                if config['parent']:
                    parent_type = location_types.get(config['parent'])
                
                location_type, created = LocationType.objects.get_or_create(
                    name=config['name'],
                    defaults={
                        'description': config['description'],
                        'parent': parent_type,
                        'nestable': config['nestable']
                    }
                )
                location_types[config['name']] = location_type
                if created:
                    self.logger.info(f"Created location type: {config['name']} (parent: {config['parent']})")
                else:
                    # Update existing location type with proper parent if needed
                    if parent_type and location_type.parent != parent_type:
                        location_type.parent = parent_type
                        location_type.nestable = config['nestable']
                        location_type.save()
                        self.logger.info(f"Updated location type: {config['name']} with parent: {config['parent']}")

            # Create region first
            region_name = "NetDevOps"
            self.logger.info(f"Creating region: {region_name}")
            
            region, created = Location.objects.get_or_create(
                name=region_name,
                location_type=location_types['Region'],
                defaults={'status': active_status}
            )
            if created:
                self.logger.info(f"Created region: {region_name}")
            else:
                self.logger.info(f"Using existing region: {region_name}")

            # Create site under the region
            fixed_site_name = "netdevops.it_lab"
            self.logger.info(f"Creating site: {fixed_site_name} under region: {region_name}")

            # Create or get the site location under the region
            site, created = Location.objects.get_or_create(
                name=fixed_site_name,
                location_type=location_types['Site'],
                parent=region,
                defaults={'status': active_status}
            )
            if created:
                self.logger.info(f"Created site: {fixed_site_name} under region: {region_name}")
            else:
                self.logger.info(f"Using existing site: {fixed_site_name}")

            # Create tags if requested
            if create_tags:
                self._create_tags()

            # Create management network
            mgmt_prefix = self._create_management_network(site, management_subnet, active_status)
            
            # Create additional prefixes for the lab
            self._create_lab_prefixes(site, active_status)

            # Create VLANs if requested
            if create_vlans:
                self._create_vlans(site, active_status)

            # Create racks
            racks = self._create_racks(site, active_status)

            # Create devices
            self._create_devices(site, mgmt_prefix, active_status, racks)

            # Create interfaces and IP addresses
            self._create_interfaces_and_ips(site, mgmt_prefix, active_status)

            self.logger.info("Pre-flight lab setup completed successfully!")

        except Exception as e:
            self.logger.error(f"Error during lab setup: {str(e)}")
            raise

    def _create_tags(self):
        """Create tags for the lab."""
        from nautobot.extras.models import Tag

        tags_data = [
            {'name': 'lab', 'color': 'blue'},
            {'name': 'containerlab', 'color': 'green'},
            {'name': 'automation', 'color': 'orange'},
            {'name': 'demo', 'color': 'purple'}
        ]
        
        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(
                name=tag_data['name'],
                defaults={
                    'color': tag_data['color']
                }
            )
            if created:
                self.logger.info(f"Created tag: {tag.name}")

    def _create_management_network(self, site, management_subnet, status):
        """Create management network prefix."""
        from nautobot.ipam.models import Prefix
        
        try:
            prefix = Prefix.objects.get(prefix=management_subnet)
            self.logger.info(f"Using existing prefix: {management_subnet}")
        except Prefix.DoesNotExist:
            prefix = Prefix.objects.create(
                prefix=management_subnet,
                status=status,
                description="Management network for lab devices"
            )
            self.logger.info(f"Created prefix: {management_subnet}")
        
        return prefix

    def _create_lab_prefixes(self, site, status):
        """Create additional prefixes for the lab."""
        from nautobot.ipam.models import Prefix
        
        # Additional prefixes for the lab
        lab_prefixes = [
            {'prefix': '10.0.0.0/8', 'description': 'Lab data network'},
            {'prefix': '192.168.0.0/16', 'description': 'Lab management network'},
            {'prefix': '172.16.0.0/12', 'description': 'Lab infrastructure network'}
        ]
        
        for prefix_data in lab_prefixes:
            try:
                prefix = Prefix.objects.get(prefix=prefix_data['prefix'])
                self.logger.info(f"Using existing prefix: {prefix_data['prefix']}")
            except Prefix.DoesNotExist:
                prefix = Prefix.objects.create(
                    prefix=prefix_data['prefix'],
                    status=status,
                    description=prefix_data['description']
                )
                self.logger.info(f"Created prefix: {prefix_data['prefix']}")

    def _create_vlans(self, site, status):
        """Create VLANs for the lab."""
        from nautobot.ipam.models import VLAN
        
        vlans_data = [
            {'vid': 10, 'name': 'Management', 'description': 'Management VLAN'},
            {'vid': 20, 'name': 'Data', 'description': 'Data VLAN'},
            {'vid': 30, 'name': 'Voice', 'description': 'Voice VLAN'},
            {'vid': 100, 'name': 'Lab-Network', 'description': 'Lab network VLAN'},
            {'vid': 200, 'name': 'Automation', 'description': 'Network automation VLAN'},
            {'vid': 300, 'name': 'Testing', 'description': 'Testing and validation VLAN'}
        ]
        
        for vlan_data in vlans_data:
            try:
                # Try to find existing VLAN by name to avoid conflicts
                vlan = VLAN.objects.get(name=vlan_data['name'])
                self.logger.info(f"Using existing VLAN: {vlan_data['name']} (VID: {vlan_data['vid']})")
            except VLAN.DoesNotExist:
                vlan = VLAN.objects.create(
                    vid=vlan_data['vid'],
                    name=vlan_data['name'],
                    status=status,
                    description=vlan_data['description']
                )
                self.logger.info(f"Created VLAN: {vlan.name} (VID: {vlan.vid})")

    def _create_racks(self, site, status):
        """Create racks for the lab."""
        from nautobot.dcim.models import Rack
        
        # Create racks without rack groups (matching Design Builder)
        racks_data = [
            {'name': 'Rack-01', 'u_height': 42},
            {'name': 'Rack-02', 'u_height': 42}
        ]
        
        racks = {}
        for rack_data in racks_data:
            rack, created = Rack.objects.get_or_create(
                name=rack_data['name'],
                location=site,
                defaults={
                    'status': status,
                    'u_height': rack_data['u_height']
                }
            )
            racks[rack_data['name']] = rack
            if created:
                self.logger.info(f"Created rack: {rack_data['name']}")
            else:
                self.logger.info(f"Using existing rack: {rack_data['name']}")
        
        return racks

    def _create_devices(self, site, mgmt_prefix, status, racks):
        """Create devices for the lab."""
        from nautobot.dcim.models import Device, Platform, DeviceType, Manufacturer
        from nautobot.extras.models import Role
        
        # Get or create platforms matching the blog post topology
        platforms = {}
        platform_configs = {
            'Arista EOS': {'napalm_driver': 'eos', 'network_driver': 'arista_eos'},
            'Nokia SR Linux': {'napalm_driver': 'srl', 'network_driver': 'nokia_srl'},
            'Alpine Linux': {'napalm_driver': 'linux', 'network_driver': 'linux'}
        }
        
        for platform_name, config in platform_configs.items():
            platform, created = Platform.objects.get_or_create(
                name=platform_name,
                defaults={
                    'description': f'{platform_name} platform',
                    'napalm_driver': config.get('napalm_driver'),
                    'network_driver': config.get('network_driver')
                }
            )
            # Update NAPALM driver if it's not set or different
            if platform.napalm_driver != config.get('napalm_driver'):
                platform.napalm_driver = config.get('napalm_driver')
                platform.network_driver = config.get('network_driver')
                platform.save()
                self.logger.info(f"Updated NAPALM driver for {platform_name}: {config.get('napalm_driver')}")
            
            platforms[platform_name] = platform
            if created:
                self.logger.info(f"Created platform: {platform_name} with NAPALM driver: {config.get('napalm_driver')}")
            else:
                self.logger.info(f"Using existing platform: {platform_name} with NAPALM driver: {platform.napalm_driver}")

        # Get or create manufacturers and device types
        manufacturers = {}
        device_types = {}
        
        # Create manufacturers
        manufacturer_configs = {
            'Arista': 'Arista Networks',
            'Nokia': 'Nokia Networks',
            'Generic': 'Generic'
        }
        
        for manufacturer_name, description in manufacturer_configs.items():
            manufacturer, created = Manufacturer.objects.get_or_create(
                name=manufacturer_name,
                defaults={'description': description}
            )
            manufacturers[manufacturer_name] = manufacturer
            if created:
                self.logger.info(f"Created manufacturer: {manufacturer_name}")
        
        # Create device types
        device_type_configs = {
            'Arista EOS': {'manufacturer': 'Arista', 'model': 'cEOS'},
            'Nokia SR Linux': {'manufacturer': 'Nokia', 'model': 'SR Linux'},
            'Alpine Linux': {'manufacturer': 'Generic', 'model': 'Alpine Linux'}
        }
        
        for device_type_name, config in device_type_configs.items():
            device_type, created = DeviceType.objects.get_or_create(
                manufacturer=manufacturers[config['manufacturer']],
                model=config['model']
            )
            device_types[device_type_name] = device_type
            if created:
                self.logger.info(f"Created device type: {device_type_name}")

        # Get or create device roles
        roles = {}
        for role_name in ['Access Switch', 'Distribution Switch', 'Router', 'Server', 'Management']:
            role, created = Role.objects.get_or_create(
                name=role_name,
                defaults={'description': f'{role_name} role'}
            )
            roles[role_name] = role
            if created:
                self.logger.info(f"Created role: {role_name}")

        # Device definitions matching the Containerlab topology and Design Builder YAML
        # Access devices go to Rack-02, Nokia devices to Rack-01, virtual machines don't need racks
        devices_data = [
            {'name': 'access1', 'role': 'Access Switch', 'platform': 'Arista EOS', 'device_type': 'Arista EOS', 'rack': 'Rack-02', 'position': 11, 'face': 'front'},
            {'name': 'access2', 'role': 'Access Switch', 'platform': 'Arista EOS', 'device_type': 'Arista EOS', 'rack': 'Rack-02', 'position': 12, 'face': 'front'},
            {'name': 'dist1', 'role': 'Distribution Switch', 'platform': 'Nokia SR Linux', 'device_type': 'Nokia SR Linux', 'rack': 'Rack-01', 'position': 15, 'face': 'front'},
            {'name': 'rtr1', 'role': 'Router', 'platform': 'Nokia SR Linux', 'device_type': 'Nokia SR Linux', 'rack': 'Rack-01', 'position': 20, 'face': 'front'},
            # ztp and mgmt are virtual machines - no rack assignment needed
            {'name': 'ztp', 'role': 'Server', 'platform': 'Alpine Linux', 'device_type': 'Alpine Linux', 'rack': None, 'position': None, 'face': 'front'},
            {'name': 'mgmt', 'role': 'Management', 'platform': 'Alpine Linux', 'device_type': 'Alpine Linux', 'rack': None, 'position': None, 'face': 'front'}
        ]
        
        for device_data in devices_data:
            try:
                device = Device.objects.get(name=device_data['name'], location=site)
                self.logger.info(f"Using existing device: {device_data['name']}")
            except Device.DoesNotExist:
                # Get the rack for this device (only for physical devices)
                rack = racks.get(device_data['rack']) if device_data['rack'] else None
                
                device = Device.objects.create(
                    name=device_data['name'],
                    device_type=device_types[device_data['device_type']],
                    role=roles[device_data['role']],
                    platform=platforms[device_data['platform']],
                    location=site,
                    rack=rack,
                    position=device_data['position'],
                    face=device_data['face'],
                    status=status
                )
                if device_data['rack']:
                    self.logger.info(f"Created device: {device.name} in {device_data['rack']} at position {device_data['position']}")
                else:
                    self.logger.info(f"Created virtual machine: {device.name} (no rack assignment)")

    def _create_interfaces_and_ips(self, site, mgmt_prefix, status):
        """Create interfaces and IP addresses for devices."""
        from nautobot.dcim.models import Device, Interface
        from nautobot.ipam.models import IPAddress
        import ipaddress
        
        # Interface definitions matching Design Builder YAML
        interface_configs = {
            'access1': {
                'mgmt_ip': '172.20.20.11/24',
                'interfaces': [
                    {'name': 'Management0', 'description': 'Management interface'},
                    {'name': 'Ethernet1', 'description': 'Data interface - connected to dist1'},
                    {'name': 'Ethernet2', 'description': 'Data interface - available for connections'},
                    {'name': 'Ethernet3', 'description': 'Data interface - available for connections'}
                ]
            },
            'access2': {
                'mgmt_ip': '172.20.20.12/24',
                'interfaces': [
                    {'name': 'Management0', 'description': 'Management interface'},
                    {'name': 'Ethernet1', 'description': 'Data interface - connected to dist1'},
                    {'name': 'Ethernet2', 'description': 'Data interface - available for connections'},
                    {'name': 'Ethernet3', 'description': 'Data interface - available for connections'}
                ]
            },
            'dist1': {
                'mgmt_ip': '172.20.20.13/24',
                'interfaces': [
                    {'name': 'mgmt0', 'description': 'Management interface'},
                    {'name': 'ethernet-1/1', 'description': 'Data interface - connected to access1'},
                    {'name': 'ethernet-1/2', 'description': 'Data interface - connected to access2'},
                    {'name': 'ethernet-1/3', 'description': 'Data interface - connected to rtr1'}
                ]
            },
            'rtr1': {
                'mgmt_ip': '172.20.20.14/24',
                'interfaces': [
                    {'name': 'mgmt0', 'description': 'Management interface'},
                    {'name': 'ethernet-1/1', 'description': 'Data interface - connected to dist1'},
                    {'name': 'ethernet-1/2', 'description': 'Data interface - connected to ztp'},
                    {'name': 'ethernet-1/3', 'description': 'Data interface - connected to mgmt'}
                ]
            }
        }
        
        for device_name, config in interface_configs.items():
            try:
                device = Device.objects.get(name=device_name, location=site)
                
                # Create all interfaces for the device
                for interface_data in config['interfaces']:
                    interface, created = Interface.objects.get_or_create(
                        device=device,
                        name=interface_data['name'],
                        defaults={
                            'type': '1000base-t',
                            'status': status,
                            'description': interface_data['description']
                        }
                    )
                    if created:
                        self.logger.info(f"Created interface {interface_data['name']} for {device_name}")
                
                # Create management IP address for management interface
                mgmt_interface_name = config['interfaces'][0]['name']  # First interface is always management
                try:
                    mgmt_interface = Interface.objects.get(device=device, name=mgmt_interface_name)
                except Interface.DoesNotExist:
                    self.logger.warning(f"Management interface {mgmt_interface_name} not found for {device_name}")
                    continue
                
                # Create or get IP address
                try:
                    ip = IPAddress.objects.get(address=config['mgmt_ip'])
                    self.logger.info(f"Using existing IP: {config['mgmt_ip']}")
                except IPAddress.DoesNotExist:
                    ip = IPAddress.objects.create(
                        address=config['mgmt_ip'],
                        status=status,
                        description=f"Management IP for {device_name}"
                    )
                    self.logger.info(f"Created IP: {config['mgmt_ip']} for {device_name}")
                
                # Assign IP to management interface
                mgmt_interface.ip_addresses.add(ip)
                
                # Set as primary IP for the device
                device.primary_ip4 = ip
                device.save()
                self.logger.info(f"Set {config['mgmt_ip']} as primary IP for {device_name}")
                    
            except Device.DoesNotExist:
                self.logger.warning(f"Device {device_name} not found, skipping interface/IP creation")

register_jobs(PreflightLabSetup)