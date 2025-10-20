#!/usr/bin/env python3
"""
Integration tests for Tailscale SSH Sync Agent.
Tests complete workflows from query to result.
"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from sshsync_wrapper import get_host_status, list_hosts, get_groups
from tailscale_manager import get_tailscale_status, get_network_summary
from load_balancer import format_load_report, MachineMetrics
from utils.helpers import (
    format_bytes, format_duration, format_percentage,
    calculate_load_score, classify_load_status, classify_latency
)


def test_host_status_basic():
    """Test get_host_status() without errors."""
    print("\n✓ Testing get_host_status()...")

    try:
        result = get_host_status()

        # Validations
        assert 'hosts' in result, "Missing 'hosts' in result"
        assert isinstance(result.get('hosts', []), list), "'hosts' must be list"

        # Should have basic counts even if no hosts configured
        assert 'total_count' in result, "Missing 'total_count'"
        assert 'online_count' in result, "Missing 'online_count'"
        assert 'offline_count' in result, "Missing 'offline_count'"

        print(f"  ✓ Found {result.get('total_count', 0)} hosts")
        print(f"  ✓ Online: {result.get('online_count', 0)}")
        print(f"  ✓ Offline: {result.get('offline_count', 0)}")

        return True

    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_list_hosts():
    """Test list_hosts() function."""
    print("\n✓ Testing list_hosts()...")

    try:
        result = list_hosts(with_status=False)

        assert 'hosts' in result, "Missing 'hosts' in result"
        assert 'count' in result, "Missing 'count' in result"
        assert isinstance(result['hosts'], list), "'hosts' must be list"

        print(f"  ✓ List hosts working")
        print(f"  ✓ Found {result['count']} configured hosts")

        return True

    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_get_groups():
    """Test get_groups() function."""
    print("\n✓ Testing get_groups()...")

    try:
        groups = get_groups()

        assert isinstance(groups, dict), "Groups must be dict"

        print(f"  ✓ Groups config loaded")
        print(f"  ✓ Found {len(groups)} groups")

        for group, hosts in list(groups.items())[:3]:  # Show first 3
            print(f"    - {group}: {len(hosts)} hosts")

        return True

    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_tailscale_status():
    """Test Tailscale status check."""
    print("\n✓ Testing get_tailscale_status()...")

    try:
        status = get_tailscale_status()

        assert isinstance(status, dict), "Status must be dict"
        assert 'connected' in status, "Missing 'connected' field"

        if status.get('connected'):
            print(f"  ✓ Tailscale connected")
            print(f"  ✓ Peers: {status.get('total_count', 0)} total, {status.get('online_count', 0)} online")
        else:
            print(f"  ℹ Tailscale not connected: {status.get('error', 'Unknown')}")
            print(f"  (This is OK if Tailscale is not installed/configured)")

        return True

    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_network_summary():
    """Test network summary generation."""
    print("\n✓ Testing get_network_summary()...")

    try:
        summary = get_network_summary()

        assert isinstance(summary, str), "Summary must be string"
        assert len(summary) > 0, "Summary cannot be empty"

        print(f"  ✓ Network summary generated:")
        for line in summary.split('\n'):
            print(f"    {line}")

        return True

    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_format_helpers():
    """Test formatting helper functions."""
    print("\n✓ Testing format helpers...")

    try:
        # Test format_bytes
        assert format_bytes(1024) == "1.0 KB", "format_bytes failed for 1024"
        assert format_bytes(12582912) == "12.0 MB", "format_bytes failed for 12MB"

        # Test format_duration
        assert format_duration(65) == "1m 5s", "format_duration failed for 65s"
        assert format_duration(3665) == "1h 1m", "format_duration failed for 1h+"

        # Test format_percentage
        assert format_percentage(45.567) == "45.6%", "format_percentage failed"

        print(f"  ✓ format_bytes(12582912) = {format_bytes(12582912)}")
        print(f"  ✓ format_duration(3665) = {format_duration(3665)}")
        print(f"  ✓ format_percentage(45.567) = {format_percentage(45.567)}")

        return True

    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_load_score_calculation():
    """Test load score calculation."""
    print("\n✓ Testing calculate_load_score()...")

    try:
        # Test various scenarios
        score1 = calculate_load_score(45, 60, 40)
        assert 0 <= score1 <= 1, "Score must be 0-1"
        assert abs(score1 - 0.49) < 0.01, f"Expected ~0.49, got {score1}"

        score2 = calculate_load_score(20, 35, 30)
        assert score2 < score1, "Lower usage should have lower score"

        score3 = calculate_load_score(85, 70, 65)
        assert score3 > score1, "Higher usage should have higher score"

        print(f"  ✓ Low load (20%, 35%, 30%): {score2:.2f}")
        print(f"  ✓ Med load (45%, 60%, 40%): {score1:.2f}")
        print(f"  ✓ High load (85%, 70%, 65%): {score3:.2f}")

        return True

    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_load_classification():
    """Test load status classification."""
    print("\n✓ Testing classify_load_status()...")

    try:
        assert classify_load_status(0.28) == "low", "0.28 should be 'low'"
        assert classify_load_status(0.55) == "moderate", "0.55 should be 'moderate'"
        assert classify_load_status(0.82) == "high", "0.82 should be 'high'"

        print(f"  ✓ Score 0.28 = {classify_load_status(0.28)}")
        print(f"  ✓ Score 0.55 = {classify_load_status(0.55)}")
        print(f"  ✓ Score 0.82 = {classify_load_status(0.82)}")

        return True

    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_latency_classification():
    """Test network latency classification."""
    print("\n✓ Testing classify_latency()...")

    try:
        status1, desc1 = classify_latency(25)
        assert status1 == "excellent", "25ms should be 'excellent'"

        status2, desc2 = classify_latency(75)
        assert status2 == "good", "75ms should be 'good'"

        status3, desc3 = classify_latency(150)
        assert status3 == "fair", "150ms should be 'fair'"

        status4, desc4 = classify_latency(250)
        assert status4 == "poor", "250ms should be 'poor'"

        print(f"  ✓ 25ms: {status1} - {desc1}")
        print(f"  ✓ 75ms: {status2} - {desc2}")
        print(f"  ✓ 150ms: {status3} - {desc3}")
        print(f"  ✓ 250ms: {status4} - {desc4}")

        return True

    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_load_report_formatting():
    """Test load report formatting."""
    print("\n✓ Testing format_load_report()...")

    try:
        metrics = MachineMetrics(
            host='web-01',
            cpu_pct=45.0,
            mem_pct=60.0,
            disk_pct=40.0,
            load_score=0.49,
            status='moderate'
        )

        report = format_load_report(metrics)

        assert 'web-01' in report, "Report must include hostname"
        assert '0.49' in report, "Report must include load score"
        assert 'moderate' in report, "Report must include status"

        print(f"  ✓ Report generated:")
        for line in report.split('\n'):
            print(f"    {line}")

        return True

    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_dry_run_execution():
    """Test dry-run mode for operations."""
    print("\n✓ Testing dry-run execution...")

    try:
        from sshsync_wrapper import execute_on_all

        result = execute_on_all("uptime", dry_run=True)

        assert result.get('dry_run') == True, "Must indicate dry-run mode"
        assert 'command' in result, "Must include command"
        assert 'message' in result, "Must include message"

        print(f"  ✓ Dry-run mode working")
        print(f"  ✓ Command: {result.get('command')}")
        print(f"  ✓ Message: {result.get('message')}")

        return True

    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def main():
    """Run all integration tests."""
    print("=" * 70)
    print("INTEGRATION TESTS - Tailscale SSH Sync Agent")
    print("=" * 70)

    tests = [
        ("Host status check", test_host_status_basic),
        ("List hosts", test_list_hosts),
        ("Get groups", test_get_groups),
        ("Tailscale status", test_tailscale_status),
        ("Network summary", test_network_summary),
        ("Format helpers", test_format_helpers),
        ("Load score calculation", test_load_score_calculation),
        ("Load classification", test_load_classification),
        ("Latency classification", test_latency_classification),
        ("Load report formatting", test_load_report_formatting),
        ("Dry-run execution", test_dry_run_execution),
    ]

    results = []
    for test_name, test_func in tests:
        passed = test_func()
        results.append((test_name, passed))

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)

    print(f"\nResults: {passed_count}/{total_count} passed")

    if passed_count == total_count:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed")

    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
