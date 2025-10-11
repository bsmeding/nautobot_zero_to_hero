# Nautobot Zero to Hero - Complete Demo Environment

> ⚠️ Under Construction
>
> This repository and the accompanying "Nautobot Zero to Hero" blog posts are currently under active development. Do not use or follow at this time; content and instructions will change frequently.

*A comprehensive Nautobot development and demonstration environment that accompanies the "Nautobot Zero to Hero" blog series on netdevops.it. This repository provides everything you need to follow along with the blog posts and build a complete network automation platform.*

## 🎯 What This Repository Contains

This repository provides a complete Nautobot environment with:

- **Docker Compose Setup**: Ready-to-run Nautobot v2 with all dependencies
- **Containerlab Testbed**: Multi-vendor network lab for hands-on practice
- **Custom Jobs**: Python jobs that demonstrate automation workflows
- **Jinja2 Templates**: Configuration templates for multi-vendor devices
- **Config Contexts**: Hierarchical configuration data for platform-specific settings
- **Configuration Management**: Complete Nautobot configuration with plugins
- **Blog Series Integration**: Structured to follow the "Nautobot Zero to Hero" series

## 📁 Repository Structure

```
nautobot_zero_to_hero/
├── docker compose.yml          # Main Docker Compose configuration
├── .env                        # Environment variables (create this file)
├── install.sh                 # Automated installation (Docker, Containerlab, /etc/hosts, optional GUI)
├── update_hosts.sh            # Update /etc/hosts with lab device hostnames
├── configure_ssh_handler.sh   # Configure ssh:// protocol handler for clickable links
├── get_config.sh              # Helper script to copy files from container
├── Makefile                   # Build automation for Python virtual environment
├── README.md                  # This comprehensive guide
├── nautobot_advanced_settings.md  # Advanced configuration options
├── .gitignore                 # Git ignore rules
├── config/
│   └── nautobot_config.py     # Nautobot configuration with plugins
├── jobs/
│   └── jobs/                  # Custom Nautobot jobs
│       ├── __init__.py        # Makes jobs a Python package
│       ├── test_job.py        # Example job
│       ├── sitebuilder/       # Site management jobs
│       ├── utilities/         # Utility functions
│       ├── device_hook.py     # Device change hooks
│       ├── interface_hook.py  # Interface change hooks
│       └── site_hook.py       # Site change hooks
├── templates/                 # Jinja2 configuration templates
│   └── interface_basic.j2     # Basic interface template
└── containerlab/              # Containerlab network lab
    ├── nautobot-lab.clab.yml  # Lab topology
    └── README.md              # Lab setup instructions
```

## 🚀 Quick Start

> 📖 **Detailed Installation Guide**: See [`INSTALLATION.md`](INSTALLATION.md) for comprehensive installation options and troubleshooting.

### Prerequisites

- Docker and Docker Compose installed
- Git for version control
- Basic understanding of networking concepts
- Familiarity with command-line operations
- **For local development scripts**: `make` and `python3.12-venv` (see Development Workflow section below)
- **Optional**: Desktop environment for GUI and ssh:// link support

### 1. Clone and Setup

```bash
# Clone the repository
git clone [https://github.com/bsmeding/nautobot_zero_to_hero.git](https://github.com/bsmeding/nautobot_zero_to_hero.git)
cd nautobot_zero_to_hero
```

#### Option A: Automated Installation (Recommended)

Use the automated installation script to install all prerequisites:

```bash
# Standard installation (Docker, Containerlab, /etc/hosts)
bash install.sh

# OR: Install with desktop environment and ssh:// link support
INSTALL_DESKTOP=true bash install.sh
```

**What it installs:**
- ✅ Docker and Docker Compose
- ✅ Containerlab
- ✅ Updates `/etc/hosts` with lab device hostnames
- ✅ **Optional**: XFCE desktop environment (lightweight)
- ✅ **Optional**: Visual Studio Code
- ✅ **Optional**: Firefox browser
- ✅ **Optional**: ssh:// protocol handler (click ssh links to open terminal)

