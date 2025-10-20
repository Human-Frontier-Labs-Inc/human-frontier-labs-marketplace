#!/usr/bin/env python3
"""
Helper utilities for Tailscale SSH Sync Agent.
Provides common formatting, parsing, and utility functions.
"""

import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import yaml
import logging

logger = logging.getLogger(__name__)


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes as human-readable string.

    Args:
        bytes_value: Number of bytes

    Returns:
        Formatted string (e.g., "12.3 MB", "1.5 GB")

    Example:
        >>> format_bytes(12582912)
        "12.0 MB"
        >>> format_bytes(1610612736)
        "1.5 GB"
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def format_duration(seconds: float) -> str:
    """
    Format duration as human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "2m 15s", "1h 30m")

    Example:
        >>> format_duration(135)
        "2m 15s"
        >>> format_duration(5430)
        "1h 30m 30s"
    """
    if seconds < 60:
        return f"{int(seconds)}s"

    minutes = int(seconds // 60)
    secs = int(seconds % 60)

    if minutes < 60:
        return f"{minutes}m {secs}s" if secs > 0 else f"{minutes}m"

    hours = minutes // 60
    minutes = minutes % 60

    parts = [f"{hours}h"]
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 and hours == 0:  # Only show seconds if < 1 hour
        parts.append(f"{secs}s")

    return " ".join(parts)


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format percentage with specified decimals.

    Args:
        value: Percentage value (0-100)
        decimals: Number of decimal places

    Returns:
        Formatted string (e.g., "45.5%")

    Example:
        >>> format_percentage(45.567)
        "45.6%"
    """
    return f"{value:.{decimals}f}%"


def parse_ssh_config(config_path: Optional[Path] = None) -> Dict[str, Dict[str, str]]:
    """
    Parse SSH config file for host definitions.

    Args:
        config_path: Path to SSH config (default: ~/.ssh/config)

    Returns:
        Dict mapping host aliases to their configuration:
        {
            'host-alias': {
                'hostname': '100.64.1.10',
                'user': 'admin',
                'port': '22',
                'identityfile': '~/.ssh/id_ed25519'
            }
        }

    Example:
        >>> hosts = parse_ssh_config()
        >>> hosts['homelab-1']['hostname']
        '100.64.1.10'
    """
    if config_path is None:
        config_path = Path.home() / '.ssh' / 'config'

    if not config_path.exists():
        logger.warning(f"SSH config not found: {config_path}")
        return {}

    hosts = {}
    current_host = None

    try:
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Host directive
                if line.lower().startswith('host '):
                    host_alias = line.split(maxsplit=1)[1]
                    # Skip wildcards
                    if '*' not in host_alias and '?' not in host_alias:
                        current_host = host_alias
                        hosts[current_host] = {}

                # Configuration directives
                elif current_host:
                    parts = line.split(maxsplit=1)
                    if len(parts) == 2:
                        key, value = parts
                        hosts[current_host][key.lower()] = value

        return hosts

    except Exception as e:
        logger.error(f"Error parsing SSH config: {e}")
        return {}


def parse_sshsync_config(config_path: Optional[Path] = None) -> Dict[str, List[str]]:
    """
    Parse sshsync config file for group definitions.

    Args:
        config_path: Path to sshsync config (default: ~/.config/sshsync/config.yaml)

    Returns:
        Dict mapping group names to list of hosts:
        {
            'production': ['prod-web-01', 'prod-db-01'],
            'development': ['dev-laptop', 'dev-desktop']
        }

    Example:
        >>> groups = parse_sshsync_config()
        >>> groups['production']
        ['prod-web-01', 'prod-db-01']
    """
    if config_path is None:
        config_path = Path.home() / '.config' / 'sshsync' / 'config.yaml'

    if not config_path.exists():
        logger.warning(f"sshsync config not found: {config_path}")
        return {}

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        return config.get('groups', {})

    except Exception as e:
        logger.error(f"Error parsing sshsync config: {e}")
        return {}


def get_timestamp(iso: bool = True) -> str:
    """
    Get current timestamp.

    Args:
        iso: If True, return ISO format; otherwise human-readable

    Returns:
        Timestamp string

    Example:
        >>> get_timestamp(iso=True)
        "2025-10-19T19:43:41Z"
        >>> get_timestamp(iso=False)
        "2025-10-19 19:43:41"
    """
    now = datetime.now()
    if iso:
        return now.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        return now.strftime("%Y-%m-%d %H:%M:%S")


def safe_execute(func, *args, default=None, **kwargs) -> Any:
    """
    Execute function with error handling.

    Args:
        func: Function to execute
        *args: Positional arguments
        default: Value to return on error
        **kwargs: Keyword arguments

    Returns:
        Function result or default on error

    Example:
        >>> safe_execute(int, "not_a_number", default=0)
        0
        >>> safe_execute(int, "42")
        42
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error executing {func.__name__}: {e}")
        return default


def validate_path(path: str, must_exist: bool = True) -> bool:
    """
    Check if path is valid and accessible.

    Args:
        path: Path to validate
        must_exist: If True, path must exist

    Returns:
        True if valid, False otherwise

    Example:
        >>> validate_path("/tmp")
        True
        >>> validate_path("/nonexistent", must_exist=True)
        False
    """
    p = Path(path).expanduser()

    if must_exist:
        return p.exists()
    else:
        # Check if parent directory exists (for paths that will be created)
        return p.parent.exists()


def parse_disk_usage(df_output: str) -> Dict[str, Any]:
    """
    Parse 'df' command output.

    Args:
        df_output: Output from 'df -h' command

    Returns:
        Dict with disk usage info:
        {
            'filesystem': '/dev/sda1',
            'size': '100G',
            'used': '45G',
            'available': '50G',
            'use_pct': 45,
            'mount': '/'
        }

    Example:
        >>> output = "Filesystem     Size  Used Avail Use% Mounted on\\n/dev/sda1      100G   45G   50G  45% /"
        >>> parse_disk_usage(output)
        {'filesystem': '/dev/sda1', 'size': '100G', ...}
    """
    lines = df_output.strip().split('\n')
    if len(lines) < 2:
        return {}

    # Parse last line (actual data, not header)
    data_line = lines[-1]
    parts = data_line.split()

    if len(parts) < 6:
        return {}

    try:
        return {
            'filesystem': parts[0],
            'size': parts[1],
            'used': parts[2],
            'available': parts[3],
            'use_pct': int(parts[4].rstrip('%')),
            'mount': parts[5]
        }
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing disk usage: {e}")
        return {}


def parse_memory_usage(free_output: str) -> Dict[str, Any]:
    """
    Parse 'free' command output (Linux).

    Args:
        free_output: Output from 'free -m' command

    Returns:
        Dict with memory info:
        {
            'total': 16384,  # MB
            'used': 8192,
            'free': 8192,
            'use_pct': 50.0
        }

    Example:
        >>> output = "Mem:   16384   8192   8192   0   0   0"
        >>> parse_memory_usage(output)
        {'total': 16384, 'used': 8192, ...}
    """
    lines = free_output.strip().split('\n')

    for line in lines:
        if line.startswith('Mem:'):
            parts = line.split()
            if len(parts) >= 3:
                try:
                    total = int(parts[1])
                    used = int(parts[2])
                    free = int(parts[3]) if len(parts) > 3 else (total - used)

                    return {
                        'total': total,
                        'used': used,
                        'free': free,
                        'use_pct': (used / total * 100) if total > 0 else 0
                    }
                except (ValueError, IndexError) as e:
                    logger.error(f"Error parsing memory usage: {e}")

    return {}


def parse_cpu_load(uptime_output: str) -> Dict[str, float]:
    """
    Parse 'uptime' command output for load averages.

    Args:
        uptime_output: Output from 'uptime' command

    Returns:
        Dict with load averages:
        {
            'load_1min': 0.45,
            'load_5min': 0.38,
            'load_15min': 0.32
        }

    Example:
        >>> output = "19:43:41 up 5 days, 2:15, 3 users, load average: 0.45, 0.38, 0.32"
        >>> parse_cpu_load(output)
        {'load_1min': 0.45, 'load_5min': 0.38, 'load_15min': 0.32}
    """
    # Find "load average:" part
    match = re.search(r'load average:\s+([\d.]+),\s+([\d.]+),\s+([\d.]+)', uptime_output)

    if match:
        try:
            return {
                'load_1min': float(match.group(1)),
                'load_5min': float(match.group(2)),
                'load_15min': float(match.group(3))
            }
        except ValueError as e:
            logger.error(f"Error parsing CPU load: {e}")

    return {}


def format_host_status(host: str, online: bool, groups: List[str],
                       latency: Optional[int] = None,
                       tailscale_connected: bool = False) -> str:
    """
    Format host status as display string.

    Args:
        host: Host name
        online: Whether host is online
        groups: List of groups host belongs to
        latency: Latency in ms (optional)
        tailscale_connected: Tailscale connection status

    Returns:
        Formatted status string

    Example:
        >>> format_host_status("web-01", True, ["production", "web"], 25, True)
        "🟢 web-01 (production, web) - Online - Tailscale: Connected | Latency: 25ms"
    """
    icon = "🟢" if online else "🔴"
    status = "Online" if online else "Offline"
    group_str = ", ".join(groups) if groups else "no group"

    parts = [f"{icon} {host} ({group_str}) - {status}"]

    if tailscale_connected:
        parts.append("Tailscale: Connected")

    if latency is not None and online:
        parts.append(f"Latency: {latency}ms")

    return " - ".join(parts)


def calculate_load_score(cpu_pct: float, mem_pct: float, disk_pct: float) -> float:
    """
    Calculate composite load score for a machine.

    Args:
        cpu_pct: CPU usage percentage (0-100)
        mem_pct: Memory usage percentage (0-100)
        disk_pct: Disk usage percentage (0-100)

    Returns:
        Load score (0-1, lower is better)

    Formula:
        score = (cpu * 0.4) + (mem * 0.3) + (disk * 0.3)

    Example:
        >>> calculate_load_score(45, 60, 40)
        0.48  # (0.45*0.4 + 0.60*0.3 + 0.40*0.3)
    """
    return (cpu_pct * 0.4 + mem_pct * 0.3 + disk_pct * 0.3) / 100


def classify_load_status(score: float) -> str:
    """
    Classify load score into status category.

    Args:
        score: Load score (0-1)

    Returns:
        Status string: "low", "moderate", or "high"

    Example:
        >>> classify_load_status(0.28)
        "low"
        >>> classify_load_status(0.55)
        "moderate"
        >>> classify_load_status(0.82)
        "high"
    """
    if score < 0.4:
        return "low"
    elif score < 0.7:
        return "moderate"
    else:
        return "high"


def classify_latency(latency_ms: int) -> Tuple[str, str]:
    """
    Classify network latency.

    Args:
        latency_ms: Latency in milliseconds

    Returns:
        Tuple of (status, description)

    Example:
        >>> classify_latency(25)
        ("excellent", "Ideal for interactive tasks")
        >>> classify_latency(150)
        ("fair", "May impact interactive workflows")
    """
    if latency_ms < 50:
        return ("excellent", "Ideal for interactive tasks")
    elif latency_ms < 100:
        return ("good", "Suitable for most operations")
    elif latency_ms < 200:
        return ("fair", "May impact interactive workflows")
    else:
        return ("poor", "Investigate network issues")


def get_hosts_from_groups(group: str, groups_config: Dict[str, List[str]]) -> List[str]:
    """
    Get list of hosts in a group.

    Args:
        group: Group name
        groups_config: Groups configuration dict

    Returns:
        List of host names in group

    Example:
        >>> groups = {'production': ['web-01', 'db-01']}
        >>> get_hosts_from_groups('production', groups)
        ['web-01', 'db-01']
    """
    return groups_config.get(group, [])


def get_groups_for_host(host: str, groups_config: Dict[str, List[str]]) -> List[str]:
    """
    Get list of groups a host belongs to.

    Args:
        host: Host name
        groups_config: Groups configuration dict

    Returns:
        List of group names

    Example:
        >>> groups = {'production': ['web-01'], 'web': ['web-01', 'web-02']}
        >>> get_groups_for_host('web-01', groups)
        ['production', 'web']
    """
    return [group for group, hosts in groups_config.items() if host in hosts]


def run_command(command: str, timeout: int = 10) -> Tuple[bool, str, str]:
    """
    Run shell command with timeout.

    Args:
        command: Command to execute
        timeout: Timeout in seconds

    Returns:
        Tuple of (success, stdout, stderr)

    Example:
        >>> success, stdout, stderr = run_command("echo hello")
        >>> success
        True
        >>> stdout.strip()
        "hello"
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return (
            result.returncode == 0,
            result.stdout,
            result.stderr
        )

    except subprocess.TimeoutExpired:
        return (False, "", f"Command timed out after {timeout}s")
    except Exception as e:
        return (False, "", str(e))


def main():
    """Test helper functions."""
    print("Testing helper functions...\n")

    # Test formatting
    print("1. Format bytes:")
    print(f"   12582912 bytes = {format_bytes(12582912)}")
    print(f"   1610612736 bytes = {format_bytes(1610612736)}")

    print("\n2. Format duration:")
    print(f"   135 seconds = {format_duration(135)}")
    print(f"   5430 seconds = {format_duration(5430)}")

    print("\n3. Format percentage:")
    print(f"   45.567 = {format_percentage(45.567)}")

    print("\n4. Calculate load score:")
    score = calculate_load_score(45, 60, 40)
    print(f"   CPU 45%, Mem 60%, Disk 40% = {score:.2f}")
    print(f"   Status: {classify_load_status(score)}")

    print("\n5. Classify latency:")
    latencies = [25, 75, 150, 250]
    for lat in latencies:
        status, desc = classify_latency(lat)
        print(f"   {lat}ms: {status} - {desc}")

    print("\n6. Parse SSH config:")
    ssh_hosts = parse_ssh_config()
    print(f"   Found {len(ssh_hosts)} hosts")

    print("\n7. Parse sshsync config:")
    groups = parse_sshsync_config()
    print(f"   Found {len(groups)} groups")
    for group, hosts in groups.items():
        print(f"   - {group}: {len(hosts)} hosts")

    print("\n✅ All helpers tested successfully")


if __name__ == "__main__":
    main()
