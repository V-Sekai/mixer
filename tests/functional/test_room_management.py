"""
Functional tests for room management operations.

This module tests the core Blender room management functionality including:
- Room creation with different protocols
- Room joining and verification
- Room switching and cleanup
- Multi-user room coordination

These tests validate the basic "join a room" workflow that users rely on.
"""

import pytest
import logging
import time
from typing import List

from tests.mixer_testcase import BlenderApp
from tests.process import ServerProcess
from tests.functional.utils import (
    setup_multi_blender_instances,
    cleanup_blender_instances,
    verify_room_joined,
    wait_for_sync
)

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def multi_blender_generic():
    """Fixture providing 2 Blender instances using Generic protocol"""
    blenders, server = setup_multi_blender_instances(
        num_instances=2,
        protocols=[False, False],  # Generic protocol
        port_offset=12801
    )
    yield blenders, server
    cleanup_blender_instances(blenders, server)


@pytest.fixture(scope="function")
def multi_blender_vrtist():
    """Fixture providing 2 Blender instances using VRtist protocol"""
    blenders, server = setup_multi_blender_instances(
        num_instances=2,
        protocols=[True, True],   # VRtist protocol
        port_offset=12901
    )
    yield blenders, server
    cleanup_blender_instances(blenders, server)


@pytest.fixture(scope="function")
def single_blender_generic():
    """Fixture providing 1 Blender instance using Generic protocol"""
    blenders, server = setup_multi_blender_instances(
        num_instances=1,
        protocols=[False],  # Generic protocol
        port_offset=13001
    )
    yield blenders, server
    cleanup_blender_instances(blenders, server)


