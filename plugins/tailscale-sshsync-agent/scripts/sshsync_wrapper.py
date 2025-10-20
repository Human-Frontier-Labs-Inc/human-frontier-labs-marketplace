#!/usr/bin/env python3
"""
SSH Sync wrapper for Tailscale SSH Sync Agent.
Python interface to sshsync CLI operations.
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import logging

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.helpers import parse_ssh_config, parse_sshsync_config, format_bytes, format_duration
from utils.validators import validate_host, validate_group, validate_path_exists, validate_timeout, validate_command

logger = logging.getLogger(__name__)


def get_host_status(group: Optional[str] = None) -> Dict:
    """
    Get online/offline status of hosts.

    Args:
        group: Optional group to filter (None = all hosts)

    Returns:
        Dict with status info

    Example:
        >>> status = get_host_status()
        >>> status['online_count']
        8
    """
    try:
        # Run sshsync ls --with-status
        cmd = ["sshsync", "ls", "--with-status"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            return {'error': result.stderr, 'hosts': []}

        # Parse output
        hosts = []
        for line in result.stdout.strip().split('\n'):
            if not line or line.startswith('Host') or line.startswith('---'):
                continue

            parts = line.split()
            if len(parts) >= 2:
                host_name = parts[0]
                status = parts[1] if len(parts) > 1 else 'unknown'

                hosts.append({
                    'host': host_name,
                    'online': status.lower() in ['online', 'reachable', '✓'],
                    'status': status
                })

        # Filter by group if specified
        if group:
            groups_config = parse_sshsync_config()
            group_hosts = groups_config.get(group, [])
            hosts = [h for h in hosts if h['host'] in group_hosts]

        online_count = sum(1 for h in hosts if h['online'])

        return {
            'hosts': hosts,
            'total_count': len(hosts),
            'online_count': online_count,
            'offline_count': len(hosts) - online_count,
            'availability_pct': (online_count / len(hosts) * 100) if hosts else 0
        }

    except Exception as e:
        logger.error(f"Error getting host status: {e}")
        return {'error': str(e), 'hosts': []}


def execute_on_all(command: str, timeout: int = 10, dry_run: bool = False) -> Dict:
    """
    Execute command on all hosts.

    Args:
        command: Command to execute
        timeout: Timeout in seconds
        dry_run: If True, don't actually execute

    Returns:
        Dict with results per host

    Example:
        >>> result = execute_on_all("uptime", timeout=15)
        >>> len(result['results'])
        10
    """
    validate_command(command)
    validate_timeout(timeout)

    if dry_run:
        return {
            'dry_run': True,
            'command': command,
            'message': 'Would execute on all hosts'
        }

    try:
        cmd = ["sshsync", "all", f"--timeout={timeout}", command]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 30)

        # Parse results (format varies, simplified here)
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'command': command
        }

    except subprocess.TimeoutExpired:
        return {'error': f'Command timed out after {timeout}s'}
    except Exception as e:
        return {'error': str(e)}


def execute_on_group(group: str, command: str, timeout: int = 10, dry_run: bool = False) -> Dict:
    """
    Execute command on specific group.

    Args:
        group: Group name
        command: Command to execute
        timeout: Timeout in seconds
        dry_run: Preview without executing

    Returns:
        Dict with execution results

    Example:
        >>> result = execute_on_group("web-servers", "df -h /var/www")
        >>> result['success']
        True
    """
    groups_config = parse_sshsync_config()
    validate_group(group, list(groups_config.keys()))
    validate_command(command)
    validate_timeout(timeout)

    if dry_run:
        group_hosts = groups_config.get(group, [])
        return {
            'dry_run': True,
            'group': group,
            'hosts': group_hosts,
            'command': command,
            'message': f'Would execute on {len(group_hosts)} hosts in group {group}'
        }

    try:
        cmd = ["sshsync", "group", f"--timeout={timeout}", group, command]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 30)

        return {
            'success': result.returncode == 0,
            'group': group,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'command': command
        }

    except subprocess.TimeoutExpired:
        return {'error': f'Command timed out after {timeout}s'}
    except Exception as e:
        return {'error': str(e)}


def execute_on_host(host: str, command: str, timeout: int = 10) -> Dict:
    """
    Execute command on single host.

    Args:
        host: Host name
        command: Command to execute
        timeout: Timeout in seconds

    Returns:
        Dict with result

    Example:
        >>> result = execute_on_host("web-01", "hostname")
        >>> result['stdout']
        "web-01"
    """
    ssh_hosts = parse_ssh_config()
    validate_host(host, list(ssh_hosts.keys()))
    validate_command(command)
    validate_timeout(timeout)

    try:
        cmd = ["ssh", "-o", f"ConnectTimeout={timeout}", host, command]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)

        return {
            'success': result.returncode == 0,
            'host': host,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'command': command
        }

    except subprocess.TimeoutExpired:
        return {'error': f'Command timed out after {timeout}s'}
    except Exception as e:
        return {'error': str(e)}


def push_to_hosts(local_path: str, remote_path: str,
                  hosts: Optional[List[str]] = None,
                  group: Optional[str] = None,
                  recurse: bool = False,
                  dry_run: bool = False) -> Dict:
    """
    Push files to hosts.

    Args:
        local_path: Local file/directory path
        remote_path: Remote destination path
        hosts: Specific hosts (None = all if group also None)
        group: Group name
        recurse: Recursive copy
        dry_run: Preview without executing

    Returns:
        Dict with push results

    Example:
        >>> result = push_to_hosts("./dist", "/var/www/app", group="production", recurse=True)
        >>> result['success']
        True
    """
    validate_path_exists(local_path)

    if dry_run:
        return {
            'dry_run': True,
            'local_path': local_path,
            'remote_path': remote_path,
            'hosts': hosts,
            'group': group,
            'recurse': recurse,
            'message': 'Would push files'
        }

    try:
        cmd = ["sshsync", "push"]

        if hosts:
            for host in hosts:
                cmd.extend(["--host", host])
        elif group:
            cmd.extend(["--group", group])
        else:
            cmd.append("--all")

        if recurse:
            cmd.append("--recurse")

        cmd.extend([local_path, remote_path])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'local_path': local_path,
            'remote_path': remote_path
        }

    except subprocess.TimeoutExpired:
        return {'error': 'Push operation timed out'}
    except Exception as e:
        return {'error': str(e)}


def pull_from_host(host: str, remote_path: str, local_path: str,
                   recurse: bool = False, dry_run: bool = False) -> Dict:
    """
    Pull files from host.

    Args:
        host: Host to pull from
        remote_path: Remote file/directory path
        local_path: Local destination path
        recurse: Recursive copy
        dry_run: Preview without executing

    Returns:
        Dict with pull results

    Example:
        >>> result = pull_from_host("web-01", "/var/log/nginx", "./logs", recurse=True)
        >>> result['success']
        True
    """
    ssh_hosts = parse_ssh_config()
    validate_host(host, list(ssh_hosts.keys()))

    if dry_run:
        return {
            'dry_run': True,
            'host': host,
            'remote_path': remote_path,
            'local_path': local_path,
            'recurse': recurse,
            'message': f'Would pull from {host}'
        }

    try:
        cmd = ["sshsync", "pull", "--host", host]

        if recurse:
            cmd.append("--recurse")

        cmd.extend([remote_path, local_path])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        return {
            'success': result.returncode == 0,
            'host': host,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'remote_path': remote_path,
            'local_path': local_path
        }

    except subprocess.TimeoutExpired:
        return {'error': 'Pull operation timed out'}
    except Exception as e:
        return {'error': str(e)}


def list_hosts(with_status: bool = True) -> Dict:
    """
    List all configured hosts.

    Args:
        with_status: Include online/offline status

    Returns:
        Dict with hosts info

    Example:
        >>> result = list_hosts(with_status=True)
        >>> len(result['hosts'])
        10
    """
    if with_status:
        return get_host_status()
    else:
        ssh_hosts = parse_ssh_config()
        return {
            'hosts': [{'host': name} for name in ssh_hosts.keys()],
            'count': len(ssh_hosts)
        }


def get_groups() -> Dict[str, List[str]]:
    """
    Get all defined groups and their members.

    Returns:
        Dict mapping group names to host lists

    Example:
        >>> groups = get_groups()
        >>> groups['production']
        ['prod-web-01', 'prod-db-01']
    """
    return parse_sshsync_config()


def main():
    """Test sshsync wrapper functions."""
    print("Testing sshsync wrapper...\n")

    print("1. List hosts:")
    result = list_hosts(with_status=False)
    print(f"   Found {result.get('count', 0)} hosts")

    print("\n2. Get groups:")
    groups = get_groups()
    print(f"   Found {len(groups)} groups")
    for group, hosts in groups.items():
        print(f"   - {group}: {len(hosts)} hosts")

    print("\n3. Test dry-run:")
    result = execute_on_all("uptime", dry_run=True)
    print(f"   Dry-run: {result.get('message', 'OK')}")

    print("\n✅ sshsync wrapper tested")


if __name__ == "__main__":
    main()
