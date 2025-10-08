"""Job to configure network services on devices using config context data."""

from nautobot.apps.jobs import Job, MultiObjectVar, BooleanVar, register_jobs
from nautobot.dcim.models import Device
import pyeapi


name = "Network Services"


class ConfigureNetworkServices(Job):
    """Configure network services (NTP, DNS, Syslog, SNMP) on devices using config context."""

    class Meta:
        name = "Configure Network Services"
        description = "Configure NTP, DNS, Syslog, and SNMP on devices using config context data"
        has_sensitive_variables = False

    devices = MultiObjectVar(
        model=Device,
        description="Devices to configure",
        required=True
    )

    config_ntp = BooleanVar(
        description="Configure NTP servers",
        default=True
    )

    config_dns = BooleanVar(
        description="Configure DNS servers",
        default=True
    )

    config_syslog = BooleanVar(
        description="Configure Syslog hosts",
        default=True
    )

    config_snmp = BooleanVar(
        description="Configure SNMP",
        default=True
    )

    dry_run = BooleanVar(
        description="Dry run - show commands without applying",
        default=True
    )

    def run(self, devices, config_ntp, config_dns, config_syslog, config_snmp, dry_run):
        """Configure network services on selected devices."""
        
        self.logger.info(f"{'DRY RUN - ' if dry_run else ''}Configuring network services on {len(devices)} devices")
        self.logger.info(f"Services: NTP={config_ntp}, DNS={config_dns}, Syslog={config_syslog}, SNMP={config_snmp}")
        
        for device in devices:
            self.logger.info("=" * 80)
            self.logger.info(f"Processing device: {device.name} ({device.platform})")
            
            # Get config context for the device
            config_context = device.get_config_context()
            
            if not config_context:
                self.logger.warning(f"No config context found for {device.name} - skipping")
                continue
            
            # Check if platform_specific data exists
            if 'platform_specific' not in config_context:
                self.logger.warning(f"No platform_specific config context for {device.name} - skipping")
                continue
            
            platform_info = config_context.get('platform_specific', {})
            mgmt_interface = platform_info.get('management_interface', '')
            
            # Determine platform type
            is_arista = mgmt_interface == 'Management0'
            is_nokia = mgmt_interface == 'mgmt0'
            
            if not is_arista and not is_nokia:
                self.logger.warning(f"Unknown platform for {device.name} - skipping")
                continue
            
            # Build configuration commands
            config_commands = []
            
            # NTP Configuration
            if config_ntp and 'ntp_servers' in config_context:
                self.logger.info(f"Building NTP configuration for {device.name}")
                ntp_commands = self._build_ntp_config(config_context, is_arista)
                config_commands.extend(ntp_commands)
            
            # DNS Configuration
            if config_dns and 'dns_servers' in config_context:
                self.logger.info(f"Building DNS configuration for {device.name}")
                dns_commands = self._build_dns_config(config_context, is_arista)
                config_commands.extend(dns_commands)
            
            # Syslog Configuration
            if config_syslog and 'syslog_hosts' in config_context:
                self.logger.info(f"Building Syslog configuration for {device.name}")
                syslog_commands = self._build_syslog_config(config_context, is_arista, platform_info)
                config_commands.extend(syslog_commands)
            
            # SNMP Configuration
            if config_snmp and 'snmp' in config_context:
                self.logger.info(f"Building SNMP configuration for {device.name}")
                snmp_commands = self._build_snmp_config(config_context, is_arista)
                config_commands.extend(snmp_commands)
            
            # Domain name (reset to default, then add new)
            if 'domain_name' in config_context:
                if is_arista:
                    # Modern Arista EOS uses 'dns domain' instead of 'ip domain-name'
                    config_commands.insert(0, f"dns domain {config_context['domain_name']}")
                    config_commands.insert(0, "default dns domain")  # Reset domain to default first
                elif is_nokia:
                    config_commands.insert(0, f"/ system name domain-name {config_context['domain_name']}")
            
            if not config_commands:
                self.logger.warning(f"No configuration commands generated for {device.name}")
                continue
            
            # Display commands
            self.logger.info(f"\nConfiguration commands for {device.name}:")
            self.logger.info("-" * 60)
            for cmd in config_commands:
                self.logger.info(f"  {cmd}")
            self.logger.info("-" * 60)
            
            # Apply configuration if not dry run
            if not dry_run:
                self._apply_config(device, config_commands, is_arista, platform_info)
            else:
                self.logger.info(f"DRY RUN - Configuration not applied to {device.name}")
        
        if dry_run:
            self.logger.success("DRY RUN completed - Review commands above")
        else:
            self.logger.success("Network services configuration completed!")

    def _build_ntp_config(self, context, is_arista):
        """Build NTP configuration commands."""
        commands = []
        ntp_servers = context.get('ntp_servers', [])
        
        # For Arista, reset to default NTP config first (removes all NTP servers)
        if is_arista:
            commands.append("default ntp")  # Reset NTP to default (removes all config)
        
        for ntp_server in ntp_servers:
            if is_arista:
                commands.append(f"ntp server {ntp_server}")
            else:  # Nokia
                commands.append(f"/ system ntp server {ntp_server}")
        
        # Add source interface for Arista (modern syntax)
        if is_arista:
            ntp_source = context.get('platform_specific', {}).get('ntp_source_interface')
            if ntp_source:
                # Modern Arista EOS uses 'ntp local-interface' instead of 'ntp source'
                commands.append(f"ntp local-interface {ntp_source}")
        
        return commands

    def _build_dns_config(self, context, is_arista):
        """Build DNS configuration commands."""
        commands = []
        dns_servers = context.get('dns_servers', [])
        
        # For Arista, reset DNS to default (removes all DNS servers)
        if is_arista:
            commands.append("default ip name-server")  # Reset DNS to default
        
        for dns_server in dns_servers:
            if is_arista:
                commands.append(f"ip name-server {dns_server}")
            else:  # Nokia
                commands.append(f"/ system dns server-list [ {dns_server} ]")
        
        return commands

    def _build_syslog_config(self, context, is_arista, platform_info):
        """Build Syslog configuration commands."""
        commands = []
        syslog_hosts = context.get('syslog_hosts', [])
        
        # For Arista, reset syslog hosts to default
        if is_arista:
            # Reset logging host to default (removes all hosts)
            commands.append("default logging host")
        
        for syslog in syslog_hosts:
            host = syslog.get('host')
            port = syslog.get('port', 514)
            
            if is_arista:
                commands.append(f"logging host {host}")
            else:  # Nokia
                commands.append(f"/ system logging remote-server {host} port {port}")
        
        # Add logging buffer and source for Arista
        if is_arista:
            logging_config = platform_info.get('logging', {})
            source_intf = logging_config.get('source_interface')
            buffer_size = logging_config.get('buffer_size')
            
            if source_intf:
                commands.append(f"logging source-interface {source_intf}")
            if buffer_size:
                commands.append(f"logging buffered {buffer_size}")
        
        return commands

    def _build_snmp_config(self, context, is_arista):
        """Build SNMP configuration commands."""
        commands = []
        snmp = context.get('snmp', {})
        community = snmp.get('community')
        location = snmp.get('location')
        
        if is_arista:
            # Reset SNMP to default (removes all SNMP config)
            if community or location:
                commands.append("default snmp-server")  # Reset SNMP to default
            if community:
                commands.append(f"snmp-server community {community} ro")
            if location:
                commands.append(f"snmp-server location {location}")
        else:  # Nokia
            if community:
                commands.append(f"/ system snmp community {community} access-permissions ro")
            if location:
                commands.append(f"/ system snmp location {location}")
        
        return commands

    def _apply_config(self, device, config_commands, is_arista, platform_info):
        """Apply configuration to the device."""
        
        # Get primary IP address
        primary_ip = device.primary_ip4 or device.primary_ip
        if not primary_ip:
            self.logger.error(f"No primary IP address for {device.name} - cannot connect")
            return
        
        host = str(primary_ip.address.ip)
        
        try:
            if is_arista:
                self._apply_config_arista(device.name, host, config_commands, platform_info)
            else:
                self.logger.warning(f"Nokia configuration push not implemented yet for {device.name}")
                self.logger.info(f"Commands to apply manually:\n" + "\n".join(config_commands))
        
        except Exception as e:
            self.logger.error(f"Failed to apply configuration to {device.name}: {str(e)}")

    def _apply_config_arista(self, device_name, host, config_commands, platform_info):
        """Apply configuration to Arista device using eAPI."""
        
        try:
            # Create connection
            connection = pyeapi.connect(
                transport="https",
                host=host,
                username="admin",
                password="admin",
                port=443,
            )
            node = pyeapi.client.Node(connection)
            
            # Apply configuration
            self.logger.info(f"Connecting to {device_name} at {host}...")
            node.config(config_commands)
            
            # Save configuration
            save_cmd = platform_info.get('cli_commands', {}).get('save_config', 'write memory')
            node.enable(save_cmd)
            
            self.logger.success(f"Configuration applied successfully to {device_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to {device_name}: {str(e)}")
            raise


register_jobs(ConfigureNetworkServices)

