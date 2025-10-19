# Setting Up the Device Configuration Hook

The Device Configuration Hook is created, but it needs to be configured in Nautobot to actually trigger on device changes.

## Step 1: Enable the Job

1. Navigate to **Jobs → Jobs**
2. Find **"Device Configuration Hook"** (under "Lifecycle hooks")
3. Click on it
4. If not already enabled, check the **"Enabled"** checkbox
5. Click **Update**

## Step 2: Create a Job Hook

1. Navigate to **Extensibility → Job Hooks**
2. Click **+ Add**
3. Fill in the following fields:

### Basic Configuration

| Field | Value |
|-------|-------|
| **Name** | `Auto Provision on Device Update` |
| **Content Types** | Select: `dcim \| device` |
| **Enabled** | ✅ Checked |
| **Job** | Select: `Device Configuration Hook` |

### Trigger Configuration

| Field | Value |
|-------|-------|
| **Type Create** | ✅ Check if you want provisioning on new devices |
| **Type Update** | ✅ Check (recommended) |
| **Type Delete** | ❌ Leave unchecked |

### Job Parameters (JSON)

Add this in the **Job** field parameters:

**For Testing (Recommended First):**
```json
{
  "auto_provision_on_create": false,
  "auto_provision_on_update": true,
  "dry_run": true
}
```

**For Production (After Testing):**
```json
{
  "auto_provision_on_create": true,
  "auto_provision_on_update": true,
  "dry_run": false
}
```

## Step 3: Save

Click **Create** at the bottom.

## Step 4: Test

1. Go to **Devices → Devices**
2. Click on a device (e.g., `access1`)
3. Click **Edit**
4. Change the **Name** field (e.g., from `access1` to `access1-test`)
5. Click **Update**
6. Go to **Jobs → Job Results**
7. Look for **"Device Configuration Hook"** execution
8. Click on it to see the logs

You should now see:
```
Device Hook Triggered: UPDATE
Device: access1-test (...)
Device updated: access1-test
Changed fields: ['name']
Configuration-relevant fields changed: ['name']
Auto-provision on update is enabled
Triggering Device Provisioning Job...
...
```

## Troubleshooting

### Hook doesn't trigger

**Check:**
- Job Hook is enabled
- Job Hook has correct Content Type (`dcim | device`)
- Type Update is checked
- Job is enabled

### Hook triggers but does nothing

**Check Job Hook parameters:**
```json
{
  "auto_provision_on_create": false,  // or true
  "auto_provision_on_update": true,   // Must be true!
  "dry_run": true                     // true for testing
}
```

### Hook triggers but skips provisioning

**Check device has:**
- Platform configured
- Platform has NAPALM driver
- Primary IPv4 address
- Status is Active/Planned/Staged

## Configuration Options

### Conservative (Testing)
```json
{
  "auto_provision_on_create": false,
  "auto_provision_on_update": true,
  "dry_run": true
}
```
- Only triggers on updates
- Dry run mode (preview only)
- Safe for testing

### Moderate (Recommended)
```json
{
  "auto_provision_on_create": false,
  "auto_provision_on_update": true,
  "dry_run": false
}
```
- Only triggers on updates
- Actually deploys configurations
- Good for maintaining compliance

### Aggressive (Full Automation)
```json
{
  "auto_provision_on_create": true,
  "auto_provision_on_update": true,
  "dry_run": false
}
```
- Triggers on both create and update
- Actually deploys configurations
- Full zero-touch automation

## What Gets Triggered

The hook only triggers when these fields change:
- ✅ `name` (hostname)
- ✅ `primary_ip4` (management IP)
- ✅ `platform`
- ✅ `role`
- ✅ `location`
- ✅ `status`

Changes to other fields (comments, tags, etc.) will NOT trigger provisioning.

## Complete Setup Checklist

- [ ] Job "Device Configuration Hook" is enabled
- [ ] Job Hook created in Extensibility → Job Hooks
- [ ] Job Hook has Content Type = `dcim | device`
- [ ] Job Hook has Type Update checked
- [ ] Job Hook is enabled
- [ ] Job Hook has parameters configured (JSON)
- [ ] Tested by editing a device
- [ ] Verified in Job Results

## Related Documentation

- [Auto Provisioning Hook](./AUTO_PROVISIONING_HOOK.md) - Detailed documentation
- [Device Provisioning](./DEVICE_PROVISIONING.md) - Provisioning guide
- [Provisioning Architecture](./PROVISIONING_ARCHITECTURE.md) - How it works

---

Once configured, your devices will automatically stay in sync with Nautobot! 🚀

