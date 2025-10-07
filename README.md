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
- **Configuration Management**: Complete Nautobot configuration with plugins
- **Blog Series Integration**: Structured to follow the "Nautobot Zero to Hero" series

## 📁 Repository Structure

```
nautobot_zero_to_hero/
├── docker-compose.yml          # Main Docker Compose configuration
├── .env                        # Environment variables (create this file)
├── get_config.sh              # Helper script to copy files from container
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

### Prerequisites

- Docker and Docker Compose installed
- Git for version control
- Basic understanding of networking concepts
- Familiarity with command-line operations

### 1. Clone and Setup

```bash
# Clone the repository
git clone [https://github.com/bsmeding/nautobot_zero_to_hero.git](https://github.com/bsmeding/nautobot_zero_to_hero.git)
cd nautobot_zero_to_hero

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
docker-compose up -d

# Check status
docker-compose ps
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

- Create and activate a local venv:

```bash
make install
source .venv/bin/activate
```

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
   docker-compose restart nautobot
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

### Modifying Configuration

1. **Edit** `config/nautobot_config.py` for basic changes
2. **See** `nautobot_advanced_settings.md` for advanced configuration options
3. **Restart** Nautobot to apply changes:
   ```bash
   docker-compose restart nautobot
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
docker-compose ps

# View Nautobot logs
docker-compose logs nautobot

# Check database connectivity
docker-compose exec nautobot nautobot-server shell -c "from django.db import connection; print(connection.ensure_connection())"

# Test job execution
docker-compose exec nautobot nautobot-server run_job --job-name "Test Job"
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
docker-compose down -v
docker-compose up -d

# View all logs
docker-compose logs -f

# Access Nautobot shell
docker-compose exec nautobot nautobot-server shell

# Backup database
docker-compose exec postgres pg_dump -U nautobot nautobot > backup.sql
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
