"""Initial data required for core sites."""

from nautobot.apps.jobs import register_jobs

from nautobot_design_builder.design_job import DesignJob

from .context import InitialDesignContext


class InitialData(DesignJob):
    """Initialize the database with default values needed by the site designs."""
    has_sensitive_variables = False
    # routers_per_site = IntegerVar(min_value=1, max_value=6, default=2)

    class Meta:
        """Metadata needed to implement the backbone site design."""

        name = "Initial Data"
        commit_default = False
        design_files = [
            # Organization (01xx) - Location, Location Types, Racks, Rack Groups, Tenants, Tenant Groups, Contacts, Teams, Dynamic Groups, Tags, Statuses, Roles
            "designs/0101_locations.j2",             # Locations, Location Types
            # "designs/0103_tenant_groups.j2",         # Tenant Groups, Tenants
            "designs/0104_roles.j2",                 # Roles
            # "designs/0102_racks.j2",                 # Racks
            "designs/0105_tags.j2",                  # Tags
            "designs/0106_statuses.j2",              # Statuses

            "designs/0109_manufacturers.j2",         # Manufacturers (needed for cloud providers and devices)
            "designs/0302_platforms.j2",             # Platforms (needed for devices)
            "designs/0303_device_types.j2",          # Device Types (needed for devices)
            "designs/0501_prefixes.j2",              # Prefixes (needed for devices)
            "designs/1101_git_repositories.j2",      # Git Repositories (needed for devices)


        ]
        context_class = InitialDesignContext
        version = "1.0.0"
        description = "Create default data"
        docs = """This script creates comprehensive default data for Nautobot to use with Lab for Blog posts in the NetDevOps.it series

        """


register_jobs(InitialData)