#!/usr/bin/env python3
"""
Go code parser utilities for Bubble Tea maintenance agent.
Extracts models, functions, types, and code structure.
"""

import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path


def extract_model_struct(content: str) -> Optional[Dict[str, any]]:
    """Extract the main model struct from Go code."""

    # Pattern: type XxxModel struct { ... }
    pattern = r'type\s+(\w*[Mm]odel)\s+struct\s*\{([^}]+)\}'
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        return None

    model_name = match.group(1)
    model_body = match.group(2)

    # Parse fields
    fields = []
    for line in model_body.split('\n'):
        line = line.strip()
        if not line or line.startswith('//'):
            continue

        # Parse field: name type [tag]
        field_match = re.match(r'(\w+)\s+([^\s`]+)(?:\s+`([^`]+)`)?', line)
        if field_match:
            fields.append({
                "name": field_match.group(1),
                "type": field_match.group(2),
                "tag": field_match.group(3) if field_match.group(3) else None
            })

    return {
        "name": model_name,
        "fields": fields,
        "field_count": len(fields),
        "raw_body": model_body
    }


def extract_update_function(content: str) -> Optional[Dict[str, any]]:
    """Extract the Update() function."""

    # Find Update function
    pattern = r'func\s+\((\w+)\s+(\*?)(\w+)\)\s+Update\s*\([^)]*\)\s*\([^)]*\)\s*\{(.+?)(?=\nfunc\s|\Z)'
    match = re.search(pattern, content, re.DOTALL | re.MULTILINE)

    if not match:
        return None

    receiver_name = match.group(1)
    is_pointer = match.group(2) == '*'
    receiver_type = match.group(3)
    function_body = match.group(4)

    # Count cases in switch statements
    case_count = len(re.findall(r'\bcase\s+', function_body))

    # Find message types handled
    handled_messages = re.findall(r'case\s+(\w+\.?\w*):', function_body)

    return {
        "receiver_name": receiver_name,
        "receiver_type": receiver_type,
        "is_pointer_receiver": is_pointer,
        "body_lines": len(function_body.split('\n')),
        "case_count": case_count,
        "handled_messages": list(set(handled_messages)),
        "raw_body": function_body
    }


def extract_view_function(content: str) -> Optional[Dict[str, any]]:
    """Extract the View() function."""

    pattern = r'func\s+\((\w+)\s+(\*?)(\w+)\)\s+View\s*\(\s*\)\s+string\s*\{(.+?)(?=\nfunc\s|\Z)'
    match = re.search(pattern, content, re.DOTALL | re.MULTILINE)

    if not match:
        return None

    receiver_name = match.group(1)
    is_pointer = match.group(2) == '*'
    receiver_type = match.group(3)
    function_body = match.group(4)

    # Analyze complexity
    string_concat_count = len(re.findall(r'\+\s*"', function_body))
    lipgloss_calls = len(re.findall(r'lipgloss\.', function_body))

    return {
        "receiver_name": receiver_name,
        "receiver_type": receiver_type,
        "is_pointer_receiver": is_pointer,
        "body_lines": len(function_body.split('\n')),
        "string_concatenations": string_concat_count,
        "lipgloss_calls": lipgloss_calls,
        "raw_body": function_body
    }


def extract_init_function(content: str) -> Optional[Dict[str, any]]:
    """Extract the Init() function."""

    pattern = r'func\s+\((\w+)\s+(\*?)(\w+)\)\s+Init\s*\(\s*\)\s+tea\.Cmd\s*\{(.+?)(?=\nfunc\s|\Z)'
    match = re.search(pattern, content, re.DOTALL | re.MULTILINE)

    if not match:
        return None

    receiver_name = match.group(1)
    is_pointer = match.group(2) == '*'
    receiver_type = match.group(3)
    function_body = match.group(4)

    return {
        "receiver_name": receiver_name,
        "receiver_type": receiver_type,
        "is_pointer_receiver": is_pointer,
        "body_lines": len(function_body.split('\n')),
        "raw_body": function_body
    }


def extract_custom_messages(content: str) -> List[Dict[str, any]]:
    """Extract custom message type definitions."""

    # Pattern: type xxxMsg struct { ... }
    pattern = r'type\s+(\w+Msg)\s+struct\s*\{([^}]*)\}'
    matches = re.finditer(pattern, content, re.DOTALL)

    messages = []
    for match in matches:
        msg_name = match.group(1)
        msg_body = match.group(2)

        # Parse fields
        fields = []
        for line in msg_body.split('\n'):
            line = line.strip()
            if not line or line.startswith('//'):
                continue

            field_match = re.match(r'(\w+)\s+([^\s]+)', line)
            if field_match:
                fields.append({
                    "name": field_match.group(1),
                    "type": field_match.group(2)
                })

        messages.append({
            "name": msg_name,
            "fields": fields,
            "field_count": len(fields)
        })

    return messages


