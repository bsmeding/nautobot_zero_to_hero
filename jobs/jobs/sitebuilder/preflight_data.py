"""
Pre-flight Data Job

Creates location types, custom fields, and locations from simple
config variables at the top of this file. Nautobot v2 compatible.
"""

from django.contrib.contenttypes.models import ContentType
from django.db import transaction

# v2 imports
from nautobot.apps.jobs import Job, BooleanVar, register_jobs

from nautobot.dcim.models import Location, LocationType
from nautobot.extras.models import CustomField, CustomFieldChoice, Status


# =========================
# ======= CONFIG ==========
# =========================

# Default Status name to apply to created Location records
DEFAULT_LOCATION_STATUS_NAME = "Active"

# Toggle whether to create locations (instances) after creating types
PRECREATE_LOCATIONS = True

# LocationTypes to ensure exist. You can now add `content_types` to each item,
# listing the Django content types (as "app_label.model") allowed at that type.
LOCATION_TYPES = [
    {
        "name": "Region",
        "nestable": True,
        "description": "Regional grouping",
        # Usually regions don't host objects, so leave content_types empty or omit
        # "content_types": []
    },
    {
        "name": "Site",
        "nestable": True,
        "description": "Site location type for Nautobot sites",
        "content_types": [
            "dcim.rack",
            "dcim.device",
            "dcim.powerpanel",
            "dcim.powerfeed",
            # If your environment uses IPAM objects at a site, include these:
            "ipam.prefix",
            "ipam.vlan",
        ],
    },
]

# Locations (instances) to create (if PRECREATE_LOCATIONS is True).
LOCATIONS = [
    {"name": "US East",        "type": "Region", "description": "Region: US East"},
    {"name": "US West",        "type": "Region", "description": "Region: US West"},
    {"name": "Europe West",    "type": "Region", "description": "Region: Europe West"},
    {"name": "Europe Central", "type": "Region", "description": "Region: Europe Central"},
    {"name": "Asia Pacific",   "type": "Region", "description": "Region: Asia Pacific"},
    # Example child:
    # {"name": "SFO-01", "type": "Site", "parent": {"name": "US West", "type": "Region"}, "description": "San Francisco #1"},
]

# Custom field definitions for locations (v2 uses `key`, not `name`)
CUSTOM_FIELDS = [
    {
        "key": "site_slug",
        "label": "Site Slug",
        "type": "text",
        "required": True,
        "description": "The slug for the site",
        "weight": 100,
        "validation_regex": "^[a-z0-9-]+$",
    },
    {
        "key": "site_code",
        "label": "Site Code",
        "type": "text",
        "required": True,
        "description": "Site code identifier (migrating from site_slug)",
        "weight": 200,
        "validation_regex": "^[A-Z0-9-]+$",
    },
    {
        "key": "site_config_type",
        "label": "Site Config Selector",
        "type": "select",
        "required": False,
        "description": "The type of configuration to use for the site",
        "weight": 300,
        "choices": [
            {"value": "v1", "label": "v1"},
            {"value": "v2.1", "label": "v2.1"},
            {"value": "v2.3", "label": "v2.3"},
        ],
    },
    {
        "key": "site_environment",
        "label": "Site Environment",
        "type": "select",
        "required": True,
        "description": "The environment type for the site",
        "weight": 400,
        "choices": [
            {"value": "production", "label": "Production"},
            {"value": "staging", "label": "Staging"},
            {"value": "development", "label": "Development"},
            {"value": "testing", "label": "Testing"},
        ],
    },
]


