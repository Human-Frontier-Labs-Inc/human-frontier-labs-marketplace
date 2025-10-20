# Installation Guide

Complete step-by-step tutorial for setting up Tailscale SSH Sync Agent.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step 1: Install Tailscale](#step-1-install-tailscale)
3. [Step 2: Install sshsync](#step-2-install-sshsync)
4. [Step 3: Configure SSH](#step-3-configure-ssh)
5. [Step 4: Configure sshsync Groups](#step-4-configure-sshsync-groups)
6. [Step 5: Install Agent](#step-5-install-agent)
7. [Step 6: Test Installation](#step-6-test-installation)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, ensure you have:

- **Operating System**: macOS, Linux, or BSD
- **Python**: Version 3.10 or higher
- **pip**: Python package installer
- **Claude Code**: Installed and running
- **Remote machines**: At least one machine you want to manage
- **SSH access**: Ability to SSH to remote machines

**Check Python version**:
```bash
python3 --version
# Should show: Python 3.10.x or higher
```

**Check pip**:
```bash
pip3 --version
# Should show: pip xx.x.x from ...
```

## Step 1: Install Tailscale

Tailscale provides secure networking between your machines.

### macOS

```bash
# Install via Homebrew
brew install tailscale

# Start Tailscale
sudo tailscale up

# Follow authentication link in terminal
# This will open browser to log in
```

### Linux (Ubuntu/Debian)

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Start and authenticate
sudo tailscale up

# Follow authentication link
```

### Linux (Fedora/RHEL)

```bash
# Add repository
sudo dnf config-manager --add-repo https://pkgs.tailscale.com/stable/fedora/tailscale.repo

# Install
sudo dnf install tailscale

# Enable and start
sudo systemctl enable --now tailscaled
sudo tailscale up
```

### Verify Installation

```bash
# Check Tailscale status
tailscale status

# Should show list of machines in your tailnet
# Example output:
# 100.64.1.10  homelab-1    user@    linux   -
# 100.64.1.11  laptop       user@    macOS   -
```

**Important**: Install and authenticate Tailscale on **all machines** you want to manage.

## Step 2: Install sshsync

sshsync is the CLI tool for managing SSH operations across multiple hosts.

```bash
# Install via pip
pip3 install sshsync

# Or use pipx for isolated installation
pipx install sshsync
```

### Verify Installation

```bash
# Check version
sshsync --version

# Should show: sshsync, version x.x.x
```

### Common Installation Issues

**Issue**: `pip3: command not found`

**Solution**:
```bash
# macOS
brew install python3

# Linux (Ubuntu/Debian)
sudo apt install python3-pip

# Linux (Fedora/RHEL)
sudo dnf install python3-pip
```

**Issue**: Permission denied during install

**Solution**:
```bash
# Install for current user only
pip3 install --user sshsync

# Or use pipx
pip3 install --user pipx
pipx install sshsync
```

## Step 3: Configure SSH

SSH configuration defines how to connect to each machine.

### Step 3.1: Generate SSH Keys (if you don't have them)

```bash
# Generate ed25519 key (recommended)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Press Enter to use default location (~/.ssh/id_ed25519)
# Enter passphrase (or leave empty for no passphrase)
```

**Output**:
```
Your identification has been saved in /Users/you/.ssh/id_ed25519
Your public key has been saved in /Users/you/.ssh/id_ed25519.pub
```

### Step 3.2: Copy Public Key to Remote Machines

For each remote machine:

```bash
# Copy SSH key to remote
ssh-copy-id user@machine-hostname

# Example:
ssh-copy-id admin@100.64.1.10
```

**Manual method** (if ssh-copy-id doesn't work):

```bash
# Display public key
cat ~/.ssh/id_ed25519.pub

# SSH to remote machine
ssh user@remote-host

# On remote machine:
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "your-public-key-here" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
exit
```

### Step 3.3: Test SSH Connection

```bash
# Test connection (should not ask for password)
ssh user@remote-host "hostname"

# If successful, should print remote hostname
```

### Step 3.4: Create SSH Config File

Edit `~/.ssh/config`:

```bash
vim ~/.ssh/config
```

**Add host entries**:

```
# Production servers
Host prod-web-01
  HostName prod-web-01.tailnet.ts.net
  User deploy
  IdentityFile ~/.ssh/id_ed25519
  Port 22

Host prod-web-02
  HostName 100.64.1.21
  User deploy
  IdentityFile ~/.ssh/id_ed25519

Host prod-db-01
  HostName 100.64.1.30
  User deploy
  IdentityFile ~/.ssh/id_ed25519

# Development
Host dev-laptop
  HostName dev-laptop.tailnet.ts.net
  User developer
  IdentityFile ~/.ssh/id_ed25519

Host dev-desktop
  HostName 100.64.1.40
  User developer
  IdentityFile ~/.ssh/id_ed25519

# Homelab
Host homelab-1
  HostName 100.64.1.10
  User admin
  IdentityFile ~/.ssh/id_ed25519

Host homelab-2
  HostName 100.64.1.11
  User admin
  IdentityFile ~/.ssh/id_ed25519
```

**Important fields**:
- **Host**: Alias you'll use (e.g., "homelab-1")
- **HostName**: Actual hostname or IP (Tailscale hostname or IP)
- **User**: SSH username on remote machine
- **IdentityFile**: Path to SSH private key

### Step 3.5: Set Correct Permissions

```bash
# SSH config should be readable only by you
chmod 600 ~/.ssh/config

# SSH directory permissions
chmod 700 ~/.ssh

# Private key permissions
chmod 600 ~/.ssh/id_ed25519

# Public key permissions
chmod 644 ~/.ssh/id_ed25519.pub
```

### Step 3.6: Verify All Hosts

Test each host in your config:

```bash
# Test each host
ssh homelab-1 "echo 'Connection successful'"
ssh prod-web-01 "echo 'Connection successful'"
ssh dev-laptop "echo 'Connection successful'"

# Should connect without asking for password
```

## Step 4: Configure sshsync Groups

Groups organize your hosts for easy management.

### Step 4.1: Initialize sshsync Configuration

```bash
# Sync hosts and create groups
sshsync sync
```

**What this does**:
1. Reads all hosts from `~/.ssh/config`
2. Prompts you to assign hosts to groups
3. Creates `~/.config/sshsync/config.yaml`

### Step 4.2: Follow Interactive Prompts

```
Found 7 ungrouped hosts:
1. homelab-1
2. homelab-2
3. prod-web-01
4. prod-web-02
5. prod-db-01
6. dev-laptop
7. dev-desktop

Assign groups now? [Y/n]: Y

Enter group name for homelab-1 (or skip): homelab
Enter group name for homelab-2 (or skip): homelab
Enter group name for prod-web-01 (or skip): production,web
Enter group name for prod-web-02 (or skip): production,web
Enter group name for prod-db-01 (or skip): production,database
Enter group name for dev-laptop (or skip): development
Enter group name for dev-desktop (or skip): development
```

**Tips**:
- Hosts can belong to multiple groups (separate with commas)
- Use meaningful group names (production, development, web, database, homelab)
- Skip hosts you don't want to group yet

### Step 4.3: Verify Configuration

```bash
# View generated config
cat ~/.config/sshsync/config.yaml
```

**Expected output**:
```yaml
groups:
  production:
    - prod-web-01
    - prod-web-02
    - prod-db-01
  web:
    - prod-web-01
    - prod-web-02
  database:
    - prod-db-01
  development:
    - dev-laptop
    - dev-desktop
  homelab:
    - homelab-1
    - homelab-2
```

### Step 4.4: Test sshsync

```bash
# List hosts
sshsync ls

# List with status
sshsync ls --with-status

# Test command execution
sshsync all "hostname"

# Test group execution
sshsync group homelab "uptime"
```

## Step 5: Install Agent

### Step 5.1: Navigate to Agent Directory

```bash
cd /path/to/tailscale-sshsync-agent
```

### Step 5.2: Verify Agent Structure

```bash
# List files
ls -la

# Should see:
# .claude-plugin/
# scripts/
# tests/
# references/
# SKILL.md
# README.md
# VERSION
# CHANGELOG.md
# etc.
```

### Step 5.3: Validate marketplace.json

```bash
# Check JSON is valid
python3 -c "import json; json.load(open('.claude-plugin/marketplace.json')); print('✅ Valid JSON')"

# Should output: ✅ Valid JSON
```

### Step 5.4: Install via Claude Code

In Claude Code:

```
/plugin marketplace add /absolute/path/to/tailscale-sshsync-agent
```

**Example**:
```
/plugin marketplace add /Users/you/tailscale-sshsync-agent
```

**Expected output**:
```
✓ Plugin installed successfully
✓ Skill: tailscale-sshsync-agent
✓ Description: Manages distributed workloads and file sharing...
```

### Step 5.5: Verify Installation

In Claude Code:

```
"Which of my machines are online?"
```

**Expected response**: Agent should activate and check your Tailscale network.

## Step 6: Test Installation

### Test 1: Host Status

**Query**:
```
"Which of my machines are online?"
```

**Expected**: List of hosts with online/offline status

### Test 2: List Groups

**Query**:
```
"What groups do I have configured?"
```

**Expected**: List of your sshsync groups

### Test 3: Execute Command

**Query**:
```
"Check disk space on homelab machines"
```

**Expected**: Disk usage for hosts in homelab group

### Test 4: Dry-Run

**Query**:
```
"Show me what would happen if I ran 'uptime' on all machines (dry-run)"
```

**Expected**: Preview without execution

### Test 5: Run Test Suite

```bash
cd /path/to/tailscale-sshsync-agent

# Run all tests
python3 tests/test_integration.py

# Should show:
# Results: 11/11 passed
# 🎉 All tests passed!
```

## Troubleshooting

### Agent Not Activating

**Symptoms**: Agent doesn't respond to queries about machines/hosts

**Solutions**:

1. **Check installation**:
   ```
   /plugin list
   ```
   Should show `tailscale-sshsync-agent` in list.

2. **Reinstall**:
   ```
   /plugin remove tailscale-sshsync-agent
   /plugin marketplace add /path/to/tailscale-sshsync-agent
   ```

3. **Check marketplace.json**:
   ```bash
   cat .claude-plugin/marketplace.json
   # Verify "description" field matches SKILL.md frontmatter
   ```

### SSH Connection Fails

**Symptoms**: "Permission denied" or "Connection refused"

**Solutions**:

1. **Check SSH key**:
   ```bash
   ssh-add -l
   # Should list your SSH key
   ```

   If not listed:
   ```bash
   ssh-add ~/.ssh/id_ed25519
   ```

2. **Test SSH directly**:
   ```bash
   ssh -v hostname
   # -v shows verbose debug info
   ```

3. **Verify authorized_keys on remote**:
   ```bash
   ssh hostname "cat ~/.ssh/authorized_keys"
   # Should contain your public key
   ```

### Tailscale Connection Issues

**Symptoms**: Hosts show as offline in Tailscale

**Solutions**:

1. **Check Tailscale status**:
   ```bash
   tailscale status
   ```

2. **Restart Tailscale**:
   ```bash
   # macOS
   brew services restart tailscale

   # Linux
   sudo systemctl restart tailscaled
   ```

3. **Re-authenticate**:
   ```bash
   sudo tailscale up
   ```

### sshsync Errors

**Symptoms**: "sshsync: command not found"

**Solutions**:

1. **Reinstall sshsync**:
   ```bash
   pip3 install --upgrade sshsync
   ```

2. **Check PATH**:
   ```bash
   which sshsync
   # Should show path to sshsync
   ```

   If not found, add to PATH:
   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

### Config File Issues

**Symptoms**: "Group not found" or "Host not found"

**Solutions**:

1. **Verify SSH config**:
   ```bash
   cat ~/.ssh/config
   # Check host aliases are correct
   ```

2. **Verify sshsync config**:
   ```bash
   cat ~/.config/sshsync/config.yaml
   # Check groups are defined
   ```

3. **Re-sync**:
   ```bash
   sshsync sync
   ```

### Test Failures

**Symptoms**: Tests fail with errors

**Solutions**:

1. **Check dependencies**:
   ```bash
   pip3 list | grep -E "sshsync|pyyaml"
   ```

2. **Check Python version**:
   ```bash
   python3 --version
   # Must be 3.10+
   ```

3. **Run tests individually**:
   ```bash
   python3 tests/test_helpers.py
   python3 tests/test_validation.py
   python3 tests/test_integration.py
   ```

## Post-Installation

### Recommended Next Steps

1. **Create more groups** for better organization:
   ```bash
   sshsync gadd staging
   sshsync gadd backup-servers
   ```

2. **Test file operations**:
   ```
   "Push test file to homelab machines (dry-run)"
   ```

3. **Set up automation**:
   - Create scripts for common tasks
   - Schedule backups
   - Automate deployments

4. **Review documentation**:
   - Read `references/sshsync-guide.md` for advanced sshsync usage
   - Read `references/tailscale-integration.md` for Tailscale tips

### Security Checklist

- ✅ SSH keys are password-protected
- ✅ SSH config has correct permissions (600)
- ✅ Private keys have correct permissions (600)
- ✅ Tailscale ACLs configured (if using teams)
- ✅ Only necessary hosts have SSH access
- ✅ Regularly review connected devices in Tailscale

## Summary

You now have:

1. ✅ Tailscale installed and connected
2. ✅ sshsync installed and configured
3. ✅ SSH keys set up on all machines
4. ✅ SSH config with all hosts
5. ✅ sshsync groups organized
6. ✅ Agent installed in Claude Code
7. ✅ Tests passing

**Start using**:

```
"Which machines are online?"
"Run this on the least loaded machine"
"Push files to production servers"
"Deploy to staging then production"
```

For more examples, see README.md and SKILL.md.

## Support

If you encounter issues:

1. Check this troubleshooting section
2. Review references/ for detailed guides
3. Check DECISIONS.md for architecture rationale
4. Run tests to verify installation

Happy automating! 🚀
