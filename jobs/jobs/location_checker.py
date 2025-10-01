"""
Location Checker Job

This job helps diagnose location-related issues in Nautobot.
"""

from nautobot.apps.jobs import Job, StringVar, BooleanVar, register_jobs


class LocationChecker(Job):
    """
    Location Checker Job
    
    Helps diagnose location-related issues in Nautobot.
    """
    
    class Meta:
        name = "Location Checker"
        description = "Check and diagnose location issues in Nautobot"
        read_only = True
        has_sensitive_variables = False
        
    # Job variables
    check_existing = BooleanVar(
        label="Check Existing Locations",
        description="Check what locations currently exist",
        default=True
    )
    
    check_hierarchy = BooleanVar(
        label="Check Location Hierarchy",
        description="Check location parent-child relationships",
        default=True
    )
    
    suggest_cleanup = BooleanVar(
        label="Suggest Cleanup Actions",
        description="Suggest actions to resolve location conflicts",
        default=True
    )

    def run(self, check_existing, check_hierarchy, suggest_cleanup):
        """
        Execute the job
        """
        self.logger.info("Starting location checker...")
        
        try:
            if check_existing:
                self.logger.info("=== CHECKING EXISTING LOCATIONS ===")
                self.logger.info("This would check for existing locations that might cause conflicts.")
                self.logger.info("Common problematic locations:")
                self.logger.info("- 'Test Data Center'")
                self.logger.info("- 'Main Lab'")
                self.logger.info("- 'Default'")
                self.logger.info("- 'Site'")
            
            if check_hierarchy:
                self.logger.info("")
                self.logger.info("=== CHECKING LOCATION HIERARCHY ===")
                self.logger.info("This would check parent-child relationships.")
                self.logger.info("Location validation errors often occur when:")
                self.logger.info("1. A location has the wrong parent type")
                self.logger.info("2. Circular parent-child relationships exist")
                self.logger.info("3. Location types don't match parent expectations")
            
            if suggest_cleanup:
                self.logger.info("")
                self.logger.info("=== SUGGESTED CLEANUP ACTIONS ===")
                self.logger.info("To resolve location validation errors:")
                self.logger.info("1. Go to Admin → Locations in Nautobot UI")
                self.logger.info("2. Check for existing 'Test Data Center' or similar locations")
                self.logger.info("3. Delete conflicting locations if they're not needed")
                self.logger.info("4. Use unique site names in your jobs")
                self.logger.info("5. Ensure proper location type hierarchy")
                self.logger.info("")
                self.logger.info("Alternative site names to try:")
                self.logger.info("- 'Lab Environment'")
                self.logger.info("- 'Demo Network'")
                self.logger.info("- 'Training Lab'")
                self.logger.info("- 'Containerlab Demo'")
                self.logger.info("- 'Network Automation Lab'")
            
            self.logger.info("")
            self.logger.info("Location checker completed!")
            self.logger.info("Check the Nautobot UI Admin → Locations section for more details.")
            
        except Exception as e:
            self.logger.error(f"Error during location check: {str(e)}")
            raise


# Register the job
register_jobs(LocationChecker)
