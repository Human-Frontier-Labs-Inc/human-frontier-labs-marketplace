#!/usr/bin/env python3
"""
Tests for helper utilities.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from utils.helpers import *


def test_format_bytes():
    """Test byte formatting."""
    assert format_bytes(0) == "0.0 B"
    assert format_bytes(512) == "512.0 B"
    assert format_bytes(1024) == "1.0 KB"
    assert format_bytes(1048576) == "1.0 MB"
    assert format_bytes(1073741824) == "1.0 GB"
    print("✓ format_bytes() passed")
    return True


def test_format_duration():
    """Test duration formatting."""
    assert format_duration(30) == "30s"
    assert format_duration(65) == "1m 5s"
    assert format_duration(3600) == "1h"
    assert format_duration(3665) == "1h 1m"
    assert format_duration(7265) == "2h 1m"
    print("✓ format_duration() passed")
    return True


def test_format_percentage():
    """Test percentage formatting."""
    assert format_percentage(45.567) == "45.6%"
    assert format_percentage(100) == "100.0%"
    assert format_percentage(0.123, decimals=2) == "0.12%"
    print("✓ format_percentage() passed")
    return True


def test_calculate_load_score():
    """Test load score calculation."""
    score = calculate_load_score(50, 50, 50)
    assert 0 <= score <= 1
    assert abs(score - 0.5) < 0.01

    score_low = calculate_load_score(20, 30, 25)
    score_high = calculate_load_score(80, 85, 90)
    assert score_low < score_high

    print("✓ calculate_load_score() passed")
    return True


def test_classify_load_status():
    """Test load status classification."""
    assert classify_load_status(0.2) == "low"
    assert classify_load_status(0.5) == "moderate"
    assert classify_load_status(0.8) == "high"
    print("✓ classify_load_status() passed")
    return True


def test_classify_latency():
    """Test latency classification."""
    status, desc = classify_latency(25)
    assert status == "excellent"
    assert "interactive" in desc.lower()

    status, desc = classify_latency(150)
    assert status == "fair"

    print("✓ classify_latency() passed")
    return True


def test_parse_disk_usage():
    """Test disk usage parsing."""
    sample_output = """Filesystem     Size  Used Avail Use% Mounted on
/dev/sda1      100G   45G   50G  45% /"""

    result = parse_disk_usage(sample_output)
    assert result['filesystem'] == '/dev/sda1'
    assert result['size'] == '100G'
    assert result['used'] == '45G'
    assert result['use_pct'] == 45

    print("✓ parse_disk_usage() passed")
    return True


def test_parse_cpu_load():
    """Test CPU load parsing."""
    sample_output = "19:43:41 up 5 days, 2:15, 3 users, load average: 0.45, 0.38, 0.32"

    result = parse_cpu_load(sample_output)
    assert result['load_1min'] == 0.45
    assert result['load_5min'] == 0.38
    assert result['load_15min'] == 0.32

    print("✓ parse_cpu_load() passed")
    return True


def test_get_timestamp():
    """Test timestamp generation."""
    ts_iso = get_timestamp(iso=True)
    assert 'T' in ts_iso
    assert 'Z' in ts_iso

    ts_human = get_timestamp(iso=False)
    assert ' ' in ts_human
    assert len(ts_human) == 19  # YYYY-MM-DD HH:MM:SS

    print("✓ get_timestamp() passed")
    return True


def test_validate_path():
    """Test path validation."""
    assert validate_path("/tmp", must_exist=True) == True
    assert validate_path("/nonexistent_path_12345", must_exist=False) == False

    print("✓ validate_path() passed")
    return True


def test_safe_execute():
    """Test safe execution wrapper."""
    # Should return result on success
    result = safe_execute(int, "42")
    assert result == 42

    # Should return default on failure
    result = safe_execute(int, "not_a_number", default=0)
    assert result == 0

    print("✓ safe_execute() passed")
    return True


def main():
    """Run all helper tests."""
    print("=" * 70)
    print("HELPER TESTS")
    print("=" * 70)

    tests = [
        test_format_bytes,
        test_format_duration,
        test_format_percentage,
        test_calculate_load_score,
        test_classify_load_status,
        test_classify_latency,
        test_parse_disk_usage,
        test_parse_cpu_load,
        test_get_timestamp,
        test_validate_path,
        test_safe_execute,
    ]

    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")

    print(f"\nResults: {passed}/{len(tests)} passed")
    return passed == len(tests)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
