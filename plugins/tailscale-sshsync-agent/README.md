# Tailscale SSH Sync Agent

Intelligent workload distribution and file sharing across Tailscale SSH-connected machines using sshsync.

## Overview

This Claude Code agent automates distributed computing operations across your Tailscale network:

- 🔍 **Monitor** host availability and health across your network
- ⚖️ **Balance** workloads intelligently based on machine resources
- 📤 **Sync** files across groups of machines
- 🚀 **Deploy** applications with multi-stage pipelines
- 🔄 **Execute** commands in parallel across host groups
- 🏥 **Health check** services across infrastructure

## Quick Start

### 1. Prerequisites

- Python 3.10+
- Tailscale installed and connected
- SSH configured with key authentication

### 2. Install sshsync

```bash
pip install sshsync
```

### 3. Configure Hosts

Edit `~/.ssh/config` with your Tailscale hosts:

```
Host homelab-1
  HostName homelab-1.tailnet.ts.net
  User admin
  IdentityFile ~/.ssh/id_ed25519

Host prod-web-01
  HostName 100.64.1.20
  User deploy
  IdentityFile ~/.ssh/id_ed25519
```

### 4. Initialize Groups

```bash
sshsync sync
```

Follow prompts to organize hosts into groups.

### 5. Install Agent

```bash
/plugin marketplace add /path/to/tailscale-sshsync-agent
```

### 6. Start Using

```
"Which of my machines are online?"
"Run this task on the least loaded machine"
"Push this directory to all production servers"
"Deploy to staging, test, then production"
```

## Use Cases

### Host Monitoring

**Query:** "Which machines are online?"

**Result:**
```
🟢 homelab-1 (homelab) - Online - Tailscale: Connected | Latency: 15ms
🟢 prod-web-01 (production, web) - Online - Tailscale: Connected | Latency: 25ms
🔴 dev-laptop (development) - Offline - Last seen: 2h ago
```

### Load-Balanced Execution

**Query:** "Run this npm build on the least loaded machine"

**Result:**
```
✓ Selected host: web-03
  Reason: Lowest load score (0.28)
  - CPU: 20% (vs avg 45%)
  - Memory: 35% (vs avg 60%)

Executing: npm run build
[Build output...]
✓ Completed in 2m 15s
```

### File Synchronization

**Query:** "Sync my code to all development machines"

**Result:**
```
📤 Syncing: ~/projects/myapp → /var/www/myapp
Group: development (3 hosts)

✓ dev-laptop: Synced 145 files in 8s
✓ dev-desktop: Synced 145 files in 6s
✓ dev-server: Synced 145 files in 10s

Summary: 3/3 successful (435 files, 36.9 MB total)
```

### Multi-Stage Deployment

**Query:** "Deploy to staging, test, then production"

**Result:**
```
Stage 1: Staging Deployment ✓
Stage 2: Validation ✓
Stage 3: Production Deployment ✓
Stage 4: Verification ✓

✅ Deployment completed successfully in 12m 45s
```

## Features

### Core Operations

- **Host Status**: Check which machines are online/offline
- **Load Balancing**: Select optimal host for tasks based on CPU, memory, disk
- **Group Execution**: Run commands across groups (production, development, etc.)
- **File Transfer**: Push/pull files to/from hosts and groups
- **Workflows**: Common multi-machine workflows (deploy, backup, sync, restart)

### Intelligent Features

- **Automatic host discovery** via Tailscale network status
- **Real-time load metrics** for optimal task placement
- **Parallel execution** across multiple hosts
- **Dry-run mode** for previewing operations
- **Connection validation** before operations
- **Comprehensive error handling** with helpful messages

### Safety Features

