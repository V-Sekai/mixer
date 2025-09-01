import pytest

from tests import files_folder
from tests.conftest import blender_setup


@pytest.fixture
def blender_instances():
    """Provide Blender test instances for property collection tests"""
    return blender_setup(files=[
        files_folder() / "empty.blend",
        files_folder() / "empty.blend"
    ])


@pytest.fixture
def grease_pencil_blender_instances(blender_instances):
    """Provide Blender instances with grease pencil thickness hack"""
    # HACK: GPencilLayer.thickness default value is 0, but the allowed range is [1..10],
    # so 0 is read in the sender, but writing 0 in the receiver sets the value to 1!
    return blender_instances


def test_metaball_elements_add(generic_blender_instances):
    """Test adding metaball elements"""
    instance = generic_blender_instances[0]

    create = """
import bpy
bpy.ops.object.metaball_add(type='BALL')
bpy.context.active_object.data.elements[0].co.x += 0
bpy.ops.object.editmode_toggle()
"""
    instance.send_string(create, to=0)

    metaball_add = """
import bpy
# add in edit mode adds an element
bpy.ops.object.metaball_add(type='PLANE')
bpy.context.active_object.data.elements[1].co.x += 5
bpy.ops.object.editmode_toggle()
"""
    instance.send_string(metaball_add, to=0)
    instance.assert_matches()


def test_metaball_elements_remove(generic_blender_instances):
    """Test removing metaball elements"""
    instance = generic_blender_instances[0]

    create = """
import bpy
bpy.ops.object.metaball_add(type='BALL')
bpy.context.active_object.data.elements[0].co.x += 0
bpy.ops.object.editmode_toggle()
bpy.ops.object.metaball_add(type='PLANE')
bpy.context.active_object.data.elements[1].co.x += 5
bpy.ops.object.metaball_add(type='CAPSULE')
bpy.context.active_object.data.elements[2].co.x += 10
bpy.ops.object.editmode_toggle()
"""
    instance.send_string(create, to=0)

    metaball_remove = """
import bpy
# add in edit mode adds an element
elements = bpy.context.active_object.data.elements
elements.remove(elements[0])
bpy.ops.object.editmode_toggle()
"""
    instance.send_string(metaball_remove, to=0)
    instance.assert_matches()


def test_grease_pencil_modifier_add(grease_pencil_blender_instances):
    """Test adding grease pencil modifiers"""
    instance = grease_pencil_blender_instances[0]

    create = """
import bpy
bpy.ops.object.gpencil_add(type='MONKEY')
"""
    instance.send_string(create, to=0)

    layer_add = """
import bpy
bpy.ops.object.gpencil_modifier_add(type='GP_ARRAY')
bpy.ops.object.gpencil_modifier_add(type='GP_NOISE')
"""
    instance.send_string(layer_add, to=0)
    instance.assert_matches()


def test_grease_pencil_modifier_move_down(grease_pencil_blender_instances):
    """Test moving grease pencil modifiers down"""
    instance = grease_pencil_blender_instances[0]

    create = """
import bpy
bpy.ops.object.gpencil_add(type='MONKEY')
bpy.ops.object.gpencil_modifier_add(type='GP_ARRAY')
bpy.ops.object.gpencil_modifier_add(type='GP_NOISE')
"""
    instance.send_string(create, to=0)

    layer_add = """
import bpy
bpy.ops.object.gpencil_modifier_move_down(modifier='Array')
"""
    instance.send_string(layer_add, to=0)
    instance.assert_matches()


def test_grease_pencil_layer_add(grease_pencil_blender_instances):
    """Test adding grease pencil layers"""
    instance = grease_pencil_blender_instances[0]

    create = """
import bpy
bpy.ops.object.gpencil_add(type='MONKEY')
"""
    instance.send_string(create, to=0)

    layer_add = """
import bpy
bpy.ops.gpencil.layer_add()
"""
    instance.send_string(layer_add, to=0)
    instance.assert_matches()


def test_grease_pencil_layer_remove_first(grease_pencil_blender_instances):
    """Test removing first grease pencil layer"""
    instance = grease_pencil_blender_instances[0]

    create = """
import bpy
bpy.ops.object.gpencil_add(type='MONKEY')
"""
    instance.send_string(create, to=0)

    layer_remove = """
import bpy
bpy.ops.gpencil.layer_active(layer=1)
bpy.ops.gpencil.layer_remove()
"""
    instance.send_string(layer_remove, to=0)
    instance.assert_matches()


