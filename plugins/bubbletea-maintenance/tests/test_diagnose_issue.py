#!/usr/bin/env python3
"""
Tests for diagnose_issue.py
"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from diagnose_issue import diagnose_issue, _check_blocking_operations, _check_hardcoded_dimensions


def test_diagnose_issue_basic():
    """Test basic issue diagnosis."""
    print("\n✓ Testing diagnose_issue()...")

    # Create test Go file
    test_code = '''
package main

import tea "github.com/charmbracelet/bubbletea"

type model struct {
    width  int
    height int
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    return m, nil
}

func (m model) View() string {
    return "Hello"
}
'''

    test_file = Path("/tmp/test_bubbletea_app.go")
    test_file.write_text(test_code)

    result = diagnose_issue(str(test_file))

    assert 'issues' in result, "Missing 'issues' key"
    assert 'health_score' in result, "Missing 'health_score' key"
    assert 'summary' in result, "Missing 'summary' key"
    assert isinstance(result['issues'], list), "Issues should be a list"
    assert isinstance(result['health_score'], int), "Health score should be int"

    print(f"  ✓ Found {len(result['issues'])} issue(s)")
    print(f"  ✓ Health score: {result['health_score']}/100")

    # Cleanup
    test_file.unlink()

    return True


def test_blocking_operations_detection():
    """Test detection of blocking operations."""
    print("\n✓ Testing blocking operation detection...")

    test_code = '''
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyMsg:
        data, _ := http.Get("https://example.com")  // BLOCKING!
        m.data = data
    }
    return m, nil
}
'''

    lines = test_code.split('\n')
    issues = _check_blocking_operations(test_code, lines, "test.go")

    assert len(issues) > 0, "Should detect blocking HTTP request"
    assert issues[0]['severity'] == 'CRITICAL', "Should be CRITICAL severity"
    assert 'HTTP request' in issues[0]['issue'], "Should identify HTTP as issue"

    print(f"  ✓ Detected {len(issues)} blocking operation(s)")
    print(f"  ✓ Severity: {issues[0]['severity']}")

    return True


def test_hardcoded_dimensions_detection():
    """Test detection of hardcoded dimensions."""
    print("\n✓ Testing hardcoded dimensions detection...")

    test_code = '''
func (m model) View() string {
    content := lipgloss.NewStyle().
        Width(80).
        Height(24).
        Render(m.content)
    return content
}
'''

    lines = test_code.split('\n')
    issues = _check_hardcoded_dimensions(test_code, lines, "test.go")

    assert len(issues) >= 2, "Should detect both Width and Height"
    assert any('Width' in i['issue'] for i in issues), "Should detect hardcoded Width"
    assert any('Height' in i['issue'] for i in issues), "Should detect hardcoded Height"

    print(f"  ✓ Detected {len(issues)} hardcoded dimension(s)")

    return True


def test_no_issues_clean_code():
    """Test with clean code that has no issues."""
    print("\n✓ Testing with clean code...")

    test_code = '''
package main

import tea "github.com/charmbracelet/bubbletea"

type model struct {
    termWidth  int
    termHeight int
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.WindowSizeMsg:
        m.termWidth = msg.Width
        m.termHeight = msg.Height
    case tea.KeyMsg:
        return m, fetchDataCmd  // Non-blocking
    }
    return m, nil
}

func (m model) View() string {
    return lipgloss.NewStyle().
        Width(m.termWidth).
        Height(m.termHeight).
        Render("Clean!")
}

func fetchDataCmd() tea.Msg {
    // Runs in background
    return dataMsg{}
}
'''

    test_file = Path("/tmp/test_clean_app.go")
    test_file.write_text(test_code)

    result = diagnose_issue(str(test_file))

    assert result['health_score'] >= 80, "Clean code should have high health score"
    print(f"  ✓ Health score: {result['health_score']}/100 (expected >=80)")

    # Cleanup
    test_file.unlink()

    return True


def test_invalid_path():
    """Test with invalid file path."""
    print("\n✓ Testing with invalid path...")

    result = diagnose_issue("/nonexistent/path/file.go")

    assert 'error' in result, "Should return error for invalid path"
    assert result['validation']['status'] == 'error', "Validation should be error"

    print("  ✓ Correctly handled invalid path")

    return True


def main():
    """Run all tests."""
    print("="*70)
    print("UNIT TESTS - diagnose_issue.py")
    print("="*70)

    tests = [
        ("Basic diagnosis", test_diagnose_issue_basic),
        ("Blocking operations", test_blocking_operations_detection),
        ("Hardcoded dimensions", test_hardcoded_dimensions_detection),
        ("Clean code", test_no_issues_clean_code),
        ("Invalid path", test_invalid_path),
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
