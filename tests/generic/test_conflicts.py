"""
VRtist conflicts tests - converted to natural pytest format
Tests for conflicting operations that are sensitive to network timings,
for instance rename a collection on one side and add to collection on the other side.

Such conflits need a server with throttling control to reproduce the problem reliably.

"""
import time
import pytest
import unittest

from mixer.broadcaster.common import MessageType

from tests import files_folder
import tests.blender_snippets as bl
from tests.blender.blender_testcase import BlenderTestCase
from tests.mixer_testcase import BlenderDesc


@pytest.fixture
def generic_throttled_instances():
    """Provide VRtist test instances with throttling setup (Pattern 4 Fix: Legacy Method Remnants)"""
    from tests.vrtist.vrtist_testcase import VRtistTestCase
    from tests.blender.blender_testcase import BlenderTestCase

    try:
        file = files_folder() / "file2.blend"
        blenderdesc = BlenderDesc(load_file=file)
        blenderdescs = [blenderdesc, BlenderDesc()]

        # Create VRtist test instance
        vrtist_test = VRtistTestCase()
        vrtist_test.sender = BlenderTestCase()
        vrtist_test.receiver = BlenderTestCase()

        # Setup BlenderDescs
        vrtist_test.sender.blenderdescs = blenderdescs
        vrtist_test.receiver.blenderdescs = blenderdescs
        vrtist_test.vrtist_protocol = False
        vrtist_test.latency = 1

        # CRITICAL: Initialize _blenders list that VRtistTestCase._sender property depends on
        vrtist_test._blenders = [vrtist_test.sender, vrtist_test.receiver]

        yield vrtist_test

    except Exception as e:
        pytest.fail(f"Failed to setup throttled test instances: {e}")
    finally:
        # Cleanup
        pass  # VRtist instances have complex cleanup that requires proper server shutdown


def test_empty_unlinked(generic_throttled_instances):
    """Test creating unlinked empty objects"""
    instance = generic_throttled_instances

    empties = 2
    scenes = 1
    instance.expected_counts = {MessageType.BLENDER_DATA_CREATE: empties + scenes}

    create_empty = bl.data_objects_new("Empty", None)
    instance.send_strings([create_empty], to=0)
    time.sleep(0.0)
    instance.send_strings([create_empty], to=1)

    # Custom assert matches for throttled timing
    time.sleep(4 * instance.latency)
    instance.assert_matches()


def test_empty_unlinked_many(generic_throttled_instances):
    """Test creating many unlinked empty objects"""
    instance = generic_throttled_instances

    empties = 2 * 5
    scenes = 1
    instance.expected_counts = {MessageType.BLENDER_DATA_CREATE: empties + scenes}

    create_empty = bl.data_objects_new("Empty", None)
    create_empties = [create_empty] * 5
    instance.send_strings(create_empties, to=0)
    time.sleep(0.0)
    instance.send_strings(create_empties, to=1)

    # Custom assert matches for throttled timing
    time.sleep(4 * instance.latency)
    instance.assert_matches()


@pytest.mark.parametrize("vrtist_protocol", [False])
def test_object_in_master_collection(generic_throttled_instances, vrtist_protocol):
    """Test creating objects in master collection"""
    instance = generic_throttled_instances
    instance.vrtist_protocol = vrtist_protocol

    command = """
import bpy
viewlayer = bpy.data.scenes["Scene"].view_layers["View Layer"]
viewlayer.active_layer_collection = viewlayer.layer_collection
bpy.ops.object.light_add(type="POINT", location=({location}))
"""

    command_0 = command.format(location="0.0, -3.0, 0.0")
    instance.send_string(command_0, to=0)
    time.sleep(0.0)
    command_1 = command.format(location="0.0, 3.0, 0.0")
    instance.send_string(command_1, to=1)

    # Custom assert matches for throttled timing
    time.sleep(4 * instance.latency)
    instance.assert_matches()


