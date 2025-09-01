import pytest
from tests.conftest import BlenderTestMixin


@pytest.fixture
def blender_instances():
    """Provide standard Blender instances for proxy tests"""
    return BlenderTestMixin()


def force_sync(instance):
    """Helper function to force synchronization"""
    action = """
import bpy
bpy.data.scenes[0].use_gravity = not bpy.data.scenes[0].use_gravity
"""
    instance.send_string(action)
    return instance


def test_just_join(blender_instances):
    """Test basic joining without modifications"""
    instance = blender_instances
    instance.end_test()


def test_duplicate_uuid_metaball(blender_instances):
    """Test duplicate UUID handling with metaballs"""
    # with metaballs the effect of duplicate uuids is visible as they are not
    # handled by the VRtist protocol
    instance = blender_instances

    action = """
import bpy
bpy.ops.object.metaball_add(type='BALL', location=(0,0,0))
obj = bpy.context.active_object
"""
    instance.send_string(action)

    action = """
import bpy
D = bpy.data
bpy.ops.object.duplicate()
bpy.ops.transform.translate(value=(0, 4, 0))
"""
    instance.send_string(action)

    force_sync(instance)
    instance.end_test()


# Struct Collection Proxy Tests
def test_light_falloff_curve_add_point(blender_instances):
    """Test adding points to light falloff curve"""
    instance = blender_instances

    action = """
import bpy
bpy.ops.object.light_add(type='POINT')
"""
    instance.send_string(action)

    # HACK it seems that we do not receive the depsgraph update
    # for light.falloff_curve.curves[0].points so add a Light member update

    action = """
import bpy
light = bpy.data.lights['Point']
light.falloff_curve.curves[0].points.new(0.5, 0.5)
light.distance = 20
"""
    instance.send_string(action)
    instance.end_test()


def test_scene_render_view_add_remove(blender_instances):
    """Test adding and removing scene render views"""
    instance = blender_instances

    action = """
import bpy
views = bpy.data.scenes[0].render.views
bpy.ops.scene.render_view_add()
index = views.active_index
views[2].use = False
views.remove(views[0])
"""
    instance.send_string(action)
    instance.end_test()


@pytest.mark.skip(reason="see internal issue #298")
def test_scene_color_management_curve(blender_instances):
    """Test scene color management curve modifications"""
    instance = blender_instances

    action = """
import bpy
settings = bpy.data.scenes[0].view_settings
settings.use_curve_mapping = True
rgb = settings.curve_mapping.curves[3]
points = rgb.points
points.new(0.2, 0.8)
points.new(0.7, 0.3)
"""
    instance.send_string(action)
    instance.end_test()
