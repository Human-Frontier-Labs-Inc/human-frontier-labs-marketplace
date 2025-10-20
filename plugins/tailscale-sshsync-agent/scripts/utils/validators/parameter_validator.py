#!/usr/bin/env python3
"""
Parameter validators for Tailscale SSH Sync Agent.
Validates user inputs before making operations.
"""

from typing import List, Optional
from pathlib import Path
import re
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_host(host: str, valid_hosts: Optional[List[str]] = None) -> str:
    """
    Validate host parameter.

    Args:
        host: Host name or alias
        valid_hosts: List of valid hosts (None to skip check)

    Returns:
        str: Validated and normalized host name

    Raises:
        ValidationError: If host is invalid

    Example:
        >>> validate_host("web-01")
        "web-01"
        >>> validate_host("web-01", ["web-01", "web-02"])
        "web-01"
    """
    if not host:
        raise ValidationError("Host cannot be empty")

    if not isinstance(host, str):
        raise ValidationError(f"Host must be string, got {type(host)}")

    # Normalize (strip whitespace, lowercase for comparison)
    host = host.strip()

    # Basic validation: alphanumeric, dash, underscore, dot
    if not re.match(r'^[a-zA-Z0-9._-]+$', host):
        raise ValidationError(
            f"Invalid host name format: {host}\n"
            "Host names must contain only letters, numbers, dots, dashes, and underscores"
        )

    # Check if valid (if list provided)
    if valid_hosts:
        # Try exact match first
        if host in valid_hosts:
            return host

        # Try case-insensitive match
        for valid_host in valid_hosts:
            if host.lower() == valid_host.lower():
                return valid_host

        # Not found - provide suggestions
        suggestions = [h for h in valid_hosts if host[:3].lower() in h.lower()]
        raise ValidationError(
            f"Invalid host: {host}\n"
            f"Valid options: {', '.join(valid_hosts[:10])}\n"
            + (f"Did you mean: {', '.join(suggestions[:3])}?" if suggestions else "")
        )

    return host


def validate_group(group: str, valid_groups: Optional[List[str]] = None) -> str:
    """
    Validate group parameter.

    Args:
        group: Group name
        valid_groups: List of valid groups (None to skip check)

    Returns:
        str: Validated group name

    Raises:
        ValidationError: If group is invalid

    Example:
        >>> validate_group("production")
        "production"
        >>> validate_group("prod", ["production", "development"])
        ValidationError: Invalid group: prod
    """
    if not group:
        raise ValidationError("Group cannot be empty")

    if not isinstance(group, str):
        raise ValidationError(f"Group must be string, got {type(group)}")

    # Normalize
    group = group.strip().lower()

    # Basic validation
    if not re.match(r'^[a-z0-9_-]+$', group):
        raise ValidationError(
            f"Invalid group name format: {group}\n"
            "Group names must contain only lowercase letters, numbers, dashes, and underscores"
        )

    # Check if valid (if list provided)
    if valid_groups:
        if group not in valid_groups:
            suggestions = [g for g in valid_groups if group[:3] in g]
            raise ValidationError(
                f"Invalid group: {group}\n"
                f"Valid groups: {', '.join(valid_groups)}\n"
                + (f"Did you mean: {', '.join(suggestions[:3])}?" if suggestions else "")
            )

    return group


def validate_path_exists(path: str, must_be_file: bool = False,
                        must_be_dir: bool = False) -> Path:
    """
    Validate path exists and is accessible.

    Args:
        path: Path to validate
        must_be_file: If True, path must be a file
        must_be_dir: If True, path must be a directory

    Returns:
        Path: Validated Path object

    Raises:
        ValidationError: If path is invalid

    Example:
        >>> validate_path_exists("/tmp", must_be_dir=True)
        Path('/tmp')
        >>> validate_path_exists("/nonexistent")
        ValidationError: Path does not exist: /nonexistent
    """
    if not path:
        raise ValidationError("Path cannot be empty")

    p = Path(path).expanduser().resolve()

    if not p.exists():
        raise ValidationError(
            f"Path does not exist: {path}\n"
            f"Resolved to: {p}"
        )

    if must_be_file and not p.is_file():
        raise ValidationError(f"Path must be a file: {path}")

    if must_be_dir and not p.is_dir():
        raise ValidationError(f"Path must be a directory: {path}")

    return p


def validate_timeout(timeout: int, min_timeout: int = 1,
                     max_timeout: int = 600) -> int:
    """
    Validate timeout parameter.

    Args:
        timeout: Timeout in seconds
        min_timeout: Minimum allowed timeout
        max_timeout: Maximum allowed timeout

    Returns:
        int: Validated timeout

    Raises:
        ValidationError: If timeout is invalid

    Example:
        >>> validate_timeout(10)
        10
        >>> validate_timeout(0)
        ValidationError: Timeout must be between 1 and 600 seconds
    """
    if not isinstance(timeout, int):
        raise ValidationError(f"Timeout must be integer, got {type(timeout)}")

    if timeout < min_timeout:
        raise ValidationError(
            f"Timeout too low: {timeout}s (minimum: {min_timeout}s)"
        )

    if timeout > max_timeout:
        raise ValidationError(
            f"Timeout too high: {timeout}s (maximum: {max_timeout}s)"
        )

    return timeout