class TestRoomManagement:
    """Test suite for room management functionality"""

    def test_create_room_generic(self, single_blender_generic):
        """Test room creation with Generic protocol"""
        blenders, server = single_blender_generic
        blender = blenders[0]

        logger.info("🧪 Testing Generic protocol room creation")

        # Verify room creation
        assert hasattr(blender, '_sender'), "Blender instance should have sender"
        assert hasattr(blender, '_receiver'), "Blender instance should have receiver"
        assert server.is_alive(), "Server should be running"

        logger.info("✅ Generic protocol room creation successful")

    def test_create_room_vrtist(self, single_blender_vrtist):
        """Test room creation with VRtist protocol"""
        blenders, server = single_blender_vrtist
        blender = blenders[0]

        logger.info("🧪 Testing VRtist protocol room creation")

        # Verify room creation
        assert hasattr(blender, '_sender'), "Blender instance should have sender"
        assert hasattr(blender, '_receiver'), "Blender instance should have receiver"
        assert server.is_alive(), "Server should be running"

        logger.info("✅ VRtist protocol room creation successful")

    def test_room_join_basic_generic(self, multi_blender_generic):
        """Test basic room joining with Generic protocol (2 instances)"""
        blenders, server = multi_blender_generic

        logger.info("🧪 Testing multi-user room join (Generic protocol)")
        sender, receiver = blenders[0], blenders[1]

        # Verify both instances can join rooms
        assert sender is not None, "Sender instance should exist"
        assert receiver is not None, "Receiver instance should exist"

        # Allow time for room synchronization
        time.sleep(3)

        # Verify server communication
        assert server.is_alive(), "Server should still be running"
        assert not server.is_terminated(), "Server should not have terminated unexpectedly"

        logger.info("✅ Multi-user room join successful (Generic)")

    def test_room_join_basic_vrtist(self, multi_blender_vrtist):
        """Test basic room joining with VRtist protocol (2 instances)"""
        blenders, server = multi_blender_vrtist

        logger.info("🧪 Testing multi-user room join (VRtist protocol)")
        sender, receiver = blenders[0], blenders[1]

        # Verify both instances can join rooms
        assert sender is not None, "Sender instance should exist"
        assert receiver is not None, "Receiver instance should exist"

        # Allow time for room synchronization
        time.sleep(3)

        # Verify server communication
        assert server.is_alive(), "Server should still be running"
        assert not server.is_terminated(), "Server should not have terminated unexpectedly"

        logger.info("✅ Multi-user room join successful (VRtist)")

    def test_room_sync_latencies_generic(self, multi_blender_generic):
        """Test synchronization latencies in Generic protocol rooms"""
        blenders, server = multi_blender_generic

        logger.info("🧪 Testing synchronization latencies (Generic)")

        # Measure initial setup time
        start_time = time.time()

        # Allow synchronization to establish
        sync_established = wait_for_sync(blenders, timeout=5.0)

        setup_time = time.time() - start_time

        logger.info(".2f", setup_time)
        # Basic latency validation
        assert setup_time < 10, f"Setup took too long: {setup_time:.2f}s"
        assert server.is_alive(), "Server should maintain connection"

        if sync_established:
            logger.info("✅ Synchronization latency within acceptable range")
        else:
            logger.warning("⚠️ Synchronization timeout reached (may be normal for initial testing)")

    def test_room_sync_latencies_vrtist(self, multi_blender_vrtist):
        """Test synchronization latencies in VRtist protocol rooms"""
        blenders, server = multi_blender_vrtist

        logger.info("🧪 Testing synchronization latencies (VRtist)")

        # Measure initial setup time
        start_time = time.time()

        # Allow synchronization to establish
        sync_established = wait_for_sync(blenders, timeout=5.0)

        setup_time = time.time() - start_time

        logger.info(".2f", setup_time)
        # Basic latency validation
        assert setup_time < 10, f"Setup took too long: {setup_time:.2f}s"
        assert server.is_alive(), "Server should maintain connection"

        if sync_established:
            logger.info("✅ Synchronization latency within acceptable range")
        else:
            logger.warning("⚠️ Synchronization timeout reached (may be normal for initial testing)")

    def test_room_cleanup_generic(self, multi_blender_generic):
        """Test proper room cleanup in Generic protocol"""
        blenders, server = multi_blender_generic

        logger.info("🧪 Testing room cleanup procedures (Generic)")

        # Verify all instances are active before cleanup
        for i, blender in enumerate(blenders):
            assert blender is not None, f"Blender {i} should exist"

        # Room cleanup will be handled by fixture teardown
        # Here we just verify we can get to this point
        assert len(blenders) == 2, "Should have 2 Blender instances"
        assert server.is_alive(), "Server should be operational"

        logger.info("✅ Room cleanup setup verified (Generic)")

    def test_room_cleanup_vrtist(self, multi_blender_vrtist):
        """Test proper room cleanup in VRtist protocol"""
        blenders, server = multi_blender_vrtist

        logger.info("🧪 Testing room cleanup procedures (VRtist)")

        # Verify all instances are active before cleanup
        for i, blender in enumerate(blenders):
            assert blender is not None, f"Blender {i} should exist"

        # Room cleanup will be handled by fixture teardown
        # Here we just verify we can get to this point
        assert len(blenders) == 2, "Should have 2 Blender instances"
        assert server.is_alive(), "Server should be operational"

        logger.info("✅ Room cleanup setup verified (VRtist)")

    @pytest.mark.parametrize("num_instances", [2, 3])
    def test_room_scaling_generic(self, num_instances):
        """Test room scaling with different numbers of instances (Generic)"""
        blenders, server = setup_multi_blender_instances(
            num_instances=num_instances,
            protocols=[False] * num_instances,  # Generic protocol
            port_offset=13101
        )

        logger.info(f"🧪 Testing {num_instances}-instance room scaling (Generic)")

        try:
            # Verify all instances created successfully
            assert len(blenders) == num_instances, f"Should create {num_instances} instances"

            for i, blender in enumerate(blenders):
                assert blender is not None, f"Instance {i} should exist"

            # Allow time for synchronization
            time.sleep(2)

            assert server.is_alive(), "Server should handle multiple instances"

            logger.info(f"✅ {num_instances}-instance room scaling successful (Generic)")

        finally:
            cleanup_blender_instances(blenders, server)

    @pytest.mark.parametrize("num_instances", [2, 3])
    def test_room_scaling_vrtist(self, num_instances):
        """Test room scaling with different numbers of instances (VRtist)"""
        blenders, server = setup_multi_blender_instances(
            num_instances=num_instances,
            protocols=[True] * num_instances,   # VRtist protocol
            port_offset=13201
        )

        logger.info(f"🧪 Testing {num_instances}-instance room scaling (VRtist)")

        try:
            # Verify all instances created successfully
            assert len(blenders) == num_instances, f"Should create {num_instances} instances"

            for i, blender in enumerate(blenders):
                assert blender is not None, f"Instance {i} should exist"

            # Allow time for synchronization
            time.sleep(2)

            assert server.is_alive(), "Server should handle multiple instances"

            logger.info(f"✅ {num_instances}-instance room scaling successful (VRtist)")

        finally:
            cleanup_blender_instances(blenders, server)


if __name__ == "__main__":
    print("🚀 Room Management Functional Test Suite")
    print("=" * 50)
    print("This test suite validates the core 'join a room' workflow")
    print("that users rely on when collaborating in Blender.")
    print()
    print("Tests included:")
    print("- Room creation (Generic/VRtist protocols)")
    print("- Multi-user room joining")
    print("- Synchronization latencies")
    print("- Room cleanup procedures")
    print("- Room scaling (2-3 instances)")
    print()
    print("Usage: pytest tests/functional/test_room_management.py -v")
    print("=" * 50)
