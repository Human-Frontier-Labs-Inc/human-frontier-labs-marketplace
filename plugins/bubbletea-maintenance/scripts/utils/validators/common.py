#!/usr/bin/env python3
"""
Common validation utilities for Bubble Tea maintenance agent.
"""

from typing import Dict, List, Any, Optional


def validate_result_structure(result: Dict[str, Any], required_keys: List[str]) -> Dict[str, Any]:
    """
    Validate that a result dictionary has required keys.

    Args:
        result: Result dictionary to validate
        required_keys: List of required key names

    Returns:
        Validation dict with status, summary, and checks
    """
    if 'error' in result:
        return {
            "status": "error",
            "summary": result['error'],
            "valid": False
        }

    checks = {}
    for key in required_keys:
        checks[f"has_{key}"] = key in result and result[key] is not None

    all_pass = all(checks.values())

    status = "pass" if all_pass else "fail"
    summary = "Validation passed" if all_pass else f"Missing required keys: {[k for k, v in checks.items() if not v]}"

    return {
        "status": status,
        "summary": summary,
        "checks": checks,
        "valid": all_pass
    }


def validate_issue_list(issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate a list of issues has proper structure.

    Expected issue structure:
    - severity: CRITICAL, HIGH, WARNING, or INFO
    - category: performance, layout, reliability, etc.
    - issue: Description
    - location: File path and line number
    - explanation: Why it's a problem
    - fix: How to fix it
    """
    if not isinstance(issues, list):
        return {
            "status": "error",
            "summary": "Issues must be a list",
            "valid": False
        }

    required_fields = ["severity", "issue", "location", "explanation"]
    valid_severities = ["CRITICAL", "HIGH", "MEDIUM", "WARNING", "LOW", "INFO"]

    checks = {
        "is_list": True,
        "all_have_severity": True,
        "valid_severity_values": True,
        "all_have_issue": True,
        "all_have_location": True,
        "all_have_explanation": True
    }

    for issue in issues:
        if not isinstance(issue, dict):
            checks["is_list"] = False
            continue

        if "severity" not in issue:
            checks["all_have_severity"] = False
        elif issue["severity"] not in valid_severities:
            checks["valid_severity_values"] = False

        if "issue" not in issue or not issue["issue"]:
            checks["all_have_issue"] = False

        if "location" not in issue or not issue["location"]:
            checks["all_have_location"] = False

        if "explanation" not in issue or not issue["explanation"]:
            checks["all_have_explanation"] = False

    all_pass = all(checks.values())
    status = "pass" if all_pass else "warning"

    failed = [k for k, v in checks.items() if not v]
    summary = "All issues properly structured" if all_pass else f"Issues have problems: {failed}"

    return {
        "status": status,
        "summary": summary,
        "checks": checks,
        "valid": all_pass,
        "issue_count": len(issues)
    }


def validate_score(score: int, min_val: int = 0, max_val: int = 100) -> bool:
    """Validate a numeric score is in range."""
    return isinstance(score, (int, float)) and min_val <= score <= max_val


def validate_health_score(health_score: int) -> Dict[str, Any]:
    """Validate health score and categorize."""
    if not validate_score(health_score):
        return {
            "status": "error",
            "summary": "Invalid health score",
            "valid": False
        }

    if health_score >= 90:
        category = "excellent"
        status = "pass"
    elif health_score >= 75:
        category = "good"
        status = "pass"
    elif health_score >= 60:
        category = "fair"
        status = "warning"
    elif health_score >= 40:
        category = "poor"
        status = "warning"
    else:
        category = "critical"
        status = "critical"

    return {
        "status": status,
        "summary": f"{category.capitalize()} health ({health_score}/100)",
        "category": category,
        "valid": True,
        "score": health_score
    }


def validate_file_path(file_path: str) -> bool:
    """Validate file path format."""
    from pathlib import Path
    try:
        path = Path(file_path)
        return path.exists()
    except Exception:
        return False


def validate_best_practices_compliance(compliance: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Validate best practices compliance structure."""
    if not isinstance(compliance, dict):
        return {
            "status": "error",
            "summary": "Compliance must be a dictionary",
            "valid": False
        }

    required_tip_fields = ["status", "score", "message"]
    valid_statuses = ["pass", "fail", "warning", "info"]

    checks = {
        "has_tips": len(compliance) > 0,
        "all_tips_valid": True,
        "valid_statuses": True,
        "valid_scores": True
    }

    for tip_name, tip_data in compliance.items():
        if not isinstance(tip_data, dict):
            checks["all_tips_valid"] = False
            continue

        for field in required_tip_fields:
            if field not in tip_data:
                checks["all_tips_valid"] = False

        if tip_data.get("status") not in valid_statuses:
            checks["valid_statuses"] = False

        if not validate_score(tip_data.get("score", -1)):
            checks["valid_scores"] = False

    all_pass = all(checks.values())
    status = "pass" if all_pass else "warning"

    return {
        "status": status,
        "summary": f"Validated {len(compliance)} tips",
        "checks": checks,
        "valid": all_pass,
        "tip_count": len(compliance)
    }


def validate_bottlenecks(bottlenecks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate performance bottleneck list."""
    if not isinstance(bottlenecks, list):
        return {
            "status": "error",
            "summary": "Bottlenecks must be a list",
            "valid": False
        }

    required_fields = ["severity", "category", "issue", "location", "explanation", "fix"]
    valid_severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    valid_categories = ["performance", "memory", "io", "rendering"]

    checks = {
        "is_list": True,
        "all_have_severity": True,
        "valid_severities": True,
        "all_have_category": True,
        "valid_categories": True,
        "all_have_fix": True
    }

    for bottleneck in bottlenecks:
        if not isinstance(bottleneck, dict):
            checks["is_list"] = False
            continue

        if "severity" not in bottleneck:
            checks["all_have_severity"] = False
        elif bottleneck["severity"] not in valid_severities:
            checks["valid_severities"] = False

        if "category" not in bottleneck:
            checks["all_have_category"] = False
        elif bottleneck["category"] not in valid_categories:
            checks["valid_categories"] = False

        if "fix" not in bottleneck or not bottleneck["fix"]:
            checks["all_have_fix"] = False

    all_pass = all(checks.values())
    status = "pass" if all_pass else "warning"

    return {
        "status": status,
        "summary": f"Validated {len(bottlenecks)} bottlenecks",
        "checks": checks,
        "valid": all_pass,
        "bottleneck_count": len(bottlenecks)
    }


def validate_architecture_analysis(result: Dict[str, Any]) -> Dict[str, Any]:
    """Validate architecture analysis result."""
    required_keys = ["current_pattern", "complexity_score", "recommended_pattern", "refactoring_steps"]

    checks = {}
    for key in required_keys:
        checks[f"has_{key}"] = key in result and result[key] is not None

    # Validate complexity score
    if "complexity_score" in result:
        checks["valid_complexity_score"] = validate_score(result["complexity_score"])
    else:
        checks["valid_complexity_score"] = False

    # Validate refactoring steps
    if "refactoring_steps" in result:
        checks["has_refactoring_steps"] = isinstance(result["refactoring_steps"], list) and len(result["refactoring_steps"]) > 0
    else:
        checks["has_refactoring_steps"] = False

    all_pass = all(checks.values())
    status = "pass" if all_pass else "warning"

    return {
        "status": status,
        "summary": "Architecture analysis validated" if all_pass else "Architecture analysis incomplete",
        "checks": checks,
        "valid": all_pass
    }


def validate_layout_fixes(fixes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate layout fix list."""
    if not isinstance(fixes, list):
        return {
            "status": "error",
            "summary": "Fixes must be a list",
            "valid": False
        }

    required_fields = ["location", "original", "fixed", "explanation"]

    checks = {
        "is_list": True,
        "all_have_location": True,
        "all_have_explanation": True,
        "all_have_fix": True
    }

    for fix in fixes:
        if not isinstance(fix, dict):
            checks["is_list"] = False
            continue

        if "location" not in fix or not fix["location"]:
            checks["all_have_location"] = False

        if "explanation" not in fix or not fix["explanation"]:
            checks["all_have_explanation"] = False

        if "fixed" not in fix or not fix["fixed"]:
            checks["all_have_fix"] = False

    all_pass = all(checks.values())
    status = "pass" if all_pass else "warning"

    return {
        "status": status,
        "summary": f"Validated {len(fixes)} fixes",
        "checks": checks,
        "valid": all_pass,
        "fix_count": len(fixes)
    }


# Example usage
if __name__ == "__main__":
    # Test validation functions
    test_issues = [
        {
            "severity": "CRITICAL",
            "category": "performance",
            "issue": "Blocking operation",
            "location": "main.go:45",
            "explanation": "HTTP call blocks event loop",
            "fix": "Move to tea.Cmd"
        }
    ]

    result = validate_issue_list(test_issues)
    print(f"Issue validation: {result}")

    health_result = validate_health_score(75)
    print(f"Health validation: {health_result}")
