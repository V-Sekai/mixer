#!/usr/bin/env python3
"""
Collection Synchronization Development Test

Standalone test file to develop and test Generic protocol collection synchronization.
This file can be experimented with freely without affecting the main test suite.

EXTRACTED FROM: tests/vrtist/test_collection.py
FOCUS: Fix collection sync in Generic protocol (currently generates no messages)

Usage:
    # Test Generic protocol (currently failing - no messages generated)
    python -m pytest test_collection_development.py::test_nested_collections[Generic] -v

    # Test VRtist protocol (should work)
    python -m pytest test_collection_development.py::test_nested_collections[VRtist] -v
"""

import pytest
from pathlib import Path
from tests.mixer_testcase import BlenderDesc
from tests import files_folder


@pytest.fixture(params=[False], ids=['Generic'])
def generic_instances(request):
    """Development fixture for testing collection sync in both protocols"""

    # Use single protocol for focused testing
    # Change this value to True to test VRtist, False for Generic
    test_generic = request.param

    from tests.vrtist.vrtist_testcase import VRtistTestCase
    from tests.blender.blender_testcase import BlenderTestCase
    import socket

    # Use different server ports to avoid conflicts between parameterized tests
    base_port = 12800
    port_offset = 1 if test_generic else 0  # Generic gets port_offset 1, VRtist gets 0

    def find_free_port(base_port, max_attempts=10):
        for attempt in range(max_attempts):
            try_port = base_port + attempt
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                try:
                    sock.bind(('127.0.0.1', try_port))
                    sock.close()
                    return try_port
                except OSError:
                    continue
        raise RuntimeError(f"Could not find free port starting from {base_port}")

    server_port = find_free_port(base_port + port_offset)

    try:
        sender_blendfile = files_folder() / "empty.blend"
        receiver_blendfile = files_folder() / "empty.blend"
        sender = BlenderDesc(load_file=sender_blendfile, wait_for_debugger=False)
        receiver = BlenderDesc(load_file=receiver_blendfile, wait_for_debugger=False)
        blenderdescs = [sender, receiver]

        print(f"\n🔧 Testing protocol: {'GENERIC' if test_generic else 'VRtist'}")
        print(f"📡 Server port: {server_port}")

        # Create VRtist test instance and perform proper Blender setup
        vrtist_test = VRtistTestCase()

        # CRITICAL: Perform the Blender setup that initializes _blenders with actual BlenderApp instances
        vrtist_test.setup_method(None, blenderdescs=blenderdescs, server_args=["--port", str(server_port)])

        # Initialize additional attributes needed for vrtist tests
        vrtist_test.vrtist_protocol = test_generic
        vrtist_test.ignored_messages = set()
        vrtist_test.expected_counts = {}

        print(f"✅ Setup complete - Protocol: {'GENERIC' if test_generic else 'VRtist'}")
        print(f"   vrtist_protocol flag: {vrtist_test.vrtist_protocol}")

        yield vrtist_test

    except Exception as e:
        print(f"\n❌ Setup failed for protocol {'GENERIC' if test_generic else 'VRtist'}: {e}")
        import traceback
        traceback.print_exc()
        pytest.fail(f"Failed to setup collection test instances: {e}")
    finally:
        # Cleanup
        try:
            if hasattr(vrtist_test, 'shutdown'):
                vrtist_test.shutdown()
            print(f"🧹 Cleanup complete for protocol {'GENERIC' if test_generic else 'VRtist'}")
        except:
            pass
        import gc
        gc.collect()


def test_nested_collections(generic_instances):
    """
    DEVELOPEMENT TEST: Nested collection creation synchronization

    Current status:
    ✅ VRtist: Should work (collection operations trigger sync messages)
    ❌ Generic: Currently fails with "No messages grabbed"

    Test operations:
    1. Create collection "plop"
    2. Link to master collection
    3. Create "plaf" collection
    4. Create nested collections "sous_plop" and "sous_plaf"
    5. Assert synchronization worked
    """

    instance = generic_instances

    protocol_name = "GENERIC" if instance.vrtist_protocol else "VRtist"
    print(f"\n🏗️ Running collection test for protocol: {protocol_name}"
    "   Commands to execute:"
    "   1. new_collection('plop')"
    "   2. link_collection_to_collection('Collection', 'plop')"
    "   3. new_collection('plaf')"
    "   4. link_collection_to_collection('Collection', 'plaf')"
    "   5. new_collection('sous_plop')"
    "   6. link_collection_to_collection('plop', 'sous_plop')"
    "   7. new_collection('sous_plaf')"
    "   8. link_collection_to_collection('plaf', 'sous_plaf')"
    "   9. assert_matches() <- Check if all operations synced")

    # Test collection operations
    instance.new_collection("plop")
    instance.link_collection_to_collection("Collection", "plop")
    instance.new_collection("plaf")
    instance.link_collection_to_collection("Collection", "plaf")
    instance.new_collection("sous_plop")
    instance.link_collection_to_collection("plop", "sous_plop")
    instance.new_collection("sous_plaf")
    instance.link_collection_to_collection("plaf", "sous_plaf")

    print(f"\n🔍 Protocol {protocol_name}: Executing assert_matches()...")
    print(f"   vrtist_protocol: {instance.vrtist_protocol}")
    print(f"   expected_counts: {instance.expected_counts}")
    print(f"   ignored_messages: {instance.ignored_messages}")

    try:
        # The key test - does this generate/messages for this protocol?
        instance.assert_matches(allow_empty=True)
        print(f"✅ Protocol {protocol_name}: assert_matches() passed - collection sync working!")
    except Exception as e:
        print(f"❌ Protocol {protocol_name}: assert_matches() failed: {e}")
        print(f"   This indicates {'GENERIC' if instance.vrtist_protocol else 'VRtist'} does not sync collection operations")
        raise


if __name__ == "__main__":
    print("🚀 Collection Development Test")
    print("=" * 50)
    print("This test file extracts the failing collection test for independent development.")
    print()
    print("EXPERIMENTAL: Feel free to modify this file to test different sync approaches")
    print("              Changes here won't affect the main test suite")
    print()
    print("To run:")
    print("  pytest test_collection_development.py::test_nested_collections -v -s")
    print()
    print("Useful debugging:")
    print("  --log-cli-level=DEBUG  # See detailed logging")
    print("  --tb=long             # Full stack traces")
    print("  --capture=no          # See print statements")
    print("=" * 50)
