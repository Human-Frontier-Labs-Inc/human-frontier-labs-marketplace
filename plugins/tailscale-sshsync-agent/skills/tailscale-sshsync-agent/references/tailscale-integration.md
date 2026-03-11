# Tailscale Integration Guide

How to use Tailscale SSH with sshsync for secure, zero-config remote access.

## What is Tailscale?

Tailscale is a zero-config VPN that creates a secure network between your devices using WireGuard. It provides:

- **Peer-to-peer encrypted connections**
- **No port forwarding required**
- **Works across NATs and firewalls**
- **MagicDNS for easy device addressing**
- **Built-in SSH functionality**
- **Access control lists (ACLs)**

## Why Tailscale + sshsync?

Combining Tailscale with sshsync gives you:

1. **Secure connections** everywhere (Tailscale encryption)
2. **Simple addressing** (MagicDNS hostnames)
3. **Multi-host operations** (sshsync groups and execution)
4. **No firewall configuration** needed
5. **Works from anywhere** (coffee shop, home, office)

## Setup

### 1. Install Tailscale

**macOS**:
```bash
brew install tailscale
```

**Linux**:
```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

**Verify Installation**:
```bash
tailscale version
```

### 2. Connect to Tailscale

```bash
# Start Tailscale
sudo tailscale up

# Follow the authentication link
# This opens browser to authenticate

# Verify connection
tailscale status
```

### 3. Configure SSH via Tailscale

Tailscale provides two SSH options:

#### Option A: Tailscale SSH (Built-in)

**Enable on each machine**:
```bash
sudo tailscale up --ssh
```

**Use**:
```bash
tailscale ssh user@machine-name
```

**Advantages**:
- No SSH server configuration needed
- Uses Tailscale authentication
- Automatic key management

#### Option B: Standard SSH over Tailscale (Recommended for sshsync)

**Configure SSH config** to use Tailscale hostnames:

```bash
# ~/.ssh/config

Host homelab-1
  HostName homelab-1.tailnet-name.ts.net
  User admin
  IdentityFile ~/.ssh/id_ed25519

# Or use Tailscale IP directly
Host homelab-2
  HostName 100.64.1.10
  User admin
  IdentityFile ~/.ssh/id_ed25519
```

**Advantages**:
- Works with all SSH tools (including sshsync)
- Standard SSH key authentication
- More flexibility

## Getting Tailscale Hostnames and IPs

### View All Machines

```bash
tailscale status
```

**Output**:
```
100.64.1.10  homelab-1    user@    linux   -
100.64.1.11  homelab-2    user@    linux   -
100.64.1.20  laptop       user@    macOS   -
100.64.1.30  phone        user@    iOS     offline
```

### Get MagicDNS Hostname

**Format**: `machine-name.tailnet-name.ts.net`

**Find your tailnet name**:
```bash
tailscale status --json | grep -i tailnet
```

Or check in Tailscale admin console: https://login.tailscale.com/admin/machines

### Get Tailscale IP

```bash
# Your own IP
tailscale ip -4

# Another machine's IP (from status output)
tailscale status | grep machine-name
```

## Testing Connectivity

### Ping via Tailscale

```bash
# Ping by hostname
tailscale ping homelab-1

# Ping by IP
tailscale ping 100.64.1.10
```

**Successful output**:
```
pong from homelab-1 (100.64.1.10) via DERP(nyc) in 45ms
pong from homelab-1 (100.64.1.10) via DERP(nyc) in 43ms
```

**Failed output**:
```
timeout waiting for pong
```

### SSH Test

```bash
# Test SSH connection
ssh user@homelab-1.tailnet.ts.net

# Or with IP
ssh user@100.64.1.10
```

## Configuring sshsync with Tailscale

### Step 1: Add Tailscale Hosts to SSH Config

```bash
vim ~/.ssh/config
```

**Example configuration**:
```
# Production servers
Host prod-web-01
  HostName prod-web-01.tailnet.ts.net
  User deploy
  IdentityFile ~/.ssh/id_ed25519

Host prod-web-02
  HostName prod-web-02.tailnet.ts.net
  User deploy
  IdentityFile ~/.ssh/id_ed25519

Host prod-db-01
  HostName prod-db-01.tailnet.ts.net
  User deploy
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

# Development
Host dev-laptop
  HostName dev-laptop.tailnet.ts.net
  User developer
  IdentityFile ~/.ssh/id_ed25519
```

### Step 2: Test Each Host

```bash
# Test connectivity to each host
ssh prod-web-01 "hostname"
ssh homelab-1 "hostname"
ssh dev-laptop "hostname"
```

### Step 3: Initialize sshsync

```bash
# Sync hosts and create groups
sshsync sync

