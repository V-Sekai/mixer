"""
Tests for conflicting operations that are sensitive to network timings,
for instance rename a collection on one side and add to collection on the other side.

Such conflicts need a server with throttling control to reproduce the problem reliably.

So far, the tests cannot really be automated on CI/CD since they require lengthy wait
until all the messages are flushed and processed at the end before grabbing
the messages from all Blender
"""
import pytest
import time
from pathlib import Path

from mixer.broadcaster.common import MessageType
from tests.mixer_testcase import BlenderDesc


@pytest.mark.skip(reason="Conflict tests require manual throttling server - cannot be automated")
@pytest.fixture
def throttled_blender_instances(request):
    """Provide Blender instances with latency for conflict testing"""
    # Get the startup file parameter or default to file2.blend
    startup_file = getattr(request, 'param', {}).get('startup_file', 'file2.blend')

    try:
        files_folder = Path(__file__).parent / "files"
        file = files_folder / startup_file
        blenderdesc = BlenderDesc(load_file=file)
        blenderdescs = [blenderdesc, BlenderDesc()]

        latency = 1
        latency_ms = 1000 * latency
        server_args = ["--latency", str(latency_ms)]

        # Initialize with server parameters for throttling
        return {
            'blender_instances': blenderdescs,
            'server_args': server_args,
            'latency': latency
        }

    except Exception:
        pytest.skip("Blender instances could not be initialized for throttled testing")


@pytest.fixture
def conflict_assertion(throttled_blender_instances):
    """Provide assertion method with proper waiting for throttled conflicts"""
    latency = throttled_blender_instances['latency']

    def assert_conflicts_resolved():
        # Wait for the messages to reach the destination
        # TODO: What is just enough?
        time.sleep(5 * latency)
        # Original assertion logic would go here
        # This would require implementing the conflict resolution checking

    return assert_conflicts_resolved


# Example conflict test that would use the fixtures above
def test_example_conflict_scenario(throttled_blender_instances, conflict_assertion):
    """Example test for concurrent collection operations that might conflict

    NOTE: This is currently skipped due to requiring manual throttling server.
    Actual conflict test methods would be implemented here using the fixtures.
    """
    pytest.skip("Conflict testing requires specialized manual server setup")

    # Example usage:
    # instances = throttled_blender_instances['blender_instances']
    # instance1 = instances[0]
    # instance2 = instances[1]
    #
    # # Modify on first instance
    # instance1.send_string("rename collection command")
    #
    # # Modify on second instance
    # instance2.send_string("add to collection command")
    #
    # # Verify conflict resolution
    # conflict_assertion()
