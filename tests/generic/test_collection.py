"""
VRtist collection tests - converted to natural pytest format
"""
import pytest

from tests import files_folder
from tests.mixer_testcase import BlenderDesc


@pytest.fixture(params=[False], ids=['Generic'])
def generic_instances(request):
    """Provide VRtist test instances with basic Blender setup"""
    from tests.vrtist.vrtist_testcase import VRtistTestCase
    from tests.blender.blender_testcase import BlenderTestCase
    import socket

    # Use different server ports to avoid conflicts between parameterized tests
    base_port = 12800
    port_offset = 0 if request.param else 1

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
        sender_blendfile = files_folder() / "basic.blend"
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
        pytest.fail(f"Failed to setup vrtist instances: {e}")
    finally:
        # Cleanup
        if hasattr(vrtist_test, 'shutdown'):
            vrtist_test.shutdown()
        import gc
        gc.collect()


def test_nested_collections(generic_instances):
    """Test creating nested collection hierarchies"""
    instance = generic_instances

    instance.new_collection("plop")
    instance.link_collection_to_collection("Collection", "plop")
    instance.new_collection("plaf")
    instance.link_collection_to_collection("Collection", "plaf")
    instance.new_collection("sous_plop")
    instance.link_collection_to_collection("plop", "sous_plop")
    instance.new_collection("sous_plaf")
    instance.link_collection_to_collection("plaf", "sous_plaf")
    instance.assert_matches()


def test_collection_linked_twice(generic_instances):
    """Test collection linked to multiple parent collections"""
    instance = generic_instances

    instance.new_collection("C1")
    instance.new_collection("C2")
    instance.link_collection_to_collection("Collection", "C1")
    instance.link_collection_to_collection("Collection", "C2")
    instance.new_collection("CC")
    instance.link_collection_to_collection("C1", "CC")
    instance.link_collection_to_collection("C2", "CC")
    instance.assert_matches()


def test_collection_different_order(generic_instances):
    """Test collection creation in different order (regression test)"""
    instance = generic_instances

    instance.new_collection("plop")
    instance.link_collection_to_collection("Collection", "plop")
    instance.new_collection("plaf")
    instance.link_collection_to_collection("Collection", "plaf")
    # it used to fail in this order and work after collection rename
    # so keep the test
    instance.new_collection("sous_plaf")
    instance.link_collection_to_collection("plaf", "sous_plaf")
    instance.new_collection("sous_plop")
    instance.link_collection_to_collection("plop", "sous_plop")
    instance.assert_matches()


def test_collection_name_clash(generic_instances):
    """Test collection creation with name conflicts"""
    instance = generic_instances

    instance.create_collection_in_collection("Collection", "plop")
    instance.create_collection_in_collection("Collection", "Collection")
    instance.create_collection_in_collection("plop", "plop")
    instance.assert_matches()


def test_collection_objects(generic_instances):
    """Test creating objects within collections"""
    instance = generic_instances

    instance.create_object_in_collection("Collection", "new_object_0_0")
    instance.create_object_in_collection("Collection", "new_object_0_1")
    instance.create_collection_in_collection("Collection", "sub_collection_0")
    instance.create_object_in_collection("sub_collection_0", "new_object_0_2")
    instance.assert_matches()


def test_object_linked_to_collections(generic_instances):
    """Test object linked to multiple collections"""
    instance = generic_instances

    instance.new_collection("C1")
    instance.new_collection("C2")
    instance.link_collection_to_collection("Collection", "C1")
    instance.link_collection_to_collection("Collection", "C2")
    instance.new_object("OO")
    instance.link_object_to_collection("Collection", "OO")
    instance.link_object_to_collection("C1", "OO")
    instance.link_object_to_collection("C2", "OO")
    instance.assert_matches()


