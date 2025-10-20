#!/usr/bin/env python3
"""
Debug performance issues in Bubble Tea applications.
Identifies bottlenecks in Update(), View(), and concurrent operations.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional


def debug_performance(code_path: str, profile_data: str = "") -> Dict[str, Any]:
    """
    Identify performance bottlenecks in Bubble Tea application.

    Args:
        code_path: Path to Go file or directory
        profile_data: Optional profiling data (pprof output, benchmark results)

    Returns:
        Dictionary containing:
        - bottlenecks: List of performance issues with locations and fixes
        - metrics: Performance metrics (if available)
        - recommendations: Prioritized optimization suggestions
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

    # Analyze performance for each file
    all_bottlenecks = []
    for go_file in go_files:
        bottlenecks = _analyze_performance(go_file)
        all_bottlenecks.extend(bottlenecks)

    # Sort by severity
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    all_bottlenecks.sort(key=lambda x: severity_order.get(x['severity'], 999))

    # Generate recommendations
    recommendations = _generate_performance_recommendations(all_bottlenecks)

    # Estimate metrics
    metrics = _estimate_metrics(all_bottlenecks, go_files)

    # Summary
    critical_count = sum(1 for b in all_bottlenecks if b['severity'] == 'CRITICAL')
    high_count = sum(1 for b in all_bottlenecks if b['severity'] == 'HIGH')

    if critical_count > 0:
        summary = f"⚠️  Found {critical_count} critical performance issue(s)"
    elif high_count > 0:
        summary = f"⚠️  Found {high_count} high-priority performance issue(s)"
    elif all_bottlenecks:
        summary = f"Found {len(all_bottlenecks)} potential optimization(s)"
    else:
        summary = "✅ No major performance issues detected"

    # Validation
    validation = {
        "status": "critical" if critical_count > 0 else "warning" if high_count > 0 else "pass",
        "summary": summary,
        "checks": {
            "fast_update": critical_count == 0,
            "fast_view": high_count == 0,
            "no_memory_leaks": not any(b['category'] == 'memory' for b in all_bottlenecks),
            "efficient_rendering": not any(b['category'] == 'rendering' for b in all_bottlenecks)
        }
    }

    return {
        "bottlenecks": all_bottlenecks,
        "metrics": metrics,
        "recommendations": recommendations,
        "summary": summary,
        "profile_data": profile_data if profile_data else None,
        "validation": validation
    }


def _analyze_performance(file_path: Path) -> List[Dict[str, Any]]:
    """Analyze a single Go file for performance issues."""
    bottlenecks = []

    try:
        content = file_path.read_text()
    except Exception as e:
        return []

    lines = content.split('\n')
    rel_path = file_path.name

    # Performance checks
    bottlenecks.extend(_check_update_performance(content, lines, rel_path))
    bottlenecks.extend(_check_view_performance(content, lines, rel_path))
    bottlenecks.extend(_check_string_operations(content, lines, rel_path))
    bottlenecks.extend(_check_regex_performance(content, lines, rel_path))
    bottlenecks.extend(_check_loop_efficiency(content, lines, rel_path))
    bottlenecks.extend(_check_allocation_patterns(content, lines, rel_path))
    bottlenecks.extend(_check_concurrent_operations(content, lines, rel_path))
    bottlenecks.extend(_check_io_operations(content, lines, rel_path))

    return bottlenecks


