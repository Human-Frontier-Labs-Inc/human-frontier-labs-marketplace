#!/usr/bin/env python3
"""
Apply Bubble Tea best practices validation.
Validates code against 11 expert tips from tip-bubbltea-apps.md.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple


# Path to tips reference
TIPS_FILE = Path("/Users/williamvansickleiii/charmtuitemplate/charm-tui-template/tip-bubbltea-apps.md")


def apply_best_practices(code_path: str, tips_file: str = None) -> Dict[str, Any]:
    """
    Validate Bubble Tea code against best practices from tip-bubbltea-apps.md.

    Args:
        code_path: Path to Go file or directory
        tips_file: Optional path to tips file (defaults to standard location)

    Returns:
        Dictionary containing:
        - compliance: Status for each of 11 tips
        - overall_score: 0-100
        - recommendations: List of improvements
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

    # Read all Go code
    all_content = ""
    for go_file in go_files:
        try:
            all_content += go_file.read_text() + "\n"
        except Exception:
            pass

    # Check each tip
    compliance = {}

    compliance["tip_1_fast_event_loop"] = _check_tip_1_fast_event_loop(all_content, go_files)
    compliance["tip_2_debug_dumping"] = _check_tip_2_debug_dumping(all_content, go_files)
    compliance["tip_3_live_reload"] = _check_tip_3_live_reload(path)
    compliance["tip_4_receiver_methods"] = _check_tip_4_receiver_methods(all_content, go_files)
    compliance["tip_5_message_ordering"] = _check_tip_5_message_ordering(all_content, go_files)
    compliance["tip_6_model_tree"] = _check_tip_6_model_tree(all_content, go_files)
    compliance["tip_7_layout_arithmetic"] = _check_tip_7_layout_arithmetic(all_content, go_files)
    compliance["tip_8_terminal_recovery"] = _check_tip_8_terminal_recovery(all_content, go_files)
    compliance["tip_9_teatest"] = _check_tip_9_teatest(path)
    compliance["tip_10_vhs"] = _check_tip_10_vhs(path)
    compliance["tip_11_resources"] = {"status": "info", "score": 100, "message": "Check leg100.github.io for more tips"}

    # Calculate overall score
    scores = [tip["score"] for tip in compliance.values()]
    overall_score = int(sum(scores) / len(scores))

    # Generate recommendations
    recommendations = []
    for tip_name, tip_data in compliance.items():
        if tip_data["status"] == "fail":
            recommendations.append(tip_data.get("recommendation", f"Implement {tip_name}"))

    # Summary
    if overall_score >= 90:
        summary = f"✅ Excellent! Score: {overall_score}/100. Following best practices."
    elif overall_score >= 70:
        summary = f"✓ Good. Score: {overall_score}/100. Some improvements possible."
    elif overall_score >= 50:
        summary = f"⚠️  Fair. Score: {overall_score}/100. Several best practices missing."
    else:
        summary = f"❌ Poor. Score: {overall_score}/100. Many best practices not followed."

    # Validation
    validation = {
        "status": "pass" if overall_score >= 70 else "warning" if overall_score >= 50 else "fail",
        "summary": summary,
        "checks": {
            "fast_event_loop": compliance["tip_1_fast_event_loop"]["status"] == "pass",
            "has_debugging": compliance["tip_2_debug_dumping"]["status"] == "pass",
            "proper_layout": compliance["tip_7_layout_arithmetic"]["status"] == "pass",
            "has_recovery": compliance["tip_8_terminal_recovery"]["status"] == "pass"
        }
    }

    return {
        "compliance": compliance,
        "overall_score": overall_score,
        "recommendations": recommendations,
        "summary": summary,
        "files_analyzed": len(go_files),
        "validation": validation
    }


