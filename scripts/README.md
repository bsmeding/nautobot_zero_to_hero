# Demo Scripts - Nautobot Zero to Hero

This directory contains progressive demo scripts that demonstrate network automation concepts from simple static scripts to dynamic Nautobot-integrated jobs.

## Prerequisites

Before running these scripts, you need to install the following system packages:

### On Ubuntu/Debian/WSL
```bash
sudo apt update
sudo apt install -y make python3.12-venv
```

### On Fedora/RHEL/CentOS
```bash
sudo dnf install -y make python3.12
```

### On macOS (Homebrew)
```bash
brew install make python@3.12
```

## Setup

### 1. Create Virtual Environment

From the repository root directory:

```bash
make install
```

This will:
- Create a Python virtual environment in `.venv/`
- Install required Python packages (pyeapi, requests, jinja2)
- Upgrade pip, setuptools, and wheel

**Activation:**
- **If you have auto-activation configured** (direnv, autoenv, or custom shell hooks): The `.venv` will activate automatically when entering the directory
- **Otherwise**: Manually activate with `source .venv/bin/activate`

### 2. Ensure Lab is Running

Make sure your containerlab devices are deployed and reachable:

```bash
cd containerlab
sudo containerlab deploy -t nautobot-lab.clab.yml
```

## Running the Scripts

The scripts are numbered to show progression from basic to advanced:

### 1. Basic Static Configuration
```bash
python scripts/1_config_hostname.py
```
Simple hostname configuration on a single device.

### 2. Interface Configuration
```bash
python scripts/2_config_interface.py
```
Static interface configuration example.

### 3. Arista Configuration
```bash
python scripts/3_config_arista.py
```
Arista-specific configuration with static inventory (access1 and access2).

### 4. Jinja2 Template Configuration
```bash
python scripts/4_config_arista_template.py
```
Demonstrates Jinja2 template rendering with static inventory. Configures hostname, Loopback0, and interfaces using templates.

### 5. Transition to Nautobot with Templates
```bash
export NB_TOKEN=YOUR_API_TOKEN
export NB_URL=http://localhost:8081  # Optional, defaults to http://localhost:8081
python scripts/5_config_arista_template_nautobot.py
```
Bridges the gap between static inventory and Nautobot. Fetches devices from Nautobot API and renders Jinja2 templates with dynamic data.

**Getting an API Token:**
1. Log into Nautobot: http://localhost:8080
2. Navigate to: Profile → API Tokens
3. Click "Add API Token"
4. Copy the token and export it as `NB_TOKEN`

### 6. Dynamic Loopback Configuration
```bash
export NB_TOKEN=YOUR_API_TOKEN
python scripts/6_dynamic_config_access_ports_on_access1_and_access2.py
```
Dynamic configuration of access ports using Nautobot inventory with advanced IP assignment logic.

### 7. Transform to Nautobot Job
```bash
python scripts/7_transform_to_nautobot_job.py
```
Example showing how to convert a standalone script into a Nautobot Job.

## Dependency Management

### Freeze Current Dependencies
After installing additional packages, you can freeze them to `requirements.txt`:

```bash
make freeze
```

This creates/updates `scripts/requirements.txt` with all installed packages and versions.

### Install from Frozen Requirements
If `scripts/requirements.txt` exists, you can install from it:

```bash
source .venv/bin/activate
pip install -r scripts/requirements.txt
```

## Important Notes

### pyeapi Usage
These scripts use the **pyeapi** library for Arista devices. Important points:

- **Create a connection first, then wrap it in a Node object**
- **Use `node.config()` for configuration commands** - pyeapi automatically handles entering/exiting config mode
- **Use `node.enable()` for privileged exec commands** - like `write memory`
- **Don't manually send** `configure terminal`, `end`, or `exit` - pyeapi handles this automatically

Example:
```python
# ✅ Correct way
import pyeapi

connection = pyeapi.connect(
    transport="https",
    host="172.20.20.11",
    username="admin",
    password="admin",
    port=443
)
node = pyeapi.client.Node(connection)
node.config(["hostname switch1", "interface Ethernet1", "no shutdown"])
node.enable("write memory")

# ❌ Wrong way (will cause errors)
node = pyeapi.connect(...)  # This returns a connection, not a node
node.config([...])  # This will fail - connection has no config() method
```

## Troubleshooting

### "command not found: make"
Install the `make` package using the instructions in the Prerequisites section above.

### "No module named 'venv'"
Install `python3.12-venv` using the instructions in the Prerequisites section above.

### "Invalid input (privileged mode required)" error
This means you're trying to use `node.execute()` with config mode commands. Use `node.config()` instead (see Important Notes above).

### "Connection refused" when running scripts
Ensure your containerlab is running and devices are accessible:
```bash
sudo containerlab inspect -t containerlab/nautobot-lab.clab.yml
```

### Authentication failures
Check device credentials in the containerlab configuration:
- Arista devices: username `admin`, password `admin`
- Nokia SR Linux: username `admin`, password `NokiaSrl1!`

## Next Steps

After running these demo scripts, you can:
1. Convert them to Nautobot Jobs (see script 7)
2. Copy job templates to `jobs/jobs/` directory
3. Restart Nautobot to load new jobs
4. Run jobs from Nautobot UI
5. **Implement JobHooks for automated triggers** - The next evolution!

### Progression: Scripts → Jobs → JobHooks

This repository demonstrates the complete automation journey:

```
📝 Scripts (1-6)          →  📦 Nautobot Jobs (7)      →  🎣 JobHooks (interface_hook.py)
├─ Run manually            ├─ Trigger from UI            ├─ Automatic triggers
├─ Static/External data    ├─ Interactive inputs         ├─ React to Nautobot changes
├─ Local development       ├─ Access Nautobot data       ├─ Real-time device sync
└─ Testing concepts        └─ Scheduled execution        └─ Event-driven automation
```

**JobHooks Example:**
The repository includes an **Interface Configuration Hook** (`jobs/jobs/interface_hook.py`) that automatically configures network devices when interfaces are created or updated in Nautobot. This represents the ultimate automation level - zero manual intervention!

See:
- [Interface Hook Documentation](../jobs/jobs/INTERFACE_HOOK.md)
- Main [README.md](../README.md) - JobHooks section

