"""Lab Setup Job for Containerlab Topology."""

from nautobot.apps.jobs import register_jobs

from nautobot_design_builder.design_job import DesignJob

from ..initial_data.context import InitialDesignContext


class LabSetup(DesignJob):
    """Initialize the database with lab setup data for Containerlab topology."""
    has_sensitive_variables = False

    class Meta:
        """Metadata needed to start the lab setup"""
        name = "Lab Setup"
        commit_default = False
        design_files = [
            "lab_setup.yaml",
        ]
        context_class = InitialDesignContext
        version = "1.0.0"
        description = "Create lab setup"
        docs = """This script creates a lab setup for Nautobot to use with Lab for Blog posts in the NetDevOps.it series"""


register_jobs(LabSetup)