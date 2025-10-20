#!/usr/bin/env python3
"""
Fix Lipgloss layout issues in Bubble Tea applications.
Identifies hardcoded dimensions, incorrect calculations, overflow issues, etc.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional


def fix_layout_issues(code_path: str, description: str = "") -> Dict[str, Any]:
    """
    Diagnose and fix common Lipgloss layout problems.

    Args:
        code_path: Path to Go file or directory
        description: Optional user description of layout issue

    Returns:
        Dictionary containing:
        - layout_issues: List of identified layout problems with fixes
        - lipgloss_improvements: General recommendations
        - code_fixes: Concrete code changes to apply
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

    # Analyze all files for layout issues
    all_layout_issues = []
    all_code_fixes = []

    for go_file in go_files:
        issues, fixes = _analyze_layout_issues(go_file)
        all_layout_issues.extend(issues)
        all_code_fixes.extend(fixes)

    # Generate improvement recommendations
    lipgloss_improvements = _generate_improvements(all_layout_issues)

    # Summary
    critical_count = sum(1 for i in all_layout_issues if i['severity'] == 'CRITICAL')
    warning_count = sum(1 for i in all_layout_issues if i['severity'] == 'WARNING')

    if critical_count > 0:
        summary = f"🚨 Found {critical_count} critical layout issue(s)"
    elif warning_count > 0:
        summary = f"⚠️  Found {warning_count} layout issue(s) to address"
    elif all_layout_issues:
        summary = f"Found {len(all_layout_issues)} minor layout improvement(s)"
    else:
        summary = "✅ No major layout issues detected"

    # Validation
    validation = {
        "status": "critical" if critical_count > 0 else "warning" if warning_count > 0 else "pass",
        "summary": summary,
        "checks": {
            "no_hardcoded_dimensions": not any(i['type'] == 'hardcoded_dimensions' for i in all_layout_issues),
            "proper_height_calc": not any(i['type'] == 'incorrect_height' for i in all_layout_issues),
            "handles_padding": not any(i['type'] == 'missing_padding_calc' for i in all_layout_issues),
            "handles_overflow": not any(i['type'] == 'overflow' for i in all_layout_issues)
        }
    }

    return {
        "layout_issues": all_layout_issues,
        "lipgloss_improvements": lipgloss_improvements,
        "code_fixes": all_code_fixes,
        "summary": summary,
        "user_description": description,
        "files_analyzed": len(go_files),
        "validation": validation
    }