def extract_tea_commands(content: str) -> List[Dict[str, any]]:
    """Extract tea.Cmd functions."""

    # Pattern: func xxxCmd() tea.Msg { ... }
    pattern = r'func\s+(\w+)\s*\(\s*\)\s+tea\.Msg\s*\{(.+?)^\}'
    matches = re.finditer(pattern, content, re.DOTALL | re.MULTILINE)

    commands = []
    for match in matches:
        cmd_name = match.group(1)
        cmd_body = match.group(2)

        # Check for blocking operations
        has_http = bool(re.search(r'\bhttp\.(Get|Post|Do)', cmd_body))
        has_sleep = bool(re.search(r'time\.Sleep', cmd_body))
        has_io = bool(re.search(r'\bos\.(Open|Read|Write)', cmd_body))

        commands.append({
            "name": cmd_name,
            "body_lines": len(cmd_body.split('\n')),
            "has_http": has_http,
            "has_sleep": has_sleep,
            "has_io": has_io,
            "is_blocking": has_http or has_io  # sleep is expected in commands
        })

    return commands


def extract_imports(content: str) -> List[str]:
    """Extract import statements."""

    imports = []

    # Single import
    single_pattern = r'import\s+"([^"]+)"'
    imports.extend(re.findall(single_pattern, content))

    # Multi-line import block
    block_pattern = r'import\s+\(([^)]+)\)'
    block_matches = re.finditer(block_pattern, content, re.DOTALL)
    for match in block_matches:
        block_content = match.group(1)
        # Extract quoted imports
        quoted = re.findall(r'"([^"]+)"', block_content)
        imports.extend(quoted)

    return list(set(imports))


def find_bubbletea_components(content: str) -> List[Dict[str, any]]:
    """Find usage of Bubble Tea components (list, viewport, etc.)."""

    components = []

    component_patterns = {
        "list": r'list\.Model',
        "viewport": r'viewport\.Model',
        "textinput": r'textinput\.Model',
        "textarea": r'textarea\.Model',
        "table": r'table\.Model',
        "progress": r'progress\.Model',
        "spinner": r'spinner\.Model',
        "timer": r'timer\.Model',
        "stopwatch": r'stopwatch\.Model',
        "filepicker": r'filepicker\.Model',
        "paginator": r'paginator\.Model',
    }

    for comp_name, pattern in component_patterns.items():
        if re.search(pattern, content):
            # Count occurrences
            count = len(re.findall(pattern, content))
            components.append({
                "component": comp_name,
                "occurrences": count
            })

    return components


def analyze_code_structure(file_path: Path) -> Dict[str, any]:
    """Comprehensive code structure analysis."""

    try:
        content = file_path.read_text()
    except Exception as e:
        return {"error": str(e)}

    return {
        "model": extract_model_struct(content),
        "update": extract_update_function(content),
        "view": extract_view_function(content),
        "init": extract_init_function(content),
        "custom_messages": extract_custom_messages(content),
        "tea_commands": extract_tea_commands(content),
        "imports": extract_imports(content),
        "components": find_bubbletea_components(content),
        "file_size": len(content),
        "line_count": len(content.split('\n')),
        "uses_lipgloss": '"github.com/charmbracelet/lipgloss"' in content,
        "uses_bubbletea": '"github.com/charmbracelet/bubbletea"' in content
    }


def find_function_by_name(content: str, func_name: str) -> Optional[str]:
    """Find a specific function by name and return its body."""

    pattern = rf'func\s+(?:\([^)]+\)\s+)?{func_name}\s*\([^)]*\)[^{{]*\{{(.+?)(?=\nfunc\s|\Z)'
    match = re.search(pattern, content, re.DOTALL | re.MULTILINE)

    if match:
        return match.group(1)
    return None


def extract_state_machine_states(content: str) -> Optional[Dict[str, any]]:
    """Extract state machine enum if present."""

    # Pattern: type xxxState int; const ( state1 state2 = iota ... )
    state_type_pattern = r'type\s+(\w+State)\s+(int|string)'
    state_type_match = re.search(state_type_pattern, content)

    if not state_type_match:
        return None

    state_type = state_type_match.group(1)

    # Find const block with iota
    const_pattern = rf'const\s+\(([^)]+)\)'
    const_matches = re.finditer(const_pattern, content, re.DOTALL)

    states = []
    for const_match in const_matches:
        const_body = const_match.group(1)
        if state_type in const_body and 'iota' in const_body:
            # Extract state names
            state_names = re.findall(rf'(\w+)\s+{state_type}', const_body)
            states = state_names
            break

    return {
        "type": state_type,
        "states": states,
        "count": len(states)
    }


# Example usage and testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: go_parser.py <go_file>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    result = analyze_code_structure(file_path)

    import json
    print(json.dumps(result, indent=2))
