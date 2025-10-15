# Automation Journey: From Scripts to JobHooks

This document outlines the complete automation journey demonstrated in this repository, from simple standalone scripts to fully automated event-driven configuration management.

## 🎯 The Complete Path

```
Level 1: Scripts        Level 2: Templates     Level 3: Nautobot API    Level 4: Jobs         Level 5: JobHooks
┌──────────────┐       ┌──────────────────┐   ┌──────────────────┐    ┌───────────────┐     ┌────────────────┐
│              │       │                  │   │                  │    │               │     │                │
│  Static      │  →    │  Jinja2          │ → │  Dynamic from    │ →  │  Interactive  │  →  │  Event-Driven  │
│  Hardcoded   │       │  Templates       │   │  Nautobot        │    │  UI Jobs      │     │  Automation    │
│              │       │                  │   │                  │    │               │     │                │
└──────────────┘       └──────────────────┘   └──────────────────┘    └───────────────┘     └────────────────┘
   Scripts 1-3            Script 4              Script 5-6             Script 7           interface_hook.py
```

## 📚 Learning Path

### Level 1: Static Scripts (Scripts 1-3)

**What you learn:**
- Basic device connection (pyeapi)
- Configuration commands
- Error handling
- Static inventory management

**Files:**
- `scripts/1_config_hostname.py` - Simple hostname config
- `scripts/2_config_interface.py` - Interface configuration
- `scripts/3_config_arista.py` - Multi-device static config

**Characteristics:**
- ✅ Simple and straightforward
- ✅ Easy to understand
- ✅ Good for testing/learning
- ❌ Hardcoded values
- ❌ Not scalable
- ❌ Requires manual execution

**Example:**
```python
ARISTA_DEVICES = [
    {"host": "172.20.20.11", "hostname": "access1"},
    {"host": "172.20.20.12", "hostname": "access2"},
]
```

---

### Level 2: Templates (Script 4)

**What you learn:**
- Jinja2 templating
- Separation of data and logic
- Template rendering
- Configuration abstraction

**Files:**
- `scripts/4_config_arista_template.py` - Static inventory with Jinja2 templates

**Characteristics:**
- ✅ Reusable templates
- ✅ Cleaner code
- ✅ Easier to maintain
- ❌ Still static inventory
- ❌ Manual execution
- ❌ Data embedded in script

**Example:**
```jinja2
hostname {{ device.name }}
!
interface Loopback0
  ip address {{ device.loopback_ip }}/32
```

---

### Level 3: Nautobot API Integration (Scripts 5-6)

**What you learn:**
- REST API interaction
- Dynamic data fetching
- Source of Truth concept
- Nautobot data models

**Files:**
- `scripts/5_config_arista_template_nautobot.py` - Fetch from Nautobot, render templates
- `scripts/6_dynamic_config_access_ports_on_access1_and_access2.py` - Advanced IP logic

**Characteristics:**
- ✅ Dynamic inventory from Nautobot
- ✅ Single Source of Truth
- ✅ Scalable to many devices
- ✅ Real device data
- ❌ Still manual execution
- ❌ Runs outside Nautobot

**Example:**
```python
devices = get_access_devices(nb_url, token)
for device in devices:
    interfaces = get_device_interfaces(nb_url, token, device["id"])
    rendered = tmpl.render(device=device, interfaces=interfaces)
```

---

### Level 4: Nautobot Jobs (Script 7)

**What you learn:**
- Job framework
- UI integration
- Job inputs/parameters
- Logging and results
- Scheduling

**Files:**
- `scripts/7_transform_to_nautobot_job.py` - Example of converting script to Job

**Characteristics:**
- ✅ Run from Nautobot UI
- ✅ User inputs via forms
- ✅ Built-in logging
- ✅ Can be scheduled
- ✅ Role-based access control
- ❌ Still requires manual trigger

**Example:**
```python
class MyConfigJob(Job):
    device = ObjectVar(
        model=Device,
        required=True,
        label="Device to Configure"
    )
    
    def run(self, device):
        self.log_info(f"Configuring {device.name}")
```

---

### Level 5: JobHooks - Event-Driven Automation ⭐

**What you learn:**
- Event-driven architecture
- Automated triggers
- Real-time synchronization
- Zero-touch automation

**Files:**
- `jobs/jobs/interface_hook.py` - Automatic interface configuration
- `jobs/jobs/device_hook.py` - Device change monitoring

**Characteristics:**
- ✅ Fully automated
- ✅ Event-driven (create/update/delete)
- ✅ Real-time sync
- ✅ Zero manual intervention
- ✅ Always consistent with Nautobot
- 🎯 **ULTIMATE AUTOMATION GOAL**

**Example:**
```python
class InterfaceJobHookReceiver(JobHookReceiver):
    class Meta:
        name = "Interface Configuration Hook"
        object_type = Interface  # Triggers on Interface changes
    
    def run(self, commit, **kwargs):
        action = kwargs.get("action")  # "created", "updated", "deleted"
        
        if action == "created":
            # Automatically configure interface on device!
            self._push_config_to_device(device, config_commands)
```