def _check_tip_1_fast_event_loop(content: str, files: List[Path]) -> Dict[str, Any]:
    """Tip 1: Keep the event loop fast."""
    # Check for blocking operations in Update() or View()
    blocking_patterns = [
        r'\btime\.Sleep\s*\(',
        r'\bhttp\.(Get|Post|Do)\s*\(',
        r'\bos\.Open\s*\(',
        r'\bio\.ReadAll\s*\(',
        r'\bexec\.Command\([^)]+\)\.Run\(\)',
    ]

    has_blocking = any(re.search(pattern, content) for pattern in blocking_patterns)
    has_tea_cmd = bool(re.search(r'tea\.Cmd', content))

    if has_blocking and not has_tea_cmd:
        return {
            "status": "fail",
            "score": 0,
            "message": "Blocking operations found in event loop without tea.Cmd",
            "recommendation": "Move blocking operations to tea.Cmd goroutines",
            "explanation": "Blocking ops in Update()/View() freeze the UI. Use tea.Cmd for I/O."
        }
    elif has_blocking and has_tea_cmd:
        return {
            "status": "warning",
            "score": 50,
            "message": "Blocking operations present but tea.Cmd is used",
            "recommendation": "Verify all blocking ops are in tea.Cmd, not Update()/View()",
            "explanation": "Review code to ensure blocking operations are properly wrapped"
        }
    else:
        return {
            "status": "pass",
            "score": 100,
            "message": "No blocking operations detected in event loop",
            "explanation": "Event loop appears to be non-blocking"
        }


def _check_tip_2_debug_dumping(content: str, files: List[Path]) -> Dict[str, Any]:
    """Tip 2: Dump messages to a file for debugging."""
    has_spew = bool(re.search(r'github\.com/davecgh/go-spew', content))
    has_debug_write = bool(re.search(r'(dump|debug|log)\s+io\.Writer', content))
    has_fmt_fprintf = bool(re.search(r'fmt\.Fprintf', content))

    if has_spew or has_debug_write:
        return {
            "status": "pass",
            "score": 100,
            "message": "Debug message dumping capability detected",
            "explanation": "Using spew or debug writer for message inspection"
        }
    elif has_fmt_fprintf:
        return {
            "status": "warning",
            "score": 60,
            "message": "Basic logging present, but no structured message dumping",
            "recommendation": "Add spew.Fdump for detailed message inspection",
            "explanation": "fmt.Fprintf works but spew provides better message structure"
        }
    else:
        return {
            "status": "fail",
            "score": 0,
            "message": "No debug message dumping detected",
            "recommendation": "Add message dumping with go-spew:\n" +
                             "import \"github.com/davecgh/go-spew/spew\"\n" +
                             "type model struct { dump io.Writer }\n" +
                             "func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {\n" +
                             "    if m.dump != nil { spew.Fdump(m.dump, msg) }\n" +
                             "    // ... rest of Update()\n" +
                             "}",
            "explanation": "Message dumping helps debug complex message flows"
        }


def _check_tip_3_live_reload(path: Path) -> Dict[str, Any]:
    """Tip 3: Live reload code changes."""
    # Check for air config or similar
    has_air_config = (path / ".air.toml").exists()
    has_makefile_watch = False

    if (path / "Makefile").exists():
        makefile = (path / "Makefile").read_text()
        has_makefile_watch = bool(re.search(r'watch:|live:', makefile))

    if has_air_config:
        return {
            "status": "pass",
            "score": 100,
            "message": "Live reload configured with air",
            "explanation": "Found .air.toml configuration"
        }
    elif has_makefile_watch:
        return {
            "status": "pass",
            "score": 100,
            "message": "Live reload configured in Makefile",
            "explanation": "Found watch/live target in Makefile"
        }
    else:
        return {
            "status": "info",
            "score": 100,
            "message": "No live reload detected (optional)",
            "recommendation": "Consider adding air for live reload during development",
            "explanation": "Live reload improves development speed but is optional"
        }


def _check_tip_4_receiver_methods(content: str, files: List[Path]) -> Dict[str, Any]:
    """Tip 4: Use pointer vs value receivers judiciously."""
    # Check Update() receiver type (should be value receiver)
    update_value_receiver = bool(re.search(r'func\s+\(m\s+\w+\)\s+Update\s*\(', content))
    update_pointer_receiver = bool(re.search(r'func\s+\(m\s+\*\w+\)\s+Update\s*\(', content))

    if update_pointer_receiver:
        return {
            "status": "warning",
            "score": 60,
            "message": "Update() uses pointer receiver (uncommon pattern)",
            "recommendation": "Consider value receiver for Update() (standard pattern)",
            "explanation": "Value receiver is standard for Update() in Bubble Tea"
        }
    elif update_value_receiver:
        return {
            "status": "pass",
            "score": 100,
            "message": "Update() uses value receiver (correct)",
            "explanation": "Following standard Bubble Tea pattern"
        }
    else:
        return {
            "status": "info",
            "score": 100,
            "message": "No Update() method found or unable to detect",
            "explanation": "Could not determine receiver type"
        }


