# Distributed Gummy Orchestrator

Coordinate gummy-agent tasks across your Tailscale network using intelligent load balancing.

## Quick Start

### Installation

```bash
# Install the skill
cd ~
/plugin marketplace add ./distributed-gummy-orchestrator
```

### Prerequisites

- ✅ `dw` command installed and configured
- ✅ `gummy-agent` installed on remote hosts
- ✅ Tailscale network active
- ✅ SSH access to hosts via `~/.ssh/config`

### Basic Usage

**Find best host and execute task:**

"Run database optimization on the least loaded host"

**Distribute work across network:**

"I have database work and API work - distribute optimally"

**Monitor all specialists:**

"Show all specialists running across my network"

**Sync and execute:**

"Sync codebase to node-2 and run frontend specialist there"

## How It Works

1. **Load Analysis**: Executes `dwload` to get cluster metrics
2. **Host Selection**: Chooses optimal node based on CPU, memory, load average
3. **Sync**: Uses `dwsync` to ensure code is current
4. **Execute**: Runs `dwrun <host> "gummy task..."` on selected node
5. **Monitor**: Aggregates specialist status across network

## Example Workflows

### Load-Balanced Task

```
User: "Run this on optimal host"
↓
Agent: d load → selects node-1 (lowest score)
Agent: d sync node-1
Agent: d run node-1 "gummy task 'optimize queries'"
↓
Result: Task running on best available host
```

### Parallel Distribution

```
User: "Test on all platforms"
↓
Agent: d status → finds 3 hosts online
Agent: d sync all hosts
Agent: d run host1 "test" & d run host2 "test" & d run host3 "test"
↓
Result: All tests running in parallel
```

### Network Monitoring

```
User: "Show all specialists"
↓
Agent: d status → lists online hosts
Agent: For each host: d run "ls ~/.gummy/specialists"
Agent: Aggregates specialist metadata
↓
Result: Unified dashboard of all specialists across network
```

## Configuration

Optional config at `~/.config/distributed-gummy/config.yaml`:

```yaml
load_weights:
  cpu: 0.4
  memory: 0.3
  load_average: 0.3

sync_exclude:
  - node_modules
  - .git
  - dist

host_preferences:
  database:
    - node-1
  frontend:
    - node-2
```

## Testing

Test the orchestrator:

```bash
cd ~/distributed-gummy-orchestrator
python3 scripts/orchestrate_gummy.py
```

Expected output:
```
======================================================================
DISTRIBUTED GUMMY ORCHESTRATOR - TEST
======================================================================

✓ Testing load metrics...
  node-1: CPU 15%, Score 0.23
  node-2: CPU 45%, Score 0.56

✓ Testing host status...
  node-1: online
  node-2: online

✓ Testing optimal host selection...
  Best host: node-1 (score: 0.23)

✓ Testing specialist monitoring...
  node-1: 2 specialists
    - database-expert
    - api-developer

✓ Testing comprehensive report...
  2/2 hosts online, 2 active specialists

======================================================================
✅ ALL TESTS COMPLETE
======================================================================
```

## Troubleshooting

**"No hosts available"**
```bash
# Check Tailscale
tailscale status

# Check dw command
d status

# Verify SSH
ssh <host> echo "OK"
```

**"Sync failed"**
```bash
# Test sync manually
d sync <host>

# Check rsync
which rsync
```

**"Gummy not found"**
```bash
# Check remote installation
d run <host> "which gummy"

# Install if needed
d run <host> "brew install WillyV3/tap/gummy-agent"
```

## Architecture

```
Main Claude
    ↓
Orchestrator (this skill)
    ↓
dw command
    ↓
┌─────────┬─────────┬─────────┐
│ node-1  │ node-2  │ node-3  │
│ gummy   │ gummy   │ gummy   │
│ agents  │ agents  │ agents  │
└─────────┴─────────┴─────────┘
```

## Examples

**Load-balanced execution:**
```
"Run database optimization on best host"
→ Selects node-1 (CPU 15%, load 0.23)
→ Syncs codebase
→ Executes: gummy task 'optimize database queries'
→ Returns: Task active on node-1
```

**Parallel testing:**
```
"Test on all nodes"
→ Finds 4 online hosts
→ Syncs to all
→ Launches parallel: unit + integration + e2e + perf
→ Returns: All tests complete in 8 min (vs 32 min sequential)
```

**Intelligent distribution:**
```
"Optimize database and build API"
→ Analyzes: database=CPU-intensive, API=I/O-bound
→ Selects: node-1 (low CPU), node-2 (low I/O)
→ Launches both in parallel
→ Returns: Both tasks running optimally
```

## Version

1.0.0 - Initial release (2025-10-19)

## Author

WillyV3 - breakshit.blog - @humanfrontierlabs
