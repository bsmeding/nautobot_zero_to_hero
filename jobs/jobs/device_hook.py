from nautobot.apps.jobs import register_jobs, BooleanVar
from nautobot.extras.jobs import JobHookReceiver
from nautobot.dcim.models import Device

name = "Lifecycle hooks"

class DeviceJobHookReceiver(JobHookReceiver):
    class Meta:
        name = "Device Configuration Hook"
        description = "Automatically provision device when created/updated in Nautobot"
        object_type = Device  # Target model for this Job Hook Receiver
        enabled = False  # Set to True to enable automatic provisioning
        
    # Add configuration options for the hook
    auto_provision_on_create = BooleanVar(
        description="Automatically provision device when created",
        default=False,
        required=False,
    )
    
    auto_provision_on_update = BooleanVar(
        description="Automatically provision device when updated",
        default=True,
        required=False,
    )
    
    dry_run = BooleanVar(
        description="Run provisioning in dry-run mode (preview only)",
        default=True,
        required=False,
    )

    def run(self, auto_provision_on_create=False, auto_provision_on_update=True, dry_run=True, **kwargs):
        """Entry point for Job Hook execution.

        The Job Hook system passes event context via kwargs. Common keys include:
        - action: one of "created", "updated", "deleted"
        - object_pk: the primary key of the Device
        - object_repr: string representation
        - changed_data: dict of changed fields (for updates)
        - user: username (if available)
        """
        # Get ObjectChange object from kwargs
        object_change = kwargs.get("object_change")
        
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
            object_repr = str(object_change.changed_object) if object_change.changed_object else f"Device {object_change.changed_object_id}"
            changed_data = object_change.object_data_v2 or {}

        self.logger.debug(f"action={action}, object_pk={object_pk}, object_repr={object_repr}")

        # Check if action is valid
        if not action:
            self.logger.warning("Device hook triggered but no action provided")
            self.logger.warning("Available kwargs keys: " + str(list(kwargs.keys())))
            return

        self.logger.info("=" * 80)
        self.logger.info(f"Device Hook Triggered: {action.upper()}")
        self.logger.info(f"Device: {object_repr} ({object_pk})")
        self.logger.info("=" * 80)

        # Get the device object
        try:
            device = Device.objects.get(pk=object_pk)
        except Device.DoesNotExist:
            self.logger.error(f"Device with PK {object_pk} not found")
            return

        # Handle different actions
        if action in ["created", "create"]:
            self.logger.success(f"Device created: {object_repr}")
            
            if auto_provision_on_create:
                self.logger.info("Auto-provision on create is enabled")
                self._provision_device(device, dry_run)
            else:
                self.logger.info("Auto-provision on create is disabled. Set 'auto_provision_on_create' to enable.")
        
        elif action in ["updated", "update"]:
            self.logger.success(f"Device updated: {object_repr}")
            
            # For ObjectChange, get changed fields differently
            if object_change:
                # Get pre and post change data to determine what changed
                pre_change = object_change.object_data or {}
                post_change = object_change.object_data_v2 or {}
                changed_fields = [key for key in post_change.keys() if pre_change.get(key) != post_change.get(key)]
            else:
                # Old-style changed_data
                changed_fields = list(changed_data.keys())
            
            self.logger.info(f"Changed fields: {changed_fields}")
            
            # Check if configuration-relevant fields were changed, if so we maybe need to re-provision the device
            config_relevant_fields = [
                'name',           # Hostname change
                'primary_ip4',    # IP address change
                'platform',       # Platform change
                'role',           # Role change
                'location',       # Location change
                'status',         # Status change
            ]
            
            relevant_changes = [field for field in changed_fields if field in config_relevant_fields]
            
            if relevant_changes:
                self.logger.info(f"Configuration-relevant fields changed: {relevant_changes}")
                
                if auto_provision_on_update:
                    # When auto-provision on update is enabled, run the provisioning job (device get latest corrrect intended config automatically)
                    self.logger.info("Auto-provision on update is enabled")
                    # Run provisioning job, sent dry_run from this Job to the provision_device job
                    self._provision_device(device, dry_run)
                else:
                    self.logger.info("Auto-provision on update is disabled. Set 'auto_provision_on_update' to enable.")
            else:
                self.logger.info("No configuration-relevant fields changed. Skipping provisioning.")
        
        elif action in ["deleted", "delete"]:
            self.logger.success(f"Device deleted: {object_repr}")
            self.logger.info("No action needed for deleted devices")
        
        else:
            self.logger.info(f"Unknown action '{action}' for {object_repr}")

    def _provision_device(self, device, dry_run=True):
        """Trigger the provision device job."""
        self.logger.info("-" * 80)
        self.logger.info("Triggering Device Provisioning Job...")
        
        # Validate device is ready for provisioning
        if not self._validate_device_ready(device):
            self.logger.warning("Device is not ready for provisioning. Skipping.")
            return
        
        try:
            # Import the ProvisionDevice job
            from .provision_device import ProvisionDevice
            
            # Create an instance of the provision job
            provision_job = ProvisionDevice()
            
            # Copy logger context
            provision_job.logger = self.logger
            
            # Run the provision job
            self.logger.info(f"Running provision job for {device.name} (dry_run={dry_run})...")
            
            provision_job.run(
                device=device,
                dry_run=dry_run,
                replace_config=False,  # Always use merge mode for auto-provisioning
                commit_changes=True,
                show_debug=False  # Keep logs clean for automatic provisioning
            )
            
            self.logger.success(f"Provision job completed for {device.name}")
            
        except ImportError as e:
            self.logger.error(f"Could not import ProvisionDevice job: {e}")
            self.logger.error("Ensure provision_device.py is in the same directory")
        
        except Exception as e:
            self.logger.error(f"Error running provision job: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def _validate_device_ready(self, device):
        """Check if device is ready for provisioning."""
        
        # Check if device has platform
        if not device.platform:
            self.logger.warning(f"Device {device.name} has no platform configured")
            return False
        
        # Check if platform has NAPALM driver
        if not device.platform.napalm_driver:
            self.logger.warning(
                f"Platform {device.platform.name} has no NAPALM driver configured"
            )
            return False
        
        # Check if device has primary IP
        if not device.primary_ip4:
            self.logger.warning(f"Device {device.name} has no primary IPv4 address")
            return False
        
        # Check if device status is active
        if device.status and device.status.name not in ['Active', 'Planned', 'Staged']:
            self.logger.warning(
                f"Device {device.name} status is '{device.status.name}'. "
                "Only Active, Planned, or Staged devices will be provisioned."
            )
            return False
        
        self.logger.success(f"Device {device.name} is ready for provisioning")
        return True


register_jobs(DeviceJobHookReceiver)


