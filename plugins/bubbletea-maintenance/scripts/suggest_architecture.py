#!/usr/bin/env python3
"""
Suggest architectural improvements for Bubble Tea applications.
Analyzes complexity and recommends patterns like model trees, composable views, etc.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional


def suggest_architecture(code_path: str, complexity_level: str = "auto") -> Dict[str, Any]:
    """
    Analyze code and suggest architectural improvements.

    Args:
        code_path: Path to Go file or directory
        complexity_level: "auto" (detect), "simple", "medium", "complex"

    Returns:
        Dictionary containing:
        - current_pattern: Detected architectural pattern
        - complexity_score: 0-100 (higher = more complex)
        - recommended_pattern: Suggested pattern for improvement
        - refactoring_steps: List of steps to implement
        - code_templates: Example code for new pattern
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

    # Read all code
    all_content = ""
    for go_file in go_files:
        try:
            all_content += go_file.read_text() + "\n"
        except Exception:
            pass

    # Analyze current architecture
    current_pattern = _detect_current_pattern(all_content)
    complexity_score = _calculate_complexity(all_content, go_files)

    # Auto-detect complexity level if needed
    if complexity_level == "auto":
        if complexity_score < 30:
            complexity_level = "simple"
        elif complexity_score < 70:
            complexity_level = "medium"
        else:
            complexity_level = "complex"

    # Generate recommendations
    recommended_pattern = _recommend_pattern(current_pattern, complexity_score, complexity_level)
    refactoring_steps = _generate_refactoring_steps(current_pattern, recommended_pattern, all_content)
    code_templates = _generate_code_templates(recommended_pattern, all_content)

    # Summary
    if recommended_pattern == current_pattern:
        summary = f"✅ Current architecture ({current_pattern}) is appropriate for complexity level"
    else:
        summary = f"💡 Recommend refactoring from {current_pattern} to {recommended_pattern}"

    # Validation
    validation = {
        "status": "pass" if recommended_pattern == current_pattern else "info",
        "summary": summary,
        "checks": {
            "complexity_analyzed": complexity_score >= 0,
            "pattern_detected": current_pattern != "unknown",
            "has_recommendations": len(refactoring_steps) > 0,
            "has_templates": len(code_templates) > 0
        }
    }

    return {
        "current_pattern": current_pattern,
        "complexity_score": complexity_score,
        "complexity_level": complexity_level,
        "recommended_pattern": recommended_pattern,
        "refactoring_steps": refactoring_steps,
        "code_templates": code_templates,
        "summary": summary,
        "analysis": {
            "files_analyzed": len(go_files),
            "model_count": _count_models(all_content),
            "view_functions": _count_view_functions(all_content),
            "state_fields": _count_state_fields(all_content)
        },
        "validation": validation
    }


def _detect_current_pattern(content: str) -> str:
    """Detect the current architectural pattern."""

    # Check for various patterns
    patterns_detected = []

    # Pattern 1: Flat Model (single model struct, no child models)
    has_model = bool(re.search(r'type\s+\w*[Mm]odel\s+struct', content))
    has_child_models = bool(re.search(r'\w+Model\s+\w+Model', content))

    if has_model and not has_child_models:
        patterns_detected.append("flat_model")

    # Pattern 2: Model Tree (parent model with child models)
    if has_child_models:
        patterns_detected.append("model_tree")

    # Pattern 3: Multi-view (multiple view rendering based on state)
    has_view_switcher = bool(re.search(r'switch\s+m\.\w*(view|mode|screen|state)', content, re.IGNORECASE))
    if has_view_switcher:
        patterns_detected.append("multi_view")

    # Pattern 4: Component-based (using Bubble Tea components like list, viewport, etc.)
    bubbletea_components = [
        'list.Model',
        'viewport.Model',
        'textinput.Model',
        'textarea.Model',
        'table.Model',
        'progress.Model',
        'spinner.Model'
    ]
    component_count = sum(1 for comp in bubbletea_components if comp in content)

    if component_count >= 3:
        patterns_detected.append("component_based")
    elif component_count >= 1:
        patterns_detected.append("uses_components")

    # Pattern 5: State Machine (explicit state enums/constants)
    has_state_enum = bool(re.search(r'type\s+\w*State\s+(int|string)', content))
    has_iota_states = bool(re.search(r'const\s+\(\s*\w+State\s+\w*State\s+=\s+iota', content))

    if has_state_enum or has_iota_states:
        patterns_detected.append("state_machine")

    # Pattern 6: Event-driven (heavy use of custom messages)
    custom_msg_count = len(re.findall(r'type\s+\w+Msg\s+struct', content))
    if custom_msg_count >= 5:
        patterns_detected.append("event_driven")

    # Return the most dominant pattern
    if "model_tree" in patterns_detected:
        return "model_tree"
    elif "state_machine" in patterns_detected and "multi_view" in patterns_detected:
        return "state_machine_multi_view"
    elif "component_based" in patterns_detected:
        return "component_based"
    elif "multi_view" in patterns_detected:
        return "multi_view"
    elif "flat_model" in patterns_detected:
        return "flat_model"
    elif has_model:
        return "basic_model"
    else:
        return "unknown"