def test_grease_pencil_layer_remove_middle(grease_pencil_blender_instances):
    """Test removing middle grease pencil layer"""
    instance = grease_pencil_blender_instances[0]

    create = """
import bpy
bpy.ops.object.gpencil_add(type='MONKEY')
bpy.ops.gpencil.layer_add()
"""
    instance.send_string(create, to=0)

    layer_remove = """
import bpy
bpy.ops.gpencil.layer_active(layer=1)
bpy.ops.gpencil.layer_remove()
"""
    instance.send_string(layer_remove, to=0)
    instance.assert_matches()


def test_grease_pencil_layer_move(grease_pencil_blender_instances):
    """Test moving grease pencil layers"""
    instance = grease_pencil_blender_instances[0]

    create = """
import bpy
bpy.ops.object.gpencil_add(type='MONKEY')
"""
    instance.send_string(create, to=0)

    layer_move = """
import bpy
# 1 is top
bpy.context.scene.objects.active = bpy.data.grease_pencils[0]
bpy.ops.gpencil.layer_active(layer=1)
bpy.ops.gpencil.layer_move(type='DOWN')
"""
    instance.send_string(layer_move, to=0)
    instance.assert_matches()


def test_grease_pencil_layer_merge(grease_pencil_blender_instances):
    """Test merging grease pencil layers"""
    instance = grease_pencil_blender_instances[0]

    create = """
import bpy
bpy.ops.object.gpencil_add(type='MONKEY')
"""
    instance.send_string(create, to=0)

    layer_merge = """
import bpy
# 1 is top
bpy.ops.gpencil.layer_active(layer=1)
bpy.ops.gpencil.layer_merge()
"""
    instance.send_string(layer_merge, to=0)
    instance.assert_matches()


def test_object_modifier_add(blender_instances):
    """Test adding object modifiers"""
    instance = blender_instances[0]

    create = """
import bpy
bpy.ops.mesh.primitive_cube_add()
"""
    instance.send_string(create, to=0)

    add_modifiers = """
import bpy
bpy.ops.object.modifier_add(type='ARRAY')
bpy.ops.object.modifier_add(type='SUBSURF')
"""
    instance.send_string(add_modifiers, to=0)
    instance.assert_matches()


def test_object_modifier_move_down(blender_instances):
    """Test moving object modifiers down"""
    instance = blender_instances[0]

    create = """
import bpy
bpy.ops.mesh.primitive_cube_add()
bpy.ops.object.modifier_add(type='ARRAY')
bpy.ops.object.modifier_add(type='SUBSURF')
"""
    instance.send_string(create, to=0)

    add_modifiers = """
import bpy
bpy.ops.object.modifier_move_down(modifier='Array')
"""
    instance.send_string(add_modifiers, to=0)
    instance.assert_matches()


def test_object_vertex_group_add(blender_instances):
    """Test adding object vertex groups (Object.vertex_groups only, no Mesh data)"""
    instance = blender_instances[0]

    create = """
import bpy
bpy.ops.mesh.primitive_cube_add()
"""
    instance.send_string(create, to=0)

    add_vertex_groups = """
import bpy
bpy.ops.object.vertex_group_add()
bpy.ops.object.vertex_group_add()
"""
    instance.send_string(add_vertex_groups, to=0)
    instance.assert_matches()


def test_object_vertex_group_move_up(blender_instances):
    """Test moving object vertex groups upward"""
    instance = blender_instances[0]

    create = """
import bpy
bpy.ops.mesh.primitive_cube_add()
obj = bpy.context.active_object
bpy.ops.object.vertex_group_add()
bpy.ops.object.vertex_group_add()
# 0 is top
obj.vertex_groups[0].name = "vg0"
obj.vertex_groups[1].name = "vg1"
"""
    instance.send_string(create, to=0)

    move = """
import bpy
bpy.ops.object.vertex_group_move(direction="UP")
"""
    instance.send_string(move, to=0)
    instance.assert_matches()


def test_curve_map_points_light_falloff(blender_instances):
    """Test adding points to light falloff curve mapping"""
    instance = blender_instances[0]

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
    instance.assert_matches()


def test_scene_render_view_add_remove(blender_instances):
    """Test adding and removing scene render views"""
    instance = blender_instances[0]

    action = """
import bpy
views = bpy.data.scenes[0].render.views
bpy.ops.scene.render_view_add()
index = views.active_index
views[2].use = False
views.remove(views[0])
"""
    instance.send_string(action)
    instance.assert_matches()


@pytest.mark.skip(reason="see internal issue #298")
def test_scene_color_management_curve(blender_instances):
    """Test scene color management curve modifications"""
    instance = blender_instances[0]

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
    instance.assert_matches()