def validate_command(command: str, allow_dangerous: bool = False) -> str:
    """
    Basic command safety validation.

    Args:
        command: Command to validate
        allow_dangerous: If False, block potentially dangerous commands

    Returns:
        str: Validated command

    Raises:
        ValidationError: If command is invalid or dangerous

    Example:
        >>> validate_command("ls -la")
        "ls -la"
        >>> validate_command("rm -rf /", allow_dangerous=False)
        ValidationError: Potentially dangerous command blocked: rm -rf
    """
    if not command:
        raise ValidationError("Command cannot be empty")

    if not isinstance(command, str):
        raise ValidationError(f"Command must be string, got {type(command)}")

    command = command.strip()

    if not allow_dangerous:
        # Check for dangerous patterns
        dangerous_patterns = [
            (r'\brm\s+-rf\s+/', "rm -rf on root directory"),
            (r'\bmkfs\.', "filesystem formatting"),
            (r'\bdd\s+.*of=/dev/', "disk writing with dd"),
            (r':(){:|:&};:', "fork bomb"),
            (r'>\s*/dev/sd[a-z]', "direct disk writing"),
        ]

        for pattern, description in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                raise ValidationError(
                    f"Potentially dangerous command blocked: {description}\n"
                    f"Command: {command}\n"
                    "Use allow_dangerous=True if you really want to execute this"
                )

    return command


def validate_hosts_list(hosts: List[str], valid_hosts: Optional[List[str]] = None) -> List[str]:
    """
    Validate a list of hosts.

    Args:
        hosts: List of host names
        valid_hosts: List of valid hosts (None to skip check)

    Returns:
        List[str]: Validated host names

    Raises:
        ValidationError: If any host is invalid

    Example:
        >>> validate_hosts_list(["web-01", "web-02"])
        ["web-01", "web-02"]
    """
    if not hosts:
        raise ValidationError("Hosts list cannot be empty")

    if not isinstance(hosts, list):
        raise ValidationError(f"Hosts must be list, got {type(hosts)}")

    validated = []
    errors = []

    for host in hosts:
        try:
            validated.append(validate_host(host, valid_hosts))
        except ValidationError as e:
            errors.append(str(e))

    if errors:
        raise ValidationError(
            f"Invalid hosts in list:\n" + "\n".join(errors)
        )

    return validated


def main():
    """Test validators."""
    print("Testing parameter validators...\n")

    # Test host validation
    print("1. Testing validate_host():")
    try:
        host = validate_host("web-01", ["web-01", "web-02", "db-01"])
        print(f"   ✓ Valid host: {host}")
    except ValidationError as e:
        print(f"   ✗ Error: {e}")

    try:
        host = validate_host("invalid-host", ["web-01", "web-02"])
        print(f"   ✗ Should have failed!")
    except ValidationError as e:
        print(f"   ✓ Correctly rejected: {e.args[0].split(chr(10))[0]}")

    # Test group validation
    print("\n2. Testing validate_group():")
    try:
        group = validate_group("production", ["production", "development"])
        print(f"   ✓ Valid group: {group}")
    except ValidationError as e:
        print(f"   ✗ Error: {e}")

    # Test path validation
    print("\n3. Testing validate_path_exists():")
    try:
        path = validate_path_exists("/tmp", must_be_dir=True)
        print(f"   ✓ Valid path: {path}")
    except ValidationError as e:
        print(f"   ✗ Error: {e}")

    # Test timeout validation
    print("\n4. Testing validate_timeout():")
    try:
        timeout = validate_timeout(10)
        print(f"   ✓ Valid timeout: {timeout}s")
    except ValidationError as e:
        print(f"   ✗ Error: {e}")

    try:
        timeout = validate_timeout(0)
        print(f"   ✗ Should have failed!")
    except ValidationError as e:
        print(f"   ✓ Correctly rejected: {e.args[0].split(chr(10))[0]}")

    # Test command validation
    print("\n5. Testing validate_command():")
    try:
        cmd = validate_command("ls -la")
        print(f"   ✓ Safe command: {cmd}")
    except ValidationError as e:
        print(f"   ✗ Error: {e}")

    try:
        cmd = validate_command("rm -rf /", allow_dangerous=False)
        print(f"   ✗ Should have failed!")
    except ValidationError as e:
        print(f"   ✓ Correctly blocked: {e.args[0].split(chr(10))[0]}")

    print("\n✅ All parameter validators tested")


if __name__ == "__main__":
    main()
