"""Job to render device configuration from config context template."""

from nautobot.apps.jobs import Job, ObjectVar, register_jobs
from nautobot.dcim.models import Device
from jinja2 import Template
from pathlib import Path

name = "LAB Setup"

class RenderConfigFromContext(Job):
    """Render device configuration using config context data."""

    class Meta:
        name = "Render Config from Context"
        description = "Generate device configuration using config context and Jinja2 template"
        has_sensitive_variables = False

    device = ObjectVar(
        model=Device,
        description="Device to generate configuration for",
        required=True
    )

    def run(self, device):
        """Render configuration for the selected device."""
        
        # Get the device's config context
        config_context = device.get_config_context()
        
        if not config_context:
            self.logger.warning(f"No config context found for device {device.name}")
            return
        
        # Load the Jinja2 template
        template_path = Path(__file__).parent.parent.parent / "templates" / "base_config_from_context.j2"
        
        if not template_path.exists():
            self.logger.error(f"Template not found at {template_path}")
            return
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Create Jinja2 template
        template = Template(template_content)
        
        # Render the template with device and config context data
        rendered_config = template.render(
            device=device,
            **config_context  # Unpack all config context data as variables
        )
        
        # Log the rendered configuration
        self.logger.info(f"Rendered configuration for {device.name}:")
        self.logger.info("=" * 80)
        for line in rendered_config.split('\n'):
            self.logger.info(line)
        self.logger.info("=" * 80)
        
        # Add demo code for: 
        # - Save to a file
        # - Push to the device
        # - Store as a configuration backup
        # - Compare with running config
        
        self.logger.success(f"Configuration rendered successfully for {device.name}")
        
        return rendered_config


register_jobs(RenderConfigFromContext)

