"""
Validators package for Tailscale SSH Sync Agent.
"""

from .parameter_validator import (
    ValidationError,
    validate_host,
    validate_group,
    validate_path_exists,
    validate_timeout,
    validate_command
)

from .host_validator import (
    validate_ssh_config,
    validate_host_reachable,
    validate_group_members,
    get_invalid_hosts
)

from .connection_validator import (
    validate_ssh_connection,
    validate_tailscale_connection,
    validate_ssh_key,
    get_connection_diagnostics
)

__all__ = [
    'ValidationError',
    'validate_host',
    'validate_group',
    'validate_path_exists',
    'validate_timeout',
    'validate_command',
    'validate_ssh_config',
    'validate_host_reachable',
    'validate_group_members',
    'get_invalid_hosts',
    'validate_ssh_connection',
    'validate_tailscale_connection',
    'validate_ssh_key',
    'get_connection_diagnostics',
]
