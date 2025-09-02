"""
VRtist scene tests - converted to natural pytest format
"""
import pytest

from mixer.broadcaster.common import MessageType

from tests import files_folder
from tests.mixer_testcase import BlenderDesc
from tests.vrtist.vrtist_testcase import VRtistTestCase


@pytest.fixture(params=[False], ids=['Generic'])
def generic_scene_instances(request):
    """Provide VRtist test instances for scene tests"""
    from tests.vrtist.vrtist_testcase import VRtistTestCase
    import socket

    # Use different server ports to avoid conflicts between parameterized tests
    base_port = 12900
    port_offset = 1 if request.param else 0  # Generic gets port_offset 1, VRtist gets 0

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

        # Create VRtist test instance and perform proper Blender setup
        vrtist_test = VRtistTestCase()

        # CRITICAL: Perform the Blender setup that initializes _blenders with actual BlenderApp instances
        vrtist_test.setup_method(None, blenderdescs=blenderdescs, server_args=["--port", str(server_port)])

        # Initialize additional attributes needed for vrtist tests
        vrtist_test.vrtist_protocol = request.param
        vrtist_test.ignored_messages = set()
        vrtist_test.expected_counts = {}

        yield vrtist_test

    except Exception as e:
        pytest.fail(f"Failed to setup scene test instances: {e}")
    finally:
        # Cleanup
        if hasattr(vrtist_test, 'shutdown'):
            vrtist_test.shutdown()
        import gc
        gc.collect()


# Scene-related tests starting with an "empty" document
def test_create_scene(generic_scene_instances):
    """Test scene creation operations"""
    instance = generic_scene_instances
    instance.vrtist_protocol = False

    instance.new_scene("scene_1")
    instance.new_scene("scene_2")
    # temporary : create an object since update_post is not called after scene creation
    instance.new_object("object_0_0")

    instance.expected_counts = {MessageType.SCENE: 3}
    instance.flush_collections()
    instance.assert_matches()


def test_link_collection_to_scene(generic_scene_instances):
    """Test linking collections to scenes"""
    instance = generic_scene_instances
    instance.vrtist_protocol = False

    instance.new_collection("collection_0_0")
    instance.link_collection_to_scene("Scene", "collection_0_0")
    instance.remove_scene("Scene")
    instance.new_collection("collection_1_0")
    instance.new_collection("collection_1_1")
    instance.link_collection_to_scene("Scene", "collection_1_0")
    instance.link_collection_to_scene("Scene", "collection_1_1")

    instance.expected_counts = {MessageType.ADD_COLLECTION_TO_SCENE: 3}
    instance.flush_collections()
    instance.assert_matches()


def test_unlink_collection_from_scene(generic_scene_instances):
    """Test unlinking collections from scenes"""
    instance = generic_scene_instances
    instance.vrtist_protocol = False

    instance.new_collection("UNLINKED_collection_1_0")
    instance.new_collection("LINKED_collection_1_1")
    instance.link_collection_to_scene("Scene", "UNLINKED_collection_1_0")
    instance.link_collection_to_scene("Scene", "LINKED_collection_1_1")
    instance.unlink_collection_from_scene("Scene", "UNLINKED_collection_1_0")

    instance.expected_counts = {MessageType.ADD_COLLECTION_TO_SCENE: 1}
    instance.flush_collections()
    instance.assert_matches()


def test_link_object_to_scene(generic_scene_instances):
    """Test linking objects to scenes"""
    instance = generic_scene_instances
    instance.vrtist_protocol = False

    instance.new_object("object_0_0")
    instance.link_object_to_scene("Scene", "object_0_0")
    instance.new_object("object_1_0")
    instance.new_object("object_1_1")
    instance.link_object_to_scene("Scene", "object_1_0")
    instance.link_object_to_scene("Scene", "object_1_1")
    instance.expected_counts = {MessageType.ADD_OBJECT_TO_SCENE: 3}
    instance.flush_collections()
    instance.assert_matches()


def test_link_object_to_scene_and_collection(generic_scene_instances):
    """Test linking objects to both scenes and collections"""
    instance = generic_scene_instances
    instance.vrtist_protocol = False

    instance.new_object("object")
    instance.link_object_to_scene("Scene", "object")
    instance.new_collection("collection")
    instance.link_collection_to_scene("Scene", "collection")
    instance.link_object_to_collection("collection", "object")
    instance.flush_collections()
    instance.assert_matches()


def test_unlink_object_from_scene(generic_scene_instances):
    """Test unlinking objects from scenes"""
    instance = generic_scene_instances
    instance.vrtist_protocol = False

    instance.new_object("UNLINKED_object_1_0")
    instance.new_object("LINKED_object_1_1")

    instance.link_object_to_scene("Scene", "UNLINKED_object_1_0")
    instance.link_object_to_scene("Scene", "LINKED_object_1_1")
    instance.unlink_object_from_scene("Scene", "UNLINKED_object_1_0")
    instance.expected_counts = {
        MessageType.REMOVE_OBJECT_FROM_SCENE: 0,
        MessageType.ADD_OBJECT_TO_SCENE: 1,
    }
    instance.flush_collections()
    instance.assert_matches()


def test_rename_object_in_scene(generic_scene_instances):
    """Test renaming objects within scenes"""
    instance = generic_scene_instances
    instance.vrtist_protocol = False

    instance.new_object("object_1_0")
    instance.new_object("OLD_object_1_1")

    instance.link_object_to_scene("Scene", "object_1_0")
    instance.link_object_to_scene("Scene", "OLD_object_1_1")
    instance.rename_object("OLD_object_1_1", "NEW_object_1_1")

    instance.expected_counts = {MessageType.ADD_OBJECT_TO_SCENE: 2}
    instance.flush_collections()
    instance.assert_matches()


def test_rename_collection_in_scene(generic_scene_instances):
    """Test renaming collections within scenes"""
    instance = generic_scene_instances
    instance.vrtist_protocol = False

    instance.new_collection("collection_1_0")
    instance.new_collection("OLD_collection_1_1")

    instance.link_collection_to_scene("Scene", "collection_1_0")
    instance.link_collection_to_scene("Scene", "OLD_collection_1_1")
    instance.rename_collection("OLD_collection_1_1", "NEW_collection_1_1")
    instance.expected_counts = {
        MessageType.ADD_COLLECTION_TO_SCENE: 2,
    }

    instance.flush_collections()
    instance.assert_matches()


if __name__ == "__main__":
    pytest.main([__file__])
