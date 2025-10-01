"""
Pre-flight Lab Setup Job

This job populates Nautobot with the lab topology data from the Containerlab setup.
Based on the lab topology from: https://netdevops.it/blog/building-a-reusable-network-automation-lab-with-containerlab/

This demonstrates how to programmatically create Nautobot objects using Jobs.
"""

from nautobot.apps.jobs import Job, StringVar, BooleanVar, register_jobs


class PreflightLabSetup(Job):
    """Pre-flight lab setup job to populate Nautobot with Containerlab lab topology."""
    
    class Meta:
        name = "Pre-flight Lab Setup"
        description = "Populate Nautobot with Containerlab lab topology data"
        has_sensitive_variables = False

    site_name = StringVar(
        description="Site name for the lab (will be ignored to avoid conflicts)",
        default="Lab Data Center",
        required=True
    )
    
    management_subnet = StringVar(
        description="Management subnet (CIDR notation)",
        default="172.20.20.0/24",
        required=True
    )
    
    create_vlans = BooleanVar(
        description="Create VLANs for the lab",
        default=True
    )
    
    create_tags = BooleanVar(
        description="Create tags for the lab",
        default=True
    )

    def run(self, site_name, management_subnet, create_vlans, create_tags):
        self.logger.info("Starting pre-flight lab setup...")

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

            # Create or get Site location type
            site_type, created = LocationType.objects.get_or_create(
                name="Site",
                defaults={'description': "Site location type"}
            )
            if created:
                self.logger.info("Created Site location type")

            # Create a completely unique site name using timestamp and job ID
            import time
            timestamp = int(time.time())
            unique_site_name = f"Containerlab-Lab-{timestamp}-{self.job.id}"
            self.logger.info(f"Creating unique site: {unique_site_name}")

            # Create the site with the unique name
            site = Location.objects.create(
                name=unique_site_name,
                location_type=site_type,
                slug=f"containerlab-lab-{timestamp}-{self.job.id}",
                status=active_status
            )
            self.logger.info(f"Created site: {unique_site_name}")

            # Create tags if requested
            if create_tags:
                self._create_tags()

            # Create management network
            mgmt_prefix = self._create_management_network(site, management_subnet, active_status)

            # Create VLANs if requested
            if create_vlans:
                self._create_vlans(site, active_status)

            # Create devices
            self._create_devices(site, mgmt_prefix, active_status)

            # Create interfaces and IP addresses
            self._create_interfaces_and_ips(site, mgmt_prefix, active_status)

            self.logger.info("Pre-flight lab setup completed successfully!")

        except Exception as e:
            self.logger.error(f"Error during lab setup: {str(e)}")
            raise

    def _create_tags(self):
        """Create tags for the lab."""
        from nautobot.extras.models import Tag, Status
        
        try:
            active_status = Status.objects.get(name='Active')
        except Status.DoesNotExist:
            active_status = Status.objects.first()

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
                    'color': tag_data['color'],
                    'status': active_status
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
                site=site,
                description="Management network for lab devices"
            )
            self.logger.info(f"Created prefix: {management_subnet}")
        
        return prefix

    def _create_vlans(self, site, status):
        """Create VLANs for the lab."""
        from nautobot.ipam.models import VLAN
        
        vlans_data = [
            {'vid': 10, 'name': 'Management', 'description': 'Management VLAN'},
            {'vid': 20, 'name': 'Data', 'description': 'Data VLAN'},
            {'vid': 30, 'name': 'Voice', 'description': 'Voice VLAN'}
        ]
        
        for vlan_data in vlans_data:
            try:
                vlan = VLAN.objects.get(vid=vlan_data['vid'], site=site)
                self.logger.info(f"Using existing VLAN: {vlan_data['name']} (VID: {vlan_data['vid']})")
            except VLAN.DoesNotExist:
                vlan = VLAN.objects.create(
                    vid=vlan_data['vid'],
                    name=vlan_data['name'],
                    description=vlan_data['description'],
                    status=status,
                    site=site
                )
                self.logger.info(f"Created VLAN: {vlan.name} (VID: {vlan.vid})")

    def _create_devices(self, site, mgmt_prefix, status):
        """Create devices for the lab."""
        from nautobot.dcim.models import Device, Platform
        from nautobot.extras.models import Role
        
        # Get or create platforms
        platforms = {}
        for platform_name in ['arista_eos', 'nokia_srl', 'nokia_sros']:
            platform, created = Platform.objects.get_or_create(
                name=platform_name,
                defaults={'description': f'{platform_name} platform'}
            )
            platforms[platform_name] = platform
            if created:
                self.logger.info(f"Created platform: {platform_name}")

        # Get or create device roles
        roles = {}
        for role_name in ['Access Switch', 'Distribution Switch', 'Router']:
            role, created = Role.objects.get_or_create(
                name=role_name,
                defaults={'description': f'{role_name} role'}
            )
            roles[role_name] = role
            if created:
                self.logger.info(f"Created role: {role_name}")

        # Device definitions
        devices_data = [
            {'name': 'access1', 'role': 'Access Switch', 'platform': 'arista_eos'},
            {'name': 'access2', 'role': 'Access Switch', 'platform': 'arista_eos'},
            {'name': 'dist1', 'role': 'Distribution Switch', 'platform': 'nokia_srl'},
            {'name': 'rtr1', 'role': 'Router', 'platform': 'nokia_sros'}
        ]
        
        for device_data in devices_data:
            try:
                device = Device.objects.get(name=device_data['name'], site=site)
                self.logger.info(f"Using existing device: {device_data['name']}")
            except Device.DoesNotExist:
                device = Device.objects.create(
                    name=device_data['name'],
                    device_type=None,  # Will be set by platform
                    role=roles[device_data['role']],
                    platform=platforms[device_data['platform']],
                    site=site,
                    status=status
                )
                self.logger.info(f"Created device: {device.name}")

    def _create_interfaces_and_ips(self, site, mgmt_prefix, status):
        """Create interfaces and IP addresses for devices."""
        from nautobot.dcim.models import Device, Interface
        from nautobot.ipam.models import IPAddress
        import ipaddress
        
        # IP address mapping
        ip_mapping = {
            'access1': '172.20.20.11',
            'access2': '172.20.20.12',
            'dist1': '172.20.20.13',
            'rtr1': '172.20.20.14'
        }
        
        for device_name, ip_addr in ip_mapping.items():
            try:
                device = Device.objects.get(name=device_name, site=site)
                
                # Create management interface
                interface, created = Interface.objects.get_or_create(
                    device=device,
                    name='eth0',
                    defaults={
                        'type': '1000base-t',
                        'status': status
                    }
                )
                if created:
                    self.logger.info(f"Created interface eth0 for {device_name}")
                
                # Create IP address
                try:
                    ip = IPAddress.objects.get(address=ip_addr)
                    self.logger.info(f"Using existing IP: {ip_addr}")
                except IPAddress.DoesNotExist:
                    ip = IPAddress.objects.create(
                        address=ip_addr,
                        status=status,
                        assigned_object=interface,
                        description=f"Management IP for {device_name}"
                    )
                    self.logger.info(f"Created IP: {ip_addr} for {device_name}")
                    
            except Device.DoesNotExist:
                self.logger.warning(f"Device {device_name} not found, skipping interface/IP creation")

register_jobs(PreflightLabSetup)