"""
VRtist misc tests - converted to natural pytest format
"""
import unittest
import pytest

from mixer.broadcaster.common import MessageType

from tests import files_folder
from tests.vrtist.vrtist_testcase import VRtistTestCase
from tests.mixer_testcase import BlenderDesc
from tests import blender_snippets as bl


@pytest.fixture(params=[False, True], ids=['Generic', 'VRtist'])
def vrtist_misc_instances(request):
    """Provide VRtist test instances for misc tests (Pattern 4 Fix: Legacy Method Remnants)"""
    from tests.vrtist.vrtist_testcase import VRtistTestCase
    import socket

    # Use different server ports to avoid conflicts between parameterized tests
    base_port = 12800
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
        # Use unique server port to avoid conflicts
        vrtist_test.setup_method(None, blenderdescs=blenderdescs, server_args=["--port", str(server_port)])

        # Initialize additional attributes needed for vrtist tests
        vrtist_test.vrtist_protocol = request.param  # Use the parameterized value properly
        vrtist_test.ignored_messages = set()
        vrtist_test.expected_counts = {}

        yield vrtist_test

    except Exception as e:
        import pytest
        pytest.fail(f"Failed to setup misc test instances: {e}")
    finally:
        # Cleanup
        if hasattr(vrtist_test, 'shutdown'):
            vrtist_test.shutdown()
        import gc
        gc.collect()


# Tests for spontaneous renaming operations (fixture handles parameterization)
def test_spontaneous_rename_object_empty(vrtist_misc_instances):
    """Test spontaneous renaming with empty objects"""
    instance = vrtist_misc_instances
    # vrtist_protocol is now set in the fixture based on the parameterization

    instance.send_strings([bl.data_objects_new("Empty", None), bl.data_objects_new("Empty", None)], to=0)

    instance.send_strings([bl.data_objects_rename("Empty.001", "Empty")], to=0)
    instance.send_strings([bl.data_objects_rename("Empty.001", "Empty")], to=0)
    instance.send_strings([bl.data_objects_rename("Empty.001", "Empty")], to=0)
    instance.send_strings([bl.data_objects_rename("Empty.001", "Empty")], to=0)

    instance.send_strings([bl.data_objects_new("Another_empty", None)], to=0)

    instance.assert_matches()


def test_spontaneous_rename_light(vrtist_misc_instances):
    """Test spontaneous renaming with light objects"""
    instance = vrtist_misc_instances
    if instance.vrtist_protocol:
        import pytest
        pytest.skip("FAILS in VRtist mode")

    instance.send_strings([bl.ops_objects_light_add("POINT"), bl.ops_objects_light_add("POINT")], to=0)

    instance.send_strings([bl.data_objects_rename("Point.001", "Point")], to=0)
    instance.send_strings([bl.data_objects_rename("Point.001", "Point")], to=0)
    instance.send_strings([bl.data_objects_rename("Point.001", "Point")], to=0)

    instance.assert_matches()


def test_referenced_datablock_light(vrtist_misc_instances):
    """Test renaming datablock referenced by Object.data - light"""
    instance = vrtist_misc_instances

    if vrtist_protocol:
        pytest.skip("Broken in VRtist-only")

    instance.send_strings([bl.ops_objects_light_add("POINT")], to=0)
    instance.send_strings([bl.data_lights_rename("Point", "__Point")], to=0)
    instance.send_strings([bl.data_lights_update("__Point", ".energy = 0")], to=0)

    instance.assert_matches()


@pytest.mark.parametrize("vrtist_protocol", [False, True])
def test_referenced_datablock_material(vrtist_misc_instances, vrtist_protocol):
    """Test renaming datablock referenced by Object.data - material"""
    instance = vrtist_misc_instances
    instance.vrtist_protocol = vrtist_protocol

    if vrtist_protocol:
        pytest.skip("Broken in VRtist-only")

    instance.ignored_messages |= {MessageType.MATERIAL, MessageType.OBJECT_VISIBILITY}

    s = """
import bpy
mesh = bpy.data.meshes.new("mesh")
obj = bpy.data.objects.new("obj", mesh)
mat = bpy.data.materials.new("mat")
obj.active_material = mat
"""
    instance.send_string(s)
    instance.assert_matches()


