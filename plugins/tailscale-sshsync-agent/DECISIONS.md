# Architecture Decisions

Documentation of all technical decisions made for Tailscale SSH Sync Agent.

## Tool Selection

### Selected Tool: sshsync

**Justification:**

✅ **Advantages:**
- **Ready-to-use**: Available via `pip install sshsync`
- **Group management**: Built-in support for organizing hosts into groups
- **Integration**: Works with existing SSH config (`~/.ssh/config`)
- **Simple API**: Easy-to-wrap CLI interface
- **Parallel execution**: Commands run concurrently across hosts
- **File operations**: Push/pull with recursive support
- **Timeout handling**: Per-command timeouts for reliability
- **Active maintenance**: Regular updates and bug fixes
- **Python-based**: Easy to extend and integrate

✅ **Coverage:**
- All SSH-accessible hosts
- Works with any SSH server (Linux, macOS, BSD, etc.)
- Platform-agnostic (runs on any OS with Python)

✅ **Cost:**
- Free and open-source
- No API keys or subscriptions required
- No rate limits

✅ **Documentation:**
- Clear command-line interface
- PyPI documentation available
- GitHub repository with examples

**Alternatives Considered:**

❌ **Fabric (Python library)**
- Pros: Pure Python, very flexible
- Cons: Requires writing more code, no built-in group management
- **Rejected because**: sshsync provides ready-made functionality

❌ **Ansible**
- Pros: Industry standard, very powerful
- Cons: Requires learning YAML playbooks, overkill for simple operations
- **Rejected because**: Too heavyweight for ad-hoc commands and file transfers

❌ **pssh (parallel-ssh)**
- Pros: Simple parallel SSH
- Cons: No group management, no file transfer built-in, less actively maintained
- **Rejected because**: sshsync has better group management and file operations

❌ **Custom SSH wrapper**
- Pros: Full control
- Cons: Reinventing the wheel, maintaining parallel execution logic
- **Rejected because**: sshsync already provides what we need

**Conclusion:**

sshsync is the best tool for this use case because it:
1. Provides group-based host management out of the box
2. Handles parallel execution automatically
3. Integrates with existing SSH configuration
4. Supports both command execution and file transfers
5. Requires minimal wrapper code

## Integration: Tailscale

**Decision**: Integrate with Tailscale for network connectivity

**Justification:**

✅ **Why Tailscale:**
- **Zero-config VPN**: No manual firewall/NAT configuration
- **Secure by default**: WireGuard encryption
- **Works everywhere**: Coffee shop, home, office, cloud
- **MagicDNS**: Easy addressing (machine-name.tailnet.ts.net)
- **Standard SSH**: Works with all SSH tools including sshsync
- **No overhead**: Uses regular SSH protocol over Tailscale network

✅ **Integration approach:**
- Tailscale provides the network layer
- Standard SSH works over Tailscale
- sshsync operates normally using Tailscale hostnames/IPs
- No Tailscale-specific code needed in core operations
- Tailscale status checking for diagnostics

**Alternatives:**

❌ **Direct public internet + port forwarding**
- Cons: Complex firewall setup, security risks, doesn't work on mobile/restricted networks
- **Rejected because**: Requires too much configuration and has security concerns

❌ **Other VPNs (WireGuard, OpenVPN, ZeroTier)**
- Cons: More manual configuration, less zero-config
- **Rejected because**: Tailscale is easier to set up and use

**Conclusion:**

Tailscale + standard SSH is the optimal combination:
- Secure connectivity without configuration
- Works with existing SSH tools
- No vendor lock-in (can use other VPNs if needed)

## Architecture

### Structure: Modular Scripts + Utilities

**Decision**: Separate concerns into focused modules

```
scripts/
├── sshsync_wrapper.py         # sshsync CLI interface
├── tailscale_manager.py       # Tailscale operations
├── load_balancer.py           # Task distribution logic
├── workflow_executor.py       # Common workflows
└── utils/
    ├── helpers.py             # Formatting, parsing
    └── validators/            # Input validation
```

**Justification:**

✅ **Modularity:**
- Each script has single responsibility
- Easy to test independently
- Easy to extend without breaking others

✅ **Reusability:**
- Helpers used across all scripts
- Validators prevent duplicate validation logic
- Workflows compose lower-level operations

