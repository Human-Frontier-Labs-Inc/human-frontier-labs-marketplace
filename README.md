# Human Frontier Labs - Claude Code Plugin Marketplace

Public marketplace for Claude Code plugins focused on development tools, coding standards, and terminal UI applications.

**Repository**: https://github.com/Human-Frontier-Labs-Inc/human-frontier-labs-marketplace

---

## Installation

Install the entire marketplace:

```bash
/plugin marketplace add Human-Frontier-Labs-Inc/human-frontier-labs-marketplace
```

Or install individual plugins:

```bash
/plugin add Human-Frontier-Labs-Inc/human-frontier-labs-marketplace/carebridge-standards
/plugin add Human-Frontier-Labs-Inc/human-frontier-labs-marketplace/bubbletea-designer
/plugin add Human-Frontier-Labs-Inc/human-frontier-labs-marketplace/bubbletea-maintenance
/plugin add Human-Frontier-Labs-Inc/human-frontier-labs-marketplace/tailscale-sshsync-agent
/plugin add Human-Frontier-Labs-Inc/human-frontier-labs-marketplace/distributed-gummy-orchestrator
```

---

## Available Plugins

### 🏥 CareBridge Standards

**Category**: Coding Standards
**Version**: 1.0.0

Comprehensive coding standards and architectural patterns for the CareBridge eldercare management application.

**Features:**
- Next.js 15+ patterns and requirements
- Stripe integration best practices
- Neon database operation guidelines
- Case context management patterns
- Component creation rules
- React 19 compatibility standards

**Use When:**
- Working on CareBridge codebase
- Need Next.js 15 guidance
- Implementing Stripe payments
- Managing database operations with Neon

**Activation Keywords:**
- "carebridge standards"
- "check carebridge patterns"
- "next.js 15 requirements"

---

### 🎨 Bubble Tea Designer

**Category**: Development Tools
**Version**: 1.0.0

Automates Bubble Tea TUI design by analyzing requirements and mapping to Charmbracelet ecosystem components.

**Features:**
- Requirement analysis for TUI applications
- Component selection from Charmbracelet ecosystem
- Architecture generation for terminal UIs
- Implementation workflow creation
- Best practices for Bubble Tea development

**Use When:**
- Designing new terminal user interfaces
- Planning Bubble Tea applications
- Selecting appropriate TUI components
- Need design guidance for terminal apps

**Activation Keywords:**
- "design bubble tea TUI"
- "create terminal UI"
- "plan bubbletea app"
- "which charmbracelet components should I use"

---

### 🔧 Bubble Tea Maintenance

**Category**: Development Tools
**Version**: 1.0.0

Expert debugging and maintenance agent for existing Bubble Tea TUI applications.

**Features:**
- Issue diagnosis (blocking operations, layout problems, memory leaks)
- Best practices validation (11 expert tips)
- Performance bottleneck detection
- Architecture recommendations (model tree, multi-view patterns)
- Lipgloss layout fixes
- Comprehensive health check analysis

**Use When:**
- Debugging existing Bubble Tea apps
- Optimizing TUI performance
- Fixing layout issues
- Refactoring terminal applications
- Applying Bubble Tea best practices

**Activation Keywords:**
- "debug my bubble tea app"
- "optimize bubbletea performance"
- "fix TUI layout issues"
- "why is my TUI slow"
- "apply bubbletea best practices"

---

### 🌐 Tailscale SSH Sync Agent

**Category**: Infrastructure
**Version**: 1.0.0

Manages distributed workloads and file sharing across Tailscale SSH-connected machines using sshsync.

**Features:**
- Remote command execution across Tailscale network
- Intelligent load balancing based on CPU/memory
- File synchronization workflows
- Host health monitoring
- Multi-machine orchestration
- Workload distribution strategies

**Use When:**
- Need to run commands on remote machines
- Distributing workloads across your Tailscale network
- Syncing files between machines
- Finding the least loaded machine
- Orchestrating multi-host operations

**Activation Keywords:**
- "which machines are online"
- "run this on the least loaded machine"
- "push to production"
- "sync files to all machines"
- "check host status"