def _check_update_performance(content: str, lines: List[str], file_path: str) -> List[Dict[str, Any]]:
    """Check Update() function for performance issues."""
    bottlenecks = []

    # Find Update() function
    update_start = -1
    update_end = -1
    brace_count = 0

    for i, line in enumerate(lines):
        if re.search(r'func\s+\([^)]+\)\s+Update\s*\(', line):
            update_start = i
            brace_count = line.count('{') - line.count('}')
        elif update_start >= 0:
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0:
                update_end = i
                break

    if update_start < 0:
        return bottlenecks

    update_lines = lines[update_start:update_end+1] if update_end > 0 else lines[update_start:]
    update_code = '\n'.join(update_lines)

    # Check 1: Blocking I/O in Update()
    blocking_patterns = [
        (r'\bhttp\.(Get|Post|Do)\s*\(', "HTTP request", "CRITICAL"),
        (r'\btime\.Sleep\s*\(', "Sleep call", "CRITICAL"),
        (r'\bos\.(Open|Read|Write)', "File I/O", "CRITICAL"),
        (r'\bio\.ReadAll\s*\(', "ReadAll", "CRITICAL"),
        (r'\bexec\.Command\([^)]+\)\.Run\(\)', "Command execution", "CRITICAL"),
        (r'\bdb\.(Query|Exec)', "Database operation", "CRITICAL"),
    ]

    for pattern, operation, severity in blocking_patterns:
        matches = re.finditer(pattern, update_code)
        for match in matches:
            # Find line number within Update()
            line_offset = update_code[:match.start()].count('\n')
            actual_line = update_start + line_offset

            bottlenecks.append({
                "severity": severity,
                "category": "performance",
                "issue": f"Blocking {operation} in Update()",
                "location": f"{file_path}:{actual_line+1}",
                "time_impact": "Blocks event loop (16ms+ delay)",
                "explanation": f"{operation} blocks the event loop, freezing the UI",
                "fix": f"Move to tea.Cmd goroutine:\n\n" +
                       f"func fetch{operation.replace(' ', '')}() tea.Msg {{\n" +
                       f"    // Runs in background, doesn't block\n" +
                       f"    result, err := /* your {operation.lower()} */\n" +
                       f"    return resultMsg{{data: result, err: err}}\n" +
                       f"}}\n\n" +
                       f"// In Update():\n" +
                       f"case tea.KeyMsg:\n" +
                       f"    if key.String() == \"r\" {{\n" +
                       f"        return m, fetch{operation.replace(' ', '')}  // Non-blocking\n" +
                       f"    }}",
                "code_example": f"return m, fetch{operation.replace(' ', '')}"
            })

    # Check 2: Heavy computation in Update()
    computation_patterns = [
        (r'for\s+.*range\s+\w+\s*\{[^}]{100,}\}', "Large loop", "HIGH"),
        (r'json\.(Marshal|Unmarshal)', "JSON processing", "MEDIUM"),
        (r'regexp\.MustCompile\s*\(', "Regex compilation", "HIGH"),
    ]

    for pattern, operation, severity in computation_patterns:
        matches = re.finditer(pattern, update_code, re.DOTALL)
        for match in matches:
            line_offset = update_code[:match.start()].count('\n')
            actual_line = update_start + line_offset

            bottlenecks.append({
                "severity": severity,
                "category": "performance",
                "issue": f"Heavy {operation} in Update()",
                "location": f"{file_path}:{actual_line+1}",
                "time_impact": "May exceed 16ms budget",
                "explanation": f"{operation} can be expensive, consider optimizing",
                "fix": "Optimize:\n" +
                       "- Cache compiled regexes (compile once, reuse)\n" +
                       "- Move heavy processing to tea.Cmd\n" +
                       "- Use incremental updates instead of full recalculation",
                "code_example": "var cachedRegex = regexp.MustCompile(`pattern`)  // Outside Update()"
            })

    return bottlenecks