def test_unlink_objects_from_collection(generic_instances):
    """Test removing objects from collections"""
    instance = generic_instances

    instance.create_collection_in_collection("Collection", "sub_collection_1")
    instance.create_object_in_collection("Collection", "new_object_0_0")
    instance.create_object_in_collection("Collection", "new_object_0_1")
    instance.create_object_in_collection("sub_collection_1", "new_object_1_0")
    instance.create_object_in_collection("sub_collection_1", "new_object_1_1")

    instance.unlink_object_from_collection("Collection", "new_object_0_0")
    instance.unlink_object_from_collection("Collection", "new_object_0_1")
    instance.unlink_object_from_collection("sub_collection_1", "new_object_1_0")
    instance.unlink_object_from_collection("sub_collection_1", "new_object_1_1")
    instance.assert_matches()


def test_unlink_collections_from_collection(generic_instances):
    """Test removing collections from parent collections"""
    instance = generic_instances

    instance.create_collection_in_collection("Collection", "plaf0")
    instance.create_collection_in_collection("Collection", "plaf1")
    instance.unlink_collection_from_collection("Collection", "plaf0")
    instance.unlink_collection_from_collection("Collection", "plaf1")

    instance.remove_collection("plaf0")
    instance.remove_collection("plaf1")

    instance.create_collection_in_collection("Collection", "plaf1")
    instance.unlink_collection_from_collection("Collection", "plaf1")
    instance.assert_matches()


def test_collection_instances_after_join(generic_instances):
    """Test creating collection instances after joining"""
    instance = generic_instances

    instance.create_collection_in_collection("Collection", "src")
    instance.create_object_in_collection("src", "new_object_0_0")
    instance.create_collection_in_collection("Collection", "dst")
    instance.new_collection_instance("src", "src_instance_in_Collection")
    instance.new_collection_instance("src", "src_instance_in_dst")
    instance.link_object_to_collection("Collection", "src_instance_in_Collection")
    instance.link_object_to_collection("dst", "src_instance_in_dst")
    instance.assert_matches()


@pytest.mark.skip(reason="Timing problem - instances before join")
def test_collection_instances_before_join(generic_instances):
    """Test creating collection instances before joining - has timing issues"""
    instance = generic_instances

    # Disconnect and reconnect to test pre-join instance creation
    instance._sender.disconnect_mixer()
    instance._receiver.disconnect_mixer()

    instance.create_collection_in_collection("Collection", "src")
    instance.create_object_in_collection("src", "new_object_0_0")
    instance.create_collection_in_collection("Collection", "dst")
    instance.new_collection_instance("src", "src_instance_in_Collection")
    instance.new_collection_instance("src", "src_instance_in_dst")
    instance.link_object_to_collection("Collection", "src_instance_in_Collection")
    instance.link_object_to_collection("dst", "src_instance_in_dst")

    instance._sender.connect_and_join_mixer(vrtist_protocol=instance.vrtist_protocol)
    instance._receiver.connect_and_join_mixer(vrtist_protocol=instance.vrtist_protocol)
    instance.assert_matches()


def test_collection_rename(generic_instances):
    """Test renaming collections and their contents"""
    instance = generic_instances

    instance.create_collection_in_collection("Collection", "old_name")
    instance.create_object_in_collection("old_name", "object_0")
    instance.create_object_in_collection("old_name", "object_1")
    instance.create_collection_in_collection("old_name", "collection_0_old")
    instance.create_collection_in_collection("old_name", "collection_1_old")
    instance.create_object_in_collection("collection_0_old", "object_0_0")

    instance.rename_collection("collection_1_old", "collection_1_new")
    instance.rename_collection("old_name", "new_name")
    instance.rename_collection("collection_0_old", "collection_0_new")
    instance.assert_matches()


# Tests starting from empty Blend files
@pytest.fixture(params=[False], ids=['Generic'])
def generic_empty_instances(request):
    """Provide VRtist test instances with empty Blender setup"""
    from tests.vrtist.vrtist_testcase import VRtistTestCase
    import socket

    # Use different server ports to avoid conflicts between parameterized tests
    base_port = 13000
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
        pytest.fail(f"Failed to setup empty vrtist instances: {e}")
    finally:
        # Cleanup
        if hasattr(vrtist_test, 'shutdown'):
            vrtist_test.shutdown()
        import gc
        gc.collect()


