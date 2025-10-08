# Nautobot Development Environment

This is a comprehensive Docker Compose setup for Nautobot v2 with local development capabilities for configuration, plugins, and custom jobs.

## About Nautobot

Nautobot serves as a **Single Source of Truth (SSoT)** for managing network infrastructure. It provides a centralized repository for device information, configuration management, compliance checks, automation, and vulnerability reporting. Nautobot can also synchronize with various third-party tools to enhance automation and management.

For more information about Nautobot's capabilities as the ultimate network CMDB, check out: [Nautobot: The Single Source of Truth (SSoT) for Network Automation](https://netdevops.it/nautobot_the_ultimate_network_cmdb/)

## Features

- **Local Configuration Editing**: Edit `nautobot_config.py` locally
- **Plugin Development**: Pre-configured with 12+ popular Nautobot plugins
- **Local Job Development**: Develop custom jobs in the `./jobs/` directory
- **Automatic Setup**: Helper script to copy files from container if needed
- **Full Stack**: Includes PostgreSQL, Redis, and Celery workers
- **Production Ready**: Comprehensive configuration for enterprise use

## Getting Started

### Clone the Repository

```bash
git clone https://github.com/bsmeding/nautobot_development_environment.git
cd nautobot_development_environment
```

## Directory Structure

```
.
├── docker compose.yml          # Main Docker Compose configuration
├── .env                       # Environment variables (create this file)
├── get_config.sh              # Helper script to copy files from container
├── README.md                  # Comprehensive documentation
├── .gitignore                 # Git ignore rules
├── config/
│   └── nautobot_config.py     # Nautobot configuration with plugins
└── jobs/
    └── jobs/                  # Custom jobs directory
        ├── __init__.py        # Makes jobs a Python package
        └── example_job.py     # Example job template
```

## Quick Start