✅ **Maintainability:**
- Clear file organization
- Easy to locate specific functionality
- Separation of concerns

**Alternatives:**

❌ **Monolithic single script**
- Cons: Hard to test, hard to maintain, becomes too large
- **Rejected because**: Doesn't scale well

❌ **Over-engineered class hierarchy**
- Cons: Unnecessary complexity for this use case
- **Rejected because**: Simple functions are sufficient

**Conclusion:**

Modular functional approach provides good balance of simplicity and maintainability.

### Validation Strategy: Multi-Layer

**Decision**: Validate at multiple layers

**Layers:**

1. **Parameter validation** (`parameter_validator.py`)
   - Validates user inputs before any operations
   - Prevents invalid hosts, groups, paths, etc.

2. **Host validation** (`host_validator.py`)
   - Validates SSH configuration exists
   - Checks host reachability
   - Validates group membership

3. **Connection validation** (`connection_validator.py`)
   - Tests actual SSH connectivity
   - Verifies Tailscale status
   - Checks SSH key authentication

**Justification:**

✅ **Early failure:**
- Catch errors before expensive operations
- Clear error messages at each layer

✅ **Comprehensive:**
- Multiple validation points catch different issues
- Reduces runtime failures

✅ **User-friendly:**
- Helpful error messages with suggestions
- Clear indication of what went wrong

**Conclusion:**

Multi-layer validation provides robust error handling and great user experience.

## Load Balancing Strategy

### Decision: Simple Composite Score

**Formula:**
```python
score = (cpu_pct * 0.4) + (mem_pct * 0.3) + (disk_pct * 0.3)
```

**Weights:**
- CPU: 40% (most important for compute tasks)
- Memory: 30% (important for data processing)
- Disk: 30% (important for I/O operations)

**Justification:**

✅ **Simple and effective:**
- Easy to understand
- Fast to calculate
- Works well for most workloads

✅ **Balanced:**
- Considers multiple resource types
- No single metric dominates

**Alternatives:**

❌ **CPU only**
- Cons: Ignores memory-bound and I/O-bound tasks
- **Rejected because**: Too narrow

❌ **Complex ML-based prediction**
- Cons: Overkill, slow, requires training data
- **Rejected because**: Unnecessary complexity

❌ **Fixed round-robin**
- Cons: Doesn't consider actual load
- **Rejected because**: Can overload already-busy hosts

**Conclusion:**

Simple weighted score provides good balance without complexity.

## Error Handling Philosophy

### Decision: Graceful Degradation + Clear Messages

**Principles:**

1. **Fail early with validation**: Catch errors before operations
2. **Isolate failures**: One host failure doesn't stop others
3. **Clear messages**: Tell user exactly what went wrong and how to fix
4. **Automatic retry**: Retry transient errors (network, timeout)
5. **Dry-run support**: Preview operations before execution

**Implementation:**

```python
# Example error handling pattern
try:
    validate_host(host)
    validate_ssh_connection(host)
    result = execute_command(host, command)
except ValidationError as e:
    return {'error': str(e), 'suggestion': 'Fix: ...'}
except ConnectionError as e:
    return {'error': str(e), 'diagnostics': get_diagnostics(host)}
```

**Justification:**

✅ **Better UX:**
- Users know exactly what's wrong
- Suggestions help fix issues quickly

✅ **Reliability:**
- Automatic retry handles transient issues
- Dry-run prevents mistakes

✅ **Debugging:**
- Clear error messages speed up troubleshooting
- Diagnostics provide actionable information

**Conclusion:**

Graceful degradation with helpful messages creates better user experience.

## Caching Strategy

**Decision**: Minimal caching for real-time accuracy

**What we cache:**
- Nothing (v1.0.0)

**Why no caching:**
- Host status changes frequently
- Load metrics change constantly
- Operations need real-time data
- Cache invalidation is complex

**Future consideration (v2.0):**
- Cache Tailscale status (60s TTL)
- Cache group configuration (5min TTL)
- Cache SSH config parsing (5min TTL)

**Justification:**

✅ **Simplicity:**
- No cache invalidation logic needed
- No stale data issues

✅ **Accuracy:**
- Always get current state
- No surprises from cached data