**Desktop Environment Benefits:**
- Click `ssh://admin@access1` links to auto-open SSH connection
- GUI browser for accessing Nautobot UI
- Better WSL integration with WSLg
- Includes: XFCE Desktop, VS Code, Firefox browser, Terminal emulator

**When to install desktop:**
- ✅ If using WSL and want GUI support
- ✅ If you want clickable ssh:// links  
- ✅ If you prefer graphical tools
- ❌ Skip if using headless server
- ❌ Skip if you only use command-line tools

#### Option B: Manual Setup

If you prefer manual installation, create the environment file:

```bash
# Create environment file with default values
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

### 2. Start Nautobot

```bash
# Start the complete Nautobot stack
docker compose up -d

# Check status
docker compose ps
```

### 3. Access Nautobot

- **URL**: http://localhost:8080
- **Username**: `admin`
- **Password**: `admin`

### 4. Setup Containerlab Lab

See installation instuctions [Containerlab Getting Started](https://netdevops.it/tutorials/containerlab_getting_started/)

```bash
# Navigate to containerlab directory
cd containerlab

# Deploy the network lab
sudo containerlab deploy -t nautobot-lab.clab.yml

# Check lab status
sudo containerlab show -t nautobot-lab.clab.yml
```

### 5. Update /etc/hosts (Optional but Recommended)

Add lab device hostnames to your `/etc/hosts` file for easier access:

**Option 1: Standalone script**
```bash
sudo bash update_hosts.sh
```

**Option 2: Already included in install.sh**
```bash
# If you ran install.sh, hosts file is already updated
# Otherwise, run the update script above
```

**What gets added:**
- `nautobotlab.dev` → 127.0.0.1 (Nautobot UI)
- `access1.lab` / `access1` → 172.20.20.11
- `access2.lab` / `access2` → 172.20.20.12
- `dist1.lab` / `dist1` → 172.20.20.13
- `rtr1.lab` / `rtr1` → 172.20.20.14
- `ztp.lab` / `ztp` → 172.20.20.15
- `mgmt.lab` / `mgmt` → 172.20.20.16

**Benefits:**
```bash
# Access Nautobot with friendly URL
http://nautobotlab.dev:8080

# SSH to devices using hostnames
ssh admin@access1
ssh admin@dist1.lab
ping rtr1
```

### 6. Configure SSH Protocol Handler (Optional)

Enable clickable `ssh://` links that automatically open SSH connections in your terminal:

**Option 1: Included with desktop installation**
```bash
# Already configured if you ran: INSTALL_DESKTOP=true bash install.sh
```

**Option 2: Standalone configuration**
```bash
# Configure ssh:// handler without full desktop install
bash configure_ssh_handler.sh
```

**What it does:**
- Detects your terminal emulator (xfce4-terminal, gnome-terminal, konsole)
- Creates protocol handler for `ssh://` URLs
- Registers handler with your desktop environment

**Usage examples:**
```bash
# Click these links in browser or documentation
ssh://admin@access1
ssh://admin@access1.lab
ssh://admin@172.20.20.11

# Or from command line
xdg-open ssh://admin@dist1
```

**Supported terminals:**
- XFCE Terminal (xfce4-terminal)
- GNOME Terminal (gnome-terminal)
- KDE Konsole (konsole)
- Generic (x-terminal-emulator)

## 📚 Blog Series Integration

This repository is designed to work seamlessly with the "Nautobot Zero to Hero" blog series. Each part of the series builds upon the previous, and this repository provides the complete environment to follow along.

### Series Overview

- **Part 1**: Foundation Setup - Deploy Nautobot and create first inventory
- **Part 2**: Device Discovery & Onboarding - Automatically discover network devices
- **Part 3**: Configuration Compliance - Set up Golden Config for compliance
- **Part 4**: Automated Remediation - Fix configuration drift automatically
- **Part 5**: Event-Driven Automation - Respond to network changes in real-time
- **Part 6**: Full Deployment & Validation - Complete production setup
- **Parts 7-10**: Advanced features (API integrations, GitOps, multi-vendor, etc.)

### Using This Repository with the Blog Series