# Add hosts to groups
sshsync gadd production
# Select: prod-web-01, prod-web-02, prod-db-01

sshsync gadd homelab
# Select: homelab-1, homelab-2

sshsync gadd development
# Select: dev-laptop
```

### Step 4: Verify Configuration

```bash
# List all hosts with status
sshsync ls --with-status

# Test command execution
sshsync all "uptime"

# Test group execution
sshsync group production "df -h"
```

## Advanced Tailscale Features

### Tailnet Lock

Prevents unauthorized device additions:

```bash
tailscale lock status
```

### Exit Nodes

Route all traffic through a specific machine:

```bash
# Enable exit node on a machine
sudo tailscale up --advertise-exit-node

# Use exit node from another machine
sudo tailscale set --exit-node=exit-node-name
```

### Subnet Routing

Access networks behind Tailscale machines:

```bash
# Advertise subnet routes
sudo tailscale up --advertise-routes=192.168.1.0/24
```

### ACLs (Access Control Lists)

Control who can access what: https://login.tailscale.com/admin/acls

**Example ACL**:
```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["group:admins"],
      "dst": ["*:22", "*:80", "*:443"]
    },
    {
      "action": "accept",
      "src": ["group:developers"],
      "dst": ["tag:development:*"]
    }
  ]
}
```

## Troubleshooting

### Machine Shows Offline

**Check Tailscale status**:
```bash
tailscale status
```

**Restart Tailscale**:
```bash
# macOS
brew services restart tailscale

# Linux
sudo systemctl restart tailscaled
```

**Re-authenticate**:
```bash
sudo tailscale up
```

### Cannot Connect via SSH

1. **Verify Tailscale connectivity**:
   ```bash
   tailscale ping machine-name
   ```

2. **Check SSH is running** on remote:
   ```bash
   tailscale ssh machine-name "systemctl status sshd"
   ```

3. **Verify SSH keys**:
   ```bash
   ssh-add -l
   ```

4. **Test SSH directly**:
   ```bash
   ssh -v user@machine-name.tailnet.ts.net
   ```

### High Latency

**Check connection method**:
```bash
tailscale status
```

Look for "direct" vs "DERP relay":
- **Direct**: Low latency (< 50ms)
- **DERP relay**: Higher latency (100-200ms)

**Force direct connection**:
```bash
# Ensure both machines can establish P2P
# May require NAT traversal
```

### MagicDNS Not Working

**Enable MagicDNS**:
1. Go to https://login.tailscale.com/admin/dns
2. Enable MagicDNS

**Verify**:
```bash
nslookup machine-name.tailnet.ts.net
```

## Security Best Practices

1. **Use SSH keys**, not passwords
2. **Enable Tailnet Lock** to prevent unauthorized devices
3. **Use ACLs** to restrict access
4. **Regularly review** connected devices
5. **Set up key expiry** for team members who leave
6. **Use tags** for machine roles
7. **Enable two-factor auth** for Tailscale account

## Monitoring

### Check Network Status

```bash
# All machines
tailscale status

# Self status
tailscale status --self

# JSON format for parsing
tailscale status --json
```

### View Logs

```bash
# macOS
tail -f /var/log/tailscaled.log

# Linux
journalctl -u tailscaled -f
```

## Use Cases with sshsync

### 1. Deploy to All Production Servers

```bash
sshsync push --group production --recurse ./dist /var/www/app
sshsync group production "cd /var/www/app && pm2 restart all"
```

### 2. Collect Logs from All Servers

```bash
sshsync pull --group production /var/log/app/error.log ./logs/
```

### 3. Update All Homelab Machines

```bash
sshsync group homelab "sudo apt update && sudo apt upgrade -y"
```

### 4. Check Disk Space Everywhere

```bash
sshsync all "df -h /"
```

### 5. Sync Configuration Across Machines

```bash
sshsync push --all ~/dotfiles/.bashrc ~/.bashrc
sshsync push --all ~/dotfiles/.vimrc ~/.vimrc
```

## Summary

Tailscale + sshsync = **Powerful Remote Management**

- ✅ Secure connections everywhere (WireGuard encryption)
- ✅ No firewall configuration needed
- ✅ Easy addressing (MagicDNS)
- ✅ Multi-host operations (sshsync groups)
- ✅ Works from anywhere

**Quick Start**:
1. Install Tailscale: `brew install tailscale`
2. Connect: `sudo tailscale up`
3. Configure SSH config with Tailscale hostnames
4. Initialize sshsync: `sshsync sync`
5. Start managing: `sshsync all "uptime"`

For more: https://tailscale.com/kb/
