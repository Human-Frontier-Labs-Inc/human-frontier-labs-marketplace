#!/usr/bin/env python3
"""
Host validators for Tailscale SSH Sync Agent.
Validates host configuration and availability.
"""

import subprocess
from typing import List, Dict, Optional
from pathlib import Path
import logging

from .parameter_validator import ValidationError

logger = logging.getLogger(__name__)


def validate_ssh_config(host: str, config_path: Optional[Path] = None) -> bool:
    """
    Check if host has SSH config entry.

    Args:
        host: Host name to check
        config_path: Path to SSH config (default: ~/.ssh/config)

    Returns:
        True if host is in SSH config

    Raises:
        ValidationError: If host not found in config

    Example:
        >>> validate_ssh_config("web-01")
        True
    """
    if config_path is None:
        config_path = Path.home() / '.ssh' / 'config'

    if not config_path.exists():
        raise ValidationError(
            f"SSH config file not found: {config_path}\n"
            "Create ~/.ssh/config with your host definitions"
        )

    # Parse SSH config for this host
    host_found = False

    try:
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.lower().startswith('host ') and host in line:
                    host_found = True
                    break

        if not host_found:
            raise ValidationError(
                f"Host '{host}' not found in SSH config: {config_path}\n"
                "Add host to SSH config:\n"
                f"Host {host}\n"
                f"  HostName <IP_ADDRESS>\n"
                f"  User <USERNAME>"
            )

        return True

    except IOError as e:
        raise ValidationError(f"Error reading SSH config: {e}")


def validate_host_reachable(host: str, timeout: int = 5) -> bool:
    """
    Check if host is reachable via ping.

    Args:
        host: Host name to check
        timeout: Timeout in seconds

    Returns:
        True if host is reachable

    Raises:
        ValidationError: If host is not reachable

    Example:
        >>> validate_host_reachable("web-01", timeout=5)
        True
    """
    try:
        # Try to resolve via SSH config first
        result = subprocess.run(
            ["ssh", "-G", host],
            capture_output=True,
            text=True,
            timeout=2
        )

        if result.returncode == 0:
            # Extract hostname from SSH config
            for line in result.stdout.split('\n'):
                if line.startswith('hostname '):
                    actual_host = line.split()[1]
                    break
            else:
                actual_host = host
        else:
            actual_host = host

        # Ping the host
        ping_result = subprocess.run(
            ["ping", "-c", "1", "-W", str(timeout), actual_host],
            capture_output=True,
            text=True,
            timeout=timeout + 1
        )

        if ping_result.returncode == 0:
            return True
        else:
            raise ValidationError(
                f"Host '{host}' ({actual_host}) is not reachable\n"
                "Check:\n"
                "1. Host is powered on\n"
                "2. Tailscale is connected\n"
                "3. Network connectivity"
            )

    except subprocess.TimeoutExpired:
        raise ValidationError(f"Timeout checking host '{host}' (>{timeout}s)")
    except Exception as e:
        raise ValidationError(f"Error checking host '{host}': {e}")


def validate_group_members(group: str, groups_config: Dict[str, List[str]]) -> List[str]:
    """
    Ensure group has valid members.

    Args:
        group: Group name
        groups_config: Groups configuration dict

    Returns:
        List of valid hosts in group

    Raises:
        ValidationError: If group is empty or has no valid members

    Example:
        >>> groups = {'production': ['web-01', 'db-01']}
        >>> validate_group_members('production', groups)
        ['web-01', 'db-01']
    """
    if group not in groups_config:
        raise ValidationError(
            f"Group '{group}' not found in configuration\n"
            f"Available groups: {', '.join(groups_config.keys())}"
        )

    members = groups_config[group]

    if not members:
        raise ValidationError(
            f"Group '{group}' has no members\n"
            f"Add hosts to group with: sshsync gadd {group}"
        )

    if not isinstance(members, list):
        raise ValidationError(
            f"Invalid group configuration for '{group}': members must be a list"
        )

    return members


def get_invalid_hosts(hosts: List[str], config_path: Optional[Path] = None) -> List[str]:
    """
    Find hosts without valid SSH config.

    Args:
        hosts: List of host names
        config_path: Path to SSH config

    Returns:
        List of hosts without valid config

    Example:
        >>> get_invalid_hosts(["web-01", "nonexistent"])
        ["nonexistent"]
    """
    if config_path is None:
        config_path = Path.home() / '.ssh' / 'config'

    if not config_path.exists():
        return hosts  # All invalid if no config

    # Parse SSH config
    valid_hosts = set()
    try:
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.lower().startswith('host '):
                    host_alias = line.split(maxsplit=1)[1]
                    if '*' not in host_alias and '?' not in host_alias:
                        valid_hosts.add(host_alias)
    except IOError:
        return hosts

    # Find invalid hosts
    return [h for h in hosts if h not in valid_hosts]


def main():
    """Test host validators."""
    print("Testing host validators...\n")

    print("1. Testing validate_ssh_config():")
    try:
        validate_ssh_config("localhost")
        print("   ✓ localhost has SSH config")
    except ValidationError as e:
        print(f"   Note: {e.args[0].split(chr(10))[0]}")

    print("\n2. Testing get_invalid_hosts():")
    test_hosts = ["localhost", "nonexistent-host-12345"]
    invalid = get_invalid_hosts(test_hosts)
    print(f"   Invalid hosts: {invalid}")

    print("\n✅ Host validators tested")


if __name__ == "__main__":
    main()