1. **Start with Part 1**: Use the basic setup to deploy Nautobot
2. **Follow Each Part**: Jobs and templates are organized by series progression
3. **Practice with Containerlab**: Use the included lab for hands-on practice
4. **Customize for Your Environment**: Adapt the examples to your network

## 🔧 Default Configuration

### Included Plugins

The default configuration includes these popular Nautobot plugins:

- **Device Onboarding**: Automatically discover and onboard devices
- **Golden Config**: Configuration compliance and drift detection
- **Device Lifecycle**: Device lifecycle management
- **Capacity Metrics**: Capacity planning and monitoring
- **ChatOps**: Chat platform integrations
- **Circuit Maintenance**: Circuit maintenance scheduling
- **Device Type Library**: Device type management
- **IPFabric**: IPFabric integration
- **Merlin**: Network testing framework
- **Prometheus**: Metrics collection
- **SSoT**: Single Source of Truth integrations
- **Topology Views**: Network topology visualization

### Default Settings

- **Database**: PostgreSQL with persistent storage
- **Cache**: Redis for session and cache management
- **Background Tasks**: Celery workers for job processing
- **Web Interface**: Nginx reverse proxy
- **Port**: 8080 (configurable via .env)
- **Admin User**: admin/admin (configurable via .env)
- **Media Storage**: Automated media folder setup with proper permissions

## 📁 Media Folder Management

### Automated Media Directory Setup

This repository includes a **rock-solid media folder solution** that automatically creates and configures all required media directories with proper permissions. This eliminates common issues with device images, attachments, and other media files.

#### What It Does

The solution uses an **init container** (`nautobot-init`) that runs before the main Nautobot services to:

- ✅ **Create Required Directories**: All Nautobot media subdirectories
- ✅ **Set Proper Permissions**: `755` permissions for container access
- ✅ **Universal Compatibility**: Works for any user on any system
- ✅ **No Manual Setup**: Zero configuration required after clone

#### Media Directories Created

```
media/
├── device-images/          # Device photos and diagrams
├── devicetype-images/      # Device type images
├── image-attachments/      # General image attachments
├── moduletype-images/      # Module type images
└── rack-elevations/        # Rack elevation diagrams
```

#### Why This Solution?

**The Problem**: Without proper media directory setup, you'll encounter errors like:
- `celery-worker-1` cannot access `/opt/nautobot/media/devicetype-images`
- Permission denied when uploading device images
- Missing directories cause job failures

**The Solution**: 
- **Init Container**: Lightweight Alpine container creates directories
- **Proper Dependencies**: Main services wait for init completion
- **No Database Dependency**: Alpine avoids PostgreSQL connection issues
- **Cross-Platform**: Works on Windows, macOS, and Linux

#### How It Works

1. **Init Container Runs First**: `nautobot-init` creates directories and sets permissions
2. **Service Dependencies**: Main Nautobot services wait for init completion
3. **Automatic Setup**: No manual intervention required
4. **Persistent Storage**: Directories persist between container restarts

This solution ensures that your Nautobot deployment works immediately after `git clone` without any additional setup steps.

## 🛠️ Development Workflow

### Demo Scripts and Local venv

This repo includes a progressive demo under `scripts/` that goes from simple static scripts to dynamic inventory and a Nautobot Job template.

> 📖 **Detailed documentation**: See [`scripts/README.md`](scripts/README.md) for complete setup instructions and script descriptions.

#### Prerequisites for Local Development

Before using the Makefile commands, ensure you have the required packages installed:

```bash
# On Ubuntu/Debian/WSL
sudo apt update
sudo apt install -y make python3.12-venv

# On Fedora/RHEL/CentOS
sudo dnf install -y make python3.12

# On macOS (Homebrew)
brew install make python@3.12
```

#### Create and activate a local venv:

**If you have auto-activation configured** (direnv, autoenv, or custom shell hooks):
```bash
make install
# .venv will be automatically activated when entering the directory
```

**If you need manual activation:**
```bash
make install
source .venv/bin/activate
```

> **Note**: Some development environments automatically activate `.venv` folders. If yours does, you only need `make install`. Otherwise, manually activate with `source .venv/bin/activate`.