def _check_view_performance(content: str, lines: List[str], file_path: str) -> List[Dict[str, Any]]:
    """Check View() function for performance issues."""
    bottlenecks = []

    # Find View() function
    view_start = -1
    view_end = -1
    brace_count = 0

    for i, line in enumerate(lines):
        if re.search(r'func\s+\([^)]+\)\s+View\s*\(', line):
            view_start = i
            brace_count = line.count('{') - line.count('}')
        elif view_start >= 0:
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0:
                view_end = i
                break

    if view_start < 0:
        return bottlenecks

    view_lines = lines[view_start:view_end+1] if view_end > 0 else lines[view_start:]
    view_code = '\n'.join(view_lines)

    # Check 1: String concatenation with +
    string_concat_pattern = r'(\w+\s*\+\s*"[^"]*"\s*\+\s*\w+|\w+\s*\+=\s*"[^"]*")'
    if re.search(string_concat_pattern, view_code):
        matches = list(re.finditer(string_concat_pattern, view_code))
        if len(matches) > 5:  # Multiple concatenations
            bottlenecks.append({
                "severity": "HIGH",
                "category": "rendering",
                "issue": f"String concatenation with + operator ({len(matches)} occurrences)",
                "location": f"{file_path}:{view_start+1} (View function)",
                "time_impact": "Allocates many temporary strings",
                "explanation": "Using + for strings creates many allocations. Use strings.Builder.",
                "fix": "Replace with strings.Builder:\n\n" +
                       "import \"strings\"\n\n" +
                       "func (m model) View() string {\n" +
                       "    var b strings.Builder\n" +
                       "    b.WriteString(\"header\")\n" +
                       "    b.WriteString(m.content)\n" +
                       "    b.WriteString(\"footer\")\n" +
                       "    return b.String()\n" +
                       "}",
                "code_example": "var b strings.Builder; b.WriteString(...)"
            })

    # Check 2: Recompiling lipgloss styles
    style_in_view = re.findall(r'lipgloss\.NewStyle\(\)', view_code)
    if len(style_in_view) > 3:
        bottlenecks.append({
            "severity": "MEDIUM",
            "category": "rendering",
            "issue": f"Creating lipgloss styles in View() ({len(style_in_view)} times)",
            "location": f"{file_path}:{view_start+1} (View function)",
            "time_impact": "Recreates styles on every render",
            "explanation": "Style creation is relatively expensive. Cache styles in model.",
            "fix": "Cache styles in model:\n\n" +
                   "type model struct {\n" +
                   "    // ... other fields\n" +
                   "    headerStyle lipgloss.Style\n" +
                   "    contentStyle lipgloss.Style\n" +
                   "}\n\n" +
                   "func initialModel() model {\n" +
                   "    return model{\n" +
                   "        headerStyle: lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color(\"#FF00FF\")),\n" +
                   "        contentStyle: lipgloss.NewStyle().Padding(1),\n" +
                   "    }\n" +
                   "}\n\n" +
                   "func (m model) View() string {\n" +
                   "    return m.headerStyle.Render(\"Header\") + m.contentStyle.Render(m.content)\n" +
                   "}",
            "code_example": "m.headerStyle.Render(...)  // Use cached style"
        })

    # Check 3: Reading files in View()
    if re.search(r'\b(os\.ReadFile|ioutil\.ReadFile|os\.Open)', view_code):
        bottlenecks.append({
            "severity": "CRITICAL",
            "category": "rendering",
            "issue": "File I/O in View() function",
            "location": f"{file_path}:{view_start+1} (View function)",
            "time_impact": "Massive delay (1-100ms per render)",
            "explanation": "View() is called frequently. File I/O blocks rendering.",
            "fix": "Load file in Update(), cache in model:\n\n" +
                   "type model struct {\n" +
                   "    fileContent string\n" +
                   "}\n\n" +
                   "func loadFile() tea.Msg {\n" +
                   "    content, err := os.ReadFile(\"file.txt\")\n" +
                   "    return fileLoadedMsg{content: string(content), err: err}\n" +
                   "}\n\n" +
                   "// In Update():\n" +
                   "case fileLoadedMsg:\n" +
                   "    m.fileContent = msg.content\n\n" +
                   "// In View():\n" +
                   "return m.fileContent  // Just return cached data",
            "code_example": "return m.cachedContent  // No I/O in View()"
        })

    # Check 4: Expensive lipgloss operations
    join_vertical_count = len(re.findall(r'lipgloss\.JoinVertical', view_code))
    if join_vertical_count > 10:
        bottlenecks.append({
            "severity": "LOW",
            "category": "rendering",
            "issue": f"Many lipgloss.JoinVertical calls ({join_vertical_count})",
            "location": f"{file_path}:{view_start+1} (View function)",
            "time_impact": "Accumulates string operations",
            "explanation": "Many join operations can add up. Consider batching.",
            "fix": "Batch related joins:\n\n" +
                   "// Instead of many small joins:\n" +
                   "// line1 := lipgloss.JoinHorizontal(...)\n" +
                   "// line2 := lipgloss.JoinHorizontal(...)\n" +
                   "// ...\n\n" +
                   "// Build all lines first, join once:\n" +
                   "lines := []string{\n" +
                   "    lipgloss.JoinHorizontal(...),\n" +
                   "    lipgloss.JoinHorizontal(...),\n" +
                   "    lipgloss.JoinHorizontal(...),\n" +
                   "}\n" +
                   "return lipgloss.JoinVertical(lipgloss.Left, lines...)",
            "code_example": "lipgloss.JoinVertical(lipgloss.Left, lines...)"
        })

    return bottlenecks


