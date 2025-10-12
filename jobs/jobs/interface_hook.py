#!/usr/bin/env python3

"""
Interface JobHook: Automatically configure device interfaces when created/updated/deleted in Nautobot.
This hook triggers on Interface model changes and pushes configuration to the actual network device.
"""

from nautobot.apps.jobs import register_jobs
from nautobot.extras.jobs import JobHookReceiver
from nautobot.dcim.models import Interface

try:
    import pyeapi
    PYEAPI_AVAILABLE = True
except ImportError:
    PYEAPI_AVAILABLE = False

name = "Lifecycle hooks"

class InterfaceJobHookReceiver(JobHookReceiver):
    """JobHook that syncs Interface changes from Nautobot to network devices."""

    class Meta:
        name = "Interface Configuration Hook"
        description = "Automatically configure device interfaces when created/updated/deleted in Nautobot"
        object_type = Interface
        enabled = True  # Set to False to disable the hook

    def run(self, commit, **kwargs):
        """Entry point for Job Hook execution.

        Args:
            commit: Boolean indicating if changes should be committed
            **kwargs: Event context including:
                - action: one of "created", "updated", "deleted"
                - object_pk: the primary key of the Interface
                - object_repr: string representation
                - changed_data: dict of changed fields (for updates)
                - user: username (if available)
        """
        if not PYEAPI_AVAILABLE:
            self.log_warning("pyeapi not available - skipping device configuration")
            return

        action = kwargs.get("action")
        object_pk = kwargs.get("object_pk")
        object_repr = kwargs.get("object_repr")
        changed_data = kwargs.get("changed_data", {})

        # For deleted interfaces, we only have the pk and repr
        if action == "deleted":
            self.log_info(f"Interface deleted: {object_repr} ({object_pk})")
            self.log_warning("Cannot sync delete to device - interface object no longer exists")
            return

        # Fetch the interface object
        try:
            interface = Interface.objects.get(pk=object_pk)
        except Interface.DoesNotExist:
            self.log_error(f"Interface with pk {object_pk} not found")
            return

        # Get the device
        device = interface.device
        if not device:
            self.log_info(f"Interface {interface.name} has no device - skipping")
            return

        # Only process physical interfaces (not virtual/LAG/etc)
        if not self._is_physical_interface(interface):
            self.log_info(f"Interface {interface.name} is not physical - skipping device config")
            return

        # Get device connection details
        if not device.primary_ip4 and not device.primary_ip:
            self.log_warning(f"Device {device.name} has no primary IP - cannot connect")
            return

        # Branch by action
        if action == "created":
            self._handle_interface_create(interface, device, commit)
        elif action == "updated":
            self._handle_interface_update(interface, device, changed_data, commit)
        else:
            self.log_info(f"Interface action '{action}' for {object_repr} - no handler defined")

    def _is_physical_interface(self, interface):
        """Check if interface is a physical interface that should be configured."""
        # Skip virtual interfaces, LAGs, management, etc.
        interface_name = interface.name.lower()
        
        # List of interface types we want to configure
        physical_prefixes = ('ethernet', 'gigabitethernet', 'tengigabitethernet', 'eth')
        
        return any(interface_name.startswith(prefix) for prefix in physical_prefixes)

    def _handle_interface_create(self, interface, device, commit):
        """Handle interface creation - configure new interface on device."""
        self.log_info(f"Configuring new interface {interface.name} on device {device.name}")
        
        try:
            config_commands = self._build_interface_config(interface)
            
            if commit:
                self._push_config_to_device(device, config_commands)
                self.log_success(f"Successfully configured interface {interface.name} on {device.name}")
            else:
                self.log_info(f"Dry-run mode - would configure:\n{chr(10).join(config_commands)}")
        
        except Exception as e:
            self.log_error(f"Failed to configure interface {interface.name}: {str(e)}")

    def _handle_interface_update(self, interface, device, changed_data, commit):
        """Handle interface update - reconfigure interface on device."""
        self.log_info(f"Updating interface {interface.name} on device {device.name}")
        self.log_info(f"Changed fields: {list(changed_data.keys())}")
        
        # Only push config if relevant fields changed
        relevant_fields = {'description', 'enabled', 'mode', 'mtu', 'type'}
        if not any(field in changed_data for field in relevant_fields):
            self.log_info("No relevant fields changed - skipping device update")
            return
        
        try:
            config_commands = self._build_interface_config(interface)
            
            if commit:
                self._push_config_to_device(device, config_commands)
                self.log_success(f"Successfully updated interface {interface.name} on {device.name}")
            else:
                self.log_info(f"Dry-run mode - would update:\n{chr(10).join(config_commands)}")
        
        except Exception as e:
            self.log_error(f"Failed to update interface {interface.name}: {str(e)}")

    def _build_interface_config(self, interface):
        """Build configuration commands for an interface.
        
        Args:
            interface: Interface model instance
            
        Returns:
            List of configuration command strings
        """
        commands = [
            f"interface {interface.name}",
        ]
        
        # Add description if present
        if interface.description:
            commands.append(f"description {interface.description}")
        else:
            commands.append("no description")
        
        # Enable or disable interface
        if interface.enabled:
            commands.append("no shutdown")
        else:
            commands.append("shutdown")
        
        # Add MTU if specified and not default
        if interface.mtu and interface.mtu != 1500:
            commands.append(f"mtu {interface.mtu}")
        
        return commands

    def _push_config_to_device(self, device, config_commands):
        """Push configuration commands to the network device.
        
        Args:
            device: Device model instance
            config_commands: List of configuration command strings
            
        Raises:
            Exception: If connection or configuration fails
        """
        # Get device IP
        primary = device.primary_ip4 or device.primary_ip
        host = primary.address.ip if hasattr(primary.address, 'ip') else str(primary.address).split('/')[0]
        
        # Get platform-specific settings
        platform_name = device.platform.name.lower() if device.platform else ""
        
        # Currently only supporting Arista EOS via pyeapi
        if 'arista' not in platform_name and 'eos' not in platform_name:
            self.log_warning(f"Platform {platform_name} not supported for automatic config - only Arista EOS")
            return
        
        # Connect and push config
        self.log_debug(f"Connecting to {device.name} at {host}")
        
        try:
            connection = pyeapi.connect(
                transport="https",
                host=host,
                username="admin",  # TODO: Get from secrets/credentials
                password="admin",  # TODO: Get from secrets/credentials
                port=443,
            )
            node = pyeapi.client.Node(connection)
            
            # Push configuration
            node.config(config_commands)
            
            # Save configuration
            node.enable("write memory")
            
            self.log_debug(f"Configuration pushed successfully to {device.name}")
            
        except Exception as e:
            self.log_error(f"Failed to connect/configure {device.name}: {str(e)}")
            raise


register_jobs(InterfaceJobHookReceiver)