- Run examples (ensure your lab is up and devices reachable):

```bash
python scripts/1_config_hostname.py
python scripts/2_config_interface.py
python scripts/3_config_arista.py

# Dynamic with Nautobot inventory (requires NB_TOKEN; optional NB_URL, defaults to http://localhost:8081)
export NB_TOKEN=YOUR_API_TOKEN
python scripts/4_config_arista_template.py
python scripts/5_dynamic_config_access_ports_on_access1_and_access2.py
```

- Freeze dependencies for portability:

```bash
make freeze
```

The Job template equivalent is provided in `scripts/6_transform_to_nautobot_job.py` for copying into `jobs/` later.

### Adding Custom Jobs

1. **Create new job file** in `jobs/jobs/`:
   ```python
   # jobs/jobs/my_custom_job.py
   from nautobot.extras.jobs import Job
   
   class MyCustomJob(Job):
       class Meta:
           name = "My Custom Job"
           description = "Description of what this job does"
   
       def run(self, data, commit):
           self.log_info("Running my custom job...")
           # Your job logic here
   ```

2. **Restart Nautobot** to load the new job:

   > Always after adding/changing jobs on local system, restart the Nautobot container to reload in the GUI!

   ```bash
   docker compose restart nautobot
   ```

### JobHooks - Automated Event Triggers

JobHooks automatically trigger when objects are created, updated, or deleted in Nautobot. Perfect for real-time device configuration synchronization.

#### Interface Configuration Hook

The repository includes an **Interface Configuration Hook** that automatically configures network devices when interfaces are created or updated in Nautobot:

**Features:**
- Automatically pushes interface config to devices when created/updated in Nautobot
- Supports Arista EOS devices via pyeapi
- Syncs: description, enabled/disabled state, MTU
- Dry-run mode for testing
- Only processes physical interfaces (skips virtual/management)

**Usage Example:**
1. Create/update an interface in Nautobot UI (e.g., `Ethernet4` on `access1`)
2. Hook automatically detects the change
3. Connects to the device and pushes configuration:
   ```
   interface Ethernet4
     description Server connection
     no shutdown
   ```
4. Saves configuration on device

**Enable the Hook:**
1. Navigate to **Jobs** → **Job Hooks** in Nautobot UI
2. Find **"Interface Configuration Hook"**
3. Enable it and configure trigger events (Create, Update)

**Documentation:** See [jobs/jobs/INTERFACE_HOOK.md](jobs/jobs/INTERFACE_HOOK.md) for detailed usage and troubleshooting.

**Creating Your Own JobHooks:**

```python
# jobs/jobs/my_hook.py
from nautobot.apps.jobs import register_jobs
from nautobot.extras.jobs import JobHookReceiver
from nautobot.dcim.models import Device

class MyDeviceHook(JobHookReceiver):
    class Meta:
        name = "My Device Hook"
        description = "Run on Device create/update/delete"
        object_type = Device
    
    def run(self, commit, **kwargs):
        action = kwargs.get("action")  # "created", "updated", "deleted"
        object_pk = kwargs.get("object_pk")
        
        if action == "created":
            self.log_success(f"Device created: {object_pk}")
            # Your automation logic here

register_jobs(MyDeviceHook)
```

### Adding Jinja2 Templates

1. **Create template file** in `templates/`:
   ```jinja2
   # templates/switch_config.j2
   hostname {{ device.name }}
   !
   interface Loopback0
    description Management Loopback
    ip address {{ device.primary_ip4.address.ip }} 255.255.255.255
   ```

2. **Use in Golden Config** or custom jobs

### Config Contexts

Both the **Preflight Lab Setup** and **Design Builder Lab Setup** jobs create identical config contexts that provide hierarchical configuration data:

#### Created Config Contexts:
1. **Lab Common Configuration** (weight 1000) - NTP, DNS, Syslog, SNMP, timezone
2. **Arista Platform Configuration** (weight 2000) - Arista EOS specific settings
3. **Nokia Platform Configuration** (weight 2000) - Nokia SR Linux specific settings  
4. **Access Switch Role Configuration** (weight 3000) - Role-based settings