def _check_string_operations(content: str, lines: List[str], file_path: str) -> List[Dict[str, Any]]:
    """Check for inefficient string operations."""
    bottlenecks = []

    # Check for fmt.Sprintf in loops
    for i, line in enumerate(lines):
        if 'for' in line:
            # Check next 20 lines for fmt.Sprintf
            for j in range(i, min(i+20, len(lines))):
                if 'fmt.Sprintf' in lines[j] and 'result' in lines[j]:
                    bottlenecks.append({
                        "severity": "MEDIUM",
                        "category": "performance",
                        "issue": "fmt.Sprintf in loop",
                        "location": f"{file_path}:{j+1}",
                        "time_impact": "Allocations on every iteration",
                        "explanation": "fmt.Sprintf allocates. Use strings.Builder or fmt.Fprintf.",
                        "fix": "Use strings.Builder:\n\n" +
                               "var b strings.Builder\n" +
                               "for _, item := range items {\n" +
                               "    fmt.Fprintf(&b, \"Item: %s\\n\", item)\n" +
                               "}\n" +
                               "result := b.String()",
                        "code_example": "fmt.Fprintf(&builder, ...)"
                    })
                    break

    return bottlenecks


def _check_regex_performance(content: str, lines: List[str], file_path: str) -> List[Dict[str, Any]]:
    """Check for regex performance issues."""
    bottlenecks = []

    # Check for regexp.MustCompile in functions (not at package level)
    in_function = False
    for i, line in enumerate(lines):
        if re.match(r'^\s*func\s+', line):
            in_function = True
        elif in_function and re.match(r'^\s*$', line):
            in_function = False

        if in_function and 'regexp.MustCompile' in line:
            bottlenecks.append({
                "severity": "HIGH",
                "category": "performance",
                "issue": "Compiling regex in function",
                "location": f"{file_path}:{i+1}",
                "time_impact": "Compiles on every call (1-10ms)",
                "explanation": "Regex compilation is expensive. Compile once at package level.",
                "fix": "Move to package level:\n\n" +
                       "// At package level (outside functions)\n" +
                       "var (\n" +
                       "    emailRegex = regexp.MustCompile(`^[a-z]+@[a-z]+\\.[a-z]+$`)\n" +
                       "    phoneRegex = regexp.MustCompile(`^\\d{3}-\\d{3}-\\d{4}$`)\n" +
                       ")\n\n" +
                       "// In function\n" +
                       "func validate(email string) bool {\n" +
                       "    return emailRegex.MatchString(email)  // Reuse compiled regex\n" +
                       "}",
                "code_example": "var emailRegex = regexp.MustCompile(...)  // Package level"
            })

    return bottlenecks


