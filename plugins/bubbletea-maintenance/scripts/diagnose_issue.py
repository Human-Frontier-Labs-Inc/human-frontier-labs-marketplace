#!/usr/bin/env python3
"""
Diagnose issues in existing Bubble Tea applications.
Identifies common problems: slow event loop, layout issues, memory leaks, etc.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any


def diagnose_issue(code_path: str, description: str = "") -> Dict[str, Any]:
    """
    Analyze Bubble Tea code to identify common issues.

    Args:
        code_path: Path to Go file or directory containing Bubble Tea code
        description: Optional user description of the problem

    Returns:
        Dictionary containing:
        - issues: List of identified issues with severity, location, fix
        - summary: High-level summary
        - health_score: 0-100 score (higher is better)
        - validation: Validation report
    """
    path = Path(code_path)

    if not path.exists():
        return {
            "error": f"Path not found: {code_path}",
            "validation": {"status": "error", "summary": "Invalid path"}
        }

    # Collect all .go files
    go_files = []
    if path.is_file():
        if path.suffix == '.go':
            go_files = [path]
    else:
        go_files = list(path.glob('**/*.go'))

    if not go_files:
        return {
            "error": "No .go files found",
            "validation": {"status": "error", "summary": "No Go files"}
        }

    # Analyze all files
    all_issues = []
    for go_file in go_files:
        issues = _analyze_go_file(go_file)
        all_issues.extend(issues)

    # Calculate health score
    critical_count = sum(1 for i in all_issues if i['severity'] == 'CRITICAL')
    warning_count = sum(1 for i in all_issues if i['severity'] == 'WARNING')
    info_count = sum(1 for i in all_issues if i['severity'] == 'INFO')

    health_score = max(0, 100 - (critical_count * 20) - (warning_count * 5) - (info_count * 1))

    # Generate summary
    if critical_count == 0 and warning_count == 0:
        summary = "✅ No critical issues found. Application appears healthy."
    elif critical_count > 0:
        summary = f"❌ Found {critical_count} critical issue(s) requiring immediate attention"
    else:
        summary = f"⚠️  Found {warning_count} warning(s) that should be addressed"

    # Validation
    validation = {
        "status": "critical" if critical_count > 0 else "warning" if warning_count > 0 else "pass",
        "summary": summary,
        "checks": {
            "has_blocking_operations": critical_count > 0,
            "has_layout_issues": any(i['category'] == 'layout' for i in all_issues),
            "has_performance_issues": any(i['category'] == 'performance' for i in all_issues),
            "has_architecture_issues": any(i['category'] == 'architecture' for i in all_issues)
        }
    }

    return {
        "issues": all_issues,
        "summary": summary,
        "health_score": health_score,
        "statistics": {
            "total_issues": len(all_issues),
            "critical": critical_count,
            "warnings": warning_count,
            "info": info_count,
            "files_analyzed": len(go_files)
        },
        "validation": validation,
        "user_description": description
    }


def _analyze_go_file(file_path: Path) -> List[Dict[str, Any]]:
    """Analyze a single Go file for issues."""
    issues = []

    try:
        content = file_path.read_text()
    except Exception as e:
        return [{
            "severity": "WARNING",
            "category": "system",
            "issue": f"Could not read file: {e}",
            "location": str(file_path),
            "explanation": "File access error",
            "fix": "Check file permissions"
        }]

    lines = content.split('\n')
    rel_path = file_path.name

    # Check 1: Blocking operations in Update() or View()
    issues.extend(_check_blocking_operations(content, lines, rel_path))

    # Check 2: Hardcoded dimensions
    issues.extend(_check_hardcoded_dimensions(content, lines, rel_path))

    # Check 3: Missing terminal recovery
    issues.extend(_check_terminal_recovery(content, lines, rel_path))

    # Check 4: Message ordering assumptions
    issues.extend(_check_message_ordering(content, lines, rel_path))

    # Check 5: Model complexity
    issues.extend(_check_model_complexity(content, lines, rel_path))

    # Check 6: Memory leaks (goroutine leaks)
    issues.extend(_check_goroutine_leaks(content, lines, rel_path))

    # Check 7: Layout arithmetic issues
    issues.extend(_check_layout_arithmetic(content, lines, rel_path))

    return issues


def _check_blocking_operations(content: str, lines: List[str], file_path: str) -> List[Dict[str, Any]]:
    """Check for blocking operations in Update() or View()."""
    issues = []

    # Find Update() and View() function boundaries
    in_update = False
    in_view = False
    func_start_line = 0

    blocking_patterns = [
        (r'\btime\.Sleep\s*\(', "time.Sleep"),
        (r'\bhttp\.(Get|Post|Do)\s*\(', "HTTP request"),
        (r'\bos\.Open\s*\(', "File I/O"),
        (r'\bio\.ReadAll\s*\(', "Blocking read"),
        (r'\bexec\.Command\([^)]+\)\.Run\(\)', "Command execution"),
        (r'\bdb\.Query\s*\(', "Database query"),
    ]

    for i, line in enumerate(lines):
        # Track function boundaries
        if re.search(r'func\s+\([^)]+\)\s+Update\s*\(', line):
            in_update = True
            func_start_line = i
        elif re.search(r'func\s+\([^)]+\)\s+View\s*\(', line):
            in_view = True
            func_start_line = i
        elif in_update or in_view:
            if line.strip().startswith('func '):
                in_update = False
                in_view = False

        # Check for blocking operations
        if in_update or in_view:
            for pattern, operation in blocking_patterns:
                if re.search(pattern, line):
                    func_type = "Update()" if in_update else "View()"
                    issues.append({
                        "severity": "CRITICAL",
                        "category": "performance",
                        "issue": f"Blocking {operation} in {func_type}",
                        "location": f"{file_path}:{i+1}",
                        "code_snippet": line.strip(),
                        "explanation": f"{operation} blocks the event loop, causing UI to freeze",
                        "fix": f"Move {operation} to tea.Cmd goroutine:\n\n" +
                               f"func load{operation.replace(' ', '')}() tea.Msg {{\n" +
                               f"    // Your {operation} here\n" +
                               f"    return resultMsg{{}}\n" +
                               f"}}\n\n" +
                               f"// In Update():\n" +
                               f"return m, load{operation.replace(' ', '')}"
                    })

    return issues


def _check_hardcoded_dimensions(content: str, lines: List[str], file_path: str) -> List[Dict[str, Any]]:
    """Check for hardcoded terminal dimensions."""
    issues = []

    # Look for hardcoded width/height values
    patterns = [
        (r'\.Width\s*\(\s*(\d{2,})\s*\)', "width"),
        (r'\.Height\s*\(\s*(\d{2,})\s*\)', "height"),
        (r'MaxWidth\s*:\s*(\d{2,})', "MaxWidth"),
        (r'MaxHeight\s*:\s*(\d{2,})', "MaxHeight"),
    ]

    for i, line in enumerate(lines):
        for pattern, dimension in patterns:
            matches = re.finditer(pattern, line)
            for match in matches:
                value = match.group(1)
                if int(value) >= 20:  # Likely a terminal dimension, not small padding
                    issues.append({
                        "severity": "WARNING",
                        "category": "layout",
                        "issue": f"Hardcoded {dimension} value: {value}",
                        "location": f"{file_path}:{i+1}",
                        "code_snippet": line.strip(),
                        "explanation": "Hardcoded dimensions don't adapt to terminal size",
                        "fix": f"Use dynamic terminal size from tea.WindowSizeMsg:\n\n" +
                               f"type model struct {{\n" +
                               f"    termWidth  int\n" +
                               f"    termHeight int\n" +
                               f"}}\n\n" +
                               f"func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {{\n" +
                               f"    switch msg := msg.(type) {{\n" +
                               f"    case tea.WindowSizeMsg:\n" +
                               f"        m.termWidth = msg.Width\n" +
                               f"        m.termHeight = msg.Height\n" +
                               f"    }}\n" +
                               f"    return m, nil\n" +
                               f"}}"
                    })

    return issues


def _check_terminal_recovery(content: str, lines: List[str], file_path: str) -> List[Dict[str, Any]]:
    """Check for panic recovery and terminal cleanup."""
    issues = []

    has_defer_recover = bool(re.search(r'defer\s+func\s*\(\s*\)\s*\{[^}]*recover\(\)', content, re.DOTALL))
    has_main = bool(re.search(r'func\s+main\s*\(\s*\)', content))

    if has_main and not has_defer_recover:
        issues.append({
            "severity": "WARNING",
            "category": "reliability",
            "issue": "Missing panic recovery in main()",
            "location": file_path,
            "explanation": "Panics can leave terminal in broken state (mouse mode enabled, cursor hidden)",
            "fix": "Add defer recovery:\n\n" +
                   "func main() {\n" +
                   "    defer func() {\n" +
                   "        if r := recover(); r != nil {\n" +
                   "            tea.DisableMouseAllMotion()\n" +
                   "            tea.ShowCursor()\n" +
                   "            fmt.Println(\"Panic:\", r)\n" +
                   "            os.Exit(1)\n" +
                   "        }\n" +
                   "    }()\n\n" +
                   "    // Your program logic\n" +
                   "}"
        })

    return issues


def _check_message_ordering(content: str, lines: List[str], file_path: str) -> List[Dict[str, Any]]:
    """Check for assumptions about message ordering from concurrent commands."""
    issues = []

    # Look for concurrent command patterns without order handling
    has_batch = bool(re.search(r'tea\.Batch\s*\(', content))
    has_state_machine = bool(re.search(r'type\s+\w+State\s+(int|string)', content))

    if has_batch and not has_state_machine:
        issues.append({
            "severity": "INFO",
            "category": "architecture",
            "issue": "Using tea.Batch without explicit state tracking",
            "location": file_path,
            "explanation": "Messages from tea.Batch arrive in unpredictable order",
            "fix": "Use state machine to track operations:\n\n" +
                   "type model struct {\n" +
                   "    operations map[string]bool  // Track active operations\n" +
                   "}\n\n" +
                   "type opStartMsg struct { id string }\n" +
                   "type opDoneMsg struct { id string, result string }\n\n" +
                   "func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {\n" +
                   "    switch msg := msg.(type) {\n" +
                   "    case opStartMsg:\n" +
                   "        m.operations[msg.id] = true\n" +
                   "    case opDoneMsg:\n" +
                   "        delete(m.operations, msg.id)\n" +
                   "    }\n" +
                   "    return m, nil\n" +
                   "}"
        })

    return issues


def _check_model_complexity(content: str, lines: List[str], file_path: str) -> List[Dict[str, Any]]:
    """Check if model is too complex and should use model tree."""
    issues = []

    # Count fields in model struct
    model_match = re.search(r'type\s+(\w*[Mm]odel)\s+struct\s*\{([^}]+)\}', content, re.DOTALL)
    if model_match:
        model_body = model_match.group(2)
        field_count = len([line for line in model_body.split('\n') if line.strip() and not line.strip().startswith('//')])

        if field_count > 15:
            issues.append({
                "severity": "INFO",
                "category": "architecture",
                "issue": f"Model has {field_count} fields (complex)",
                "location": file_path,
                "explanation": "Large models are hard to maintain. Consider model tree pattern.",
                "fix": "Refactor to model tree:\n\n" +
                       "type appModel struct {\n" +
                       "    activeView int\n" +
                       "    listView   listModel\n" +
                       "    detailView detailModel\n" +
                       "}\n\n" +
                       "func (m appModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {\n" +
                       "    switch m.activeView {\n" +
                       "    case 0:\n" +
                       "        m.listView, cmd = m.listView.Update(msg)\n" +
                       "    case 1:\n" +
                       "        m.detailView, cmd = m.detailView.Update(msg)\n" +
                       "    }\n" +
                       "    return m, cmd\n" +
                       "}"
            })

    return issues


def _check_goroutine_leaks(content: str, lines: List[str], file_path: str) -> List[Dict[str, Any]]:
    """Check for potential goroutine leaks."""
    issues = []

    # Look for goroutines without cleanup
    has_go_statements = bool(re.search(r'\bgo\s+', content))
    has_context_cancel = bool(re.search(r'ctx,\s*cancel\s*:=\s*context\.', content))

    if has_go_statements and not has_context_cancel:
        issues.append({
            "severity": "WARNING",
            "category": "reliability",
            "issue": "Goroutines without context cancellation",
            "location": file_path,
            "explanation": "Goroutines may leak if not properly cancelled",
            "fix": "Use context for goroutine lifecycle:\n\n" +
                   "type model struct {\n" +
                   "    ctx    context.Context\n" +
                   "    cancel context.CancelFunc\n" +
                   "}\n\n" +
                   "func initialModel() model {\n" +
                   "    ctx, cancel := context.WithCancel(context.Background())\n" +
                   "    return model{ctx: ctx, cancel: cancel}\n" +
                   "}\n\n" +
                   "// In Update() on quit:\n" +
                   "m.cancel()  // Stops all goroutines"
        })

    return issues


def _check_layout_arithmetic(content: str, lines: List[str], file_path: str) -> List[Dict[str, Any]]:
    """Check for layout arithmetic issues."""
    issues = []

    # Look for manual height/width calculations instead of lipgloss helpers
    uses_lipgloss = bool(re.search(r'"github\.com/charmbracelet/lipgloss"', content))
    has_manual_calc = bool(re.search(r'(height|width)\s*[-+]\s*\d+', content, re.IGNORECASE))
    has_lipgloss_helpers = bool(re.search(r'lipgloss\.(Height|Width|GetVertical|GetHorizontal)', content))

    if uses_lipgloss and has_manual_calc and not has_lipgloss_helpers:
        issues.append({
            "severity": "WARNING",
            "category": "layout",
            "issue": "Manual layout calculations without lipgloss helpers",
            "location": file_path,
            "explanation": "Manual calculations are error-prone. Use lipgloss.Height() and lipgloss.Width()",
            "fix": "Use lipgloss helpers:\n\n" +
                   "// ❌ BAD:\n" +
                   "availableHeight := termHeight - 5  // Magic number!\n\n" +
                   "// ✅ GOOD:\n" +
                   "headerHeight := lipgloss.Height(header)\n" +
                   "footerHeight := lipgloss.Height(footer)\n" +
                   "availableHeight := termHeight - headerHeight - footerHeight"
        })

    return issues


# Validation function
def validate_diagnosis(result: Dict[str, Any]) -> Dict[str, Any]:
    """Validate diagnosis result."""
    if 'error' in result:
        return {"status": "error", "summary": result['error']}

    validation = result.get('validation', {})
    status = validation.get('status', 'unknown')
    summary = validation.get('summary', 'Diagnosis complete')

    checks = [
        (result.get('issues') is not None, "Has issues list"),
        (result.get('health_score') is not None, "Has health score"),
        (result.get('summary') is not None, "Has summary"),
        (len(result.get('issues', [])) >= 0, "Issues analyzed"),
    ]

    all_pass = all(check[0] for check in checks)

    return {
        "status": status,
        "summary": summary,
        "checks": {check[1]: check[0] for check in checks},
        "valid": all_pass
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: diagnose_issue.py <code_path> [description]")
        sys.exit(1)

    code_path = sys.argv[1]
    description = sys.argv[2] if len(sys.argv) > 2 else ""

    result = diagnose_issue(code_path, description)
    print(json.dumps(result, indent=2))