def _calculate_complexity(content: str, files: List[Path]) -> int:
    """Calculate complexity score (0-100)."""

    score = 0

    # Factor 1: Number of files (10 points max)
    file_count = len(files)
    score += min(10, file_count * 2)

    # Factor 2: Model field count (20 points max)
    model_match = re.search(r'type\s+(\w*[Mm]odel)\s+struct\s*\{([^}]+)\}', content, re.DOTALL)
    if model_match:
        model_body = model_match.group(2)
        field_count = len([line for line in model_body.split('\n')
                          if line.strip() and not line.strip().startswith('//')])
        score += min(20, field_count)

    # Factor 3: Number of Update() branches (20 points max)
    update_match = re.search(r'func\s+\([^)]+\)\s+Update\s*\([^)]+\)\s*\([^)]+\)\s*\{(.+?)^func\s',
                            content, re.DOTALL | re.MULTILINE)
    if update_match:
        update_body = update_match.group(1)
        case_count = len(re.findall(r'case\s+', update_body))
        score += min(20, case_count * 2)

    # Factor 4: View() complexity (15 points max)
    view_match = re.search(r'func\s+\([^)]+\)\s+View\s*\(\s*\)\s+string\s*\{(.+?)^func\s',
                          content, re.DOTALL | re.MULTILINE)
    if view_match:
        view_body = view_match.group(1)
        view_lines = len(view_body.split('\n'))
        score += min(15, view_lines // 2)

    # Factor 5: Custom message types (10 points max)
    custom_msg_count = len(re.findall(r'type\s+\w+Msg\s+struct', content))
    score += min(10, custom_msg_count * 2)

    # Factor 6: Number of views/screens (15 points max)
    view_count = len(re.findall(r'func\s+\([^)]+\)\s+render\w+', content, re.IGNORECASE))
    score += min(15, view_count * 3)

    # Factor 7: Use of channels/goroutines (10 points max)
    has_channels = len(re.findall(r'make\s*\(\s*chan\s+', content))
    has_goroutines = len(re.findall(r'\bgo\s+func', content))
    score += min(10, (has_channels + has_goroutines) * 2)

    return min(100, score)


def _recommend_pattern(current: str, complexity: int, level: str) -> str:
    """Recommend architectural pattern based on current state and complexity."""

    # Simple apps (< 30 complexity)
    if complexity < 30:
        if current in ["unknown", "basic_model"]:
            return "flat_model"  # Simple flat model is fine
        return current  # Keep current pattern

    # Medium complexity (30-70)
    elif complexity < 70:
        if current == "flat_model":
            return "multi_view"  # Evolve to multi-view
        elif current == "basic_model":
            return "component_based"  # Start using components
        return current

    # High complexity (70+)
    else:
        if current in ["flat_model", "multi_view"]:
            return "model_tree"  # Need hierarchy
        elif current == "component_based":
            return "model_tree_with_components"  # Combine patterns
        return current


def _count_models(content: str) -> int:
    """Count model structs."""
    return len(re.findall(r'type\s+\w*[Mm]odel\s+struct', content))


def _count_view_functions(content: str) -> int:
    """Count view rendering functions."""
    return len(re.findall(r'func\s+\([^)]+\)\s+(View|render\w+)', content, re.IGNORECASE))


def _count_state_fields(content: str) -> int:
    """Count state fields in model."""
    model_match = re.search(r'type\s+(\w*[Mm]odel)\s+struct\s*\{([^}]+)\}', content, re.DOTALL)
    if not model_match:
        return 0

    model_body = model_match.group(2)
    return len([line for line in model_body.split('\n')
               if line.strip() and not line.strip().startswith('//')])


def _generate_refactoring_steps(current: str, recommended: str, content: str) -> List[str]:
    """Generate step-by-step refactoring guide."""

    if current == recommended:
        return ["No refactoring needed - current architecture is appropriate"]

    steps = []

    # Flat Model → Multi-view
    if current == "flat_model" and recommended == "multi_view":
        steps = [
            "1. Add view state enum to model",
            "2. Create separate render functions for each view",
            "3. Add view switching logic in Update()",
            "4. Implement switch statement in View() to route to render functions",
            "5. Add keyboard shortcuts for view navigation"
        ]

    # Flat Model → Model Tree
    elif current == "flat_model" and recommended == "model_tree":
        steps = [
            "1. Identify logical groupings of fields in current model",
            "2. Create child model structs for each grouping",
            "3. Add Init() methods to child models",
            "4. Create parent model with child model fields",
            "5. Implement message routing in parent's Update()",
            "6. Delegate rendering to child models in View()",
            "7. Test each child model independently"
        ]

    # Multi-view → Model Tree
    elif current == "multi_view" and recommended == "model_tree":
        steps = [
            "1. Convert each view into a separate child model",
            "2. Extract view-specific state into child models",
            "3. Create parent router model with activeView field",
            "4. Implement message routing based on activeView",
            "5. Move view rendering logic into child models",
            "6. Add inter-model communication via custom messages"
        ]

    # Component-based → Model Tree with Components
    elif current == "component_based" and recommended == "model_tree_with_components":
        steps = [
            "1. Group related components into logical views",
            "2. Create view models that own related components",
            "3. Create parent model to manage view models",
            "4. Implement message routing to active view",
            "5. Keep component updates within their view models",
            "6. Compose final view from view model renders"
        ]

    # Basic Model → Component-based
    elif current == "basic_model" and recommended == "component_based":
        steps = [
            "1. Identify UI patterns that match Bubble Tea components",
            "2. Replace custom text input with textinput.Model",
            "3. Replace custom list with list.Model",
            "4. Replace custom scrolling with viewport.Model",
            "5. Update Init() to initialize components",
            "6. Route messages to components in Update()",
            "7. Compose View() using component.View() calls"
        ]

    # Generic fallback
    else:
        steps = [
            f"1. Analyze current {current} pattern",
            f"2. Study {recommended} pattern examples",
            "3. Plan gradual migration strategy",
            "4. Implement incrementally with tests",
            "5. Validate each step before proceeding"
        ]

    return steps


def _generate_code_templates(pattern: str, existing_code: str) -> Dict[str, str]:
    """Generate code templates for recommended pattern."""

    templates = {}

    if pattern == "model_tree":
        templates["parent_model"] = '''// Parent model manages child models
type appModel struct {
    activeView int

    // Child models
    listView   listViewModel
    detailView detailViewModel
    searchView searchViewModel
}

func (m appModel) Init() tea.Cmd {
    return tea.Batch(
        m.listView.Init(),
        m.detailView.Init(),
        m.searchView.Init(),
    )
}

func (m appModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    var cmd tea.Cmd

    // Global navigation
    if key, ok := msg.(tea.KeyMsg); ok {
        switch key.String() {
        case "1":
            m.activeView = 0
            return m, nil
        case "2":
            m.activeView = 1
            return m, nil
        case "3":
            m.activeView = 2
            return m, nil
        }
    }

    // Route to active child
    switch m.activeView {
    case 0:
        m.listView, cmd = m.listView.Update(msg)
    case 1:
        m.detailView, cmd = m.detailView.Update(msg)
    case 2:
        m.searchView, cmd = m.searchView.Update(msg)
    }

    return m, cmd
}

func (m appModel) View() string {
    switch m.activeView {
    case 0:
        return m.listView.View()
    case 1:
        return m.detailView.View()
    case 2:
        return m.searchView.View()
    }
    return ""
}'''

        templates["child_model"] = '''// Child model handles its own state and rendering
type listViewModel struct {
    items    []string
    cursor   int
    selected map[int]bool
}

func (m listViewModel) Init() tea.Cmd {
    return nil
}

func (m listViewModel) Update(msg tea.Msg) (listViewModel, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyMsg:
        switch msg.String() {
        case "up", "k":
            if m.cursor > 0 {
                m.cursor--
            }
        case "down", "j":
            if m.cursor < len(m.items)-1 {
                m.cursor++
            }
        case " ":
            m.selected[m.cursor] = !m.selected[m.cursor]
        }
    }
    return m, nil
}

func (m listViewModel) View() string {
    s := "Select items:\\n\\n"
    for i, item := range m.items {
        cursor := " "
        if m.cursor == i {
            cursor = ">"
        }
        checked := " "
        if m.selected[i] {
            checked = "x"
        }
        s += fmt.Sprintf("%s [%s] %s\\n", cursor, checked, item)
    }
    return s
}'''

        templates["message_passing"] = '''// Custom message for inter-model communication
type itemSelectedMsg struct {
    itemID string
}

// In listViewModel:
func (m listViewModel) Update(msg tea.Msg) (listViewModel, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyMsg:
        if msg.String() == "enter" {
            // Send message to parent (who routes to detail view)
            return m, func() tea.Msg {
                return itemSelectedMsg{itemID: m.items[m.cursor]}
            }
        }
    }
    return m, nil
}

// In appModel:
func (m appModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case itemSelectedMsg:
        // List selected item, switch to detail view
        m.detailView.LoadItem(msg.itemID)
        m.activeView = 1  // Switch to detail
        return m, nil
    }

    // Route to children...
    return m, nil
}'''

    elif pattern == "multi_view":
        templates["view_state"] = '''type viewState int

const (
    listView viewState = iota
    detailView
    searchView
)

type model struct {
    currentView viewState

    // View-specific state
    listItems   []string
    listCursor  int
    detailItem  string
    searchQuery string
}'''

        templates["view_switching"] = '''func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyMsg:
        // Global navigation
        switch msg.String() {
        case "1":
            m.currentView = listView
            return m, nil
        case "2":
            m.currentView = detailView
            return m, nil
        case "3":
            m.currentView = searchView
            return m, nil
        }

        // View-specific handling
        switch m.currentView {
        case listView:
            return m.updateListView(msg)
        case detailView:
            return m.updateDetailView(msg)
        case searchView:
            return m.updateSearchView(msg)
        }
    }
    return m, nil
}

func (m model) View() string {
    switch m.currentView {
    case listView:
        return m.renderListView()
    case detailView:
        return m.renderDetailView()
    case searchView:
        return m.renderSearchView()
    }
    return ""
}'''

    elif pattern == "component_based":
        templates["using_components"] = '''import (
    "github.com/charmbracelet/bubbles/list"
    "github.com/charmbracelet/bubbles/textinput"
    "github.com/charmbracelet/bubbles/viewport"
    tea "github.com/charmbracelet/bubbletea"
)

type model struct {
    list     list.Model
    search   textinput.Model
    viewer   viewport.Model
    activeComponent int
}

func initialModel() model {
    // Initialize components
    items := []list.Item{
        item{title: "Item 1", desc: "Description"},
        item{title: "Item 2", desc: "Description"},
    }

    l := list.New(items, list.NewDefaultDelegate(), 20, 10)
    l.Title = "Items"

    ti := textinput.New()
    ti.Placeholder = "Search..."
    ti.Focus()

    vp := viewport.New(80, 20)

    return model{
        list:   l,
        search: ti,
        viewer: vp,
        activeComponent: 0,
    }
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    var cmd tea.Cmd

    // Route to active component
    switch m.activeComponent {
    case 0:
        m.list, cmd = m.list.Update(msg)
    case 1:
        m.search, cmd = m.search.Update(msg)
    case 2:
        m.viewer, cmd = m.viewer.Update(msg)
    }

    return m, cmd
}

func (m model) View() string {
    return lipgloss.JoinVertical(
        lipgloss.Left,
        m.search.View(),
        m.list.View(),
        m.viewer.View(),
    )
}'''

    elif pattern == "state_machine_multi_view":
        templates["state_machine"] = '''type appState int

const (
    loadingState appState = iota
    listState
    detailState
    errorState
)

type model struct {
    state     appState
    prevState appState

    // State data
    items     []string
    selected  string
    error     error
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case itemsLoadedMsg:
        m.items = msg.items
        m.state = listState
        return m, nil

    case itemSelectedMsg:
        m.selected = msg.item
        m.state = detailState
        return m, loadItemDetails

    case errorMsg:
        m.prevState = m.state
        m.state = errorState
        m.error = msg.err
        return m, nil

    case tea.KeyMsg:
        if msg.String() == "esc" && m.state == errorState {
            m.state = m.prevState  // Return to previous state
            return m, nil
        }
    }

    // State-specific update
    switch m.state {
    case listState:
        return m.updateList(msg)
    case detailState:
        return m.updateDetail(msg)
    }

    return m, nil
}

func (m model) View() string {
    switch m.state {
    case loadingState:
        return "Loading..."
    case listState:
        return m.renderList()
    case detailState:
        return m.renderDetail()
    case errorState:
        return fmt.Sprintf("Error: %v\\nPress ESC to continue", m.error)
    }
    return ""
}'''

    return templates


def validate_architecture_suggestion(result: Dict[str, Any]) -> Dict[str, Any]:
    """Validate architecture suggestion result."""
    if 'error' in result:
        return {"status": "error", "summary": result['error']}

    validation = result.get('validation', {})
    status = validation.get('status', 'unknown')
    summary = validation.get('summary', 'Architecture analysis complete')

    checks = [
        (result.get('current_pattern') is not None, "Pattern detected"),
        (result.get('complexity_score') is not None, "Complexity calculated"),
        (result.get('recommended_pattern') is not None, "Recommendation generated"),
        (len(result.get('refactoring_steps', [])) > 0, "Has refactoring steps"),
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
        print("Usage: suggest_architecture.py <code_path> [complexity_level]")
        sys.exit(1)

    code_path = sys.argv[1]
    complexity_level = sys.argv[2] if len(sys.argv) > 2 else "auto"

    result = suggest_architecture(code_path, complexity_level)
    print(json.dumps(result, indent=2))