def _check_loop_efficiency(content: str, lines: List[str], file_path: str) -> List[Dict[str, Any]]:
    """Check for inefficient loops."""
    bottlenecks = []

    # Check for nested loops over large data
    for i, line in enumerate(lines):
        if re.search(r'for\s+.*range', line):
            # Look for nested loop within 30 lines
            for j in range(i+1, min(i+30, len(lines))):
                if re.search(r'for\s+.*range', lines[j]):
                    # Check indentation (nested)
                    if len(lines[j]) - len(lines[j].lstrip()) > len(line) - len(line.lstrip()):
                        bottlenecks.append({
                            "severity": "MEDIUM",
                            "category": "performance",
                            "issue": "Nested loops detected",
                            "location": f"{file_path}:{i+1}",
                            "time_impact": "O(n²) complexity",
                            "explanation": "Nested loops can be slow. Consider optimization.",
                            "fix": "Optimization strategies:\n" +
                                   "1. Use map/set for O(1) lookups instead of nested loop\n" +
                                   "2. Break early when possible\n" +
                                   "3. Process data once, cache results\n" +
                                   "4. Use channels/goroutines for parallel processing\n\n" +
                                   "Example with map:\n" +
                                   "// Instead of:\n" +
                                   "for _, a := range listA {\n" +
                                   "    for _, b := range listB {\n" +
                                   "        if a.id == b.id { found = true }\n" +
                                   "    }\n" +
                                   "}\n\n" +
                                   "// Use map:\n" +
                                   "mapB := make(map[string]bool)\n" +
                                   "for _, b := range listB {\n" +
                                   "    mapB[b.id] = true\n" +
                                   "}\n" +
                                   "for _, a := range listA {\n" +
                                   "    if mapB[a.id] { found = true }\n" +
                                   "}",
                            "code_example": "Use map for O(1) lookup"
                        })
                        break

    return bottlenecks


def _check_allocation_patterns(content: str, lines: List[str], file_path: str) -> List[Dict[str, Any]]:
    """Check for excessive allocations."""
    bottlenecks = []

    # Check for slice append in loops without pre-allocation
    for i, line in enumerate(lines):
        if re.search(r'for\s+.*range', line):
            # Check next 20 lines for append without make
            has_append = False
            for j in range(i, min(i+20, len(lines))):
                if 'append(' in lines[j]:
                    has_append = True
                    break

            # Check if slice was pre-allocated
            has_make = False
            for j in range(max(0, i-10), i):
                if 'make(' in lines[j] and 'len(' in lines[j]:
                    has_make = True
                    break

            if has_append and not has_make:
                bottlenecks.append({
                    "severity": "LOW",
                    "category": "memory",
                    "issue": "Slice append in loop without pre-allocation",
                    "location": f"{file_path}:{i+1}",
                    "time_impact": "Multiple reallocations",
                    "explanation": "Appending without pre-allocation causes slice to grow, reallocate.",
                    "fix": "Pre-allocate slice:\n\n" +
                           "// Instead of:\n" +
                           "var results []string\n" +
                           "for _, item := range items {\n" +
                           "    results = append(results, process(item))\n" +
                           "}\n\n" +
                           "// Pre-allocate:\n" +
                           "results := make([]string, 0, len(items))  // Pre-allocate capacity\n" +
                           "for _, item := range items {\n" +
                           "    results = append(results, process(item))  // No reallocation\n" +
                           "}",
                    "code_example": "results := make([]string, 0, len(items))"
                })

    return bottlenecks