#### Example Usage in Templates:
```jinja2
{# Config context data is automatically available #}
hostname {{ device.name }}
!
{% for ntp_server in ntp_servers %}
ntp server {{ ntp_server }}
{% endfor %}
!
{% if platform_specific.management_interface == 'Management0' %}
  {# Arista EOS specific #}
  {{ platform_specific.cli_commands.save_config }}
{% elif platform_specific.management_interface == 'mgmt0' %}
  {# Nokia SR Linux specific #}
  {{ platform_specific.cli_commands.save_config }}
{% endif %}
```

See [`jobs/jobs/CONFIG_CONTEXTS.md`](jobs/jobs/CONFIG_CONTEXTS.md) for detailed documentation and examples.

#### Practical Job: Configure Network Services

A ready-to-use job that configures devices using config context data:

**Job:** `Configure Network Services` (in Jobs → Network Services)

**Features:**
- 📋 Multi-device selection
- ⚙️ Configurable services: NTP, DNS, Syslog, SNMP
- 🔍 Dry-run mode to preview commands
- 🔄 Platform-aware (Arista vs Nokia)
- 🚀 Pushes config to devices via eAPI

**Quick Start:**
1. Restart Nautobot: `docker compose restart nautobot`
2. Go to: **Jobs → Network Services → Configure Network Services**
3. Select devices and services
4. Enable **Dry Run** to preview
5. Run to apply configuration

### Modifying Configuration

1. **Edit** `config/nautobot_config.py` for basic changes
2. **See** `nautobot_advanced_settings.md` for advanced configuration options
3. **Restart** Nautobot to apply changes:
   ```bash
   docker compose restart nautobot
   ```

## 🧪 Testing and Validation

### Running Jobs

1. **Access Nautobot UI**: http://localhost:8080
2. **Navigate to**: Admin → Jobs
3. **Select and run** your desired job
4. **Monitor progress** in the job results

### Testing with Containerlab

The included Containerlab lab provides a multi-vendor test environment:

- **Cisco IOS**: cisco_ios devices
- **Arista EOS**: arista_eos devices  
- **Juniper vSRX**: juniper_vsrx devices
- **Linux hosts**: linux hosts for testing

### Validation Commands

```bash
# Check Nautobot status
docker compose ps

# View Nautobot logs
docker compose logs nautobot

# Check database connectivity
docker compose exec nautobot nautobot-server shell -c "from django.db import connection; print(connection.ensure_connection())"

# Test job execution
docker compose exec nautobot nautobot-server run_job --job-name "Test Job"
```

## 🔍 Troubleshooting

### Common Issues

1. **Port already in use**: Change `NAUTOBOT_PORT` in `.env`
2. **Database connection issues**: Check PostgreSQL container status
3. **Jobs not appearing**: Restart Nautobot after adding new jobs
4. **Template errors**: Check Jinja2 syntax and variable references
5. **Media folder errors**: The automated init container handles this - no manual intervention needed

### Useful Commands

```bash
# Reset everything
docker compose down -v
docker compose up -d

# View all logs
docker compose logs -f

# Access Nautobot shell
docker compose exec nautobot nautobot-server shell

# Backup database
docker compose exec postgres pg_dump -U nautobot nautobot > backup.sql
```

## 📖 Additional Resources

- **Blog Series**: [Nautobot Zero to Hero on netdevops.it](https://netdevops.it)
- **Nautobot Documentation**: [docs.nautobot.com](https://docs.nautobot.com)
- **Advanced Settings**: See `nautobot_advanced_settings.md` for detailed configuration options
- **Containerlab Lab**: See `containerlab/README.md` for lab setup and usage

## 🤝 Support

- **Questions**: Leave comments on the blog posts
- **Issues**: Report problems in this repository
- **Contributions**: Submit pull requests for improvements
- **Community**: Join the discussion in the blog comments

---

*Happy automating! 🚀*

*This repository accompanies the "Nautobot Zero to Hero" blog series by Bart Smeding on netdevops.it.*