class PreflightDataJob(Job):
    """Create required location types, custom fields, and locations from config."""

    class Meta:
        name = "Pre-flight Data Setup"
        description = "Create location types, custom fields, and locations from config"
        has_sensitive_variables = False

    show_debug = BooleanVar(
        description="Show detailed debug information during job execution",
        default=False,
    )

    dry_run = BooleanVar(
        description="Perform a dry run without making any changes",
        default=False,
    )

    # v2: accept named form vars (and optional commit)
    def run(self, show_debug=False, dry_run=False, commit=None):
        """Execute the pre-flight data setup."""
        if dry_run:
            self.logger.info("DRY RUN MODE - No changes will be made")

        try:
            with transaction.atomic():
                # 1) Location Types (+ allowed content types)
                self.logger.info("Ensuring location types (and allowed content types) exist...")
                self._ensure_location_types(LOCATION_TYPES, show_debug, dry_run)

                # 2) Custom Fields
                self.logger.info("Ensuring custom fields exist...")
                self._ensure_custom_fields(CUSTOM_FIELDS, show_debug, dry_run)

                # 3) Locations (instances)
                if PRECREATE_LOCATIONS:
                    self.logger.info("Ensuring locations exist...")
                    self._ensure_locations(LOCATIONS, show_debug, dry_run)
                else:
                    if show_debug:
                        self.logger.debug("PRECREATE_LOCATIONS is False; skipping instance creation")

                msg = (
                    "Pre-flight data setup dry run completed - no changes made"
                    if dry_run
                    else "Pre-flight data setup completed successfully"
                )
                (getattr(self.logger, "success", self.logger.info))(msg)
                return msg

        except Exception as e:
            (getattr(self.logger, "failure", self.logger.error))(f"Failed to setup pre-flight data: {e}")
            raise

    # ---- helpers ----

    def _status_for_locations(self, name=DEFAULT_LOCATION_STATUS_NAME):
        """Ensure a Status exists with the given name, is associated to Location, and return it."""
        status = Status.objects.filter(name__iexact=name).first()
        if not status:
            color_map = {"active": "#28a745", "planned": "#2196f3", "deprecated": "#9e9e9e"}
            status = Status.objects.create(name=name, color=color_map.get(name.lower(), "#28a745"))
        ct = ContentType.objects.get_for_model(Location)
        if ct not in status.content_types.all():
            status.content_types.add(ct)
        return status

    def _ensure_location_types(self, specs, show_debug=False, dry_run=False):
        """Ensure each LocationType exists and add any specified allowed content types."""
        for spec in specs:
            name = spec["name"]
            if dry_run:
                self.logger.info(f"Would ensure LocationType '{name}' exists")
                if spec.get("content_types"):
                    self.logger.info(f"  Would allow content types on '{name}': {spec['content_types']}")
                continue

            lt, created = LocationType.objects.get_or_create(
                name=name,
                defaults={
                    "description": spec.get("description", ""),
                    "nestable": bool(spec.get("nestable", True)),
                },
            )
            if created:
                self.logger.info(f"Created LocationType: {name}")
            elif show_debug:
                self.logger.debug(f"LocationType '{name}' already exists")

            # Add allowed content types if provided
            for label in spec.get("content_types", []):
                ct = self._resolve_content_type_label(label, show_debug=show_debug)
                if not ct:
                    continue
                if ct not in lt.content_types.all():
                    lt.content_types.add(ct)
                    if show_debug:
                        self.logger.debug(f"  Added allowed content type '{label}' to LocationType '{name}'")

    def _resolve_content_type_label(self, label, show_debug=False):
        """
        Resolve "app_label.ModelName" or "app_label.model" to a ContentType.
        Returns None and logs a warning if not found.
        """
        try:
            if "." not in label:
                raise ValueError("Use 'app_label.ModelName' format, e.g., 'dcim.Device'")
            app_label, model = label.split(".", 1)
            model = model.lower()
            # Accept either CamelCase or lowercase input on the right side
            ct = ContentType.objects.get(app_label=app_label, model=model)
            return ct
        except ContentType.DoesNotExist:
            try:
                # second attempt: if they passed CamelCase, Django stores lower
                ct = ContentType.objects.get(app_label=app_label, model=model.lower())
                return ct
            except Exception:
                self.logger.warning(f"Unknown content type '{label}' — skipping")
                return None
        except Exception as e:
            if show_debug:
                self.logger.debug(f"Failed to resolve content type '{label}': {e}")
            self.logger.warning(f"Unknown content type '{label}' — skipping")
            return None

    def _ensure_custom_fields(self, fields, show_debug=False, dry_run=False):
        """Ensure required custom fields exist (v2: key=..., no validation_error_message)."""
        location_ct = ContentType.objects.get_for_model(Location)

        for field_def in fields:
            if dry_run:
                self.logger.info(f"Would ensure custom field: {field_def['key']}")
                if field_def["type"] == "select" and field_def.get("choices"):
                    for ch in field_def["choices"]:
                        self.logger.info(f"  Would ensure choice '{ch['value']}' for field {field_def['key']}")
                continue

            defaults = {
                "label": field_def["label"],
                "type": field_def["type"],
                "required": field_def["required"],
                "description": field_def["description"],
                "weight": field_def["weight"],
            }
            if field_def.get("validation_regex"):
                defaults["validation_regex"] = field_def["validation_regex"]

            cf, created = CustomField.objects.get_or_create(key=field_def["key"], defaults=defaults)
            if created:
                self.logger.info(f"Created custom field: {field_def['key']}")
            elif show_debug:
                self.logger.debug(f"Custom field already exists: {field_def['key']}")

            if location_ct not in cf.content_types.all():
                cf.content_types.add(location_ct)
                self.logger.info(f"Associated custom field {field_def['key']} with Location model")

            if field_def["type"] == "select" and field_def.get("choices"):
                for ch in field_def["choices"]:
                    _, ch_created = CustomFieldChoice.objects.get_or_create(
                        custom_field=cf, value=ch["value"], defaults={"weight": ch.get("weight", 100)}
                    )
                    if ch_created:
                        self.logger.info(f"Created choice '{ch['value']}' for field {field_def['key']}")
                    elif show_debug:
                        self.logger.debug(f"Choice '{ch['value']}' already exists for field {field_def['key']}")

    def _resolve_parent(self, parent_spec, active_status, show_debug=False, dry_run=False):
        """Find or create the parent Location if a parent spec is provided."""
        if not parent_spec:
            return None

        parent_type = LocationType.objects.get(name=parent_spec["type"])
        parent_name = parent_spec["name"]

        if dry_run:
            self.logger.info(f"  Would ensure parent Location '{parent_name}' ({parent_type.name}) exists")
            return None

        parent, created = Location.objects.get_or_create(
            name=parent_name,
            location_type=parent_type,
            defaults={
                "description": parent_spec.get("description", f"Auto-created parent: {parent_name}"),
                "status_id": active_status.id,
            },
        )
        if created and show_debug:
            self.logger.debug(f"  Created parent Location '{parent_name}' ({parent_type.name})")
        return parent

    def _ensure_locations(self, locations, show_debug=False, dry_run=False):
        """Ensure each Location instance exists per `locations` config."""
        active_status = self._status_for_locations(DEFAULT_LOCATION_STATUS_NAME)

        for item in locations:
            lt = LocationType.objects.get(name=item["type"])
            name = item["name"]
            parent_spec = item.get("parent")
            status_name = item.get("status_name", DEFAULT_LOCATION_STATUS_NAME)

            # Status per-location (fallback to default)
            status_obj = self._status_for_locations(status_name)

            if dry_run:
                path = f"{parent_spec['name']} / {name}" if parent_spec else name
                self.logger.info(f"Would ensure Location '{path}' ({lt.name}) exists with status '{status_obj.name}'")
                continue

            parent = self._resolve_parent(parent_spec, active_status, show_debug=show_debug, dry_run=dry_run)

            loc, created = Location.objects.get_or_create(
                name=name,
                location_type=lt,
                parent=parent,
                defaults={
                    "description": item.get("description", f"{lt.name}: {name}"),
                    "status_id": status_obj.id,
                },
            )
            if created:
                self.logger.info(f"Created Location '{name}' ({lt.name})")
            else:
                if not loc.status_id:
                    loc.status_id = status_obj.id
                    loc.save()
                    if show_debug:
                        self.logger.debug(f"Set missing status on Location '{name}' → {status_obj.name}")
                elif show_debug:
                    self.logger.debug(f"Location already exists: '{name}' ({lt.name})")


# Register the job
register_jobs(PreflightDataJob)
