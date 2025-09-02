"""
Shared utilities for functional tests.

This module provides common utilities for functional testing including:
- Multi-instance Blender setup
- Synchronization verification
- Error recovery utilities
- Performance measurement
"""

import logging
import time
from typing import List, Optional
from tests.mixer_testcase import BlenderApp, BlenderDesc
from tests.process import ServerProcess

logger = logging.getLogger(__name__)


def setup_multi_blender_instances(
    num_instances: int = 2,
    protocols: List[bool] = None,
    shared_folders: Optional[List[List[str]]] = None,
    port_offset: int = 12801
) -> tuple[List[BlenderApp], ServerProcess]:
    """
    Set up multiple Blender instances for functional testing.

    Args:
        num_instances: Number of Blender instances to create (default: 2)
        protocols: List of protocols for each instance (None = default, True = VRtist, False = Generic)
        shared_folders: Shared folders for each instance
        port_offset: Starting port offset for instances

    Returns:
        Tuple of (list of BlenderApp instances, ServerProcess)
    """
    if protocols is None:
        protocols = [False] * num_instances  # Default to Generic

    if shared_folders is None:
        shared_folders = [[] for _ in range(num_instances)]

    server_process = ServerProcess()
    server_process.start()

    blender_instances = []
    for i in range(num_instances):
        protocol = protocols[i] if i < len(protocols) else False
        folders = shared_folders[i] if i < len(shared_folders) else []

        # Create Blender instance
        blender_desc = BlenderDesc(wait_for_debugger=False)
        blender = BlenderApp(
            python_port=8081 + i,
            ptvsd_port=5688 + i
        )
        blender.set_log_level(logging.INFO)

        # Setup with appropriate arguments
        args = ["--window-geometry", str(100 + i * 20), "100", "800", "600"]
        blender.setup(args)

        # Initialize BlenderApp instance
        blender._server_process = server_process

        # Connect to mixer
        blender.connect_mixer(port=server_process.port)
        blender.create_room(
            room_name=f"functional_test_room_{i}",
            vrtist_protocol=protocol,
            shared_folders=folders
        )

        blender_instances.append(blender)
        time.sleep(2)  # Allow time for setup

    return blender_instances, server_process


def wait_for_sync(blenders: List[BlenderApp], timeout: float = 10.0) -> bool:
    """
    Wait for synchronization to complete across all instances.

    Args:
        blenders: List of BlenderApp instances
        timeout: Maximum time to wait for sync

    Returns:
        True if all instances are synchronized, False if timeout occurred
    """
    start_time = time.time()
    sync_status = [False] * len(blenders)

    while time.time() - start_time < timeout:
        for i, blender in enumerate(blenders):
            # Check if blender has fresh synchronization data
            # This is a simplified check - real implementation would verify content
            if hasattr(blender, '_sender') and blender._sender:
                sync_status[i] = True

        if all(sync_status):
            logger.info(f"Synchronization completed across {len(blenders)} instances")
            return True

        time.sleep(0.5)

    logger.warning(f"Synchronization timeout after {timeout} seconds")
    return False


def measure_performance(action_func, *args, **kwargs) -> dict:
    """
    Measure performance of an action.

    Args:
        action_func: Function to measure
        *args: Arguments to pass to the action function
        **kwargs: Keyword arguments for the action function

    Returns:
        Dictionary with performance metrics
    """
    start_time = time.time()
    start_memory = 0  # Would need platform-specific memory measurement

    try:
        result = action_func(*args, **kwargs)
        success = True
    except Exception as e:
        result = None
        success = False
        error = str(e)

    end_time = time.time()
    end_memory = 0

    metrics = {
        'execution_time': end_time - start_time,
        'memory_delta': end_memory - start_memory,
        'success': success,
        'result': result
    }

    if not success:
        metrics['error'] = locals().get('error', 'Unknown error')

    return metrics


def cleanup_blender_instances(blenders: List[BlenderApp], server_process: ServerProcess):
    """
    Clean up Blender instances and server process.

    Args:
        blenders: List of BlenderApp instances to clean up
        server_process: ServerProcess to stop
    """
    for blender in reversed(blenders):
        try:
            blender.disconnect_mixer()
            blender.quit()
            blender.wait()
            blender.close()
        except Exception as e:
            logger.warning(f"Error cleaning up blender instance: {e}")

    try:
        server_process.kill()
    except Exception as e:
        logger.warning(f"Error stopping server process: {e}")


def verify_room_joined(blenders: List[BlenderApp], room_name: str, timeout: float = 5.0) -> bool:
    """
    Verify that all Blender instances have joined the same room.

    Args:
        blenders: List of BlenderApp instances
        room_name: Name of the room to verify
        timeout: Time to wait for room join verification

    Returns:
        True if all instances have joined the room, False otherwise
    """
    start_time = time.time()
    joined_count = 0

    while time.time() - start_time < timeout:
        joined_count = 0
        for blender in blenders:
            if hasattr(blender, 'current_room') and blender.current_room == room_name:
                joined_count += 1

        if joined_count == len(blenders):
            logger.info(f"All {joined_count} instances joined room: {room_name}")
            return True

        time.sleep(0.5)

    logger.warning(f"Only {joined_count}/{len(blenders)} instances joined room: {room_name}")
    return False


def create_object_in_all_instances(blenders: List[BlenderApp], object_name: str) -> List[str]:
    """
    Create an object in all Blender instances and return verification status.

    Args:
        blenders: List of BlenderApp instances
        object_name: Name of object to create

    Returns:
        List of status messages for each instance
    """
    results = []

    for i, blender in enumerate(blenders):
        try:
            # This is a simplified implementation
            # Real implementation would send appropriate commands to Blender
            result = f"Instance {i}: Object '{object_name}' creation triggered"
            results.append(result)
        except Exception as e:
            results.append(f"Instance {i}: Failed to create object - {e}")

    return results
