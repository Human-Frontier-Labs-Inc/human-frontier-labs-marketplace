# Bubble Tea Maintenance & Debugging Agent

Expert agent for diagnosing, fixing, and optimizing existing Bubble Tea TUI applications.

**Version:** 1.0.0
**Created:** 2025-10-19

---

## What This Agent Does

This agent helps you maintain and improve existing Go/Bubble Tea applications by:

✅ **Diagnosing Issues** - Identifies performance bottlenecks, layout problems, memory leaks
✅ **Validating Best Practices** - Checks against 11 expert tips from tip-bubbltea-apps.md
✅ **Optimizing Performance** - Finds slow operations in Update() and View()
✅ **Suggesting Architecture** - Recommends refactoring to model tree, multi-view patterns
✅ **Fixing Layout Issues** - Solves Lipgloss dimension, padding, overflow problems
✅ **Comprehensive Analysis** - Complete health check with prioritized fixes

---

## Installation

```bash
cd /path/to/bubbletea-maintenance
/plugin marketplace add .
```

The agent will be available in your Claude Code session.

---

## Quick Start

**Analyze your Bubble Tea app:**

"Analyze my Bubble Tea application at ./myapp"

The agent will perform a comprehensive health check and provide:
- Overall health score (0-100)
- Critical issues requiring immediate attention
- Performance bottlenecks
- Layout problems
- Architecture recommendations
- Estimated fix time

---

## Core Functions

### 1. diagnose_issue()

Identifies common Bubble Tea problems:
- Blocking operations in event loop
- Hardcoded terminal dimensions
- Missing terminal recovery
- Message ordering issues
- Model complexity problems

**Usage:**
```
"Diagnose issues in ./myapp/main.go"
```

### 2. apply_best_practices()

Validates against 11 expert tips:
1. Fast event loop (no blocking)
2. Debug message dumping
3. Live reload setup
4. Proper receiver methods
5. Message ordering handling
6. Model tree architecture
7. Layout arithmetic
8. Terminal recovery
9. teatest usage
10. VHS demos
11. Additional resources

**Usage:**
```
"Check best practices for ./myapp"
```

### 3. debug_performance()

Finds performance bottlenecks:
- Slow Update() operations
- Expensive View() rendering
- String concatenation issues
- Regex compilation in functions
- Nested loops
- Memory allocations
- Goroutine leaks

**Usage:**
```
"Debug performance of my TUI"
```

### 4. suggest_architecture()

Recommends patterns based on complexity:
- **Simple** (< 30): Flat model
- **Medium** (30-70): Multi-view or component-based
- **Complex** (70+): Model tree

Provides:
- Current pattern detection
- Complexity score
- Recommended pattern
- Step-by-step refactoring guide
- Code templates

**Usage:**
```
"Suggest architecture improvements for ./myapp"
```

### 5. fix_layout_issues()

Solves Lipgloss layout problems:
- Hardcoded dimensions → dynamic sizing
- Manual calculations → lipgloss.Height()/Width()
- Missing padding accounting → GetHorizontalPadding()
- Text overflow → wordwrap or truncate
- No resize handling → tea.WindowSizeMsg
- Border sizing → GetHorizontalBorderSize()

**Usage:**
```
"Fix layout issues in my TUI"
```

### 6. comprehensive_analysis()

All-in-one health check combining all functions.

Outputs:
- Overall health score
- Priority fixes (CRITICAL → WARNING → INFO)
- Estimated fix time
- Detailed report per section

**Usage:**
```
"Run comprehensive analysis on ./myapp"
```

---

## Example Session