- **Input validation** prevents invalid operations
- **Dangerous command blocking** (can be overridden)
- **SSH key authentication** required (more secure)
- **Dry-run support** for preview before execution
- **Per-host error isolation** (one failure doesn't stop others)

## Architecture

```
sshsync_wrapper.py     - Python interface to sshsync CLI
tailscale_manager.py   - Tailscale network operations
load_balancer.py       - Intelligent task distribution
workflow_executor.py   - Common multi-machine workflows
utils/
  helpers.py           - Formatting, parsing utilities
  validators/          - Multi-layer input validation
```

## Testing

Run the test suite:

```bash
cd /path/to/tailscale-sshsync-agent

# Integration tests
python3 tests/test_integration.py

# Helper tests
python3 tests/test_helpers.py

# Validation tests
python3 tests/test_validation.py
```

**Expected Output:**

```
======================================================================
INTEGRATION TESTS - Tailscale SSH Sync Agent
======================================================================

✓ Testing get_host_status()...
  ✓ Found 5 hosts
  ✓ Online: 4
  ✓ Offline: 1

✓ Testing get_groups()...
  ✓ Groups config loaded
  ✓ Found 3 groups

... [more tests] ...

======================================================================
SUMMARY
======================================================================
✅ PASS: Host status check
✅ PASS: List hosts
✅ PASS: Get groups
... [more results] ...

Results: 11/11 passed

🎉 All tests passed!
```

## Documentation

- **SKILL.md**: Complete feature documentation
- **references/sshsync-guide.md**: sshsync CLI reference
- **references/tailscale-integration.md**: Tailscale setup guide
- **INSTALLATION.md**: Detailed setup tutorial
- **DECISIONS.md**: Architecture decisions and rationale
- **CHANGELOG.md**: Version history and changes

## Requirements

- Python 3.10 or higher
- sshsync (`pip install sshsync`)
- Tailscale (installed and connected)
- SSH configured with key authentication
- One or more remote machines accessible via Tailscale

## Configuration

### SSH Config (`~/.ssh/config`)

Define your hosts:

```
Host homelab-1
  HostName homelab-1.tailnet.ts.net
  User admin
  IdentityFile ~/.ssh/id_ed25519

Host prod-web-01
  HostName 100.64.1.20
  User deploy
  IdentityFile ~/.ssh/id_ed25519
```

### sshsync Config (`~/.config/sshsync/config.yaml`)

Organize hosts into groups:

```yaml
groups:
  production:
    - prod-web-01
    - prod-web-02
  development:
    - dev-laptop
    - dev-desktop
  homelab:
    - homelab-1
    - homelab-2
```

Created automatically with `sshsync sync`.

## Troubleshooting

### "Permission denied (publickey)"

```bash
# Add SSH key to agent
ssh-add ~/.ssh/id_ed25519

# Verify
ssh-add -l

# Copy to remote
ssh-copy-id user@host
```

### "Host not reachable"

```bash
# Check Tailscale connection
tailscale status
tailscale ping hostname

# Check SSH
ssh hostname "echo test"
```

### "sshsync not found"

```bash
# Install sshsync
pip install sshsync

# Verify
sshsync --version
```

See **references/** for detailed troubleshooting guides.

## Examples

```
# Host monitoring
"Which machines are online?"
"Show status of my Tailscale network"

# Load balancing
"Run this on the least loaded machine"
"Execute this task on the machine with most resources"

# File operations
"Push this directory to all development machines"
"Sync code across my homelab servers"
"Pull logs from all web servers"

# Multi-host commands
"Check disk space across production servers"
"Restart services on all database hosts"
"Update all homelab machines"

# Workflows
"Deploy to staging, test, then production"
"Backup files from all machines"
"Rolling restart of nginx across web servers"
```

## License

See LICENSE file.

## Version

Current version: **1.0.0**

See CHANGELOG.md for release history.

## Contributing

This agent follows the agent-creator-en protocol for autonomous agent generation.

For architecture decisions, see DECISIONS.md.

## Support

For issues or questions:
- Check references/ for guides
- Review INSTALLATION.md for setup help
- See DECISIONS.md for architecture rationale

## Estimated Time Savings

**Before (Manual):**
- Check status across 10 machines: ~5 minutes
- Deploy to 3-tier environment: ~30 minutes
- Sync files to multiple hosts: ~10 minutes per host
- **Total**: Hours per day

**After (Automated):**
- Check status: ~5 seconds
- Deploy: ~3 minutes (automated testing + deployment)
- Sync files: ~30 seconds (parallel)
- **Total**: Minutes per day

**Savings**: 90%+ time reduction for infrastructure operations
