# Changelog

All notable changes to Tailscale SSH Sync Agent will be documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2025-10-19

### Added

**Core Functionality:**
- `sshsync_wrapper.py`: Python interface to sshsync CLI operations
  - `get_host_status()`: Check online/offline status of hosts
  - `execute_on_all()`: Run commands on all configured hosts
  - `execute_on_group()`: Run commands on specific groups
  - `execute_on_host()`: Run commands on single host
  - `push_to_hosts()`: Push files to multiple hosts (with groups support)
  - `pull_from_host()`: Pull files from hosts
  - `list_hosts()`: List all configured hosts
  - `get_groups()`: Get group configuration

- `tailscale_manager.py`: Tailscale-specific operations
  - `get_tailscale_status()`: Get complete network status
  - `check_connectivity()`: Ping hosts via Tailscale
  - `get_peer_info()`: Get detailed peer information
  - `list_online_machines()`: List all online Tailscale machines
  - `validate_tailscale_ssh()`: Check if Tailscale SSH works for a host
  - `get_network_summary()`: Human-readable network summary

- `load_balancer.py`: Intelligent task distribution
  - `get_machine_load()`: Get CPU, memory, disk metrics for a machine
  - `select_optimal_host()`: Pick best host based on current load
  - `get_group_capacity()`: Get aggregate capacity of a group
  - `distribute_tasks()`: Distribute multiple tasks optimally across hosts
  - `format_load_report()`: Format load metrics as human-readable report

- `workflow_executor.py`: Common multi-machine workflows
  - `deploy_workflow()`: Full deployment pipeline (staging → test → production)
  - `backup_workflow()`: Backup files from multiple hosts
  - `sync_workflow()`: Sync files from one host to many
  - `rolling_restart()`: Zero-downtime service restart across group
  - `health_check_workflow()`: Check health endpoints across group

**Utilities:**
- `utils/helpers.py`: Common formatting and parsing functions
  - Byte formatting (`format_bytes`)
  - Duration formatting (`format_duration`)
  - Percentage formatting (`format_percentage`)
  - SSH config parsing (`parse_ssh_config`)
  - sshsync config parsing (`parse_sshsync_config`)
  - System metrics parsing (`parse_disk_usage`, `parse_memory_usage`, `parse_cpu_load`)
  - Load score calculation (`calculate_load_score`)
  - Status classification (`classify_load_status`, `classify_latency`)
  - Safe command execution (`run_command`, `safe_execute`)

- `utils/validators/`: Comprehensive validation system
  - `parameter_validator.py`: Input validation (hosts, groups, paths, timeouts, commands)
  - `host_validator.py`: Host configuration and availability validation
  - `connection_validator.py`: SSH and Tailscale connection validation

**Testing:**
- `tests/test_integration.py`: 11 end-to-end integration tests
- `tests/test_helpers.py`: 11 helper function tests
- `tests/test_validation.py`: 7 validation tests
- **Total: 29 tests** covering all major functionality

**Documentation:**
- `SKILL.md`: Complete skill documentation (6,000+ words)
  - When to use this skill
  - How it works
  - Data sources (sshsync CLI, Tailscale)
  - Detailed workflows for each operation type
  - Available scripts and functions
  - Error handling and validations
  - Performance and caching strategies
  - Usage examples
- `references/sshsync-guide.md`: Complete sshsync CLI reference
- `references/tailscale-integration.md`: Tailscale integration guide
- `README.md`: Installation and quick start guide
- `INSTALLATION.md`: Detailed setup tutorial
- `DECISIONS.md`: Architecture decisions and rationale

### Data Sources

**sshsync CLI:**
- Installation: `pip install sshsync`
- Configuration: `~/.config/sshsync/config.yaml`
- SSH config integration: `~/.ssh/config`
- Group-based host management
- Remote command execution with timeouts
- File push/pull operations (single or recursive)
- Status checking and connectivity validation

**Tailscale:**
- Zero-config VPN with WireGuard encryption
- MagicDNS for easy host addressing
- Built-in SSH capabilities
- Seamless integration with standard SSH
- Peer-to-peer connections
- Works across NATs and firewalls

### Coverage

**Operations:**
- Host status monitoring and availability checks
- Intelligent load-based task distribution
- Multi-host command execution (all hosts, groups, individual)
- File synchronization workflows (push/pull)
- Deployment pipelines (staging → production)
- Backup and sync workflows
- Rolling restarts with zero downtime
- Health checking across services

**Geographic Coverage:** All hosts in Tailscale network (global)

**Temporal Coverage:** Real-time status and operations

### Known Limitations

**v1.0.0:**
- sshsync must be installed separately (`pip install sshsync`)
- Tailscale must be configured separately
- SSH keys must be set up manually on each host
- Load balancing uses simple metrics (CPU, memory, disk)
- No built-in monitoring dashboards (terminal output only)
- No persistence of operation history (logs only)
- Requires SSH config and sshsync config to be manually maintained

### Planned for v2.0

**Enhanced Features:**
- Automated SSH key distribution across hosts
- Built-in operation history and logging database
- Web dashboard for monitoring and operations
- Advanced load balancing with custom metrics
- Scheduled operations and cron integration
- Operation rollback capabilities
- Integration with configuration management tools (Ansible, Terraform)
- Cost tracking for cloud resources
- Performance metrics collection and visualization
- Alert system for failed operations
- Multi-tenancy support for team environments

**Integrations:**
- Prometheus metrics export
- Grafana dashboard templates
- Slack/Discord notifications
- CI/CD pipeline integration
- Container orchestration support (Docker, Kubernetes)

## [Unreleased]

### Planned

- Add support for Windows hosts (PowerShell remoting)
- Improve performance for large host groups (100+)
- Add SSH connection pooling for faster operations
- Implement operation queueing for long-running tasks
- Add support for custom validation plugins
- Expand coverage to Docker containers via SSH
- Add retry strategies with exponential backoff
- Implement circuit breaker pattern for failing hosts