**Real-World Example:**

1. Network engineer creates interface in Nautobot UI:
   - Interface: `Ethernet4`
   - Device: `access1`
   - Description: `Server connection`
   - Enabled: ✅

2. JobHook automatically triggers

3. Device is configured immediately:
   ```
   interface Ethernet4
     description Server connection
     no shutdown
   write memory
   ```

4. **No scripts to run, no jobs to trigger - it just happens!**

---

## 🎓 Recommended Learning Order

### Week 1: Foundations
1. ✅ Run script 1-3 to understand basic device automation
2. ✅ Experiment with different device IPs and configurations
3. ✅ Understand pyeapi connection and command patterns

### Week 2: Templates
1. ✅ Run script 4 to see Jinja2 templates in action
2. ✅ Modify the template to add more configuration
3. ✅ Create your own template for different device types

### Week 3: Nautobot Integration
1. ✅ Set up Nautobot environment
2. ✅ Create devices, interfaces in Nautobot
3. ✅ Run scripts 5-6 to see dynamic data fetching
4. ✅ Add more devices and see how scripts scale

### Week 4: Nautobot Jobs
1. ✅ Study script 7 - the Job template
2. ✅ Convert one of your scripts to a Job
3. ✅ Add custom inputs and logging
4. ✅ Run from Nautobot UI

### Week 5: Event-Driven Automation (JobHooks)
1. ✅ Study `interface_hook.py` implementation
2. ✅ Enable the Interface Configuration Hook
3. ✅ Test by creating/updating interfaces in Nautobot
4. ✅ Watch devices automatically configure themselves!
5. ✅ Create your own JobHook for other objects (VLANs, IPs, etc.)

---

## 📊 Comparison Table

| Feature | Scripts | Templates | Nautobot API | Jobs | JobHooks |
|---------|---------|-----------|--------------|------|----------|
| **Execution** | Manual CLI | Manual CLI | Manual CLI | UI/Manual | Automatic |
| **Data Source** | Hardcoded | Hardcoded | Nautobot | Nautobot | Nautobot |
| **Scalability** | Low | Medium | High | High | High |
| **Reusability** | Low | High | High | High | High |
| **User Input** | Code edit | Code edit | Code edit | UI Form | None needed |
| **Logging** | Print | Print | Print | Built-in | Built-in |
| **Scheduling** | Cron | Cron | Cron | Built-in | Event-driven |
| **Access Control** | OS-level | OS-level | API token | RBAC | RBAC |
| **Maintenance** | High | Medium | Medium | Low | Low |
| **Time to Execute** | Seconds | Seconds | Seconds | Seconds | Milliseconds |
| **Human Intervention** | Required | Required | Required | Required | **None!** |

---

## 🚀 Real-World Use Cases

### Scripts (1-4)
- Initial device provisioning
- One-off configuration changes
- Testing and development
- Learning automation basics

### Nautobot API Integration (5-6)
- Bulk configuration updates
- Automated reporting
- External integrations
- Migration scripts

### Nautobot Jobs (7)
- Self-service portals
- Scheduled maintenance
- Compliance checks
- Configuration backups

### JobHooks (interface_hook.py)
- **Real-time device synchronization** ⭐
- Zero-touch provisioning
- Automatic VLAN provisioning
- IP address assignment automation
- Interface lifecycle management
- Compliance enforcement
- Configuration drift prevention

---

## 🎯 The Ultimate Goal: Zero-Touch Automation

JobHooks represent the pinnacle of network automation:

```
Traditional Workflow:
1. Engineer updates spreadsheet
2. Engineer updates Nautobot
3. Engineer runs script
4. Engineer verifies device
5. Repeat for each change

JobHook Workflow:
1. Engineer updates Nautobot
✨ DONE! Device automatically configured.
```

**Benefits:**
- ⚡ Instant configuration
- 🎯 Always consistent
- 🔒 No human error
- 📝 Fully audited
- 🔄 Automatic rollback (if implemented)
- 😊 Happy engineers!

---

## 📖 Further Reading

- [Scripts README](scripts/README.md) - Detailed script documentation
- [Interface Hook Documentation](jobs/jobs/INTERFACE_HOOK.md) - JobHook deep dive
- [Main README](README.md) - Complete repository guide
- [Nautobot Jobs Documentation](https://docs.nautobot.com/projects/core/en/stable/user-guide/platform-functionality/jobs/)
- [Nautobot Job Hooks](https://docs.nautobot.com/projects/core/en/stable/user-guide/platform-functionality/jobs/job-hooks/)

---

## 💡 Next Steps

1. **Start with the scripts** - Build foundation
2. **Move to templates** - Learn abstraction
3. **Integrate Nautobot** - Embrace Source of Truth
4. **Create Jobs** - Enable self-service
5. **Implement JobHooks** - Achieve automation nirvana! 🎉

Happy Automating! 🚀

