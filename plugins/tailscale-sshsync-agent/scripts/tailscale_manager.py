#!/usr/bin/env python3
"""
Tailscale manager for Tailscale SSH Sync Agent.
Tailscale-specific operations and status management.
"""

import subprocess
import re
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TailscalePeer:
    """Represents a Tailscale peer."""
    hostname: str
    ip: str
    online: bool
    last_seen: Optional[str] = None
    os: Optional[str] = None
    relay: Optional[str] = None


def get_tailscale_status() -> Dict:
    """
    Get Tailscale network status (all peers).

    Returns:
        Dict with network status:
        {
            'connected': bool,
            'peers': List[TailscalePeer],
            'online_count': int,
            'total_count': int,
            'self_ip': str
        }

    Example:
        >>> status = get_tailscale_status()
        >>> status['online_count']
        8
        >>> status['peers'][0].hostname
        'homelab-1'
    """
    try:
        # Get status in JSON format
        result = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            # Try text format if JSON fails
            result = subprocess.run(
                ["tailscale", "status"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return {
                    'connected': False,
                    'error': 'Tailscale not running or accessible',
                    'peers': []
                }

            # Parse text format
            return _parse_text_status(result.stdout)

        # Parse JSON format
        data = json.loads(result.stdout)
        return _parse_json_status(data)

    except FileNotFoundError:
        return {
            'connected': False,
            'error': 'Tailscale not installed',
            'peers': []
        }
    except subprocess.TimeoutExpired:
        return {
            'connected': False,
            'error': 'Timeout getting Tailscale status',
            'peers': []
        }
    except Exception as e:
        logger.error(f"Error getting Tailscale status: {e}")
        return {
            'connected': False,
            'error': str(e),
            'peers': []
        }


def _parse_json_status(data: Dict) -> Dict:
    """Parse Tailscale JSON status."""
    peers = []

    self_data = data.get('Self', {})
    self_ip = self_data.get('TailscaleIPs', [''])[0]

    for peer_id, peer_data in data.get('Peer', {}).items():
        hostname = peer_data.get('HostName', 'unknown')
        ips = peer_data.get('TailscaleIPs', [])
        ip = ips[0] if ips else 'unknown'
        online = peer_data.get('Online', False)
        os = peer_data.get('OS', 'unknown')

        peers.append(TailscalePeer(
            hostname=hostname,
            ip=ip,
            online=online,
            os=os
        ))

    online_count = sum(1 for p in peers if p.online)

    return {
        'connected': True,
        'peers': peers,
        'online_count': online_count,
        'total_count': len(peers),
        'self_ip': self_ip
    }


def _parse_text_status(output: str) -> Dict:
    """Parse Tailscale text status output."""
    peers = []
    self_ip = None

    for line in output.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        # Parse format: hostname  ip  status  ...
        parts = line.split()
        if len(parts) >= 2:
            hostname = parts[0]
            ip = parts[1] if len(parts) > 1 else 'unknown'

            # Check for self (usually marked with *)
            if hostname.endswith('-'):
                self_ip = ip
                continue

            # Determine online status from additional fields
            online = 'offline' not in line.lower()

            peers.append(TailscalePeer(
                hostname=hostname,
                ip=ip,
                online=online
            ))

    online_count = sum(1 for p in peers if p.online)

    return {
        'connected': True,
        'peers': peers,
        'online_count': online_count,
        'total_count': len(peers),
        'self_ip': self_ip or 'unknown'
    }


def check_connectivity(host: str, timeout: int = 5) -> bool:
    """
    Ping host via Tailscale.

    Args:
        host: Hostname to ping
        timeout: Timeout in seconds

    Returns:
        True if host responds to ping

    Example:
        >>> check_connectivity("homelab-1")
        True
    """
    try:
        result = subprocess.run(
            ["tailscale", "ping", "--timeout", f"{timeout}s", "--c", "1", host],
            capture_output=True,
            text=True,
            timeout=timeout + 2
        )

        # Check if ping succeeded
        return result.returncode == 0 or 'pong' in result.stdout.lower()

    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    except Exception as e:
        logger.error(f"Error pinging {host}: {e}")
        return False


def get_peer_info(hostname: str) -> Optional[TailscalePeer]:
    """
    Get detailed info about a specific peer.

    Args:
        hostname: Peer hostname

    Returns:
        TailscalePeer object or None if not found

    Example:
        >>> peer = get_peer_info("homelab-1")
        >>> peer.ip
        '100.64.1.10'
    """
    status = get_tailscale_status()

    if not status.get('connected'):
        return None

    for peer in status.get('peers', []):
        if peer.hostname == hostname or hostname in peer.hostname:
            return peer

    return None


def list_online_machines() -> List[str]:
    """
    List all online Tailscale machines.

    Returns:
        List of online machine hostnames

    Example:
        >>> machines = list_online_machines()
        >>> len(machines)
        8
    """
    status = get_tailscale_status()

    if not status.get('connected'):
        return []

    return [
        peer.hostname
        for peer in status.get('peers', [])
        if peer.online
    ]


def get_machine_ip(hostname: str) -> Optional[str]:
    """
    Get Tailscale IP for a machine.

    Args:
        hostname: Machine hostname

    Returns:
        IP address or None if not found

    Example:
        >>> ip = get_machine_ip("homelab-1")
        >>> ip
        '100.64.1.10'
    """
    peer = get_peer_info(hostname)
    return peer.ip if peer else None


def validate_tailscale_ssh(host: str, timeout: int = 10) -> Dict:
    """
    Check if Tailscale SSH is working for a host.

    Args:
        host: Host to check
        timeout: Connection timeout

    Returns:
        Dict with validation results:
        {
            'working': bool,
            'message': str,
            'details': Dict
        }

    Example:
        >>> result = validate_tailscale_ssh("homelab-1")
        >>> result['working']
        True
    """
    # First check if host is in Tailscale network
    peer = get_peer_info(host)

    if not peer:
        return {
            'working': False,
            'message': f'Host {host} not found in Tailscale network',
            'details': {'peer_found': False}
        }

    if not peer.online:
        return {
            'working': False,
            'message': f'Host {host} is offline in Tailscale',
            'details': {'peer_found': True, 'online': False}
        }

    # Check connectivity
    if not check_connectivity(host, timeout=timeout):
        return {
            'working': False,
            'message': f'Cannot ping {host} via Tailscale',
            'details': {'peer_found': True, 'online': True, 'ping': False}
        }

    # Try SSH connection
    try:
        result = subprocess.run(
            ["tailscale", "ssh", host, "echo", "test"],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode == 0:
            return {
                'working': True,
                'message': f'Tailscale SSH to {host} is working',
                'details': {
                    'peer_found': True,
                    'online': True,
                    'ping': True,
                    'ssh': True,
                    'ip': peer.ip
                }
            }
        else:
            return {
                'working': False,
                'message': f'Tailscale SSH failed: {result.stderr}',
                'details': {
                    'peer_found': True,
                    'online': True,
                    'ping': True,
                    'ssh': False,
                    'error': result.stderr
                }
            }

    except subprocess.TimeoutExpired:
        return {
            'working': False,
            'message': f'Tailscale SSH timed out after {timeout}s',
            'details': {'timeout': True}
        }
    except Exception as e:
        return {
            'working': False,
            'message': f'Error testing Tailscale SSH: {e}',
            'details': {'error': str(e)}
        }


def get_network_summary() -> str:
    """
    Get human-readable network summary.

    Returns:
        Formatted summary string

    Example:
        >>> print(get_network_summary())
        Tailscale Network: Connected
        Online: 8/10 machines (80%)
        Self IP: 100.64.1.5
    """
    status = get_tailscale_status()

    if not status.get('connected'):
        return "Tailscale Network: Not connected\nError: {}".format(
            status.get('error', 'Unknown error')
        )

    lines = [
        "Tailscale Network: Connected",
        f"Online: {status['online_count']}/{status['total_count']} machines ({status['online_count']/status['total_count']*100:.0f}%)",
        f"Self IP: {status.get('self_ip', 'unknown')}"
    ]

    return "\n".join(lines)


def main():
    """Test Tailscale manager functions."""
    print("Testing Tailscale manager...\n")

    print("1. Get Tailscale status:")
    status = get_tailscale_status()
    if status.get('connected'):
        print(f"   ✓ Connected")
        print(f"   Peers: {status['total_count']} total, {status['online_count']} online")
    else:
        print(f"   ✗ Not connected: {status.get('error', 'Unknown error')}")

    print("\n2. List online machines:")
    machines = list_online_machines()
    print(f"   Found {len(machines)} online machines")
    for machine in machines[:5]:  # Show first 5
        print(f"   - {machine}")

    print("\n3. Network summary:")
    print(get_network_summary())

    print("\n✅ Tailscale manager tested")


if __name__ == "__main__":
    main()
