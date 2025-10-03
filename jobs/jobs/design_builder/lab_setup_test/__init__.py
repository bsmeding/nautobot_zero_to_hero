from nautobot.apps.jobs import register_jobs
from nautobot_design_builder.design_job import DesignJob

# Create a test job that uses the simplified YAML
class LabSetupTest(DesignJob):
    class Meta:
        name = "Lab Setup Test"
        description = "Test version of lab setup to isolate Design Builder issues"
        design_file = "lab_setup_test.yaml"
        has_sensitive_variables = False

register_jobs(LabSetupTest)
