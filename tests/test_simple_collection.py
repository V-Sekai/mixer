#!/usr/bin/env python3
"""
Simple pytest collection test to verify core infrastructure works
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_conftest_imports():
    """Test that conftest imports work correctly"""
    try:
        from tests.conftest import parameterized, blender_setup, TestAssertionsMixin
        assert hasattr(parameterized, 'compatible'), "parameterized fallback missing compatible attribute"
        print("✅ conftest imports working")
        return True
    except Exception as e:
        print(f"❌ conftest imports failed: {e}")
        return False

def test_basic_blender_setup():
    """Test basic Blender instance setup"""
    try:
        from tests.conftest import blender_setup
        instances = blender_setup()
        if instances and len(instances) >= 2:
            print("✅ Basic Blender setup working")
            return True
        else:
            print("❌ Basic Blender setup returned invalid instances")
            return False
    except Exception as e:
        print(f"❌ Basic Blender setup failed: {e}")
        return False

def test_message_type_fallback():
    """Test MessageType fallback works"""
    try:
        from tests.conftest import MessageType
        assert hasattr(MessageType, 'SET_SCENE'), "MessageType missing SET_SCENE"
        print("✅ MessageType fallback working")
        return True
    except Exception as e:
        print(f"❌ MessageType fallback failed: {e}")
        return False

def main():
    """Run all simple collection tests"""
    print("🧪 Testing pytest infrastructure readiness...\n")

    results = []
    results.append(test_conftest_imports())
    results.append(test_basic_blender_setup())
    results.append(test_message_type_fallback())

    passed = sum(results)
    total = len(results)

    print(f"\n📊 Test Results: {passed}/{total} passed")

    if passed == total:
        print("✅ All infrastructure tests passed!")
        return 0
    else:
        print("❌ Some infrastructure tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