@pytest.mark.parametrize("vrtist_protocol", [False, True])
def test_unresolved_ref_in_bpy_prop_collection(vrtist_misc_instances, vrtist_protocol):
    """Test unresolved references stored in bpy_prop_collection"""
    instance = vrtist_misc_instances
    instance.vrtist_protocol = vrtist_protocol

    instance.ignored_messages |= {MessageType.MATERIAL, MessageType.OBJECT_VISIBILITY}

    s = """
import bpy
a = bpy.data.collections.new("A")
b = bpy.data.collections.new("B")
c = bpy.data.collections.new("C")
a.children.link(c)
b.children.link(c)
"""
    instance.send_string(s)
    instance.assert_matches()


@pytest.mark.parametrize("vrtist_protocol", [False])
def test_rename_datablock_light(vrtist_misc_instances, vrtist_protocol):
    """Test renaming datablock referenced by Object.data - light (only Generic mode)"""
    instance = vrtist_misc_instances
    instance.vrtist_protocol = vrtist_protocol

    if vrtist_protocol:
        pytest.skip("Broken in VRtist-only")

    instance.send_strings([bl.ops_objects_light_add("POINT")], to=0)
    instance.send_strings([bl.data_lights_rename("Point", "__Point")], to=0)
    instance.send_strings([bl.data_lights_update("__Point", ".energy = 0")], to=0)

    instance.assert_matches()


@pytest.mark.parametrize("vrtist_protocol", [False, True])
def test_object_parent(vrtist_misc_instances, vrtist_protocol):
    """Test object parenting regardless of creation order"""
    instance = vrtist_misc_instances
    instance.vrtist_protocol = vrtist_protocol

    create = """
import bpy
scene = bpy.data.scenes[0]
obj0 = bpy.data.objects.new("obj0", None)
obj1 = bpy.data.objects.new("obj1", None)
obj2 = bpy.data.objects.new("obj2", None)
scene.collection.objects.link(obj0)
scene.collection.objects.link(obj1)
scene.collection.objects.link(obj2)
obj2.parent = obj0
obj0.parent = obj1
"""
    instance.send_string(create, to=0)
    instance.assert_matches()


@pytest.mark.parametrize("vrtist_protocol", [False, True])
def test_collection_children(vrtist_misc_instances, vrtist_protocol):
    """Test collection children creation and linking"""
    instance = vrtist_misc_instances
    instance.vrtist_protocol = vrtist_protocol

    create = """
import bpy
scene = bpy.data.scenes[0]
coll0 = bpy.data.collections.new("coll0")
coll1 = bpy.data.collections.new("coll1")
coll2 = bpy.data.collections.new("coll2")
scene.collection.children.link(coll1)
coll1.children.link(coll0)
coll0.children.link(coll2)
"""
    instance.send_string(create, to=0)
    instance.assert_matches()


@pytest.mark.parametrize("vrtist_protocol", [False, True])
def test_set_datablock_ref_from_none(vrtist_misc_instances, vrtist_protocol):
    """Test setting datablock reference from None"""
    instance = vrtist_misc_instances
    instance.vrtist_protocol = vrtist_protocol

    create = """
import bpy
scene = bpy.data.scenes[0]
obj0 = bpy.data.objects.new("obj0", None)
obj1 = bpy.data.objects.new("obj1", None)
scene.collection.objects.link(obj0)
scene.collection.objects.link(obj1)
"""
    instance.send_string(create, to=0)

    set_parent = """
import bpy
scene = bpy.data.scenes[0]
obj0 = bpy.data.objects["obj0"]
obj1 = bpy.data.objects["obj1"]
obj0.parent = obj1
"""
    instance.send_string(set_parent, to=0)
    instance.assert_matches()


@pytest.mark.parametrize("vrtist_protocol", [False, True])
def test_set_datablock_ref_to_none(vrtist_misc_instances, vrtist_protocol):
    """Test setting datablock reference to None"""
    instance = vrtist_misc_instances
    instance.vrtist_protocol = vrtist_protocol

    if vrtist_protocol:
        pytest.skip("Broken in VRtist-only")

    create = """
import bpy
scene = bpy.data.scenes[0]
obj0 = bpy.data.objects.new("obj0", None)
obj1 = bpy.data.objects.new("obj1", None)
scene.collection.objects.link(obj0)
scene.collection.objects.link(obj1)
obj0.parent = obj1
"""
    instance.send_string(create, to=0)

    remove_parent = """
import bpy
scene = bpy.data.scenes[0]
obj0 = bpy.data.objects["obj0"]
obj0.parent = None
"""
    instance.send_string(remove_parent, to=0)
    instance.assert_matches()


if __name__ == "__main__":
    pytest.main([__file__])
