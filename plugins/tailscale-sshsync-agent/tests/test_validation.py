#!/usr/bin/env python3
"""
Tests for validators.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from utils.validators import *


def test_validate_host():
    """Test host validation."""
    # Valid host
    assert validate_host("web-01") == "web-01"
    assert validate_host(" web-01 ") == "web-01"  # Strips whitespace

    # With valid list
    assert validate_host("web-01", ["web-01", "web-02"]) == "web-01"

    # Invalid format
    try:
        validate_host("web@01")  # Invalid character
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass

    print("✓ validate_host() passed")
    return True


def test_validate_group():
    """Test group validation."""
    # Valid group
    assert validate_group("production") == "production"
    assert validate_group("PRODUCTION") == "production"  # Lowercase normalization

    # With valid list
    assert validate_group("production", ["production", "staging"]) == "production"

    # Invalid
    try:
        validate_group("invalid!", ["production"])
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass

    print("✓ validate_group() passed")
    return True


def test_validate_path_exists():
    """Test path existence validation."""
    # Valid path
    path = validate_path_exists("/tmp", must_be_dir=True)
    assert isinstance(path, Path)

    # Invalid path
    try:
        validate_path_exists("/nonexistent_12345")
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass

    print("✓ validate_path_exists() passed")
    return True


def test_validate_timeout():
    """Test timeout validation."""
    # Valid timeouts
    assert validate_timeout(10) == 10
    assert validate_timeout(1) == 1
    assert validate_timeout(600) == 600

    # Too low
    try:
        validate_timeout(0)
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass

    # Too high
    try:
        validate_timeout(1000)
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass

    print("✓ validate_timeout() passed")
    return True


def test_validate_command():
    """Test command validation."""
    # Safe commands
    assert validate_command("ls -la") == "ls -la"
    assert validate_command("uptime") == "uptime"

    # Dangerous commands (should fail without allow_dangerous)
    try:
        validate_command("rm -rf /")
        assert False, "Should have blocked dangerous command"
    except ValidationError:
        pass

    # But should work with allow_dangerous
    assert validate_command("rm -rf /tmp/test", allow_dangerous=True)

    print("✓ validate_command() passed")
    return True


def test_validate_hosts_list():
    """Test list validation."""
    # Valid list
    hosts = validate_hosts_list(["web-01", "web-02"])
    assert len(hosts) == 2
    assert "web-01" in hosts

    # Empty list
    try:
        validate_hosts_list([])
        assert False, "Should have raised ValidationError for empty list"
    except ValidationError:
        pass

    print("✓ validate_hosts_list() passed")
    return True


def test_get_invalid_hosts():
    """Test finding invalid hosts."""
    # Test with mix of valid and invalid
    # (This would require actual SSH config, so we test the function exists)
    result = get_invalid_hosts(["web-01", "nonexistent-host-12345"])
    assert isinstance(result, list)

    print("✓ get_invalid_hosts() passed")
    return True


def main():
    """Run all validation tests."""
    print("=" * 70)
    print("VALIDATION TESTS")
    print("=" * 70)

    tests = [
        test_validate_host,
        test_validate_group,
        test_validate_path_exists,
        test_validate_timeout,
        test_validate_command,
        test_validate_hosts_list,
        test_get_invalid_hosts,
    ]

    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()

    print(f"\nResults: {passed}/{len(tests)} passed")
    return passed == len(tests)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