**Prerequisites:**
- Tailscale installed and configured
- sshsync installed
- SSH configured for remote machines
- Host groups defined

---

### 🤖 Distributed Gummy Orchestrator

**Category**: Development
**Version**: 1.0.0

Orchestrate gummy-agents across distributed network using 'dw' command for load-balanced, multi-host AI development.

**Features:**
- Distributed Claude Code agent orchestration
- Load-balanced task distribution across hosts
- Multi-host parallel development workflows
- Intelligent agent routing with 'dw' command
- Network-aware agent spawning
- Automated workload distribution

**Use When:**
- Running AI development tasks across multiple machines
- Need parallel Claude Code agents on different hosts
- Distributing heavy computation across your network
- Orchestrating multi-host development workflows
- Load-balancing AI agent tasks

**Activation Keywords:**
- "distribute this task across hosts"
- "run gummy agent on remote machine"
- "orchestrate distributed development"
- "spawn agents across network"
- "load balance this work"

**Prerequisites:**
- gummy-agent installed on all hosts
- Network connectivity between machines
- 'dw' command configured
- Host configuration file

---

## Plugin Categories

### Coding Standards
- **carebridge-standards** - CareBridge application coding standards

### Development Tools
- **bubbletea-designer** - TUI design automation
- **bubbletea-maintenance** - TUI debugging and optimization
- **distributed-gummy-orchestrator** - Distributed AI agent orchestration

### Infrastructure
- **tailscale-sshsync-agent** - Distributed workload management and file sharing

---

## Quick Start

### 1. Install Marketplace

```bash
/plugin marketplace add Human-Frontier-Labs-Inc/human-frontier-labs-marketplace
```

### 2. List Available Plugins

```bash
/plugin marketplace list human-frontier-labs-marketplace
```

### 3. Use a Plugin

Just mention its purpose in chat:

```
"I need to design a new terminal UI with a list and detail view"
→ Activates bubbletea-designer

"My TUI is laggy when scrolling"
→ Activates bubbletea-maintenance

"What are the CareBridge standards for Stripe integration?"
→ Activates carebridge-standards
```

---

## Documentation

Each plugin includes comprehensive documentation:

- **SKILL.md** - Complete agent instructions and capabilities
- **README.md** - Quick start and usage guide
- **INSTALLATION.md** - Setup instructions
- **CHANGELOG.md** - Version history
- **DECISIONS.md** - Architecture decisions

---

## Technology Stack

### Languages & Frameworks
- **Go** - Bubble Tea TUI framework
- **TypeScript/JavaScript** - Next.js, React 19
- **Python** - Analysis scripts and utilities

### Key Technologies
- **Bubble Tea** - Terminal UI framework by Charmbracelet
- **Lipgloss** - Terminal styling library
- **Next.js 15** - React framework with App Router
- **Stripe** - Payment processing
- **Neon** - Serverless Postgres database

---

## Contributing

Want to add your plugin to this marketplace?

1. Fork https://github.com/Human-Frontier-Labs-Inc/human-frontier-labs-marketplace
2. Add your plugin to `plugins/`
3. Update `.claude-plugin/marketplace.json`
4. Submit a pull request

### Plugin Requirements
- Complete SKILL.md with activation keywords
- README.md with usage examples
- Valid marketplace.json configuration
- `strict: false` for flexibility

---

## License

All plugins in this marketplace are MIT licensed unless otherwise specified.

---

## Support

**Issues**: https://github.com/Human-Frontier-Labs-Inc/human-frontier-labs-marketplace/issues

**Questions**: Open a discussion on GitHub

---

## Version History

**v1.0.0** (2025-10-19)
- Initial marketplace release
- Added carebridge-standards v1.0.0
- Added bubbletea-designer v1.0.0
- Added bubbletea-maintenance v1.0.0
- Added tailscale-sshsync-agent v1.0.0

---

**Maintained by**: William VanSickle III
**Organization**: Human Frontier Labs
**Created**: 2025-10-19