@pytest.mark.parametrize("vrtist_protocol", [False])
def test_collection_master_rename_conflicts(generic_throttled_instances, vrtist_protocol):
    """Test collection operations with master rename conflicts"""
    instance = generic_throttled_instances
    instance.vrtist_protocol = vrtist_protocol

    # Scene cleanup
    cleanup_scenes = """
import bpy
if "Scene.001" in bpy.data.scenes:
    bpy.data.scenes.remove(bpy.data.scenes["Scene.001"])
"""
    instance.send_string(cleanup_scenes, to=0)

    # Test various conflict scenarios
    conflict_scenarios = [
        {
            "name": "add_object_vs_rename",
            "command_0": """\
import bpy
light = bpy.data.lights.new(name="point", type="POINT")
obj = bpy.data.objects.new("point", light)
bpy.data.collections["Collection1"].objects.link(obj)
""",
            "command_1": """\
import bpy
bpy.data.collections["Collection1"].name = "C1_renamed"
"""
        },
        {
            "name": "unlink_vs_rename",
            "command_0": """\
import bpy
obj = bpy.data.objects["EmptyInCollection1"]
bpy.data.collections["Collection1"].objects.unlink(obj)
""",
            "command_1": """\
import bpy
bpy.data.collections["Collection1"].name = "Collection1_renamed"
"""
        },
        {
            "name": "same_rename",
            "command_0": """\
import bpy
bpy.data.collections["Collection1"].name = "Collection1_renamed"
""",
            "command_1": """\
import bpy
bpy.data.collections["Collection1"].name = "Collection1_renamed"
"""
        }
    ]

    for scenario in conflict_scenarios:
        # Reset expected counts
        if vrtist_protocol:
            instance.expected_counts = {MessageType.TRANSFORM: 2}
        else:
            instance.expected_counts = {MessageType.BLENDER_DATA_CREATE: 2}

        instance.send_string(scenario["command_0"], to=0)
        instance.send_string(scenario["command_1"], to=1)
        time.sleep(4 * instance.latency)
        instance.assert_matches()


@pytest.mark.parametrize("vrtist_protocol", [False, True])
def test_object_scene_rename_conflicts(vrtist_throttled_instances, vrtist_protocol):
    """Test object rename conflicts with scene operations"""
    instance = vrtist_throttled_instances
    instance.vrtist_protocol = vrtist_protocol

    # Scene cleanup
    cleanup_scenes = """
import bpy
if "Scene.001" in [s.name for s in bpy.data.scenes]:
    bpy.data.scenes.remove(bpy.data.scenes["Scene.001"])
"""
    instance.send_string(cleanup_scenes, to=0)

    rename_object = """
import bpy
bpy.data.objects["A"].name = "B"
"""
    update_location = """
import bpy
bpy.data.objects["B"].location[1] = 2.
"""

    instance.send_string(rename_object, to=0)
    time.sleep(0.0)
    instance.send_string(update_location, to=1)
    time.sleep(1.0)

    # Custom assert matches for throttled timing
    time.sleep(4 * instance.latency)
    instance.assert_matches()


@pytest.mark.parametrize("vrtist_protocol", [False, True])
def test_scene_operations_conflicts(vrtist_throttled_instances, vrtist_protocol):
    """Test scene operations that cause naming conflicts"""
    instance = vrtist_throttled_instances
    instance.vrtist_protocol = vrtist_protocol

    # Scene cleanup
    cleanup_scenes = """
import bpy
for scene in list(bpy.data.scenes):
    if scene.name != "Scene":
        bpy.data.scenes.remove(scene)
"""
    instance.send_string(cleanup_scenes, to=0)

    # Test scene rename operations
    add_light_command = [bl.active_layer_master_collection(), bl.ops_objects_light_add()]
    rename_scene_command = [bl.data_scenes_rename("Scene", "Scene_renamed")]
    add_collection_command = [bl.data_collections_new("new_collection"), bl.scene_collection_children_link("new_collection")]
    update_scene_command = [bl.data_scenes_rename("Scene", "Scene_renamed2"), bl.trigger_scene_update("Scene_renamed2")]

    instance.send_strings(add_light_command, to=0)
    time.sleep(0.0)
    instance.send_strings(rename_scene_command, to=1)

    # Custom assert matches for throttled timing
    time.sleep(4 * instance.latency)
    instance.assert_matches()

    # Test add collection while scene is being renamed
    instance.send_strings(add_collection_command, to=0)
    time.sleep(0.0)
    instance.send_strings(update_scene_command, to=1)

    # Custom assert matches for throttled timing
    time.sleep(4 * instance.latency)
    instance.assert_matches()


if __name__ == "__main__":
    pytest.main([__file__])
