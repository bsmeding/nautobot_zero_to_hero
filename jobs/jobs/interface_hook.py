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
        enabled = True  # Enabled - automatically syncs interface changes to devices

    def run(self, **kwargs):
        """Entry point for Job Hook execution.

        Args:
            **kwargs: Keyword arguments from Nautobot including:
                - action: one of "created", "updated", "deleted"
                - object_pk: the primary key of the Interface
                - object_repr: string representation
                - changed_data: dict of changed fields (for updates)
                - commit: Boolean indicating if changes should be committed
                - user: username (if available)
        """
        if not PYEAPI_AVAILABLE:
            self.logger.warning("pyeapi not available - skipping device configuration")
            return

        # Get ObjectChange object from kwargs
        object_change = kwargs.get("object_change")
        commit = kwargs.get("commit", True)  # Default to True for automatic configuration
        
        if not object_change:
            # Try old-style parameters (for backwards compatibility)
            action = kwargs.get("action")
            object_pk = kwargs.get("object_pk")
            object_repr = kwargs.get("object_repr")
            changed_data = kwargs.get("changed_data", {})
        else:
            # Extract data from ObjectChange object
            action = object_change.action
            object_pk = object_change.changed_object_id
            object_repr = str(object_change.changed_object) if object_change.changed_object else f"Interface {object_change.changed_object_id}"
            changed_data = object_change.object_data_v2 or {}
        
        self.logger.info(f"Interface {action}: {object_repr} (pk={object_pk}, commit={commit})")
        
        # Check if action is valid
        if not action:
            self.logger.warning("Interface hook triggered but no action provided")
            self.logger.warning("Available kwargs keys: " + str(list(kwargs.keys())))
            return
        
        # For deleted objects, we can't fetch them
        if action in ["deleted", "delete"]:
            self.logger.warning("Cannot sync delete to device - interface object no longer exists")
            return
        
        # Fetch the interface object by ID
        if not object_pk:
            self.logger.error("No object_pk provided")
            return
            
        try:
            interface = Interface.objects.get(pk=object_pk)
        except Interface.DoesNotExist:
            self.logger.error(f"Interface with pk {object_pk} not found")
            return

        # Get the device
        device = interface.device
        if not device:
            self.logger.info(f"Interface {interface.name} has no device - skipping")
            return

        # Only process physical interfaces (not virtual/LAG/etc)
        if not self._is_physical_interface(interface):
            self.logger.info(f"Interface {interface.name} is not physical - skipping device config")
            return

        # Get device connection details
        if not device.primary_ip4 and not device.primary_ip:
            self.logger.warning(f"Device {device.name} has no primary IP - cannot connect")
            return

        # Branch by action
        if action in ["created", "create"]:
            self._handle_interface_create(interface, device, commit)
        elif action in ["updated", "update"]:
            # For ObjectChange, get changed fields differently
            if object_change:
                # Get pre and post change data to determine what changed
                pre_change = object_change.object_data or {}
                post_change = object_change.object_data_v2 or {}
                changed_fields = [key for key in post_change.keys() if pre_change.get(key) != post_change.get(key)]
                changed_data_dict = {key: post_change[key] for key in changed_fields}
            else:
                # Old-style changed_data
                changed_data_dict = changed_data
            
            self._handle_interface_update(interface, device, changed_data_dict, commit)
        else:
            self.logger.info(f"Interface action '{action}' - no handler defined")

    def _is_physical_interface(self, interface):
        """Check if interface is a physical interface that should be configured."""
        # Skip virtual interfaces, LAGs, management, etc.
        interface_name = interface.name.lower()
        
        # List of interface types we want to configure
        physical_prefixes = ('ethernet', 'gigabitethernet', 'tengigabitethernet', 'eth')
        
        return any(interface_name.startswith(prefix) for prefix in physical_prefixes)

    def _handle_interface_create(self, interface, device, commit):
        """Handle interface creation - configure new interface on device."""
        self.logger.info(f"Configuring new interface {interface.name} on device {device.name}")
        
        try:
            config_commands = self._build_interface_config(interface)
            
            if commit:
                self._push_config_to_device(device, config_commands)
                self.logger.success(f"Successfully configured interface {interface.name} on {device.name}")
            else:
                self.logger.info(f"Dry-run mode - would configure:\n{chr(10).join(config_commands)}")
        
        except Exception as e:
            self.logger.error(f"Failed to configure interface {interface.name}: {str(e)}")

    def _handle_interface_update(self, interface, device, changed_data, commit):
        """Handle interface update - reconfigure interface on device."""
        self.logger.info(f"Updating interface {interface.name} on device {device.name}")
        self.logger.info(f"Changed fields: {list(changed_data.keys())}")
        
        # Only push config if relevant fields changed
        relevant_fields = {'description', 'enabled', 'mode', 'mtu', 'type'}
        if not any(field in changed_data for field in relevant_fields):
            self.logger.info("No relevant fields changed - skipping device update")
            return
        
        try:
            config_commands = self._build_interface_config(interface)
            
            if commit:
                self._push_config_to_device(device, config_commands)
                self.logger.success(f"Successfully updated interface {interface.name} on {device.name}")
            else:
                self.logger.info(f"Dry-run mode - would update:\n{chr(10).join(config_commands)}")
        
        except Exception as e:
            self.logger.error(f"Failed to update interface {interface.name}: {str(e)}")

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
        # primary is an IPAddress object, primary.address is an IPNetwork object
        host = str(primary.address.ip) if hasattr(primary.address, 'ip') else str(primary.address).split('/')[0]
        
        # Get platform-specific settings
        platform_name = device.platform.name.lower() if device.platform else ""
        
        # Currently only supporting Arista EOS via pyeapi
        if 'arista' not in platform_name and 'eos' not in platform_name:
            self.logger.warning(f"Platform {platform_name} not supported for automatic config - only Arista EOS")
            return
        
        # Connect and push config
        self.logger.debug(f"Connecting to {device.name} at {host}")
        
        try:
            connection = pyeapi.connect(
                transport="https",
                host=host,
                username="admin",
                password="admin",
                port=443,
            )
            node = pyeapi.client.Node(connection)
            
            # Push configuration
            node.config(config_commands)
            
            # Save configuration
            node.enable("write memory")
            
            self.logger.debug(f"Configuration pushed successfully to {device.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to connect/configure {device.name}: {str(e)}")
            raise


register_jobs(InterfaceJobHookReceiver)

