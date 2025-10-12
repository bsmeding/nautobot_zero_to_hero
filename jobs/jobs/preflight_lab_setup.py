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

            # Add virtualmachine content type to Site location type
            from django.contrib.contenttypes.models import ContentType
            site_location_type = location_types['Site']
            vm_content_type = ContentType.objects.get(app_label='virtualization', model='virtualmachine')
            if vm_content_type not in site_location_type.content_types.all():
                site_location_type.content_types.add(vm_content_type)
                self.logger.info("Added virtualmachine content type to Site location type")

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

            # Create NAPALM credentials
            self._create_napalm_credentials()

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

            # Create cable connections
            self._create_cable_connections(site, active_status)

            # Create config contexts for devices
            self._create_config_contexts(site, active_status)

            # Skipping Golden Config setup per user request

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

    def _create_napalm_credentials(self):
        """Create NAPALM credentials and secrets groups for different platforms."""
        from nautobot.extras.models import Secret, SecretsGroup, DynamicGroup
        
        # NAPALM credentials for different platforms (lab environment)
        credentials_data = [
            {
                'name': 'Arista EOS NAPALM Credentials',
                'provider': 'environment-variable',
                'parameters': {
                    'variable': 'NAPALM_USERNAME',
                    'variable2': 'NAPALM_PASSWORD'
                }
            },
            {
                'name': 'Nokia SR Linux NAPALM Credentials', 
                'provider': 'environment-variable',
                'parameters': {
                    'variable': 'NAPALM_USERNAME',
                    'variable2': 'NAPALM_PASSWORD_NOKIA'
                }
            }
        ]
        
        # Create secrets
        secrets = {}
        for cred_data in credentials_data:
            try:
                secret = Secret.objects.get(name=cred_data['name'])
                self.logger.info(f"Using existing NAPALM credentials: {cred_data['name']}")
            except Secret.DoesNotExist:
                secret = Secret.objects.create(
                    name=cred_data['name'],
                    provider=cred_data['provider'],
                    parameters=cred_data['parameters']
                )
                self.logger.info(f"Created NAPALM credentials: {cred_data['name']}")
            secrets[cred_data['name']] = secret
                
        # Create credential files (for lab environment)
        self._create_credential_files()
        
        # Create secrets groups and associate with devices
        self._create_secrets_groups_and_associations(secrets)
        
        # Create dynamic groups for platform-based device grouping
        self._create_dynamic_groups()

    def _create_credential_files(self):
        """Set environment variables for NAPALM authentication."""
        import os
        
        # Set environment variables for NAPALM credentials
        os.environ['NAPALM_USERNAME'] = 'admin'
        os.environ['NAPALM_PASSWORD'] = 'admin'  # For Arista devices
        os.environ['NAPALM_PASSWORD_NOKIA'] = 'NokiaSrl1!'  # For Nokia devices
        
        self.logger.info("Set NAPALM environment variables")

    def _create_secrets_groups_and_associations(self, secrets):
        """Create secrets groups and associate them with devices."""
        from nautobot.extras.models import SecretsGroup
        from nautobot.dcim.models import Device
        
        # Create secrets groups
        secrets_groups = {}
        secrets_group_configs = [
            {
                'name': 'Arista NAPALM Secrets Group',
                'description': 'NAPALM credentials for Arista devices',
                'secrets': ['Arista EOS NAPALM Credentials']
            },
            {
                'name': 'Nokia NAPALM Secrets Group',
                'description': 'NAPALM credentials for Nokia devices',
                'secrets': ['Nokia SR Linux NAPALM Credentials']
            }
        ]
        
        for group_config in secrets_group_configs:
            try:
                secrets_group = SecretsGroup.objects.get(name=group_config['name'])
                self.logger.info(f"Using existing secrets group: {group_config['name']}")
            except SecretsGroup.DoesNotExist:
                secrets_group = SecretsGroup.objects.create(
                    name=group_config['name'],
                    description=group_config['description']
                )
                self.logger.info(f"Created secrets group: {group_config['name']}")
            
            # Add secrets to the group
            for secret_name in group_config['secrets']:
                if secret_name in secrets:
                    # Associate secret with the secrets group
                    secrets_group.secrets.add(secrets[secret_name])
                    self.logger.info(f"Added secret '{secret_name}' to secrets group '{group_config['name']}'")
            
            secrets_groups[group_config['name']] = secrets_group
        
        # Associate secrets groups with devices based on platform
        device_secrets_mapping = {
            # Arista devices
            'access1': 'Arista NAPALM Secrets Group',
            'access2': 'Arista NAPALM Secrets Group',
            # Nokia devices
            'dist1': 'Nokia NAPALM Secrets Group',
            'rtr1': 'Nokia NAPALM Secrets Group'
        }
        
        for device_name, secrets_group_name in device_secrets_mapping.items():
            try:
                device = Device.objects.get(name=device_name)
                if secrets_group_name in secrets_groups:
                    secrets_group = secrets_groups[secrets_group_name]
                    # Associate secrets group with device
                    device.secrets_group = secrets_group
                    device.save()
                    self.logger.info(f"Associated secrets group '{secrets_group_name}' with device '{device_name}'")
                
            except Device.DoesNotExist:
                self.logger.warning(f"Device '{device_name}' not found")
            except Exception as e:
                self.logger.warning(f"Failed to associate secrets group with device '{device_name}': {str(e)}")

    def _create_dynamic_groups(self):
        """Create dynamic groups for platform-based device grouping."""
        from nautobot.extras.models import DynamicGroup
        from django.contrib.contenttypes.models import ContentType
        from nautobot.dcim.models import Platform
        
        # Get the device content type
        device_content_type = ContentType.objects.get(app_label='dcim', model='device')
        
        # Dynamic group configurations with correct platform name array filters
        dynamic_group_configs = [
            {
                'name': 'Arista Devices',
                'content_type': device_content_type,
                'filter': {'platform': ['Arista EOS']},
                'description': 'All devices running Arista EOS platform'
            },
            {
                'name': 'Nokia Devices', 
                'content_type': device_content_type,
                'filter': {'platform': ['Nokia SR Linux']},
                'description': 'All devices running Nokia SR Linux platform'
            }
        ]
        
        for group_config in dynamic_group_configs:
            try:
                self.logger.info(f"Processing dynamic group: {group_config['name']} with filter: {group_config['filter']}")
                
                # Validate that all required fields are present
                if not all(key in group_config for key in ['name', 'content_type', 'filter', 'description']):
                    self.logger.error(f"Missing required fields in group_config: {group_config}")
                    continue
                
                dynamic_group = DynamicGroup.objects.get(name=group_config['name'])
                # Always update the filter to ensure it's correct
                dynamic_group.filter = group_config['filter']
                dynamic_group.description = group_config['description']
                dynamic_group.save()
                self.logger.info(f"Updated dynamic group: {group_config['name']} with filter: {group_config['filter']}")
            except DynamicGroup.DoesNotExist:
                dynamic_group = DynamicGroup.objects.create(
                    name=group_config['name'],
                    content_type=group_config['content_type'],
                    filter=group_config['filter'],
                    description=group_config['description']
                )
                self.logger.info(f"Created dynamic group: {group_config['name']} with filter: {group_config['filter']}")
            except Exception as e:
                self.logger.error(f"Error processing dynamic group {group_config['name']}: {str(e)}")
                continue

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
            
            # Create location-specific prefixes under each container with .20 third octet
            self._create_location_prefixes(prefix, site, status)

    def _create_location_prefixes(self, parent_prefix, site, status):
        """Create location-specific prefixes under each container with .20 third octet."""
        from nautobot.ipam.models import Prefix
        import ipaddress
        
        # Extract the network from the parent prefix
        parent_network = ipaddress.ip_network(parent_prefix.prefix)
        
        # Create location-specific prefix with .20 third octet
        if parent_network.version == 4:  # IPv4 only
            # Get the first two octets from parent prefix
            parent_parts = str(parent_network.network_address).split('.')
            
            if len(parent_parts) >= 2:
                # Create prefix with .20 third octet and /24 subnet
                location_prefix = f"{parent_parts[0]}.{parent_parts[1]}.20.0/24"
                
                try:
                    # Check if location prefix already exists (without location assignment)
                    existing_prefix = Prefix.objects.get(prefix=location_prefix)
                    self.logger.info(f"Using existing location prefix: {location_prefix} for {site.name}")
                except Prefix.DoesNotExist:
                    # Create new location-specific prefix (without location assignment due to Site location type constraint)
                    location_prefix_obj = Prefix.objects.create(
                        prefix=location_prefix,
                        parent=parent_prefix,
                        status=status,
                        description=f"{site.name} network under {parent_prefix.prefix}"
                    )
                    self.logger.info(f"Created location prefix: {location_prefix} for {site.name}")

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
        from nautobot.virtualization.models import VirtualMachine, Cluster, ClusterType
        from nautobot.extras.models import Role
        from nautobot.ipam.models import IPAddress
        
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
        # Physical devices in racks
        devices_data = [
            {'name': 'access1', 'role': 'Access Switch', 'platform': 'Arista EOS', 'device_type': 'Arista EOS', 'rack': 'Rack-02', 'position': 11, 'face': 'front'},
            {'name': 'access2', 'role': 'Access Switch', 'platform': 'Arista EOS', 'device_type': 'Arista EOS', 'rack': 'Rack-02', 'position': 12, 'face': 'front'},
            {'name': 'dist1', 'role': 'Distribution Switch', 'platform': 'Nokia SR Linux', 'device_type': 'Nokia SR Linux', 'rack': 'Rack-01', 'position': 15, 'face': 'front'},
            {'name': 'rtr1', 'role': 'Router', 'platform': 'Nokia SR Linux', 'device_type': 'Nokia SR Linux', 'rack': 'Rack-01', 'position': 20, 'face': 'front'}
        ]
        
        # Virtual machines (matching Design Builder YAML)
        virtual_machines_data = [
            {'name': 'workstation1', 'role': 'Server', 'platform': 'Alpine Linux'},
            {'name': 'management', 'role': 'Management', 'platform': 'Alpine Linux'}
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
                self.logger.info(f"Created device: {device.name} in {device_data['rack']} at position {device_data['position']}")
        
        # Create cluster for virtual machines (matching Design Builder YAML)
        cluster_type, created = ClusterType.objects.get_or_create(
            name="Containerlab",
            defaults={'description': 'Containerlab cluster'}
        )
        if created:
            self.logger.info("Created cluster type: Containerlab")
        
        # Create cluster group first
        from nautobot.virtualization.models import ClusterGroup
        cluster_group, created = ClusterGroup.objects.get_or_create(
            name="Lab-Cluster-Group",
            defaults={'description': 'Lab cluster group'}
        )
        if created:
            self.logger.info("Created cluster group: Lab-Cluster-Group")
        else:
            self.logger.info("Using existing cluster group: Lab-Cluster-Group")
        
        cluster, created = Cluster.objects.get_or_create(
            name="Lab-Cluster",
            defaults={
                'cluster_type': cluster_type,
                'cluster_group': cluster_group
            }
        )
        # Remove location assignment if it's set (clusters cannot be assigned to Site locations)
        if cluster.location:
            cluster.location = None
            cluster.save()
            self.logger.info(f"Removed location assignment from cluster (clusters cannot be assigned to Site locations)")
        if created:
            self.logger.info("Created cluster: Lab-Cluster")
        else:
            self.logger.info("Using existing cluster: Lab-Cluster")
        
        # Create virtual machines with IP addresses
        vm_ip_configs = {
            'workstation1': '172.20.20.15/24',
            'management': '172.20.20.16/24'
        }
        
        for vm_data in virtual_machines_data:
            try:
                vm = VirtualMachine.objects.get(name=vm_data['name'], cluster=cluster)
                self.logger.info(f"Using existing virtual machine: {vm_data['name']}")
                # Update location if not set
                if not vm.location:
                    vm.location = site
                    vm.save()
                    self.logger.info(f"Updated location for VM {vm_data['name']} to {site.name}")
            except VirtualMachine.DoesNotExist:
                vm = VirtualMachine.objects.create(
                    name=vm_data['name'],
                    cluster=cluster,
                    location=site,
                    role=roles[vm_data['role']],
                    platform=platforms[vm_data['platform']],
                    status=status
                )
                self.logger.info(f"Created virtual machine: {vm.name} at location: {site.name}")
            
            # Create VM interfaces and IP addresses (Design Builder has compatibility issues with VM interfaces)
            from nautobot.virtualization.models import VMInterface
            
            # Create eth0 interface (management) with IP address
            vm_interface, created = VMInterface.objects.get_or_create(
                virtual_machine=vm,
                name="eth0",
                defaults={
                    'status': status,
                    'description': f"Management interface for {vm_data['name']}"
                }
            )
            if created:
                self.logger.info(f"Created VM interface eth0 for {vm_data['name']}")
            
            # Create and assign IP address for management interface
            if vm_data['name'] in vm_ip_configs:
                vm_ip = vm_ip_configs[vm_data['name']]
                
                # Create or get IP address
                try:
                    ip = IPAddress.objects.get(address=vm_ip)
                    # Update DNS name if not set
                    if not ip.dns_name:
                        ip.dns_name = f"{vm_data['name']}.lab"
                        ip.save()
                        self.logger.info(f"Updated DNS name for IP {vm_ip}: {vm_data['name']}.lab")
                    else:
                        self.logger.info(f"Using existing IP: {vm_ip}")
                except IPAddress.DoesNotExist:
                    ip = IPAddress.objects.create(
                        address=vm_ip,
                        status=status,
                        dns_name=f"{vm_data['name']}.lab",
                        description=f"Primary IP for {vm_data['name']}"
                    )
                    self.logger.info(f"Created IP: {vm_ip} for {vm_data['name']} with DNS name {vm_data['name']}.lab")
                
                # Assign IP to VM interface
                vm_interface.ip_addresses.add(ip)
                self.logger.info(f"Assigned IP {vm_ip} to VM interface eth0 for {vm_data['name']}")
                
                # Set as primary IP for the VM
                vm.primary_ip4 = ip
                vm.save()
                self.logger.info(f"Set {vm_ip} as primary IP for {vm_data['name']}")
            
            # Create eth1 interface (data)
            vm_interface_eth1, created = VMInterface.objects.get_or_create(
                virtual_machine=vm,
                name="eth1",
                defaults={
                    'status': status,
                    'description': f"Data interface for {vm_data['name']}"
                }
            )
            if created:
                self.logger.info(f"Created VM interface eth1 for {vm_data['name']}")
            
            self.logger.info(f"VM interfaces and IP addresses created for {vm_data['name']}")

    def _create_interfaces_and_ips(self, site, mgmt_prefix, status):
        """Create interfaces and IP addresses for devices."""
        from nautobot.dcim.models import Device, Interface
        from nautobot.virtualization.models import VirtualMachine, VMInterface
        from nautobot.ipam.models import IPAddress
        import ipaddress
        
        # Interface definitions for devices
        device_interface_configs = {
            'access1': {
                'mgmt_ip': '172.20.20.11/24',
                'interfaces': [
                    {'name': 'Management0', 'description': 'Management interface'},
                    {'name': 'Ethernet1', 'description': 'Data interface - connected to dist1'},
                    {'name': 'Ethernet2', 'description': 'Data interface - connected to workstation1'},
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
                    {'name': 'ethernet-1/3', 'description': 'Data interface - connected to rtr1'},
                    {'name': 'ethernet-1/4', 'description': 'Data interface - available for connections'}
                ]
            },
            'rtr1': {
                'mgmt_ip': '172.20.20.14/24',
                'interfaces': [
                    {'name': 'mgmt0', 'description': 'Management interface'},
                    {'name': 'ethernet-1/1', 'description': 'Data interface - connected to dist1'},
                    {'name': 'ethernet-1/2', 'description': 'Data interface - connected to mgmt'},
                    {'name': 'ethernet-1/3', 'description': 'Data interface - available for connections'}
                ]
            }
        }
        
        # VM interface configurations
        vm_interface_configs = {
            'workstation1': {
                'mgmt_ip': '172.20.20.15/24',
                'interfaces': [
                    {'name': 'eth0', 'description': 'Management interface'},
                    {'name': 'eth1', 'description': 'Data interface - connected to access1'}
                ]
            }
        }
        
        for device_name, config in device_interface_configs.items():
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
                    # Update DNS name if not set
                    if not ip.dns_name:
                        ip.dns_name = f"{device_name}.lab"
                        ip.save()
                        self.logger.info(f"Updated DNS name for IP {config['mgmt_ip']}: {device_name}.lab")
                    else:
                        self.logger.info(f"Using existing IP: {config['mgmt_ip']}")
                except IPAddress.DoesNotExist:
                    ip = IPAddress.objects.create(
                        address=config['mgmt_ip'],
                        status=status,
                        dns_name=f"{device_name}.lab",
                        description=f"Management IP for {device_name}"
                    )
                    self.logger.info(f"Created IP: {config['mgmt_ip']} for {device_name} with DNS name {device_name}.lab")
                
                # Assign IP to management interface
                mgmt_interface.ip_addresses.add(ip)
                
                # Set as primary IP for the device
                device.primary_ip4 = ip
                device.save()
                self.logger.info(f"Set {config['mgmt_ip']} as primary IP for {device_name}")
                    
            except Device.DoesNotExist:
                self.logger.warning(f"Device {device_name} not found, skipping interface/IP creation")

        # VM interfaces are created above in the _create_devices method for both VMs
        self.logger.info("VM interfaces created for workstation1 and management VMs")

    def _create_cable_connections(self, site, status):
        """Create cable connections between devices according to lab topology."""
        from nautobot.dcim.models import Device, Interface, Cable
        from nautobot.virtualization.models import VirtualMachine, VMInterface
        
        # Note: CableType is not available in Nautobot 2.4.8, creating cables without type
        # This matches the Design Builder YAML approach which also doesn't specify cable types
        self.logger.info("Creating cables without type (matching Design Builder approach)")
        
        # Define cable connections based on lab topology
        cable_connections = [
            # Access switches to Distribution switch
            {'from_device': 'access1', 'from_interface': 'Ethernet1', 'to_device': 'dist1', 'to_interface': 'ethernet-1/1'},
            {'from_device': 'access2', 'from_interface': 'Ethernet1', 'to_device': 'dist1', 'to_interface': 'ethernet-1/2'},
            
            # Access switch to Workstation
            {'from_device': 'access1', 'from_interface': 'Ethernet2', 'to_device': 'workstation1', 'to_interface': 'eth1'},
            
            # Distribution switch to Router
            {'from_device': 'dist1', 'from_interface': 'ethernet-1/3', 'to_device': 'rtr1', 'to_interface': 'ethernet-1/1'},
            
            # Router to Management VM (handled by Preflight Job due to Design Builder VMInterface compatibility issues)
            {'from_device': 'rtr1', 'from_interface': 'ethernet-1/2', 'to_device': 'management', 'to_interface': 'eth1'},
        ]
        
        for connection in cable_connections:
            try:
                # Get the source device and interface
                if connection['from_device'] in ['workstation1', 'management']:
                    # VM interface
                    from_device = VirtualMachine.objects.get(name=connection['from_device'])
                    from_interface = VMInterface.objects.get(virtual_machine=from_device, name=connection['from_interface'])
                else:
                    # Physical device interface
                    from_device = Device.objects.get(name=connection['from_device'], location=site)
                    from_interface = Interface.objects.get(device=from_device, name=connection['from_interface'])
                
                # Get the destination device and interface
                if connection['to_device'] in ['workstation1', 'management']:
                    # VM interface
                    to_device = VirtualMachine.objects.get(name=connection['to_device'])
                    to_interface = VMInterface.objects.get(virtual_machine=to_device, name=connection['to_interface'])
                else:
                    # Physical device interface
                    to_device = Device.objects.get(name=connection['to_device'], location=site)
                    to_interface = Interface.objects.get(device=to_device, name=connection['to_interface'])
                
                # Create cable connection directly (GenericForeignKey can't be used for lookups)
                # Handle duplicates with try/except around creation
                try:
                    cable_data = {
                        'termination_a': from_interface,
                        'termination_b': to_interface,
                        'status': status,
                        'label': f"{connection['from_device']}-{connection['from_interface']} to {connection['to_device']}-{connection['to_interface']}"
                    }
                    
                    cable = Cable.objects.create(**cable_data)
                    self.logger.info(f"Created cable: {connection['from_device']}-{connection['from_interface']} to {connection['to_device']}-{connection['to_interface']}")
                except Exception as cable_error:
                    # Handle potential duplicate cable creation gracefully
                    if "unique constraint" in str(cable_error).lower() or "duplicate" in str(cable_error).lower():
                        self.logger.info(f"Using existing cable: {connection['from_device']}-{connection['from_interface']} to {connection['to_device']}-{connection['to_interface']}")
                    else:
                        raise cable_error
                    
            except Exception as e:
                self.logger.warning(f"Failed to create cable connection {connection['from_device']}-{connection['from_interface']} to {connection['to_device']}-{connection['to_interface']}: {str(e)}")
        
        # All cable connections created successfully
        self.logger.info("All cable connections created successfully")

    def _create_config_contexts(self, site, status):
        """Create config contexts for devices with platform-specific configurations."""
        from nautobot.extras.models import ConfigContext, Role
        from nautobot.dcim.models import Platform
        from django.contrib.contenttypes.models import ContentType

        # Common config context for all devices
        common_context_data = {
            "ntp_servers": [
                "192.168.1.1",
                "192.168.1.2", 
                "time.google.com"
            ],
            "dns_servers": [
                "8.8.8.8",
                "8.8.4.4",
                "1.1.1.1"
            ],
            "syslog_hosts": [
                {"host": "192.168.1.100", "port": 514},
                {"host": "192.168.1.101", "port": 514}
            ],
            "snmp": {
                "community": "nautobot_lab_ro",
                "location": "NetDevOps Lab"
            },
            "timezone": "UTC",
            "domain_name": "netdevops.lab"
        }

        # Create common config context for all lab devices
        common_context, created = ConfigContext.objects.get_or_create(
            name="Lab Common Configuration",
            defaults={
                "weight": 1000,
                "description": "Common configuration for all lab devices",
                "data": common_context_data,
                "is_active": True
            }
        )
        if created:
            self.logger.info("Created common config context")
        else:
            # Update existing context
            common_context.data = common_context_data
            common_context.weight = 1000
            common_context.save()
            self.logger.info("Updated common config context")

        # Associate with site
        common_context.locations.add(site)

        # Arista-specific configuration
        arista_context_data = {
            "platform_specific": {
                "cli_commands": {
                    "save_config": "write memory",
                    "show_version": "show version"
                },
                "management_interface": "Management0",
                "ntp_source_interface": "Management0",
                "logging": {
                    "buffer_size": 16384,
                    "source_interface": "Management0"
                },
                "banner": {
                    "motd": "Arista Device - NetDevOps Lab - Unauthorized access prohibited"
                }
            },
            "features": {
                "lldp": True,
                "stp": "rapid-pvst"
            }
        }

        arista_platform = Platform.objects.get(name="Arista EOS")
        arista_context, created = ConfigContext.objects.get_or_create(
            name="Arista Platform Configuration",
            defaults={
                "weight": 2000,
                "description": "Platform-specific configuration for Arista EOS devices",
                "data": arista_context_data,
                "is_active": True
            }
        )
        if created:
            self.logger.info("Created Arista config context")
        else:
            # Update existing context
            arista_context.data = arista_context_data
            arista_context.weight = 2000
            arista_context.save()
            self.logger.info("Updated Arista config context")

        # Associate with Arista platform
        arista_context.platforms.add(arista_platform)
        arista_context.locations.add(site)

        # Nokia-specific configuration
        nokia_context_data = {
            "platform_specific": {
                "cli_commands": {
                    "save_config": "tools system configuration save",
                    "show_version": "info system version"
                },
                "management_interface": "mgmt0",
                "ntp_source_interface": "mgmt0",
                "logging": {
                    "buffer_size": 10000,
                    "source_interface": "mgmt0"
                },
                "banner": {
                    "motd": "Nokia SR Linux Device - NetDevOps Lab - Unauthorized access prohibited"
                }
            },
            "features": {
                "lldp": True,
                "spanning_tree": "mstp"
            }
        }

        nokia_platform = Platform.objects.get(name="Nokia SR Linux")
        nokia_context, created = ConfigContext.objects.get_or_create(
            name="Nokia Platform Configuration",
            defaults={
                "weight": 2000,
                "description": "Platform-specific configuration for Nokia SR Linux devices",
                "data": nokia_context_data,
                "is_active": True
            }
        )
        if created:
            self.logger.info("Created Nokia config context")
        else:
            # Update existing context
            nokia_context.data = nokia_context_data
            nokia_context.weight = 2000
            nokia_context.save()
            self.logger.info("Updated Nokia config context")

        # Associate with Nokia platform
        nokia_context.platforms.add(nokia_platform)
        nokia_context.locations.add(site)

        # Role-specific configuration - Access Switches
        access_context_data = {
            "role_specific": {
                "port_security": {
                    "enabled": True,
                    "max_mac_addresses": 2
                },
                "default_vlan": 100,
                "allowed_vlans": [10, 20, 30, 100, 200, 300],
                "stp_portfast": True
            }
        }

        access_role = Role.objects.get(name="Access Switch")
        access_context, created = ConfigContext.objects.get_or_create(
            name="Access Switch Role Configuration",
            defaults={
                "weight": 3000,
                "description": "Role-specific configuration for access switches",
                "data": access_context_data,
                "is_active": True
            }
        )
        if created:
            self.logger.info("Created Access Switch config context")
        else:
            # Update existing context
            access_context.data = access_context_data
            access_context.weight = 3000
            access_context.save()
            self.logger.info("Updated Access Switch config context")

        # Associate with access role
        access_context.roles.add(access_role)
        access_context.locations.add(site)

        self.logger.info("Config contexts created and associated successfully")


register_jobs(PreflightLabSetup)