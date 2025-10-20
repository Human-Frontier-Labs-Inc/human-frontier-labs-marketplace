#!/usr/bin/env python3
"""
Comprehensive Bubble Tea application analysis.
Orchestrates all analysis functions for complete health check.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any

# Import all analysis functions
sys.path.insert(0, str(Path(__file__).parent))

from diagnose_issue import diagnose_issue
from apply_best_practices import apply_best_practices
from debug_performance import debug_performance
from suggest_architecture import suggest_architecture
from fix_layout_issues import fix_layout_issues


def comprehensive_bubbletea_analysis(code_path: str, detail_level: str = "standard") -> Dict[str, Any]:
    """
    Perform complete health check of Bubble Tea application.

    Args:
        code_path: Path to Go file or directory containing Bubble Tea code
        detail_level: "quick", "standard", or "deep"

    Returns:
        Dictionary containing:
        - overall_health: 0-100 score
        - sections: Results from each analysis function
        - summary: Executive summary
        - priority_fixes: Ordered list of critical/high-priority issues
        - estimated_fix_time: Time estimate for addressing issues
        - validation: Overall validation report
    """
    path = Path(code_path)

    if not path.exists():
        return {
            "error": f"Path not found: {code_path}",
            "validation": {"status": "error", "summary": "Invalid path"}
        }

    print(f"\n{'='*70}")
    print(f"COMPREHENSIVE BUBBLE TEA ANALYSIS")
    print(f"{'='*70}")
    print(f"Analyzing: {path}")
    print(f"Detail level: {detail_level}\n")

    sections = {}

    # Section 1: Issue Diagnosis
    print("🔍 [1/5] Diagnosing issues...")
    try:
        sections['issues'] = diagnose_issue(str(path))
        print(f"    ✓ Found {len(sections['issues'].get('issues', []))} issue(s)")
    except Exception as e:
        sections['issues'] = {"error": str(e)}
        print(f"    ✗ Error: {e}")

    # Section 2: Best Practices Compliance
    print("📋 [2/5] Checking best practices...")
    try:
        sections['best_practices'] = apply_best_practices(str(path))
        score = sections['best_practices'].get('overall_score', 0)
        print(f"    ✓ Score: {score}/100")
    except Exception as e:
        sections['best_practices'] = {"error": str(e)}
        print(f"    ✗ Error: {e}")

    # Section 3: Performance Analysis
    print("⚡ [3/5] Analyzing performance...")
    try:
        sections['performance'] = debug_performance(str(path))
        bottleneck_count = len(sections['performance'].get('bottlenecks', []))
        print(f"    ✓ Found {bottleneck_count} bottleneck(s)")
    except Exception as e:
        sections['performance'] = {"error": str(e)}
        print(f"    ✗ Error: {e}")

    # Section 4: Architecture Recommendations
    if detail_level in ["standard", "deep"]:
        print("🏗️  [4/5] Analyzing architecture...")
        try:
            sections['architecture'] = suggest_architecture(str(path))
            current = sections['architecture'].get('current_pattern', 'unknown')
            recommended = sections['architecture'].get('recommended_pattern', 'unknown')
            print(f"    ✓ Current: {current}, Recommended: {recommended}")
        except Exception as e:
            sections['architecture'] = {"error": str(e)}
            print(f"    ✗ Error: {e}")
    else:
        print("🏗️  [4/5] Skipping architecture (quick mode)")
        sections['architecture'] = {"skipped": "quick mode"}

    # Section 5: Layout Validation
    print("📐 [5/5] Checking layout...")
    try:
        sections['layout'] = fix_layout_issues(str(path))
        issue_count = len(sections['layout'].get('layout_issues', []))
        print(f"    ✓ Found {issue_count} layout issue(s)")
    except Exception as e:
        sections['layout'] = {"error": str(e)}
        print(f"    ✗ Error: {e}")

    print()

    # Calculate overall health
    overall_health = _calculate_overall_health(sections)

    # Extract priority fixes
    priority_fixes = _extract_priority_fixes(sections)

    # Estimate fix time
    estimated_fix_time = _estimate_fix_time(priority_fixes)

    # Generate summary
    summary = _generate_summary(overall_health, sections, priority_fixes)

    # Overall validation
    validation = {
        "status": _determine_status(overall_health),
        "summary": summary,
        "overall_health": overall_health,
        "sections_completed": len([s for s in sections.values() if 'error' not in s and 'skipped' not in s]),
        "total_sections": 5
    }

    # Print summary
    _print_summary_report(overall_health, summary, priority_fixes, estimated_fix_time)

    return {
        "overall_health": overall_health,
        "sections": sections,
        "summary": summary,
        "priority_fixes": priority_fixes,
        "estimated_fix_time": estimated_fix_time,
        "validation": validation,
        "detail_level": detail_level,
        "analyzed_path": str(path)
    }


def _calculate_overall_health(sections: Dict[str, Any]) -> int:
    """Calculate overall health score (0-100)."""

    scores = []
    weights = {
        'issues': 0.25,
        'best_practices': 0.25,
        'performance': 0.20,
        'architecture': 0.15,
        'layout': 0.15
    }

    # Issues score (inverse of health_score from diagnose_issue)
    if 'issues' in sections and 'health_score' in sections['issues']:
        scores.append((sections['issues']['health_score'], weights['issues']))

    # Best practices score
    if 'best_practices' in sections and 'overall_score' in sections['best_practices']:
        scores.append((sections['best_practices']['overall_score'], weights['best_practices']))

    # Performance score (derive from bottlenecks)
    if 'performance' in sections and 'bottlenecks' in sections['performance']:
        bottlenecks = sections['performance']['bottlenecks']
        critical = sum(1 for b in bottlenecks if b['severity'] == 'CRITICAL')
        high = sum(1 for b in bottlenecks if b['severity'] == 'HIGH')
        perf_score = max(0, 100 - (critical * 20) - (high * 10))
        scores.append((perf_score, weights['performance']))

    # Architecture score (based on complexity vs pattern appropriateness)
    if 'architecture' in sections and 'complexity_score' in sections['architecture']:
        arch_data = sections['architecture']
        # Good if recommended == current, or if complexity is low
        if arch_data.get('recommended_pattern') == arch_data.get('current_pattern'):
            arch_score = 100
        elif arch_data.get('complexity_score', 0) < 40:
            arch_score = 80  # Simple app, pattern less critical
        else:
            arch_score = 60  # Should refactor
        scores.append((arch_score, weights['architecture']))

    # Layout score (inverse of issues)
    if 'layout' in sections and 'layout_issues' in sections['layout']:
        layout_issues = sections['layout']['layout_issues']
        critical = sum(1 for i in layout_issues if i['severity'] == 'CRITICAL')
        warning = sum(1 for i in layout_issues if i['severity'] == 'WARNING')
        layout_score = max(0, 100 - (critical * 15) - (warning * 5))
        scores.append((layout_score, weights['layout']))

    # Weighted average
    if not scores:
        return 50  # No data

    weighted_sum = sum(score * weight for score, weight in scores)
    total_weight = sum(weight for _, weight in scores)

    return int(weighted_sum / total_weight)


def _extract_priority_fixes(sections: Dict[str, Any]) -> List[str]:
    """Extract priority fixes across all sections."""

    fixes = []

    # Critical issues
    if 'issues' in sections and 'issues' in sections['issues']:
        critical = [i for i in sections['issues']['issues'] if i['severity'] == 'CRITICAL']
        for issue in critical:
            fixes.append({
                "priority": "CRITICAL",
                "source": "Issues",
                "description": f"{issue['issue']} ({issue['location']})",
                "fix": issue.get('fix', 'See issue details')
            })

    # Critical performance bottlenecks
    if 'performance' in sections and 'bottlenecks' in sections['performance']:
        critical = [b for b in sections['performance']['bottlenecks'] if b['severity'] == 'CRITICAL']
        for bottleneck in critical:
            fixes.append({
                "priority": "CRITICAL",
                "source": "Performance",
                "description": f"{bottleneck['issue']} ({bottleneck['location']})",
                "fix": bottleneck.get('fix', 'See bottleneck details')
            })

    # Critical layout issues
    if 'layout' in sections and 'layout_issues' in sections['layout']:
        critical = [i for i in sections['layout']['layout_issues'] if i['severity'] == 'CRITICAL']
        for issue in critical:
            fixes.append({
                "priority": "CRITICAL",
                "source": "Layout",
                "description": f"{issue['issue']} ({issue['location']})",
                "fix": issue.get('explanation', 'See layout details')
            })

    # Best practice failures
    if 'best_practices' in sections and 'compliance' in sections['best_practices']:
        compliance = sections['best_practices']['compliance']
        failures = [tip for tip, data in compliance.items() if data['status'] == 'fail']
        for tip in failures[:3]:  # Top 3
            fixes.append({
                "priority": "WARNING",
                "source": "Best Practices",
                "description": f"Missing {tip.replace('_', ' ')}",
                "fix": compliance[tip].get('recommendation', 'See best practices')
            })

    # Architecture recommendations (if significant refactoring needed)
    if 'architecture' in sections and 'complexity_score' in sections['architecture']:
        arch_data = sections['architecture']
        if arch_data.get('complexity_score', 0) > 70:
            if arch_data.get('recommended_pattern') != arch_data.get('current_pattern'):
                fixes.append({
                    "priority": "INFO",
                    "source": "Architecture",
                    "description": f"Consider refactoring to {arch_data.get('recommended_pattern')}",
                    "fix": f"See architecture recommendations for {len(arch_data.get('refactoring_steps', []))} steps"
                })

    return fixes


def _estimate_fix_time(priority_fixes: List[Dict[str, str]]) -> str:
    """Estimate time to address priority fixes."""

    critical_count = sum(1 for f in priority_fixes if f['priority'] == 'CRITICAL')
    warning_count = sum(1 for f in priority_fixes if f['priority'] == 'WARNING')
    info_count = sum(1 for f in priority_fixes if f['priority'] == 'INFO')

    # Time estimates (in hours)
    critical_time = critical_count * 0.5  # 30 min each
    warning_time = warning_count * 0.25   # 15 min each
    info_time = info_count * 1.0          # 1 hour each (refactoring)

    total_hours = critical_time + warning_time + info_time

    if total_hours == 0:
        return "No fixes needed"
    elif total_hours < 1:
        return f"{int(total_hours * 60)} minutes"
    elif total_hours < 2:
        return f"1-2 hours"
    elif total_hours < 4:
        return f"2-4 hours"
    elif total_hours < 8:
        return f"4-8 hours"
    else:
        return f"{int(total_hours)} hours (1-2 days)"


def _generate_summary(health: int, sections: Dict[str, Any], fixes: List[Dict[str, str]]) -> str:
    """Generate executive summary."""

    if health >= 90:
        health_desc = "Excellent"
        emoji = "✅"
    elif health >= 75:
        health_desc = "Good"
        emoji = "✓"
    elif health >= 60:
        health_desc = "Fair"
        emoji = "⚠️"
    elif health >= 40:
        health_desc = "Poor"
        emoji = "❌"
    else:
        health_desc = "Critical"
        emoji = "🚨"

    critical_count = sum(1 for f in fixes if f['priority'] == 'CRITICAL')

    if health >= 80:
        summary = f"{emoji} {health_desc} health ({health}/100). Application follows most best practices."
    elif health >= 60:
        summary = f"{emoji} {health_desc} health ({health}/100). Some improvements recommended."
    elif health >= 40:
        summary = f"{emoji} {health_desc} health ({health}/100). Several issues need attention."
    else:
        summary = f"{emoji} {health_desc} health ({health}/100). Multiple critical issues require immediate fixes."

    if critical_count > 0:
        summary += f" {critical_count} critical issue(s) found."

    return summary


def _determine_status(health: int) -> str:
    """Determine overall status from health score."""
    if health >= 80:
        return "pass"
    elif health >= 60:
        return "warning"
    else:
        return "critical"


def _print_summary_report(health: int, summary: str, fixes: List[Dict[str, str]], fix_time: str):
    """Print formatted summary report."""

    print(f"{'='*70}")
    print(f"ANALYSIS COMPLETE")
    print(f"{'='*70}\n")

    print(f"Overall Health: {health}/100")
    print(f"Summary: {summary}\n")

    if fixes:
        print(f"Priority Fixes ({len(fixes)}):")
        print(f"{'-'*70}")

        # Group by priority
        critical = [f for f in fixes if f['priority'] == 'CRITICAL']
        warnings = [f for f in fixes if f['priority'] == 'WARNING']
        info = [f for f in fixes if f['priority'] == 'INFO']

        if critical:
            print(f"\n🔴 CRITICAL ({len(critical)}):")
            for i, fix in enumerate(critical, 1):
                print(f"  {i}. [{fix['source']}] {fix['description']}")

        if warnings:
            print(f"\n⚠️  WARNINGS ({len(warnings)}):")
            for i, fix in enumerate(warnings, 1):
                print(f"  {i}. [{fix['source']}] {fix['description']}")

        if info:
            print(f"\n💡 INFO ({len(info)}):")
            for i, fix in enumerate(info, 1):
                print(f"  {i}. [{fix['source']}] {fix['description']}")

    else:
        print("✅ No priority fixes needed!")

    print(f"\n{'-'*70}")
    print(f"Estimated Fix Time: {fix_time}")
    print(f"{'='*70}\n")


def validate_comprehensive_analysis(result: Dict[str, Any]) -> Dict[str, Any]:
    """Validate comprehensive analysis result."""
    if 'error' in result:
        return {"status": "error", "summary": result['error']}

    validation = result.get('validation', {})
    status = validation.get('status', 'unknown')
    summary = validation.get('summary', 'Analysis complete')

    checks = [
        (result.get('overall_health') is not None, "Health score calculated"),
        (result.get('sections') is not None, "Sections analyzed"),
        (result.get('priority_fixes') is not None, "Priority fixes extracted"),
        (result.get('summary') is not None, "Summary generated"),
    ]

    all_pass = all(check[0] for check in checks)

    return {
        "status": status,
        "summary": summary,
        "checks": {check[1]: check[0] for check in checks},
        "valid": all_pass
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: comprehensive_bubbletea_analysis.py <code_path> [detail_level]")
        print("  detail_level: quick, standard (default), or deep")
        sys.exit(1)

    code_path = sys.argv[1]
    detail_level = sys.argv[2] if len(sys.argv) > 2 else "standard"

    if detail_level not in ["quick", "standard", "deep"]:
        print(f"Invalid detail_level: {detail_level}")
        print("Must be: quick, standard, or deep")
        sys.exit(1)

    result = comprehensive_bubbletea_analysis(code_path, detail_level)

    # Save to file
    output_file = Path(code_path).parent / "bubbletea_analysis_report.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"Full report saved to: {output_file}\n")