def _check_concurrent_operations(content: str, lines: List[str], file_path: str) -> List[Dict[str, Any]]:
    """Check for concurrency issues."""
    bottlenecks = []

    # Check for goroutine leaks
    has_goroutines = bool(re.search(r'\bgo\s+func', content))
    has_context = bool(re.search(r'context\.', content))
    has_waitgroup = bool(re.search(r'sync\.WaitGroup', content))

    if has_goroutines and not (has_context or has_waitgroup):
        bottlenecks.append({
            "severity": "HIGH",
            "category": "memory",
            "issue": "Goroutines without lifecycle management",
            "location": file_path,
            "time_impact": "Goroutine leaks consume memory",
            "explanation": "Goroutines need proper cleanup to prevent leaks.",
            "fix": "Use context for cancellation:\n\n" +
                   "type model struct {\n" +
                   "    ctx    context.Context\n" +
                   "    cancel context.CancelFunc\n" +
                   "}\n\n" +
                   "func initialModel() model {\n" +
                   "    ctx, cancel := context.WithCancel(context.Background())\n" +
                   "    return model{ctx: ctx, cancel: cancel}\n" +
                   "}\n\n" +
                   "func worker(ctx context.Context) tea.Msg {\n" +
                   "    for {\n" +
                   "        select {\n" +
                   "        case <-ctx.Done():\n" +
                   "            return nil  // Stop goroutine\n" +
                   "        case <-time.After(time.Second):\n" +
                   "            // Do work\n" +
                   "        }\n" +
                   "    }\n" +
                   "}\n\n" +
                   "// In Update() on quit:\n" +
                   "m.cancel()  // Stops all goroutines",
            "code_example": "ctx, cancel := context.WithCancel(context.Background())"
        })

    return bottlenecks


def _check_io_operations(content: str, lines: List[str], file_path: str) -> List[Dict[str, Any]]:
    """Check for I/O operations that should be async."""
    bottlenecks = []

    # Check for synchronous file reads
    file_ops = [
        (r'os\.ReadFile', "os.ReadFile"),
        (r'ioutil\.ReadFile', "ioutil.ReadFile"),
        (r'os\.Open', "os.Open"),
        (r'io\.ReadAll', "io.ReadAll"),
    ]

    for pattern, op_name in file_ops:
        matches = list(re.finditer(pattern, content))
        if matches:
            # Check if in tea.Cmd (good) or in Update/View (bad)
            for match in matches:
                # Find which function this is in
                line_num = content[:match.start()].count('\n')
                context_lines = content.split('\n')[max(0, line_num-10):line_num+1]
                context_text = '\n'.join(context_lines)

                in_cmd = bool(re.search(r'func\s+\w+\(\s*\)\s+tea\.Msg', context_text))
                in_update = bool(re.search(r'func\s+\([^)]+\)\s+Update', context_text))
                in_view = bool(re.search(r'func\s+\([^)]+\)\s+View', context_text))

                if (in_update or in_view) and not in_cmd:
                    severity = "CRITICAL" if in_view else "HIGH"
                    func_name = "View()" if in_view else "Update()"

                    bottlenecks.append({
                        "severity": severity,
                        "category": "io",
                        "issue": f"Synchronous {op_name} in {func_name}",
                        "location": f"{file_path}:{line_num+1}",
                        "time_impact": "1-100ms per call",
                        "explanation": f"{op_name} blocks the event loop",
                        "fix": f"Move to tea.Cmd:\n\n" +
                               f"func loadFileCmd() tea.Msg {{\n" +
                               f"    data, err := {op_name}(\"file.txt\")\n" +
                               f"    return fileLoadedMsg{{data: data, err: err}}\n" +
                               f"}}\n\n" +
                               f"// In Update():\n" +
                               f"case tea.KeyMsg:\n" +
                               f"    if key.String() == \"o\" {{\n" +
                               f"        return m, loadFileCmd  // Non-blocking\n" +
                               f"    }}",
                        "code_example": "return m, loadFileCmd  // Async I/O"
                    })

    return bottlenecks


