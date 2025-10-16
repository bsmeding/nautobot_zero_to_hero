from nautobot.apps.jobs import register_jobs
from nautobot.extras.jobs import JobHookReceiver
from nautobot.dcim.models import Device

name = "Lifecycle hooks"

class DeviceJobHookReceiver(JobHookReceiver):
    class Meta:
        name = "Device Configuration Hook"
        description = "Automatically configure device interfaces when created/updated/deleted in Nautobot"
        object_type = Device  # Target model for this Job Hook Receiver
        enabled = False  # Disabled for now

    def run(self, commit, **kwargs):
        """Entry point for Job Hook execution.

        The Job Hook system passes event context via kwargs. Common keys include:
        - action: one of "created", "updated", "deleted"
        - object_pk: the primary key of the Device
        - object_repr: string representation
        - changed_data: dict of changed fields (for updates)
        - user: username (if available)
        """
        action = kwargs.get("action")
        object_pk = kwargs.get("object_pk")
        object_repr = kwargs.get("object_repr")
        changed_data = kwargs.get("changed_data", {})

        # Placeholder for future logic – branch by action
        if action == "created":
            self.logger.success(f"Device created: {object_repr} ({object_pk})")
        elif action == "updated":
            self.logger.success(f"Device updated: {object_repr} ({object_pk}); changes={changed_data}")
        elif action == "deleted":
            self.logger.success(f"Device deleted: {object_repr} ({object_pk})")
        else:
            self.logger.info(f"Device action '{action}' for {object_repr} ({object_pk})")


register_jobs(DeviceJobHookReceiver)