def _check_tip_5_message_ordering(content: str, files: List[Path]) -> Dict[str, Any]:
    """Tip 5: Messages from concurrent commands not guaranteed in order."""
    has_batch = bool(re.search(r'tea\.Batch\s*\(', content))
    has_concurrent_cmds = bool(re.search(r'go\s+func\s*\(', content))
    has_state_tracking = bool(re.search(r'type\s+\w*State\s+(int|string)', content)) or \
                        bool(re.search(r'operations\s+map\[string\]', content))

    if (has_batch or has_concurrent_cmds) and not has_state_tracking:
        return {
            "status": "warning",
            "score": 50,
            "message": "Concurrent commands without explicit state tracking",
            "recommendation": "Add state machine to track concurrent operations",
            "explanation": "tea.Batch messages arrive in unpredictable order"
        }
    elif has_batch or has_concurrent_cmds:
        return {
            "status": "pass",
            "score": 100,
            "message": "Concurrent commands with state tracking",
            "explanation": "Proper handling of message ordering"
        }
    else:
        return {
            "status": "pass",
            "score": 100,
            "message": "No concurrent commands detected",
            "explanation": "Message ordering is deterministic"
        }


def _check_tip_6_model_tree(content: str, files: List[Path]) -> Dict[str, Any]:
    """Tip 6: Build a tree of models for complex apps."""
    # Count model fields
    model_match = re.search(r'type\s+(\w*[Mm]odel)\s+struct\s*\{([^}]+)\}', content, re.DOTALL)
    if not model_match:
        return {
            "status": "info",
            "score": 100,
            "message": "No model struct found",
            "explanation": "Could not analyze model structure"
        }

    model_body = model_match.group(2)
    field_count = len([line for line in model_body.split('\n') if line.strip() and not line.strip().startswith('//')])

    # Check for child models
    has_child_models = bool(re.search(r'\w+Model\s+\w+Model', content))

    if field_count > 20 and not has_child_models:
        return {
            "status": "warning",
            "score": 40,
            "message": f"Large model ({field_count} fields) without child models",
            "recommendation": "Consider refactoring to model tree pattern",
            "explanation": "Large models are hard to maintain. Split into child models."
        }
    elif field_count > 15 and not has_child_models:
        return {
            "status": "info",
            "score": 70,
            "message": f"Medium model ({field_count} fields)",
            "recommendation": "Consider model tree if complexity increases",
            "explanation": "Model is getting large, monitor complexity"
        }
    elif has_child_models:
        return {
            "status": "pass",
            "score": 100,
            "message": "Using model tree pattern with child models",
            "explanation": "Good architecture for complex apps"
        }
    else:
        return {
            "status": "pass",
            "score": 100,
            "message": f"Simple model ({field_count} fields)",
            "explanation": "Model size is appropriate"
        }


def _check_tip_7_layout_arithmetic(content: str, files: List[Path]) -> Dict[str, Any]:
    """Tip 7: Layout arithmetic is error-prone."""
    uses_lipgloss = bool(re.search(r'github\.com/charmbracelet/lipgloss', content))
    has_lipgloss_helpers = bool(re.search(r'lipgloss\.(Height|Width|GetVertical|GetHorizontal)', content))
    has_hardcoded_dimensions = bool(re.search(r'\.(Width|Height)\s*\(\s*\d{2,}\s*\)', content))

    if uses_lipgloss and has_lipgloss_helpers and not has_hardcoded_dimensions:
        return {
            "status": "pass",
            "score": 100,
            "message": "Using lipgloss helpers for dynamic layout",
            "explanation": "Correct use of lipgloss.Height()/Width()"
        }
    elif uses_lipgloss and has_hardcoded_dimensions:
        return {
            "status": "warning",
            "score": 40,
            "message": "Hardcoded dimensions detected",
            "recommendation": "Use lipgloss.Height() and lipgloss.Width() for calculations",
            "explanation": "Hardcoded dimensions don't adapt to terminal size"
        }
    elif uses_lipgloss:
        return {
            "status": "warning",
            "score": 60,
            "message": "Using lipgloss but unclear if using helpers",
            "recommendation": "Use lipgloss.Height() and lipgloss.Width() for layout",
            "explanation": "Avoid manual height/width calculations"
        }
    else:
        return {
            "status": "info",
            "score": 100,
            "message": "Not using lipgloss",
            "explanation": "Layout tip applies when using lipgloss"
        }