def _generate_performance_recommendations(bottlenecks: List[Dict[str, Any]]) -> List[str]:
    """Generate prioritized performance recommendations."""
    recommendations = []

    # Group by category
    categories = {}
    for b in bottlenecks:
        cat = b['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(b)

    # Priority recommendations
    if 'performance' in categories:
        critical = [b for b in categories['performance'] if b['severity'] == 'CRITICAL']
        if critical:
            recommendations.append(
                f"🔴 CRITICAL: Move {len(critical)} blocking operation(s) to tea.Cmd goroutines"
            )

    if 'rendering' in categories:
        recommendations.append(
            f"⚡ Optimize View() rendering: Found {len(categories['rendering'])} issue(s)"
        )

    if 'memory' in categories:
        recommendations.append(
            f"💾 Fix memory issues: Found {len(categories['memory'])} potential leak(s)"
        )

    if 'io' in categories:
        recommendations.append(
            f"💿 Make I/O async: Found {len(categories['io'])} synchronous I/O call(s)"
        )

    # General recommendations
    recommendations.extend([
        "Profile with pprof to get precise measurements",
        "Use benchmarks to validate optimizations",
        "Monitor with runtime.ReadMemStats() for memory usage",
        "Test with large datasets to reveal performance issues"
    ])

    return recommendations


def _estimate_metrics(bottlenecks: List[Dict[str, Any]], files: List[Path]) -> Dict[str, Any]:
    """Estimate performance metrics based on analysis."""

    # Estimate Update() time
    critical_in_update = sum(1 for b in bottlenecks
                            if 'Update()' in b.get('issue', '') and b['severity'] == 'CRITICAL')
    high_in_update = sum(1 for b in bottlenecks
                        if 'Update()' in b.get('issue', '') and b['severity'] == 'HIGH')

    estimated_update_time = "2-5ms (good)"
    if critical_in_update > 0:
        estimated_update_time = "50-200ms (critical - UI freezing)"
    elif high_in_update > 0:
        estimated_update_time = "20-50ms (slow - noticeable lag)"

    # Estimate View() time
    critical_in_view = sum(1 for b in bottlenecks
                          if 'View()' in b.get('issue', '') and b['severity'] == 'CRITICAL')
    high_in_view = sum(1 for b in bottlenecks
                      if 'View()' in b.get('issue', '') and b['severity'] == 'HIGH')

    estimated_view_time = "1-3ms (good)"
    if critical_in_view > 0:
        estimated_view_time = "100-500ms (critical - very slow)"
    elif high_in_view > 0:
        estimated_view_time = "10-30ms (slow)"

    # Memory estimate
    goroutine_leaks = sum(1 for b in bottlenecks if 'leak' in b.get('issue', '').lower())
    memory_status = "stable"
    if goroutine_leaks > 0:
        memory_status = "growing (leaks detected)"

    return {
        "estimated_update_time": estimated_update_time,
        "estimated_view_time": estimated_view_time,
        "memory_status": memory_status,
        "total_bottlenecks": len(bottlenecks),
        "critical_issues": sum(1 for b in bottlenecks if b['severity'] == 'CRITICAL'),
        "files_analyzed": len(files),
        "note": "Run actual profiling (pprof, benchmarks) for precise measurements"
    }


def validate_performance_debug(result: Dict[str, Any]) -> Dict[str, Any]:
    """Validate performance debug result."""
    if 'error' in result:
        return {"status": "error", "summary": result['error']}

    validation = result.get('validation', {})
    status = validation.get('status', 'unknown')
    summary = validation.get('summary', 'Performance analysis complete')

    checks = [
        (result.get('bottlenecks') is not None, "Has bottlenecks list"),
        (result.get('metrics') is not None, "Has metrics"),
        (result.get('recommendations') is not None, "Has recommendations"),
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
        print("Usage: debug_performance.py <code_path> [profile_data]")
        sys.exit(1)

    code_path = sys.argv[1]
    profile_data = sys.argv[2] if len(sys.argv) > 2 else ""

    result = debug_performance(code_path, profile_data)
    print(json.dumps(result, indent=2))
