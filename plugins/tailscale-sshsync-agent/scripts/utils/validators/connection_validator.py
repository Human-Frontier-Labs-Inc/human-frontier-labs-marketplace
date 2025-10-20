#!/usr/bin/env python3
"""
Connection validators for Tailscale SSH Sync Agent.
Validates SSH and Tailscale connections.
"""

import subprocess
from typing import Dict, Optional
import logging

from .parameter_validator import ValidationError

logger = logging.getLogger(__name__)


def validate_ssh_connection(host: str, timeout: int = 10) -> bool:
    """
    Test SSH connection works.

    Args:
        host: Host to connect to
        timeout: Connection timeout in seconds

    Returns:
        True if SSH connection successful

    Raises:
        ValidationError: If connection fails

    Example:
        >>> validate_ssh_connection("web-01")
        True
    """
    try:
        # Try to execute a simple command via SSH
        result = subprocess.run(
            ["ssh", "-o", "ConnectTimeout={}".format(timeout),
             "-o", "BatchMode=yes",
             "-o", "StrictHostKeyChecking=no",
             host, "echo", "test"],
            capture_output=True,
            text=True,
            timeout=timeout + 5
        )

        if result.returncode == 0:
            return True
        else:
            # Parse error message
            error_msg = result.stderr.strip()

            if "Permission denied" in error_msg:
                raise ValidationError(
                    f"SSH authentication failed for '{host}'\n"
                    "Check:\n"
                    "1. SSH key is added: ssh-add -l\n"
                    "2. Public key is on remote: cat ~/.ssh/authorized_keys\n"
                    "3. User/key in SSH config is correct"
                )
            elif "Connection refused" in error_msg:
                raise ValidationError(
                    f"SSH connection refused for '{host}'\n"
                    "Check:\n"
                    "1. SSH server is running on remote\n"
                    "2. Port 22 is not blocked by firewall"
                )
            elif "Connection timed out" in error_msg or "timeout" in error_msg.lower():
                raise ValidationError(
                    f"SSH connection timed out for '{host}'\n"
                    "Check:\n"
                    "1. Host is reachable (ping test)\n"
                    "2. Tailscale is connected\n"
                    "3. Network connectivity"
                )
            else:
                raise ValidationError(
                    f"SSH connection failed for '{host}': {error_msg}"
                )

    except subprocess.TimeoutExpired:
        raise ValidationError(
            f"SSH connection timed out for '{host}' (>{timeout}s)"
        )
    except Exception as e:
        raise ValidationError(f"Error testing SSH connection to '{host}': {e}")


def validate_tailscale_connection(host: str) -> bool:
    """
    Test Tailscale connectivity to host.

    Args:
        host: Host to check

    Returns:
        True if Tailscale connection active

    Raises:
        ValidationError: If Tailscale not connected

    Example:
        >>> validate_tailscale_connection("web-01")
        True
    """
    try:
        # Check if tailscale is running
        result = subprocess.run(
            ["tailscale", "status"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            raise ValidationError(
                "Tailscale is not running\n"
                "Start Tailscale: sudo tailscale up"
            )

        # Check if specific host is in the network
        if host in result.stdout or host.replace('-', '.') in result.stdout:
            return True
        else:
            raise ValidationError(
                f"Host '{host}' not found in Tailscale network\n"
                "Ensure host is:\n"
                "1. Connected to Tailscale\n"
                "2. In the same tailnet\n"
                "3. Not expired/offline"
            )

    except FileNotFoundError:
        raise ValidationError(
            "Tailscale not installed\n"
            "Install: https://tailscale.com/download"
        )
    except subprocess.TimeoutExpired:
        raise ValidationError("Timeout checking Tailscale status")
    except Exception as e:
        raise ValidationError(f"Error checking Tailscale connection: {e}")


def validate_ssh_key(host: str) -> bool:
    """
    Check SSH key authentication is working.

    Args:
        host: Host to check

    Returns:
        True if SSH key auth works

    Raises:
        ValidationError: If key auth fails

    Example:
        >>> validate_ssh_key("web-01")
        True
    """
    try:
        # Test connection with explicit key-only auth
        result = subprocess.run(
            ["ssh", "-o", "BatchMode=yes",
             "-o", "PasswordAuthentication=no",
             "-o", "ConnectTimeout=5",
             host, "echo", "test"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return True
        else:
            error_msg = result.stderr.strip()

            if "Permission denied" in error_msg:
                raise ValidationError(
                    f"SSH key authentication failed for '{host}'\n"
                    "Fix:\n"
                    "1. Add your SSH key: ssh-add ~/.ssh/id_ed25519\n"
                    "2. Copy public key to remote: ssh-copy-id {}\n"
                    "3. Verify: ssh -v {} 2>&1 | grep -i 'offering public key'".format(host, host)
                )
            else:
                raise ValidationError(
                    f"SSH key validation failed for '{host}': {error_msg}"
                )

    except subprocess.TimeoutExpired:
        raise ValidationError(f"Timeout validating SSH key for '{host}'")
    except Exception as e:
        raise ValidationError(f"Error validating SSH key for '{host}': {e}")


def get_connection_diagnostics(host: str) -> Dict[str, any]:
    """
    Comprehensive connection testing.

    Args:
        host: Host to diagnose

    Returns:
        Dict with diagnostic results:
        {
            'ping': {'success': bool, 'message': str},
            'ssh': {'success': bool, 'message': str},
            'tailscale': {'success': bool, 'message': str},
            'ssh_key': {'success': bool, 'message': str}
        }

    Example:
        >>> diag = get_connection_diagnostics("web-01")
        >>> diag['ssh']['success']
        True
    """
    diagnostics = {}

    # Test 1: Ping
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "2", host],
            capture_output=True,
            timeout=3
        )
        diagnostics['ping'] = {
            'success': result.returncode == 0,
            'message': 'Host is reachable' if result.returncode == 0 else 'Host not reachable'
        }
    except Exception as e:
        diagnostics['ping'] = {'success': False, 'message': str(e)}

    # Test 2: SSH connection
    try:
        validate_ssh_connection(host, timeout=5)
        diagnostics['ssh'] = {'success': True, 'message': 'SSH connection works'}
    except ValidationError as e:
        diagnostics['ssh'] = {'success': False, 'message': str(e).split('\n')[0]}

    # Test 3: Tailscale
    try:
        validate_tailscale_connection(host)
        diagnostics['tailscale'] = {'success': True, 'message': 'Tailscale connected'}
    except ValidationError as e:
        diagnostics['tailscale'] = {'success': False, 'message': str(e).split('\n')[0]}

    # Test 4: SSH key
    try:
        validate_ssh_key(host)
        diagnostics['ssh_key'] = {'success': True, 'message': 'SSH key authentication works'}
    except ValidationError as e:
        diagnostics['ssh_key'] = {'success': False, 'message': str(e).split('\n')[0]}

    return diagnostics


def main():
    """Test connection validators."""
    print("Testing connection validators...\n")

    print("1. Testing connection diagnostics:")
    try:
        diag = get_connection_diagnostics("localhost")
        print("   Results:")
        for test, result in diag.items():
            status = "✓" if result['success'] else "✗"
            print(f"   {status} {test}: {result['message']}")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n✅ Connection validators tested")


if __name__ == "__main__":
    main()
