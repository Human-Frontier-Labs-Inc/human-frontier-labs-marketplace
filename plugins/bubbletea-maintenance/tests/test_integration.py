#!/usr/bin/env python3
"""
Integration tests for Bubble Tea Maintenance Agent.
Tests complete workflows combining multiple functions.
"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from diagnose_issue import diagnose_issue
from apply_best_practices import apply_best_practices
from debug_performance import debug_performance
from suggest_architecture import suggest_architecture
from fix_layout_issues import fix_layout_issues
from comprehensive_bubbletea_analysis import comprehensive_bubbletea_analysis


# Test fixture: Complete Bubble Tea app
TEST_APP_CODE = '''
package main

import (
    "fmt"
    "net/http"
    "time"

    tea "github.com/charmbracelet/bubbletea"
    "github.com/charmbracelet/lipgloss"
)

type model struct {
    items  []string
    cursor int
    data   string
}

func initialModel() model {
    return model{
        items: []string{"Item 1", "Item 2", "Item 3"},
        cursor: 0,
    }
}

func (m model) Init() tea.Cmd {
    return nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyMsg:
        switch msg.String() {
        case "q":
            return m, tea.Quit
        case "up":
            if m.cursor > 0 {
                m.cursor--
            }
        case "down":
            if m.cursor < len(m.items)-1 {
                m.cursor++
            }
        case "r":
            // ISSUE: Blocking HTTP request!
            resp, _ := http.Get("https://example.com")
            m.data = resp.Status
        }
    }
    return m, nil
}

func (m model) View() string {
    // ISSUE: Hardcoded dimensions
    style := lipgloss.NewStyle().
        Width(80).
        Height(24)

    s := "Select an item:\\n\\n"
    for i, item := range m.items {
        cursor := " "
        if m.cursor == i {
            cursor = ">"
        }
        // ISSUE: String concatenation
        s += fmt.Sprintf("%s %s\\n", cursor, item)
    }

    return style.Render(s)
}

func main() {
    // ISSUE: No panic recovery!
    p := tea.NewProgram(initialModel())
    p.Start()
}
'''


def test_full_workflow():
    """Test complete analysis workflow."""
    print("\n✓ Testing complete analysis workflow...")

    # Create test app
    test_dir = Path("/tmp/test_bubbletea_app")
    test_dir.mkdir(exist_ok=True)
    test_file = test_dir / "main.go"
    test_file.write_text(TEST_APP_CODE)

    # Run comprehensive analysis
    result = comprehensive_bubbletea_analysis(str(test_dir), detail_level="standard")

    # Validations
    assert 'overall_health' in result, "Missing overall_health"
    assert 'sections' in result, "Missing sections"
    assert 'priority_fixes' in result, "Missing priority_fixes"
    assert 'summary' in result, "Missing summary"

    # Check each section
    sections = result['sections']
    assert 'issues' in sections, "Missing issues section"
    assert 'best_practices' in sections, "Missing best_practices section"
    assert 'performance' in sections, "Missing performance section"
    assert 'architecture' in sections, "Missing architecture section"
    assert 'layout' in sections, "Missing layout section"

    # Should find issues in test code
    assert len(result.get('priority_fixes', [])) > 0, "Should find priority fixes"

    health = result['overall_health']
    assert 0 <= health <= 100, f"Health score {health} out of range"

    print(f"  ✓ Overall health: {health}/100")
    print(f"  ✓ Sections analyzed: {len(sections)}")
    print(f"  ✓ Priority fixes: {len(result['priority_fixes'])}")

    # Cleanup
    test_file.unlink()
    test_dir.rmdir()

    return True


def test_issue_diagnosis_finds_problems():
    """Test that diagnosis finds the known issues."""
    print("\n✓ Testing issue diagnosis...")

    test_dir = Path("/tmp/test_diagnosis")
    test_dir.mkdir(exist_ok=True)
    test_file = test_dir / "main.go"
    test_file.write_text(TEST_APP_CODE)

    result = diagnose_issue(str(test_dir))

    # Should find:
    # 1. Blocking HTTP request in Update()
    # 2. Hardcoded dimensions (80, 24)
    # (Note: Not all detections may trigger depending on pattern matching)

    issues = result.get('issues', [])
    assert len(issues) >= 1, f"Expected at least 1 issue, found {len(issues)}"

    # Check that HTTP blocking issue was found
    issue_texts = ' '.join([i['issue'] for i in issues])
    assert 'HTTP' in issue_texts or 'http' in issue_texts.lower(), "Should find HTTP blocking issue"

    print(f"  ✓ Found {len(issues)} issue(s)")
    print(f"  ✓ Health score: {result['health_score']}/100")

    # Cleanup
    test_file.unlink()
    test_dir.rmdir()

    return True


def test_performance_finds_bottlenecks():
    """Test that performance analysis finds bottlenecks."""
    print("\n✓ Testing performance analysis...")

    test_dir = Path("/tmp/test_performance")
    test_dir.mkdir(exist_ok=True)
    test_file = test_dir / "main.go"
    test_file.write_text(TEST_APP_CODE)

    result = debug_performance(str(test_dir))

    # Should find:
    # 1. Blocking HTTP in Update()
    # (Other bottlenecks may be detected depending on patterns)

    bottlenecks = result.get('bottlenecks', [])
    assert len(bottlenecks) >= 1, f"Expected at least 1 bottleneck, found {len(bottlenecks)}"

    # Check for critical bottlenecks
    critical = [b for b in bottlenecks if b['severity'] == 'CRITICAL']
    assert len(critical) > 0, "Should find CRITICAL bottlenecks"

    print(f"  ✓ Found {len(bottlenecks)} bottleneck(s)")
    print(f"  ✓ Critical: {len(critical)}")

    # Cleanup
    test_file.unlink()
    test_dir.rmdir()

    return True


def test_layout_finds_issues():
    """Test that layout analysis finds issues."""
    print("\n✓ Testing layout analysis...")

    test_dir = Path("/tmp/test_layout")
    test_dir.mkdir(exist_ok=True)
    test_file = test_dir / "main.go"
    test_file.write_text(TEST_APP_CODE)

    result = fix_layout_issues(str(test_dir))

    # Should find:
    # 1. Hardcoded dimensions or missing resize handling

    layout_issues = result.get('layout_issues', [])
    assert len(layout_issues) >= 1, f"Expected at least 1 layout issue, found {len(layout_issues)}"

    # Check for layout-related issues
    issue_types = [i['type'] for i in layout_issues]
    has_layout_issue = any(t in ['hardcoded_dimensions', 'missing_resize_handling'] for t in issue_types)
    assert has_layout_issue, "Should find layout issues"

    print(f"  ✓ Found {len(layout_issues)} layout issue(s)")

    # Cleanup
    test_file.unlink()
    test_dir.rmdir()

    return True


def test_architecture_analysis():
    """Test architecture pattern detection."""
    print("\n✓ Testing architecture analysis...")

    test_dir = Path("/tmp/test_arch")
    test_dir.mkdir(exist_ok=True)
    test_file = test_dir / "main.go"
    test_file.write_text(TEST_APP_CODE)

    result = suggest_architecture(str(test_dir))

    # Should detect pattern and provide recommendations
    assert 'current_pattern' in result, "Missing current_pattern"
    assert 'complexity_score' in result, "Missing complexity_score"
    assert 'recommended_pattern' in result, "Missing recommended_pattern"
    assert 'refactoring_steps' in result, "Missing refactoring_steps"

    complexity = result['complexity_score']
    assert 0 <= complexity <= 100, f"Complexity {complexity} out of range"

    print(f"  ✓ Current pattern: {result['current_pattern']}")
    print(f"  ✓ Complexity: {complexity}/100")
    print(f"  ✓ Recommended: {result['recommended_pattern']}")

    # Cleanup
    test_file.unlink()
    test_dir.rmdir()

    return True


def test_all_functions_return_valid_structure():
    """Test that all functions return valid result structures."""
    print("\n✓ Testing result structure validity...")

    test_dir = Path("/tmp/test_structure")
    test_dir.mkdir(exist_ok=True)
    test_file = test_dir / "main.go"
    test_file.write_text(TEST_APP_CODE)

    # Test all functions
    results = {
        "diagnose_issue": diagnose_issue(str(test_dir)),
        "apply_best_practices": apply_best_practices(str(test_dir)),
        "debug_performance": debug_performance(str(test_dir)),
        "suggest_architecture": suggest_architecture(str(test_dir)),
        "fix_layout_issues": fix_layout_issues(str(test_dir)),
    }

    for func_name, result in results.items():
        # Each should have validation
        assert 'validation' in result, f"{func_name}: Missing validation"
        assert 'status' in result['validation'], f"{func_name}: Missing validation status"
        assert 'summary' in result['validation'], f"{func_name}: Missing validation summary"

        print(f"  ✓ {func_name}: Valid structure")

    # Cleanup
    test_file.unlink()
    test_dir.rmdir()

    return True


def main():
    """Run all integration tests."""
    print("="*70)
    print("INTEGRATION TESTS - Bubble Tea Maintenance Agent")
    print("="*70)

    tests = [
        ("Full workflow", test_full_workflow),
        ("Issue diagnosis", test_issue_diagnosis_finds_problems),
        ("Performance analysis", test_performance_finds_bottlenecks),
        ("Layout analysis", test_layout_finds_issues),
        ("Architecture analysis", test_architecture_analysis),
        ("Result structure validity", test_all_functions_return_valid_structure),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n  ❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)

    print(f"\nResults: {passed_count}/{total_count} passed")

    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