```
User: "My log viewer TUI is laggy when scrolling"

Agent: Let me analyze your application...

[Runs debug_performance()]

Found the issue! Your View() function:
1. Re-reads the entire log file on every render (200ms)
2. Processes all lines instead of just the visible viewport
3. Uses string concatenation with + operator

Here's the fix:

// Cache file content
type model struct {
    logLines []string  // Cache in model
    viewport viewport.Model
}

// Load once
func loadLogFile() tea.Msg {
    content, _ := os.ReadFile("app.log")
    lines := strings.Split(string(content), "\\n")
    return logLoadedMsg{lines: lines}
}

// Update only when needed
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    case logLoadedMsg:
        m.logLines = msg.lines
        m.viewport.SetContent(strings.Join(m.logLines, "\\n"))
}

// View just renders viewport
func (m model) View() string {
    return m.viewport.View()  // Fast! No I/O
}

This will reduce render time from 200ms to ~2ms.
```

---

## Activation Keywords

The agent activates on phrases like:

- "debug my bubble tea app"
- "fix this TUI issue"
- "optimize bubbletea performance"
- "why is my TUI slow"
- "refactor bubble tea code"
- "apply bubbletea best practices"
- "fix layout issues"
- "lipgloss styling problem"
- "improve my TUI"
- "bubbletea architecture help"

---

## Reference Files

Located in `references/`:

- **common_issues.md** - Solutions to frequent problems
- **performance_guide.md** - Optimization strategies
- **layout_guide.md** - Lipgloss layout best practices
- **architecture_patterns.md** - Model tree, multi-view, state machine patterns

---

## Local Knowledge Sources

The agent uses these local files (no internet required):

- `/Users/williamvansickleiii/charmtuitemplate/charm-tui-template/tip-bubbltea-apps.md` - 11 expert tips
- `/Users/williamvansickleiii/charmtuitemplate/charm-tui-template/lipgloss-readme.md` - Lipgloss docs
- `/Users/williamvansickleiii/charmtuitemplate/vinw/` - Real-world example app
- `/Users/williamvansickleiii/charmtuitemplate/charm-examples-inventory/` - Pattern library

---

## Testing

Run the test suite:

```bash
cd bubbletea-maintenance
python3 -m pytest tests/ -v
```

Or run individual test files:

```bash
python3 tests/test_diagnose_issue.py
python3 tests/test_best_practices.py
python3 tests/test_performance.py
```

---

## Architecture

```
bubbletea-maintenance/
├── SKILL.md                           # Agent instructions (8,000 words)
├── README.md                          # This file
├── scripts/
│   ├── diagnose_issue.py              # Issue diagnosis
│   ├── apply_best_practices.py        # Best practices validation
│   ├── debug_performance.py           # Performance analysis
│   ├── suggest_architecture.py        # Architecture recommendations
│   ├── fix_layout_issues.py           # Layout fixes
│   ├── comprehensive_analysis.py      # All-in-one orchestrator
│   └── utils/
│       ├── go_parser.py               # Go code parsing
│       └── validators/
│           └── common.py              # Validation utilities
├── references/
│   ├── common_issues.md               # Issue reference
│   ├── performance_guide.md           # Performance tips
│   ├── layout_guide.md                # Layout guide
│   └── architecture_patterns.md       # Pattern catalog
├── assets/
│   ├── issue_categories.json          # Issue taxonomy
│   ├── best_practices_tips.json       # Tips database
│   └── performance_thresholds.json    # Performance targets
└── tests/
    ├── test_diagnose_issue.py
    ├── test_best_practices.py
    ├── test_performance.py
    ├── test_architecture.py
    ├── test_layout.py
    └── test_integration.py
```

---

## Limitations

This agent focuses on **maintenance and debugging**, NOT:

- ❌ Designing new TUIs from scratch (use `bubbletea-designer` for that)
- ❌ Non-Bubble Tea Go code
- ❌ Terminal emulator issues
- ❌ OS-specific problems

---

## Version History

**v1.0.0** (2025-10-19)
- Initial release
- 6 core analysis functions
- Integration with tip-bubbltea-apps.md
- Comprehensive diagnostic capabilities
- Layout issue detection and fixing
- Performance profiling
- Architecture recommendations

---

**Built with Claude Code agent-creator on 2025-10-19**

Questions or issues? Check SKILL.md for detailed documentation.