**Trade-off:**
- Slightly slower repeated operations
- More network calls

**Conclusion:**

For v1.0.0, simplicity and accuracy outweigh performance concerns. Real-time data is more valuable than speed.

## Testing Strategy

### Decision: Comprehensive Unit + Integration Tests

**Coverage:**

- **29 tests total:**
  - 11 integration tests (end-to-end workflows)
  - 11 helper tests (formatting, parsing, calculations)
  - 7 validation tests (input validation, safety checks)

**Test Philosophy:**

1. **Test real functionality**: Integration tests use actual functions
2. **Test edge cases**: Validation tests cover error conditions
3. **Test helpers**: Ensure formatting/parsing works correctly
4. **Fast execution**: All tests run in < 10 seconds
5. **No external dependencies**: Tests don't require Tailscale or sshsync to be running

**Justification:**

✅ **Confidence:**
- Tests verify code works as expected
- Catches regressions when modifying code

✅ **Documentation:**
- Tests show how to use functions
- Examples of expected behavior

✅ **Reliability:**
- Production-ready code from v1.0.0

**Conclusion:**

Comprehensive testing ensures reliable code from the start.

## Performance Considerations

### Parallel Execution

**Decision**: Leverage sshsync's built-in parallelization

- sshsync runs commands concurrently across hosts automatically
- No need to implement custom threading/multiprocessing
- Timeout applies per-host independently

**Trade-offs:**

✅ **Pros:**
- Simple to use
- Fast for large host groups
- No concurrency bugs

⚠️ **Cons:**
- Less control over parallelism level
- Can overwhelm network with too many concurrent connections

**Conclusion:**

Built-in parallelization is sufficient for most use cases. Custom control can be added in v2.0 if needed.

## Security Considerations

### SSH Key Authentication

**Decision**: Require SSH keys (no password auth)

**Justification:**

✅ **Security:**
- Keys are more secure than passwords
- Can't be brute-forced
- Can be revoked per-host

✅ **Automation:**
- Non-interactive (no password prompts)
- Works in scripts and CI/CD

**Implementation:**
- Validators check SSH key auth works
- Clear error messages guide users to set up keys
- Documentation explains SSH key setup

### Command Safety

**Decision**: Validate dangerous commands

**Dangerous patterns blocked:**
- `rm -rf /` (root deletion)
- `mkfs.*` (filesystem formatting)
- `dd.*of=/dev/` (direct disk writes)
- Fork bombs
- Direct disk writes

**Override**: Use `allow_dangerous=True` to bypass

**Justification:**

✅ **Safety:**
- Prevents accidental destructive operations
- Dry-run provides preview

✅ **Flexibility:**
- Can still run dangerous commands if explicitly allowed

**Conclusion:**

Safety by default with escape hatch for advanced users.

## Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **CLI Tool** | sshsync | Best balance of features, ease of use, and maintenance |
| **Network** | Tailscale | Zero-config secure VPN, works everywhere |
| **Architecture** | Modular scripts | Clear separation of concerns, maintainable |
| **Validation** | Multi-layer | Catch errors early with helpful messages |
| **Load Balancing** | Composite score | Simple, effective, considers multiple resources |
| **Caching** | None (v1.0) | Simplicity and real-time accuracy |
| **Testing** | 29 tests | Comprehensive coverage for reliability |
| **Security** | SSH keys + validation | Secure and automation-friendly |

## Trade-offs Accepted

1. **No caching** → Slightly slower, but always accurate
2. **sshsync dependency** → External tool, but saves development time
3. **SSH key requirement** → Setup needed, but more secure
4. **Simple load balancing** → Less sophisticated, but fast and easy to understand
5. **Terminal UI only** → No web dashboard, but simpler to develop and maintain

## Future Improvements

### v2.0 Considerations

1. **Add caching** for frequently-accessed data (Tailscale status, groups)
2. **Web dashboard** for visualization and monitoring
3. **Operation history** database for audit trail
4. **Advanced load balancing** with custom metrics
5. **Automated SSH key distribution** across hosts
6. **Integration with config management** tools (Ansible, Terraform)
7. **Container support** via SSH to Docker containers
8. **Custom validation plugins** for domain-specific checks

All decisions prioritize **simplicity**, **security**, and **maintainability** for v1.0.0.
