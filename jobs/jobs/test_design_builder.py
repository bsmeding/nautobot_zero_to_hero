"""Design Builder Lab Setup Job"""

from nautobot.apps.jobs import register_jobs
from nautobot_design_builder.design_job import DesignJob
from pathlib import Path


class DesignBuilderLabSetup(DesignJob):
    """Design builder job to populate Nautobot with Containerlab lab topology using YAML design files."""
    has_sensitive_variables = False

    class Meta:
        name = "Design Builder Lab Setup"
        description = "Populate Nautobot with Containerlab lab topology using Design Builder (includes config contexts)"
        commit_default = False
        design_files = [
            Path(__file__).parent / "design_builder" / "lab_setup" / "lab_setup.yaml"
        ]
        version = "1.0.0"


register_jobs(DesignBuilderLabSetup)