1. **First time setup** (if files don't exist locally):
   ```bash
   ./get_config.sh
   ```

2. **Optional: Create .env file for customization**:
   ```bash
   # Create .env file with default values
   cat > .env << EOF
   NAUTOBOT_PORT=8080
   POSTGRES_DB=nautobot
   POSTGRES_USER=nautobot
   POSTGRES_PASSWORD=nautobotpassword
   SUPERUSER_NAME=admin
   SUPERUSER_PASSWORD=admin
   NAUTOBOT_CONTAINER_NAME=nautobot
   POSTGRES_CONTAINER_NAME=postgres
   REDIS_CONTAINER_NAME=redis
   CELERY_BEAT_CONTAINER_NAME=nautobot_celery_beat
   CELERY_WORKER_CONTAINER_NAME=nautobot_celery_worker_1
   # Internal service discovery (matches container names)
   NAUTOBOT_DB_HOST=postgres
   NAUTOBOT_REDIS_HOST=redis
   EOF
   ```

3. **Start Nautobot**:
   ```bash
   docker compose up -d
   ```

4. **Access Nautobot**:
   - URL: http://localhost:${NAUTOBOT_PORT:-8080}
   - Username: `${SUPERUSER_NAME:-admin}`
   - Password: `${SUPERUSER_PASSWORD:-admin}`

### Environment Configuration (.env)

For easy customization, create a `.env` file in the project root:

```bash
# .env
NAUTOBOT_PORT=8080
POSTGRES_DB=nautobot
POSTGRES_USER=nautobot
POSTGRES_PASSWORD=nautobotpassword
SUPERUSER_NAME=admin
SUPERUSER_PASSWORD=admin
NAUTOBOT_CONTAINER_NAME=nautobot
POSTGRES_CONTAINER_NAME=postgres
REDIS_CONTAINER_NAME=redis
CELERY_BEAT_CONTAINER_NAME=nautobot_celery_beat
CELERY_WORKER_CONTAINER_NAME=nautobot_celery_worker_1
# Internal service discovery (matches container names)
NAUTOBOT_DB_HOST=postgres
NAUTOBOT_REDIS_HOST=redis
```

**Benefits:**
- **Easy Customization**: Change ports, credentials, and container names without editing docker compose.yml
- **Version Control Safe**: Add `.env` to `.gitignore` to keep sensitive data out of version control
- **Default Values**: If `.env` doesn't exist, Docker Compose uses built-in defaults
- **Consistent Approach**: Same method used for both single and multi-customer setups

## Local Development

### Configuration
- Edit `./config/nautobot_config.py` locally
- Changes are immediately reflected in the container
- Restart containers after major config changes: `docker compose restart`

### Plugin Configuration

This setup includes pre-configured plugins for advanced network automation. The plugins are configured in `./config/nautobot_config.py`:

#### Available Plugins

```python
PLUGINS = [
    "nautobot_bgp_models",              # BGP routing management
    "nautobot_capacity_metrics",        # Capacity monitoring
    "nautobot_data_validation_engine",  # Data validation and compliance
    "nautobot_design_builder",          # Network design patterns
    "nautobot_device_lifecycle_mgmt",   # Device lifecycle management
    "nautobot_device_onboarding",       # Automated device onboarding
    "nautobot_firewall_models",         # Firewall rule management
    "nautobot_floor_plan",              # Physical layout visualization
    "nautobot_golden_config",           # Configuration management
    "nautobot_plugin_nornir",           # Network automation integration
    "nautobot_secrets_providers",       # Secrets management
    "nautobot_ssot",                    # Single Source of Truth integrations
]
```

#### Plugin Configuration Example

```python
PLUGINS_CONFIG = {
    'nautobot_ssot': {
        'enable_sso': True,
        'enable_sync': True,
    },
    'nautobot_plugin_nornir': {
        'use_config_context': True,
        'connection_options': {
            'netmiko': {
                'extras': {
                    'global_delay_factor': 2,
                },
            },
            'napalm': {
                'extras': {
                    'optional_args': {
                        'global_delay_factor': 2,
                    },
                },
            },
        },
    },
    'nautobot_golden_config': {
        'enable_backup': True,
        'enable_compliance': True,
        'enable_intended': True,
        'enable_sotagg': True,
        'sot_agg_transposer': 'nautobot_golden_config.transposers.SoTaggTransposer',
        'backup_repository': 'backup_repo',
        'intended_repository': 'intended_repo',
        'jinja_repository': 'jinja_repo',
        'jinja_path_template': 'templates/{{ obj.platform.slug }}/{{ obj.platform.slug }}.j2',
        'backup_path_template': 'backup/{{ obj.platform.slug }}/{{ obj.name }}.cfg',
        'intended_path_template': 'intended/{{ obj.platform.slug }}/{{ obj.name }}.cfg',
        'backup_test_connectivity': False,
    },
    'nautobot_device_lifecycle_mgmt': {
        'enable_software': True,
        'enable_hardware': True,
        'enable_contract': True,
        'enable_provider': True,
        'enable_cve': True,
        'enable_software_image': True,
    },
    'nautobot_device_onboarding': {
        'default_platform': 'cisco_ios',
        'default_site': 'main',
        'default_role': 'switch',
        'default_status': 'active',
        'default_management_interface': 'GigabitEthernet0/0',
        'default_management_prefix_length': 24,
        'default_management_protocol': 'ssh',
        'default_management_port': 22,
        'default_management_timeout': 30,
        'default_management_verify_ssl': False,
        'default_management_auto_create_management_interface': True,
        'default_management_auto_create_management_ip': True,
    },
    'nautobot_data_validation_engine': {
        'enable_validation': True,
        'enable_compliance': True,
        'enable_reporting': True,
    },
    'nautobot_plugin_floorplan': {
        'enable_floorplan': True,
        'enable_rack_views': True,
        'enable_device_views': True,
    },
    'nautobot_firewall_models': {
        'enable_firewall_rules': True,
        'enable_firewall_zones': True,
        'enable_firewall_policies': True,
        'enable_firewall_services': True,
        'enable_firewall_addresses': True,
        'enable_firewall_address_groups': True,
        'enable_firewall_service_groups': True,
        'enable_firewall_rule_groups': True,
    },
    'nautobot_design_builder': {
        'enable_designs': True,
        'enable_design_instances': True,
        'enable_design_patterns': True,
    },
}
```

#### Adding New Plugins

To add a new plugin:

1. **Install the plugin** (if not already in the Docker image):
   ```bash
   docker exec nautobot pip install nautobot-your-plugin
   ```

2. **Add to PLUGINS list** in `./config/nautobot_config.py`:
   ```python
   PLUGINS = [
       # ... existing plugins ...
       "nautobot_your_plugin",
   ]
   ```

3. **Add configuration** to PLUGINS_CONFIG:
   ```python
   PLUGINS_CONFIG = {
       # ... existing config ...
       'nautobot_your_plugin': {
           'setting1': 'value1',
           'setting2': 'value2',
       },
   }
   ```

4. **Restart Nautobot**:
   ```bash
   docker compose restart nautobot
   ```

### Custom Jobs
- Add your custom jobs to `./jobs/jobs/`
- Each job should be a Python file with a class that inherits from `Job`
- See `./jobs/jobs/example_job.py` for a template
- Jobs are automatically loaded by Nautobot

### Job Development Workflow
1. Create a new Python file in `./jobs/jobs/`
2. Define your job class inheriting from `nautobot.extras.jobs.Job`
3. Implement the `run()` method
4. Save the file - it's automatically available in Nautobot
5. Test your job through the Nautobot web interface

## Services

- **nautobot**: Main Nautobot application (port 8080)
- **postgres**: PostgreSQL database
- **redis**: Redis cache and message broker
- **celery-beat**: Celery beat scheduler
- **celery-worker-1**: Celery worker for background tasks

## Troubleshooting

### If containers won't start:
1. Check if config file exists: `ls -la config/nautobot_config.py`
2. Run setup script: `./get_config.sh`
3. Check logs: `docker compose logs nautobot`

### If jobs aren't loading:
1. Ensure jobs directory structure is correct
2. Check that `__init__.py` exists in `jobs/jobs/`
3. Verify job class inherits from `Job`
4. Check Nautobot logs for import errors

## Environment Variables

Key environment variables are set in `docker compose.yml`:
- Database configuration
- Redis configuration
- Superuser credentials
- Security settings

## Notes

- The setup uses a custom Nautobot image: `bsmeding/nautobot:stable-py3.11`
- SSL is enabled but self-signed certificates are used
- Debug mode is enabled for development
- All data is persisted in Docker volumes

---

## Multi-Customer Development Setup (Optional)

This section explains how to set up multiple Nautobot development environments for different customers, allowing you to work on multiple projects simultaneously.

### Directory Structure for Multiple Customers

```
~/nautobot-projects/
├── customer-a/
│   ├── docker compose.yml
│   ├── config/
│   │   └── nautobot_config.py
│   ├── jobs/
│   │   └── jobs/
│   └── README.md
├── customer-b/
│   ├── docker compose.yml
│   ├── config/
│   │   └── nautobot_config.py
│   ├── jobs/
│   │   └── jobs/
│   └── README.md
└── customer-c/
    ├── docker compose.yml
    ├── config/
    │   └── nautobot_config.py
    ├── jobs/
    │   └── jobs/
    └── README.md
```

### Setup Process for Multiple Customers

#### Step 1: Create Customer Directory Structure

```bash
# Create main projects directory
mkdir ~/nautobot-projects
cd ~/nautobot-projects

# Clone the base environment for each customer
git clone https://github.com/bsmeding/nautobot_development_environment.git customer-a
git clone https://github.com/bsmeding/nautobot_development_environment.git customer-b
git clone https://github.com/bsmeding/nautobot_development_environment.git customer-c
```

#### Step 2: Customize Each Environment

For each customer, create a `.env` file to customize the environment:

**1. Create Customer-Specific .env Files**

```bash
# customer-a/.env
CUSTOMER_NAME=Customer A
NAUTOBOT_PORT=8080
POSTGRES_DB=nautobot_customer_a
POSTGRES_USER=nautobot_customer_a
POSTGRES_PASSWORD=customer_a_password
SUPERUSER_NAME=admin_customer_a
SUPERUSER_PASSWORD=customer_a_password
NAUTOBOT_CONTAINER_NAME=nautobot_customer_a
POSTGRES_CONTAINER_NAME=postgres_customer_a
REDIS_CONTAINER_NAME=redis_customer_a
CELERY_BEAT_CONTAINER_NAME=nautobot_celery_beat_customer_a
CELERY_WORKER_CONTAINER_NAME=nautobot_celery_worker_1_customer_a
# Internal service discovery (matches container names)
NAUTOBOT_DB_HOST=postgres_customer_a
NAUTOBOT_REDIS_HOST=redis_customer_a
```

```bash
# customer-b/.env
CUSTOMER_NAME=Customer B
NAUTOBOT_PORT=8081
POSTGRES_DB=nautobot_customer_b
POSTGRES_USER=nautobot_customer_b
POSTGRES_PASSWORD=customer_b_password
SUPERUSER_NAME=admin_customer_b
SUPERUSER_PASSWORD=customer_b_password
NAUTOBOT_CONTAINER_NAME=nautobot_customer_b
POSTGRES_CONTAINER_NAME=postgres_customer_b
REDIS_CONTAINER_NAME=redis_customer_b
CELERY_BEAT_CONTAINER_NAME=nautobot_celery_beat_customer_b
CELERY_WORKER_CONTAINER_NAME=nautobot_celery_worker_1_customer_b
# Internal service discovery (matches container names)
NAUTOBOT_DB_HOST=postgres_customer_b
NAUTOBOT_REDIS_HOST=redis_customer_b
```

```bash
# customer-c/.env
CUSTOMER_NAME=Customer C
NAUTOBOT_PORT=8082
POSTGRES_DB=nautobot_customer_c
POSTGRES_USER=nautobot_customer_c
POSTGRES_PASSWORD=customer_c_password
SUPERUSER_NAME=admin_customer_c
SUPERUSER_PASSWORD=customer_c_password
NAUTOBOT_CONTAINER_NAME=nautobot_customer_c
POSTGRES_CONTAINER_NAME=postgres_customer_c
REDIS_CONTAINER_NAME=redis_customer_c
CELERY_BEAT_CONTAINER_NAME=nautobot_celery_beat_customer_c
CELERY_WORKER_CONTAINER_NAME=nautobot_celery_worker_1_customer_c
# Internal service discovery (matches container names)
NAUTOBOT_DB_HOST=postgres_customer_c
NAUTOBOT_REDIS_HOST=redis_customer_c
```

**2. docker compose.yml Already Uses Environment Variables**

The `docker compose.yml` file is already configured to use environment variables with default values:

```yaml
# docker compose.yml (already configured with environment variables)
services:
  nautobot:
    ports:
      - "${NAUTOBOT_PORT:-8080}:8080"
    container_name: ${NAUTOBOT_CONTAINER_NAME:-nautobot}
    environment:
      - NAUTOBOT_SUPERUSER_NAME=${SUPERUSER_NAME:-admin}
      - NAUTOBOT_SUPERUSER_PASSWORD=${SUPERUSER_PASSWORD:-admin}
      - NAUTOBOT_DB_NAME=${POSTGRES_DB:-nautobot}
      # ... other environment variables

  postgres:
    container_name: ${POSTGRES_CONTAINER_NAME:-postgres}
    environment:
      - POSTGRES_DB=${POSTGRES_DB:-nautobot}
      - POSTGRES_USER=${POSTGRES_USER:-nautobot}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-nautobotpassword}

  redis:
    container_name: ${REDIS_CONTAINER_NAME:-redis}

  celery-beat:
    container_name: ${CELERY_BEAT_CONTAINER_NAME:-nautobot_celery_beat}

  celery-worker-1:
    container_name: ${CELERY_WORKER_CONTAINER_NAME:-nautobot_celery_worker_1}
```

**3. Customize Configuration**
```python
# customer-a/config/nautobot_config.py
# Customer-specific settings
ALLOWED_HOSTS = ['customer-a.example.com', 'localhost', '127.0.0.1']
SUPERUSER_NAME = 'admin_customer_a'
SUPERUSER_PASSWORD = 'customer_a_password'

# Customer-specific plugins
PLUGINS = [
    "nautobot_golden_config",      # Customer A needs config management
    "nautobot_device_onboarding",  # Customer A needs device onboarding
    # ... other plugins
]
```

#### Step 3: Customer-Specific Setup Scripts

Create customer-specific setup scripts that use the `.env` files:

```bash
# customer-a/setup_customer_a.sh
#!/bin/bash
echo "Setting up Customer A Nautobot Environment..."

# Load environment variables from .env file
source .env

# Run setup
./get_config.sh
docker compose up -d

echo "Customer A Nautobot available at: http://localhost:${NAUTOBOT_PORT}"
echo "Username: ${SUPERUSER_NAME}"
echo "Password: ${SUPERUSER_PASSWORD}"
```

```bash
# customer-b/setup_customer_b.sh
#!/bin/bash
echo "Setting up Customer B Nautobot Environment..."

# Load environment variables from .env file
source .env

# Run setup
./get_config.sh
docker compose up -d

echo "Customer B Nautobot available at: http://localhost:${NAUTOBOT_PORT}"
echo "Username: ${SUPERUSER_NAME}"
echo "Password: ${SUPERUSER_PASSWORD}"
```

#### Step 4: Management Scripts

Create a master management script:

```bash
# ~/nautobot-projects/manage_all.sh
#!/bin/bash

CUSTOMER_A_DIR="customer-a"
CUSTOMER_B_DIR="customer-b"
CUSTOMER_C_DIR="customer-c"

case "$1" in
    "start-all")
        echo "Starting all customer environments..."
        cd $CUSTOMER_A_DIR && docker compose up -d
        cd ../$CUSTOMER_B_DIR && docker compose up -d
        cd ../$CUSTOMER_C_DIR && docker compose up -d
        echo "All environments started!"
        echo "Customer A: http://localhost:$(cd $CUSTOMER_A_DIR && source .env && echo $NAUTOBOT_PORT)"
        echo "Customer B: http://localhost:$(cd $CUSTOMER_B_DIR && source .env && echo $NAUTOBOT_PORT)"
        echo "Customer C: http://localhost:$(cd $CUSTOMER_C_DIR && source .env && echo $NAUTOBOT_PORT)"
        ;;
    "stop-all")
        echo "Stopping all customer environments..."
        cd $CUSTOMER_A_DIR && docker compose down
        cd ../$CUSTOMER_B_DIR && docker compose down
        cd ../$CUSTOMER_C_DIR && docker compose down
        echo "All environments stopped!"
        ;;
    "status")
        echo "Checking status of all environments..."
        cd $CUSTOMER_A_DIR && echo "Customer A:" && docker compose ps
        cd ../$CUSTOMER_B_DIR && echo "Customer B:" && docker compose ps
        cd ../$CUSTOMER_C_DIR && echo "Customer C:" && docker compose ps
        ;;
    "logs")
        echo "Showing logs for $2..."
        cd $2 && docker compose logs -f
        ;;
    *)
        echo "Usage: $0 {start-all|stop-all|status|logs <customer-dir>}"
        echo "Examples:"
        echo "  $0 start-all"
        echo "  $0 stop-all"
        echo "  $0 status"
        echo "  $0 logs customer-a"
        exit 1
        ;;
esac
```

### Customer-Specific Customizations

#### 1. Plugin Configuration per Customer

```python
# customer-a/config/nautobot_config.py (Enterprise Customer)
PLUGINS_CONFIG = {
    'nautobot_golden_config': {
        'enable_backup': True,
        'enable_compliance': True,
        'enable_intended': True,
        'backup_repository': 'customer_a_backup_repo',
        'intended_repository': 'customer_a_intended_repo',
    },
    'nautobot_device_onboarding': {
        'default_platform': 'cisco_ios',
        'default_site': 'customer_a_main_site',
    },
}

# customer-b/config/nautobot_config.py (SMB Customer)
PLUGINS_CONFIG = {
    'nautobot_golden_config': {
        'enable_backup': True,
        'enable_compliance': False,  # SMB doesn't need compliance
        'enable_intended': False,
    },
    'nautobot_device_onboarding': {
        'default_platform': 'arista_eos',
        'default_site': 'customer_b_site',
    },
}
```

#### 2. Customer-Specific Jobs

```python
# customer-a/jobs/jobs/customer_a_backup_job.py
class CustomerABackupJob(Job):
    class Meta:
        name = "Customer A - Backup Configuration"
        description = "Customer A specific backup job"
    
    def run(self, data, commit):
        # Customer A specific backup logic
        pass

# customer-b/jobs/jobs/customer_b_monitoring_job.py
class CustomerBMonitoringJob(Job):
    class Meta:
        name = "Customer B - Network Monitoring"
        description = "Customer B specific monitoring job"
    
    def run(self, data, commit):
        # Customer B specific monitoring logic
        pass
```

### Quick Commands for Multi-Customer Management

```bash
# Start all environments
~/nautobot-projects/manage_all.sh start-all

# Check status of all environments
~/nautobot-projects/manage_all.sh status

# View logs for specific customer
~/nautobot-projects/manage_all.sh logs customer-a

# Stop all environments
~/nautobot-projects/manage_all.sh stop-all

# Individual customer management
cd ~/nautobot-projects/customer-a
docker compose up -d
docker compose logs -f
docker compose down
```

### Benefits of Using .env Files

1. **Single docker compose.yml**: No need to maintain multiple docker compose files
2. **Easy Configuration**: Simple key-value pairs in `.env` files
3. **Version Control Safe**: `.env` files can be excluded from git (add to `.gitignore`)
4. **Environment Isolation**: Each customer has completely separate configuration
5. **Easy Maintenance**: Update one `.env` file instead of modifying docker compose.yml
6. **Default Values**: Docker Compose provides fallback values if variables are missing

### Best Practices for Multi-Customer Setup

1. **Use .env Files**: Configure each customer via `.env` files instead of modifying docker compose.yml
2. **Unique Ports**: Each customer gets a unique port via `NAUTOBOT_PORT` in `.env`
3. **Unique Container Names**: Prevent conflicts via container name variables in `.env`
4. **Separate Databases**: Each customer has their own PostgreSQL database
5. **Customer-Specific Configs**: Customize plugins and settings per customer
6. **Version Control**: Each customer environment can have its own git branch
7. **Documentation**: Maintain customer-specific README files
8. **Backup Strategy**: Implement customer-specific backup procedures

### Access URLs

After setup, access each customer environment at:
- **Customer A**: http://localhost:$(cd customer-a && source .env && echo $NAUTOBOT_PORT)
- **Customer B**: http://localhost:$(cd customer-b && source .env && echo $NAUTOBOT_PORT)
- **Customer C**: http://localhost:$(cd customer-c && source .env && echo $NAUTOBOT_PORT)

Or check the `.env` file in each customer directory for the specific port configuration.