def _check_tip_8_terminal_recovery(content: str, files: List[Path]) -> Dict[str, Any]:
    """Tip 8: Recover your terminal after panics."""
    has_defer_recover = bool(re.search(r'defer\s+func\s*\(\s*\)\s*\{[^}]*recover\(\)', content, re.DOTALL))
    has_main = bool(re.search(r'func\s+main\s*\(\s*\)', content))
    has_disable_mouse = bool(re.search(r'tea\.DisableMouseAllMotion', content))

    if has_main and has_defer_recover and has_disable_mouse:
        return {
            "status": "pass",
            "score": 100,
            "message": "Panic recovery with terminal cleanup",
            "explanation": "Proper defer recover() with DisableMouseAllMotion"
        }
    elif has_main and has_defer_recover:
        return {
            "status": "warning",
            "score": 70,
            "message": "Panic recovery but missing DisableMouseAllMotion",
            "recommendation": "Add tea.DisableMouseAllMotion() in panic handler",
            "explanation": "Need to cleanup mouse mode on panic"
        }
    elif has_main:
        return {
            "status": "fail",
            "score": 0,
            "message": "Missing panic recovery in main()",
            "recommendation": "Add defer recover() with terminal cleanup",
            "explanation": "Panics can leave terminal in broken state"
        }
    else:
        return {
            "status": "info",
            "score": 100,
            "message": "No main() found (library code?)",
            "explanation": "Recovery applies to main applications"
        }


def _check_tip_9_teatest(path: Path) -> Dict[str, Any]:
    """Tip 9: Use teatest for end-to-end tests."""
    # Look for test files using teatest
    test_files = list(path.glob('**/*_test.go'))
    has_teatest = False

    for test_file in test_files:
        try:
            content = test_file.read_text()
            if 'teatest' in content or 'tea/teatest' in content:
                has_teatest = True
                break
        except Exception:
            pass

    if has_teatest:
        return {
            "status": "pass",
            "score": 100,
            "message": "Using teatest for testing",
            "explanation": "Found teatest in test files"
        }
    elif test_files:
        return {
            "status": "warning",
            "score": 60,
            "message": "Has tests but not using teatest",
            "recommendation": "Consider using teatest for TUI integration tests",
            "explanation": "teatest enables end-to-end TUI testing"
        }
    else:
        return {
            "status": "fail",
            "score": 0,
            "message": "No tests found",
            "recommendation": "Add teatest tests for key interactions",
            "explanation": "Testing improves reliability"
        }


def _check_tip_10_vhs(path: Path) -> Dict[str, Any]:
    """Tip 10: Use VHS to record demos."""
    # Look for .tape files (VHS)
    vhs_files = list(path.glob('**/*.tape'))

    if vhs_files:
        return {
            "status": "pass",
            "score": 100,
            "message": f"Found {len(vhs_files)} VHS demo file(s)",
            "explanation": "Using VHS for documentation"
        }
    else:
        return {
            "status": "info",
            "score": 100,
            "message": "No VHS demos found (optional)",
            "recommendation": "Consider adding VHS demos for documentation",
            "explanation": "VHS creates great animated demos but is optional"
        }


def validate_best_practices(result: Dict[str, Any]) -> Dict[str, Any]:
    """Validate best practices result."""
    if 'error' in result:
        return {"status": "error", "summary": result['error']}

    overall_score = result.get('overall_score', 0)
    status = "pass" if overall_score >= 70 else "warning" if overall_score >= 50 else "fail"

    return {
        "status": status,
        "summary": result.get('summary', 'Best practices check complete'),
        "score": overall_score,
        "valid": True
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: apply_best_practices.py <code_path> [tips_file]")
        sys.exit(1)

    code_path = sys.argv[1]
    tips_file = sys.argv[2] if len(sys.argv) > 2 else None

    result = apply_best_practices(code_path, tips_file)
    print(json.dumps(result, indent=2))