def _analyze_layout_issues(file_path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Analyze a single Go file for layout issues."""
    layout_issues = []
    code_fixes = []

    try:
        content = file_path.read_text()
    except Exception as e:
        return layout_issues, code_fixes

    lines = content.split('\n')
    rel_path = file_path.name

    # Check if file uses lipgloss
    uses_lipgloss = bool(re.search(r'"github\.com/charmbracelet/lipgloss"', content))

    if not uses_lipgloss:
        return layout_issues, code_fixes

    # Issue checks
    issues, fixes = _check_hardcoded_dimensions(content, lines, rel_path)
    layout_issues.extend(issues)
    code_fixes.extend(fixes)

    issues, fixes = _check_incorrect_height_calculations(content, lines, rel_path)
    layout_issues.extend(issues)
    code_fixes.extend(fixes)

    issues, fixes = _check_missing_padding_accounting(content, lines, rel_path)
    layout_issues.extend(issues)
    code_fixes.extend(fixes)

    issues, fixes = _check_overflow_issues(content, lines, rel_path)
    layout_issues.extend(issues)
    code_fixes.extend(fixes)

    issues, fixes = _check_terminal_resize_handling(content, lines, rel_path)
    layout_issues.extend(issues)
    code_fixes.extend(fixes)

    issues, fixes = _check_border_accounting(content, lines, rel_path)
    layout_issues.extend(issues)
    code_fixes.extend(fixes)

    return layout_issues, code_fixes


def _check_hardcoded_dimensions(content: str, lines: List[str], file_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Check for hardcoded width/height values."""
    issues = []
    fixes = []

    # Pattern: .Width(80), .Height(24), etc.
    dimension_pattern = r'\.(Width|Height|MaxWidth|MaxHeight)\s*\(\s*(\d{2,})\s*\)'

    for i, line in enumerate(lines):
        matches = re.finditer(dimension_pattern, line)
        for match in matches:
            dimension_type = match.group(1)
            value = int(match.group(2))

            # Likely a terminal dimension if >= 20
            if value >= 20:
                issues.append({
                    "severity": "WARNING",
                    "type": "hardcoded_dimensions",
                    "issue": f"Hardcoded {dimension_type}: {value}",
                    "location": f"{file_path}:{i+1}",
                    "current_code": line.strip(),
                    "explanation": f"Hardcoded {dimension_type} of {value} won't adapt to different terminal sizes",
                    "impact": "Layout breaks on smaller/larger terminals"
                })

                # Generate fix
                if dimension_type in ["Width", "MaxWidth"]:
                    fixed_code = re.sub(
                        rf'\.{dimension_type}\s*\(\s*{value}\s*\)',
                        f'.{dimension_type}(m.termWidth)',
                        line.strip()
                    )
                else:  # Height, MaxHeight
                    fixed_code = re.sub(
                        rf'\.{dimension_type}\s*\(\s*{value}\s*\)',
                        f'.{dimension_type}(m.termHeight)',
                        line.strip()
                    )

                fixes.append({
                    "location": f"{file_path}:{i+1}",
                    "original": line.strip(),
                    "fixed": fixed_code,
                    "explanation": f"Use dynamic terminal size from model (m.termWidth/m.termHeight)",
                    "requires": [
                        "Add termWidth and termHeight fields to model",
                        "Handle tea.WindowSizeMsg in Update()"
                    ],
                    "code_example": '''// In model:
type model struct {
    termWidth  int
    termHeight int
}

// In Update():
case tea.WindowSizeMsg:
    m.termWidth = msg.Width
    m.termHeight = msg.Height'''
                })

    return issues, fixes


def _check_incorrect_height_calculations(content: str, lines: List[str], file_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Check for manual height calculations instead of lipgloss.Height()."""
    issues = []
    fixes = []

    # Check View() function for manual calculations
    view_start = -1
    for i, line in enumerate(lines):
        if re.search(r'func\s+\([^)]+\)\s+View\s*\(', line):
            view_start = i
            break

    if view_start < 0:
        return issues, fixes

    # Look for manual arithmetic like "height - 5", "24 - headerHeight"
    manual_calc_pattern = r'(height|Height|termHeight)\s*[-+]\s*\d+'

    for i in range(view_start, min(view_start + 200, len(lines))):
        if re.search(manual_calc_pattern, lines[i], re.IGNORECASE):
            # Check if lipgloss.Height() is used in the vicinity
            context = '\n'.join(lines[max(0, i-5):i+5])
            uses_lipgloss_height = bool(re.search(r'lipgloss\.Height\s*\(', context))

            if not uses_lipgloss_height:
                issues.append({
                    "severity": "WARNING",
                    "type": "incorrect_height",
                    "issue": "Manual height calculation without lipgloss.Height()",
                    "location": f"{file_path}:{i+1}",
                    "current_code": lines[i].strip(),
                    "explanation": "Manual calculations don't account for actual rendered height",
                    "impact": "Incorrect spacing, overflow, or clipping"
                })

                # Generate fix
                fixed_code = lines[i].strip().replace(
                    "height - ", "m.termHeight - lipgloss.Height("
                ).replace("termHeight - ", "m.termHeight - lipgloss.Height(")

                fixes.append({
                    "location": f"{file_path}:{i+1}",
                    "original": lines[i].strip(),
                    "fixed": "Use lipgloss.Height() to get actual rendered height",
                    "explanation": "lipgloss.Height() accounts for padding, borders, margins",
                    "code_example": '''// ❌ BAD:
availableHeight := termHeight - 5  // Magic number!

// ✅ GOOD:
headerHeight := lipgloss.Height(m.renderHeader())
footerHeight := lipgloss.Height(m.renderFooter())
availableHeight := m.termHeight - headerHeight - footerHeight'''
                })

    return issues, fixes


def _check_missing_padding_accounting(content: str, lines: List[str], file_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Check for nested styles without padding/margin accounting."""
    issues = []
    fixes = []

    # Look for nested styles with padding
    # Pattern: Style().Padding(X).Width(Y).Render(content)
    nested_style_pattern = r'\.Padding\s*\([^)]+\).*\.Width\s*\(\s*(\w+)\s*\).*\.Render\s*\('

    for i, line in enumerate(lines):
        matches = re.finditer(nested_style_pattern, line)
        for match in matches:
            width_var = match.group(1)

            # Check if GetHorizontalPadding is used
            context = '\n'.join(lines[max(0, i-10):min(i+10, len(lines))])
            uses_get_padding = bool(re.search(r'GetHorizontalPadding\s*\(\s*\)', context))

            if not uses_get_padding and width_var != 'm.termWidth':
                issues.append({
                    "severity": "CRITICAL",
                    "type": "missing_padding_calc",
                    "issue": "Padding not accounted for in nested width calculation",
                    "location": f"{file_path}:{i+1}",
                    "current_code": line.strip(),
                    "explanation": "Setting Width() then Padding() makes content area smaller than expected",
                    "impact": "Content gets clipped or wrapped incorrectly"
                })

                fixes.append({
                    "location": f"{file_path}:{i+1}",
                    "original": line.strip(),
                    "fixed": "Account for padding using GetHorizontalPadding()",
                    "explanation": "Padding reduces available content area",
                    "code_example": '''// ❌ BAD:
style := lipgloss.NewStyle().
    Padding(2).
    Width(80).
    Render(text)  // Text area is 76, not 80!

// ✅ GOOD:
style := lipgloss.NewStyle().Padding(2)
contentWidth := 80 - style.GetHorizontalPadding()
content := lipgloss.NewStyle().Width(contentWidth).Render(text)
result := style.Width(80).Render(content)'''
                })

    return issues, fixes


def _check_overflow_issues(content: str, lines: List[str], file_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Check for potential text overflow."""
    issues = []
    fixes = []

    # Check for long strings without wrapping
    has_wordwrap = bool(re.search(r'"github\.com/muesli/reflow/wordwrap"', content))
    has_wrap_or_truncate = bool(re.search(r'(wordwrap|truncate|Truncate)', content, re.IGNORECASE))

    # Look for string rendering without width constraints
    render_pattern = r'\.Render\s*\(\s*(\w+)\s*\)'

    for i, line in enumerate(lines):
        matches = re.finditer(render_pattern, line)
        for match in matches:
            var_name = match.group(1)

            # Check if there's width control
            has_width_control = bool(re.search(r'\.Width\s*\(', line))

            if not has_width_control and not has_wrap_or_truncate and len(line) > 40:
                issues.append({
                    "severity": "WARNING",
                    "type": "overflow",
                    "issue": f"Rendering '{var_name}' without width constraint",
                    "location": f"{file_path}:{i+1}",
                    "current_code": line.strip(),
                    "explanation": "Long content can exceed terminal width",
                    "impact": "Text wraps unexpectedly or overflows"
                })

                fixes.append({
                    "location": f"{file_path}:{i+1}",
                    "original": line.strip(),
                    "fixed": "Add wordwrap or width constraint",
                    "explanation": "Constrain content to terminal width",
                    "code_example": '''// Option 1: Use wordwrap
import "github.com/muesli/reflow/wordwrap"

content := wordwrap.String(longText, m.termWidth)

// Option 2: Use lipgloss Width + truncate
style := lipgloss.NewStyle().Width(m.termWidth)
content := style.Render(longText)

// Option 3: Manual truncate
import "github.com/muesli/reflow/truncate"

content := truncate.StringWithTail(longText, uint(m.termWidth), "...")'''
                })

    return issues, fixes


def _check_terminal_resize_handling(content: str, lines: List[str], file_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Check for proper terminal resize handling."""
    issues = []
    fixes = []

    # Check if WindowSizeMsg is handled
    handles_resize = bool(re.search(r'case\s+tea\.WindowSizeMsg:', content))

    # Check if model stores term dimensions
    has_term_fields = bool(re.search(r'(termWidth|termHeight|width|height)\s+int', content))

    if not handles_resize and uses_lipgloss(content):
        issues.append({
            "severity": "CRITICAL",
            "type": "missing_resize_handling",
            "issue": "No tea.WindowSizeMsg handling detected",
            "location": file_path,
            "explanation": "Layout won't adapt when terminal is resized",
            "impact": "Content clipped or misaligned after resize"
        })

        fixes.append({
            "location": file_path,
            "original": "N/A",
            "fixed": "Add WindowSizeMsg handler",
            "explanation": "Store terminal dimensions and update on resize",
            "code_example": '''// In model:
type model struct {
    termWidth  int
    termHeight int
}

// In Update():
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.WindowSizeMsg:
        m.termWidth = msg.Width
        m.termHeight = msg.Height

        // Update child components with new size
        m.viewport.Width = msg.Width
        m.viewport.Height = msg.Height - 2  // Leave room for header
    }
    return m, nil
}

// In View():
func (m model) View() string {
    // Use m.termWidth and m.termHeight for dynamic layout
    content := lipgloss.NewStyle().
        Width(m.termWidth).
        Height(m.termHeight).
        Render(m.content)
    return content
}'''
        })

    elif handles_resize and not has_term_fields:
        issues.append({
            "severity": "WARNING",
            "type": "resize_not_stored",
            "issue": "WindowSizeMsg handled but dimensions not stored",
            "location": file_path,
            "explanation": "Handling resize but not storing dimensions for later use",
            "impact": "Can't use current terminal size in View()"
        })

    return issues, fixes


def _check_border_accounting(content: str, lines: List[str], file_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Check for border accounting in layout calculations."""
    issues = []
    fixes = []

    # Check for borders without proper accounting
    has_border = bool(re.search(r'\.Border\s*\(', content))
    has_border_width_calc = bool(re.search(r'GetHorizontalBorderSize|GetVerticalBorderSize', content))

    if has_border and not has_border_width_calc:
        # Find border usage lines
        for i, line in enumerate(lines):
            if '.Border(' in line:
                issues.append({
                    "severity": "WARNING",
                    "type": "missing_border_calc",
                    "issue": "Border used without accounting for border size",
                    "location": f"{file_path}:{i+1}",
                    "current_code": line.strip(),
                    "explanation": "Borders take space (2 chars horizontal, 2 chars vertical)",
                    "impact": "Content area smaller than expected"
                })

                fixes.append({
                    "location": f"{file_path}:{i+1}",
                    "original": line.strip(),
                    "fixed": "Account for border size",
                    "explanation": "Use GetHorizontalBorderSize() and GetVerticalBorderSize()",
                    "code_example": '''// With border:
style := lipgloss.NewStyle().
    Border(lipgloss.RoundedBorder()).
    Width(80)

// Calculate content area:
contentWidth := 80 - style.GetHorizontalBorderSize()
contentHeight := 24 - style.GetVerticalBorderSize()

// Use for inner content:
innerContent := lipgloss.NewStyle().
    Width(contentWidth).
    Height(contentHeight).
    Render(text)

result := style.Render(innerContent)'''
                })

    return issues, fixes


def uses_lipgloss(content: str) -> bool:
    """Check if file uses lipgloss."""
    return bool(re.search(r'"github\.com/charmbracelet/lipgloss"', content))


def _generate_improvements(issues: List[Dict[str, Any]]) -> List[str]:
    """Generate general improvement recommendations."""
    improvements = []

    issue_types = set(issue['type'] for issue in issues)

    if 'hardcoded_dimensions' in issue_types:
        improvements.append(
            "🎯 Use dynamic terminal sizing: Store termWidth/termHeight in model, update from tea.WindowSizeMsg"
        )

    if 'incorrect_height' in issue_types:
        improvements.append(
            "📏 Use lipgloss.Height() and lipgloss.Width() for accurate measurements"
        )

    if 'missing_padding_calc' in issue_types:
        improvements.append(
            "📐 Account for padding with GetHorizontalPadding() and GetVerticalPadding()"
        )

    if 'overflow' in issue_types:
        improvements.append(
            "📝 Use wordwrap or truncate to prevent text overflow"
        )

    if 'missing_resize_handling' in issue_types:
        improvements.append(
            "🔄 Handle tea.WindowSizeMsg to support terminal resizing"
        )

    if 'missing_border_calc' in issue_types:
        improvements.append(
            "🔲 Account for borders with GetHorizontalBorderSize() and GetVerticalBorderSize()"
        )

    # General best practices
    improvements.extend([
        "✨ Test your TUI at various terminal sizes (80x24, 120x40, 200x50)",
        "🔍 Use lipgloss debugging: Print style.String() to see computed dimensions",
        "📦 Cache computed styles in model to avoid recreation on every render",
        "🎨 Use PlaceHorizontal/PlaceVertical for alignment instead of manual padding"
    ])

    return improvements


def validate_layout_fixes(result: Dict[str, Any]) -> Dict[str, Any]:
    """Validate layout fixes result."""
    if 'error' in result:
        return {"status": "error", "summary": result['error']}

    validation = result.get('validation', {})
    status = validation.get('status', 'unknown')
    summary = validation.get('summary', 'Layout analysis complete')

    checks = [
        (result.get('layout_issues') is not None, "Has issues list"),
        (result.get('lipgloss_improvements') is not None, "Has improvements"),
        (result.get('code_fixes') is not None, "Has code fixes"),
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
        print("Usage: fix_layout_issues.py <code_path> [description]")
        sys.exit(1)

    code_path = sys.argv[1]
    description = sys.argv[2] if len(sys.argv) > 2 else ""

    result = fix_layout_issues(code_path, description)
    print(json.dumps(result, indent=2))
