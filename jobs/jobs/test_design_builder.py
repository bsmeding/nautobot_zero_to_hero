"""Test Design Builder Job"""

from nautobot.apps.jobs import register_jobs
from nautobot_design_builder.design_job import DesignJob


class TestDesignBuilder(DesignJob):
    """Test job to verify design builder functionality."""
    has_sensitive_variables = False

    class Meta:
        name = "Test Design Builder"
        description = "Test job for design builder"
        commit_default = False
        design_files = []
        version = "1.0.0"


register_jobs(TestDesignBuilder)