def test_collection_rename_empty(generic_empty_instances):
    """Test collection renaming with depsgraph updates (empty file start)"""
    instance = generic_empty_instances

    # need to be linked to master collection in order to get depsgraph updates
    s = """
import bpy
c1 = bpy.data.collections.new("c1")
master = bpy.data.scenes[0].view_layers[0].layer_collection.collection
master.children.link(c1)
c2 = bpy.data.collections.new("c2")
c1.children.link(c2)
"""
    instance.send_string(s)

    s = """
import bpy
c1 = bpy.data.collections["c1"]
c1.name = "c1_updated"
"""
    instance.send_string(s)

    instance.assert_matches()


def test_rename_unlink_object_empty(generic_empty_instances):
    """Test renaming collection and unlinking object"""
    instance = generic_empty_instances

    s = """
import bpy
c1 = bpy.data.collections.new("c1")
master = bpy.data.scenes[0].view_layers[0].layer_collection.collection
master.children.link(c1)
c2 = bpy.data.collections.new("c2")
obj = bpy.data.objects.new("obj", None)
c1.children.link(c2)
c2.objects.link(obj)
"""
    instance.send_string(s)

    s = """
import bpy
c1 = bpy.data.collections["c1"]
c2 = bpy.data.collections["c2"]
obj = bpy.data.objects["obj"]
c1.name = "c1_updated"
c1.objects.unlink(obj)
"""
    instance.send_string(s)

    instance.assert_matches()


def test_rename_unlink_object_nested_empty(generic_empty_instances):
    """Test renaming nested collection and unlinking object"""
    instance = generic_empty_instances

    s = """
import bpy
c1 = bpy.data.collections.new("c1")
master = bpy.data.scenes[0].view_layers[0].layer_collection.collection
master.children.link(c1)
c2 = bpy.data.collections.new("c2")
obj = bpy.data.objects.new("obj", None)
c1.children.link(c2)
c2.objects.link(obj)
"""
    instance.send_string(s)

    s = """
import bpy
c2 = bpy.data.collections["c2"]
obj = bpy.data.objects["obj"]
c2.name = "c2_updated"
c2.objects.unlink(obj)
"""
    instance.send_string(s)

    # on receiver c2_updated exists but is not linked to c1
    instance.assert_matches()


def test_collection_unlink_empty(generic_empty_instances):
    """Test nested collection operations (empty setup)"""
    instance = generic_empty_instances

    s = """
import bpy
c1 = bpy.data.collections.new("c1")
c2 = bpy.data.collections.new("c2")
c3 = bpy.data.collections.new("c3")
c1.children.link(c2)
c2.children.link(c3)
"""
    instance.send_string(s)

    s = """
import bpy
c2 = bpy.data.collections["c2"]
c3 = bpy.data.collections["c3"]
c2.name = "c2_updated"
"""
    instance.send_string(s)


def test_complex_collection_operations_empty(generic_empty_instances):
    """Test complex collection and object operations"""
    instance = generic_empty_instances

    s = """
import bpy
master = bpy.data.scenes[0].view_layers[0].layer_collection.collection
c1 = bpy.data.collections.new("c1")
c2 = bpy.data.collections.new("c2")
c3 = bpy.data.collections.new("c3")
obj = bpy.data.objects.new("obj", None)
master.children.link(c1)
c1.children.link(c2)
c2.children.link(c3)
c2.objects.link(obj)
"""
    instance.send_string(s)

    s = """
import bpy
c2 = bpy.data.collections["c2"]
c3 = bpy.data.collections["c3"]
obj = bpy.data.objects["obj"]
c2.name = "c2_updated"
c2.objects.unlink(obj)
"""
    # obj is not unlinked on receiver
    instance.send_string(s)

    instance.assert_matches()
