# sshsync CLI Tool Guide

Complete reference for using sshsync with Tailscale SSH Sync Agent.

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Core Commands](#core-commands)
4. [Advanced Usage](#advanced-usage)
5. [Troubleshooting](#troubleshooting)

## Installation

### Via pip

```bash
pip install sshsync
```

### Verify Installation

```bash
sshsync --version
```

## Configuration

### 1. SSH Config Setup

sshsync uses your existing SSH configuration. Edit `~/.ssh/config`:

```
# Example host entries
Host homelab-1
  HostName 100.64.1.10
  User admin
  IdentityFile ~/.ssh/id_ed25519
  Port 22

Host prod-web-01
  HostName 100.64.1.20
  User deploy
  IdentityFile ~/.ssh/id_rsa
  Port 22

Host dev-laptop
  HostName 100.64.1.30
  User developer
```

**Important Notes**:
- sshsync uses the **Host alias** (e.g., "homelab-1"), not the actual hostname
- Ensure SSH key authentication is configured
- Test each host with `ssh host-alias` before using with sshsync

### 2. Initialize sshsync Configuration

First run:

```bash
sshsync sync
```

This will:
1. Read all hosts from your SSH config
2. Prompt you to assign hosts to groups
3. Create `~/.config/sshsync/config.yaml`

### 3. sshsync Config File

Location: `~/.config/sshsync/config.yaml`

Structure:
```yaml
groups:
  production:
    - prod-web-01
    - prod-web-02
    - prod-db-01
  development:
    - dev-laptop
    - dev-desktop
  homelab:
    - homelab-1
    - homelab-2
```

**Manual Editing**:
- Groups are arbitrary labels (use what makes sense for you)
- Hosts can belong to multiple groups
- Use consistent host aliases from SSH config

## Core Commands

### List Hosts

```bash
# List all configured hosts
sshsync ls

# List with online/offline status
sshsync ls --with-status
```

**Output Example**:
```
Host            Status
homelab-1       online
homelab-2       offline
prod-web-01     online
dev-laptop      online
```

### Execute Commands

#### On All Hosts

```bash
# Execute on all configured hosts
sshsync all "df -h"

# With custom timeout (default: 10s)
sshsync all --timeout 20 "systemctl status nginx"

# Dry-run (preview without executing)
sshsync all --dry-run "reboot"
```

#### On Specific Group

```bash
# Execute on group
sshsync group production "uptime"

# With timeout
sshsync group web-servers --timeout 30 "npm run build"

# Filter with regex
sshsync group production --regex "web-.*" "df -h"
```

**Regex Filtering**:
- Filters group members by alias matching pattern
- Uses Python regex syntax
- Example: `--regex "web-0[1-3]"` matches web-01, web-02, web-03

### File Transfer

#### Push Files

```bash
# Push to specific host
sshsync push --host web-01 ./app /var/www/app

# Push to group
sshsync push --group production ./dist /var/www/app

# Push to all hosts
sshsync push --all ./config.yml /etc/app/config.yml

# Recursive push (directory with contents)
sshsync push --group web --recurse ./app /var/www/app

# Dry-run
sshsync push --group production --dry-run ./dist /var/www/app
```

**Important**:
- Local path comes first, remote path second
- Use `--recurse` for directories
- Dry-run shows what would be transferred without executing

#### Pull Files

```bash
# Pull from specific host
sshsync pull --host db-01 /var/log/mysql/error.log ./logs/

# Pull from group (creates separate directories per host)
sshsync pull --group databases /var/backups ./backups/

# Recursive pull
sshsync pull --host web-01 --recurse /var/www/app ./backup/
```

**Pull Behavior**:
- When pulling from groups, creates subdirectory per host
- Use `--recurse` to pull entire directory trees
- Destination directory created if doesn't exist

### Group Management

#### Add Hosts to Group

```bash
# Interactive: prompts to select hosts
sshsync gadd production

# Follow prompts to select which hosts to add
```

#### Add Host to SSH Config

```bash
# Interactive host addition
sshsync hadd

# Follow prompts for:
# - Host alias
# - Hostname/IP
# - Username
# - Port (optional)
# - Identity file (optional)
```

#### Sync Ungrouped Hosts

```bash
# Assign groups to hosts not yet in any group
sshsync sync
```

## Advanced Usage

### Parallel Execution

sshsync automatically executes commands in parallel across hosts:

```bash
# This runs simultaneously on all hosts in group
sshsync group web-servers "npm run build"
```

**Performance**:
- Commands execute concurrently
- Results collected as they complete
- Timeout applies per-host independently

### Timeout Strategies

Different operations need different timeouts:

```bash
# Quick checks (5-10s)
sshsync all --timeout 5 "hostname"

# Moderate operations (30-60s)
sshsync group web --timeout 60 "npm install"

# Long-running tasks (300s+)
sshsync group build --timeout 300 "docker build ."
```

**Timeout Best Practices**:
- Set timeout 20-30% longer than expected duration
- Use dry-run first to estimate timing
- Increase timeout for network-intensive operations

### Combining with Other Tools

#### With xargs

```bash
# Get list of online hosts
sshsync ls --with-status | grep online | awk '{print $1}' | xargs -I {} echo "Host {} is online"
```

#### With jq (if using JSON output)

```bash
# Parse structured output (if sshsync supports --json flag)
sshsync ls --json | jq '.hosts[] | select(.status=="online") | .name'
```

#### In Shell Scripts

```bash
#!/bin/bash

# Deploy script using sshsync
echo "Deploying to staging..."
sshsync push --group staging --recurse ./dist /var/www/app

if [ $? -eq 0 ]; then
    echo "Staging deployment successful"

    echo "Running tests..."
    sshsync group staging "cd /var/www/app && npm test"

    if [ $? -eq 0 ]; then
        echo "Tests passed, deploying to production..."
        sshsync push --group production --recurse ./dist /var/www/app
    fi
fi
```

## Troubleshooting

### Common Issues

#### 1. "Permission denied (publickey)"

**Cause**: SSH key not configured or not added to ssh-agent

**Solution**:
```bash
# Add SSH key to agent
ssh-add ~/.ssh/id_ed25519

# Verify it's added
ssh-add -l

# Copy public key to remote
ssh-copy-id user@host
```

#### 2. "Connection timed out"

**Cause**: Host is offline or network issue

**Solution**:
```bash
# Test connectivity
ping hostname

# Test Tailscale specifically
tailscale ping hostname

# Check Tailscale status
tailscale status
```

#### 3. "Host not found in SSH config"

**Cause**: Host alias not in `~/.ssh/config`

**Solution**:
```bash
# Add host to SSH config
sshsync hadd

# Or manually edit ~/.ssh/config
vim ~/.ssh/config
```

#### 4. "Group not found"

**Cause**: Group doesn't exist in sshsync config

**Solution**:
```bash
# Add hosts to new group
sshsync gadd mygroup

# Or manually edit config
vim ~/.config/sshsync/config.yaml
```

#### 5. File Transfer Fails

**Cause**: Insufficient permissions, disk space, or path doesn't exist

**Solution**:
```bash
# Check remote disk space
sshsync group production "df -h"

# Check remote path exists
sshsync group production "ls -ld /target/path"

# Check permissions
sshsync group production "ls -la /target/path"
```

### Debug Mode

While sshsync doesn't have a built-in verbose mode, you can debug underlying SSH:

```bash
# Increase SSH verbosity
SSH_VERBOSE=1 sshsync all "uptime"

# Or use dry-run to see what would execute
sshsync all --dry-run "command"
```

### Performance Issues

If operations are slow:

1. **Reduce parallelism** (run on fewer hosts at once)
2. **Increase timeout** for network-bound operations
3. **Check network latency**:
   ```bash
   sshsync all "echo $HOSTNAME" --timeout 5
   ```

### Configuration Validation

```bash
# Verify SSH config is readable
cat ~/.ssh/config

# Verify sshsync config
cat ~/.config/sshsync/config.yaml

# Test hosts individually
for host in $(sshsync ls | awk '{print $1}'); do
    echo "Testing $host..."
    ssh $host "echo OK" || echo "FAILED: $host"
done
```

## Best Practices

1. **Use meaningful host aliases** in SSH config
2. **Organize groups logically** (by function, environment, location)
3. **Always dry-run first** for destructive operations
4. **Set appropriate timeouts** based on operation type
5. **Test SSH keys** before using sshsync
6. **Keep groups updated** as infrastructure changes
7. **Use --with-status** to check availability before operations

## Integration with Tailscale

sshsync works seamlessly with Tailscale SSH:

```bash
# SSH config using Tailscale hostname
Host homelab-1
  HostName homelab-1.tailnet.ts.net
  User admin

# Or using Tailscale IP directly
Host homelab-1
  HostName 100.64.1.10
  User admin
```

**Tailscale Advantages**:
- No need for port forwarding
- Encrypted connections
- MagicDNS for easy hostnames
- Works across NATs

**Verify Tailscale**:
```bash
# Check Tailscale network
tailscale status

# Ping host via Tailscale
tailscale ping homelab-1
```

## Summary

sshsync simplifies multi-host SSH operations:
- ✅ Execute commands across host groups
- ✅ Transfer files to/from multiple hosts
- ✅ Organize hosts into logical groups
- ✅ Parallel execution for speed
- ✅ Dry-run mode for safety
- ✅ Works great with Tailscale

For more help: `sshsync --help`
