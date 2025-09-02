
import pytest
from mixer.broadcaster.common import MessageType

from tests import files_folder
from tests.conftest import blender_setup


@pytest.fixture
def generic_blender_instances():
    """Provide generic Blender test setup with sender/receiver instances"""
    files = [
        str(files_folder() / "empty.blend"),
        str(files_folder() / "empty.blend")
    ]
    return blender_setup(files=files)


# MetaBall Tests
def test_metaball_new(generic_blender_instances):
    """Test creating new metaball data"""
    instance = generic_blender_instances[0]

    create_metaball = """
import bpy
name = "mb1"
mb = bpy.data.metaballs.new(name)
e1 = mb.elements.new(type="CAPSULE")
e1.co = (1, 1, 1)
e1.radius=3
e2 = mb.elements.new(type="BALL")
e2.co = (-1, -1, -1)
obj = bpy.data.objects.new(name, mb)
bpy.data.scenes[0].collection.objects.link(obj)
e2.type = "PLANE"
"""
    instance.send_string(create_metaball)
    instance.end_test()


def test_metaball_add(generic_blender_instances):
    """Test adding metaball objects via operators"""
    instance = generic_blender_instances[0]

    action = """
import bpy
bpy.ops.object.metaball_add(type='PLANE', location=(1.0, 1.0, 1.0))
o1 = bpy.context.active_object
bpy.ops.object.metaball_add(type='CAPSULE', location=(0.0, 0.0, 0.0))
bpy.ops.object.metaball_add(type='BALL', location=(-1.0, -1.0, -1.0))
"""
    instance.send_string(action)
    instance.end_test()


def test_metaball_add_remove(generic_blender_instances):
    """Test adding and removing metaball objects"""
    instance = generic_blender_instances[0]

    action = """
import bpy
bpy.ops.object.metaball_add(type='CAPSULE', location=(0.0, 0.0, 0.0))
bpy.ops.object.metaball_add(type='PLANE', location=(1.0, 1.0, 1.0))
bpy.ops.object.metaball_add(type='BALL', location=(-1.0, -1.0, -1.0))
"""
    instance.send_string(action)

    action = """
name = "Mball.001"
import bpy
D=bpy.data
D.objects.remove(D.objects[name])
D.metaballs.remove(D.metaballs[name])
"""
    instance.send_string(action)
    instance.end_test()


# Light Tests
def test_light_add_operators(generic_blender_instances):
    """Test adding different light types via operators"""
    instance = generic_blender_instances[0]

    action = """
import bpy
bpy.ops.object.light_add(type='POINT', location=(0.0, 0.0, 0.0))
bpy.ops.object.light_add(type='SUN', location=(2.0, 0.0, 0.0))
bpy.ops.object.light_add(type='AREA', location=(4.0, 0.0, 0.0))
"""
    instance.send_string(action)
    instance.end_test()


def test_light_change_area_attrs(generic_blender_instances):
    """Test modifying AREA light attributes"""
    instance = generic_blender_instances[0]

    action = """
import bpy
bpy.ops.object.light_add(type='AREA', location=(4.0, 0.0, 0.0))
"""
    instance.send_string(action)

    action = """
import bpy
D=bpy.data
area = D.lights["Area"]
area.size = 5
area.shape = 'DISK'
"""
    instance.send_string(action)
    instance.end_test()


def test_light_morph_types(generic_blender_instances):
    """Test changing light type and attributes"""
    instance = generic_blender_instances[0]

    action = """
import bpy
bpy.ops.object.light_add(type='POINT', location=(4.0, 0.0, 0.0))
"""
    instance.send_string(action)

    action = """
import bpy
D=bpy.data
light = D.lights["Point"]
light.type = "AREA"
light = light.type_recast()
light.shape = "RECTANGLE"
"""
    instance.send_string(action)
    instance.end_test()


# Scene Tests
@pytest.fixture
def scene_blender_instances():
    """Provide Blender instances with scene messages ignored for VRtist compatibility"""
    instances = blender_setup(files=[
        files_folder() / "empty.blend",
        files_folder() / "empty.blend"
    ])
    for instance in instances:
        if hasattr(instance, 'ignored_messages'):
            instance.ignored_messages |= {MessageType.SET_SCENE}
    return instances


def test_scene_new(scene_blender_instances):
    """Test creating new scenes"""
    instance = scene_blender_instances[0]

    action = """
import bpy
bpy.ops.scene.new(type="NEW")
# force update
scene = bpy.context.scene
scene.unit_settings.system = "IMPERIAL"
scene.use_gravity = True
"""
    instance.send_string(action)
    instance.end_test()


def test_scene_delete(scene_blender_instances):
    """Test deleting newly created scenes"""
    instance = scene_blender_instances[0]

    create = """
import bpy
bpy.ops.scene.new(type="NEW")
# force update
scene = bpy.context.scene
scene.use_gravity = True
"""
    instance.send_string(create)

    delete = """
import bpy
bpy.ops.scene.delete()
"""
    instance.send_string(delete)
    instance.end_test()


def test_scene_rename(scene_blender_instances):
    """Test renaming scenes"""
    instance = scene_blender_instances[0]

    create = """
import bpy
bpy.ops.scene.new(type="NEW")
# force update
scene = bpy.context.scene
scene.use_gravity = True
"""
    instance.send_string(create)

    rename = """
import bpy
scene = bpy.context.scene
scene.name = "new_name"
"""
    instance.send_string(rename)
    instance.end_test()


def test_scene_sequencer_create(scene_blender_instances):
    """Test creating scene sequencer effects"""
    instance = scene_blender_instances[0]

    action = """
import bpy
scene = bpy.context.scene
seq = scene.sequence_editor.sequences
s0 = seq.new_effect(type='COLOR', name='color1', channel=1, frame_start=1, frame_end=10)
s1 = seq.new_effect(type='COLOR', name='color2', channel=2, frame_start=10, frame_end=20)
# The value read by default (0.) cannot be written. Set to a valid value
s0.strobe = 1.0
s1.strobe = 1.0
"""
    instance.send_string(action)
    instance.end_test()


def test_scene_view_layer_add(scene_blender_instances):
    """Test adding new view layers to scene"""
    instance = scene_blender_instances[0]

    setup = """
import bpy
scene = bpy.context.scene
vl = scene.view_layers
# makes it possible to distinguish new view layers created with NEW
vl[0].pass_alpha_threshold = 0.0
"""
    instance.send_string(setup)

    create = """
import bpy
bpy.ops.scene.view_layer_add(type="NEW")
# force sync
scene = bpy.context.scene
vl = scene.view_layers
vl[1].pass_alpha_threshold = 0.1
"""
    instance.send_string(create)
    instance.end_test()


def test_scene_view_layer_rename(scene_blender_instances):
    """Test renaming view layers in scene"""
    instance = scene_blender_instances[0]

    setup = """
import bpy
scene = bpy.context.scene
vl = scene.view_layers
# makes it possible to distinguish new view layers created with NEW
vl[0].pass_alpha_threshold = 0.0
"""
    instance.send_string(setup)

    create = """
import bpy
bpy.ops.scene.view_layer_add(type="NEW")
bpy.ops.scene.view_layer_add(type="NEW")
# force sync
scene = bpy.context.scene
vl = scene.view_layers
vl[1].pass_alpha_threshold = 0.1
vl[2].pass_alpha_threshold = 0.2
"""
    instance.send_string(create)

    rename = """
import bpy
scene = bpy.context.scene
vl = scene.view_layers
vl[0].name = "vl0"
vl[1].name = "vl1"
vl[2].name = "vl2"
"""
    instance.send_string(rename)
    instance.end_test()


def test_scene_view_layer_rename_conflict(scene_blender_instances):
    """Test view layer rename conflicts and automatic numbering"""
    instance = scene_blender_instances[0]

    create = """
import bpy
bpy.ops.scene.view_layer_add(type="NEW")
bpy.ops.scene.view_layer_add(type="NEW")
# force sync
scene = bpy.context.scene
vl = scene.view_layers
vl[1].pass_alpha_threshold = 0.1
vl[2].pass_alpha_threshold = 0.2
"""
    instance.send_string(create)

    rename = """
import bpy
scene = bpy.context.scene
vl = scene.view_layers
vl[0].name = "vl"
vl[1].name = "vl" # vl.001
vl[2].name = "vl" # vl.002
vl[0].name = "vl.001" # vl.003
"""
    instance.send_string(rename)
    instance.end_test()


def test_scene_view_layer_remove(scene_blender_instances):
    """Test removing view layers from scene"""
    instance = scene_blender_instances[0]

    create = """
import bpy
bpy.ops.scene.view_layer_add(type="NEW")
bpy.ops.scene.view_layer_add(type="NEW")
# force sync
scene = bpy.context.scene
vl = scene.view_layers
vl[1].pass_alpha_threshold = 0.1
vl[2].pass_alpha_threshold = 0.2
"""
    instance.send_string(create)

    remove = """
import bpy
scene = bpy.context.scene
vl = scene.view_layers
bpy.context.window.view_layer = vl[1]
bpy.ops.scene.view_layer_remove()
"""
    instance.send_string(remove)
    instance.end_test()


def test_scene_view_layer_add_blank(generic_blender_instances):
    """Test adding blank view layer (synchronization test)"""
    instance = generic_blender_instances[0]

    # synchronization of LayerCollection.exclude deserves a test since it must not be synchronized for the
    # master collection
    create = """
import bpy
bpy.ops.collection.create(name="Collection")
collection = bpy.data.collections[0]
bpy.data.scenes[0].collection.children.link(collection)
# collection is "included" in existing view layer
# and excluded from new view_layer
bpy.ops.scene.view_layer_add(type="EMPTY")
# force sync
scene = bpy.context.scene
vl = scene.view_layers
vl[1].pass_alpha_threshold = 0.1
"""
    instance.send_string(create)
    instance.end_test()


def test_mesh_primitive_plane_add(generic_blender_instances):
    """Test adding primitive plane mesh (same polygon sizes)"""
    instance = generic_blender_instances[0]

    action = """
import bpy
bpy.ops.mesh.primitive_plane_add()
"""
    instance.send_string(action)
    instance.end_test()


def test_mesh_edit_vertex_coordinates(generic_blender_instances):
    """Test editing mesh vertex coordinates"""
    instance = generic_blender_instances[0]

    setup = """
import bpy
bpy.ops.mesh.primitive_plane_add()
"""
    instance.send_string(setup)

    action = """
import bpy
bpy.data.meshes[0].vertices[0].co *= 2
"""
    instance.send_string(action)
    instance.end_test()


def test_mesh_primitive_cone_add(generic_blender_instances):
    """Test adding primitive cone mesh (different polygon sizes)"""
    instance = generic_blender_instances[0]

    action = """
import bpy
bpy.ops.mesh.primitive_cone_add()
"""
    instance.send_string(action)
    instance.end_test()


def test_mesh_subdivide(generic_blender_instances):
    """Test mesh subdivision operation (changes topology)"""
    instance = generic_blender_instances[0]

    setup = """
import bpy
bpy.ops.mesh.primitive_cone_add()
"""
    instance.send_string(setup)

    action = """
import bpy
bpy.ops.object.editmode_toggle()
bpy.ops.mesh.subdivide()
bpy.ops.object.editmode_toggle()
"""
    instance.send_string(action)
    instance.end_test()


def test_mesh_delete_all_vertices(generic_blender_instances):
    """Test deleting all mesh vertices"""
    instance = generic_blender_instances[0]

    setup = """
import bpy
bpy.ops.mesh.primitive_cube_add()
"""
    instance.send_string(setup)

    action = """
import bpy
bpy.ops.object.editmode_toggle()
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.delete()
bpy.ops.object.editmode_toggle()
"""
    instance.send_string(action)
    instance.end_test()


def test_mesh_add_uv_texture(generic_blender_instances):
    """Test adding UV texture to mesh"""
    instance = generic_blender_instances[0]

    setup = """
import bpy
bpy.ops.mesh.primitive_cone_add()
"""
    instance.send_string(setup)

    action = """
import bpy
bpy.ops.mesh.uv_texture_add()
"""
    instance.send_string(action)
    instance.end_test()


def test_mesh_vertex_groups_add(generic_blender_instances):
    """Test adding and managing vertex groups"""
    # Although we send a single command, Blender triggers several DG updates and parts of the vg modifications
    # are processed as updates, not creations
    instance = generic_blender_instances[0]

    action = """
import bpy
bpy.ops.mesh.primitive_plane_add(location=(0., 0., 0))
obj = bpy.data.objects[0]
vgs = obj.vertex_groups

bpy.ops.object.editmode_toggle()
bpy.ops.object.vertex_group_assign_new()
obj.vertex_groups[-1].name = "group_0"

bpy.ops.mesh.primitive_plane_add(location=(0., 0., 1))
bpy.ops.object.vertex_group_assign_new()
obj.vertex_groups[-1].name = "group_1"

bpy.ops.mesh.primitive_plane_add(location=(0., 0., 2))
bpy.ops.object.vertex_group_assign_new()
obj.vertex_groups[-1].name = "group_2"

bpy.ops.object.editmode_toggle()
"""
    instance.send_string(action)
    instance.end_test()


def test_mesh_vertex_groups_manipulation(generic_blender_instances):
    """Test vertex group manipulation operations"""
    instance = generic_blender_instances[0]

    setup = """
import bpy
bpy.ops.mesh.primitive_plane_add(location=(0., 0., 0))
obj = bpy.data.objects[0]
vgs = obj.vertex_groups

bpy.ops.object.editmode_toggle()
bpy.ops.object.vertex_group_assign_new()
vgs[-1].name = "group_0"
bpy.ops.object.editmode_toggle()
"""
    instance.send_string(setup)

    action = """
import bpy
obj = bpy.data.objects[0]
vgs = obj.vertex_groups

bpy.ops.object.editmode_toggle()
bpy.ops.mesh.primitive_plane_add(location=(0., 0., 1))
bpy.ops.object.vertex_group_assign_new()
vgs[-1].name = "group_1"
bpy.ops.object.editmode_toggle()
"""
    instance.send_string(action)
    instance.end_test()


def test_mesh_vertex_groups_move(generic_blender_instances):
    """Test moving vertex groups in list"""
    instance = generic_blender_instances[0]

    setup = """
import bpy
bpy.ops.mesh.primitive_plane_add(location=(0., 0., 0))
obj = bpy.data.objects[0]
vgs = obj.vertex_groups

bpy.ops.object.editmode_toggle()
bpy.ops.object.vertex_group_assign_new()
obj.vertex_groups[-1].name = "group_0"

bpy.ops.mesh.primitive_plane_add(location=(0., 0., 1))
bpy.ops.object.vertex_group_assign_new()
obj.vertex_groups[-1].name = "group_1"

bpy.ops.object.editmode_toggle()
"""
    instance.send_string(setup)

    action = """
import bpy
bpy.ops.object.vertex_group_move(direction="UP")
"""
    instance.send_string(action)
    instance.end_test()


def test_object_material_slots(generic_blender_instances):
    """Test creating object material slots"""
    instance = generic_blender_instances[0]

    create_action = """
import bpy
bpy.ops.mesh.primitive_plane_add(location=(0., 0., 0))
obj = bpy.data.objects[0]

mat0 = bpy.data.materials.new("mat0")
mat1 = bpy.data.materials.new("mat1")

bpy.ops.object.material_slot_add()
obj.material_slots[0].material = mat0

bpy.ops.object.material_slot_add()
# None

bpy.ops.object.material_slot_add()
obj.material_slots[2].link = "OBJECT"
obj.material_slots[2].material = mat1
"""
    instance.send_string(create_action)
    instance.end_test()


def test_object_material_slots_remove(generic_blender_instances):
    """Test removing material slots from objects"""
    instance = generic_blender_instances[0]

    create_action = """
import bpy
bpy.ops.mesh.primitive_plane_add(location=(0., 0., 0))
obj = bpy.data.objects[0]

mat0 = bpy.data.materials.new("mat0")
mat1 = bpy.data.materials.new("mat1")

bpy.ops.object.material_slot_add()
obj.material_slots[0].material = mat0

bpy.ops.object.material_slot_add()
# None

bpy.ops.object.material_slot_add()
obj.material_slots[2].link = "OBJECT"
obj.material_slots[2].material = mat1
"""
    instance.send_string(create_action)

    action = """
import bpy
obj = bpy.data.objects[0]
obj.active_material_index = 0
bpy.ops.object.material_slot_remove()
"""
    instance.send_string(action)
    instance.end_test()


def test_object_material_slots_update(generic_blender_instances):
    """Test updating object material slots"""
    instance = generic_blender_instances[0]

    create_action = """
import bpy
bpy.ops.mesh.primitive_plane_add(location=(0., 0., 0))
obj = bpy.data.objects[0]

mat0 = bpy.data.materials.new("mat0")
mat1 = bpy.data.materials.new("mat1")

bpy.ops.object.material_slot_add()
obj.material_slots[0].material = mat0

bpy.ops.object.material_slot_add()
# None

bpy.ops.object.material_slot_add()
obj.material_slots[2].link = "OBJECT"
obj.material_slots[2].material = mat1
"""
    instance.send_string(create_action)

    action = """
import bpy
obj = bpy.data.objects[0]
mat0 = bpy.data.materials.new("mat0")
mat1 = bpy.data.materials.new("mat1")

obj.material_slots[0].material = None
obj.material_slots[1].material = mat1
"""
    instance.send_string(action)
    instance.end_test()


def test_object_material_slots_move(generic_blender_instances):
    """Test moving material slots in list"""
    instance = generic_blender_instances[0]

    create_action = """
import bpy
bpy.ops.mesh.primitive_plane_add(location=(0., 0., 0))
obj = bpy.data.objects[0]

mat0 = bpy.data.materials.new("mat0")
mat1 = bpy.data.materials.new("mat1")

bpy.ops.object.material_slot_add()
obj.material_slots[0].material = mat0

bpy.ops.object.material_slot_add()
# None

bpy.ops.object.material_slot_add()
obj.material_slots[2].link = "OBJECT"
obj.material_slots[2].material = mat1
"""
    instance.send_string(create_action)

    action = """
import bpy
obj = bpy.data.objects[0]
obj.active_material_index = 0
bpy.ops.object.material_slot_move(direction='DOWN')
"""
    instance.send_string(action)
    instance.end_test()


def test_object_decimate_modifier(generic_blender_instances):
    """Test decimate modifier on objects (for SetProxy)"""
    instance = generic_blender_instances[0]

    create = """
import bpy
bpy.ops.mesh.primitive_plane_add(location=(1., 0., 0))
obj = bpy.data.objects[0]
modifier = obj.modifiers.new("decimate", "DECIMATE")
# in "planar" tab
modifier.delimit = {"SEAM", "UV"}
"""
    instance.send_string(create)
    instance.end_test()


def test_object_parent_relationships(generic_blender_instances):
    """Test object parent-child relationships"""
    instance = generic_blender_instances[0]

    create = """
import bpy
bpy.ops.mesh.primitive_plane_add(location=(1., 0., 0))
bpy.ops.mesh.primitive_plane_add(location=(0., 1., 1))
"""
    instance.send_string(create)

    parent = """
import bpy
obj0 = bpy.data.objects[0]
obj1 = bpy.data.objects[1]
bpy.context.view_layer.objects.active=obj1
obj0.select_set(True)

# obj0 is child of obj1
# the operator also modifies local_matrix and matrix_parent_inverse

bpy.ops.object.parent_set(type='OBJECT')
"""
    instance.send_string(parent)
    instance.end_test()


@pytest.fixture
def shape_key_setup():
    """Provide shape key creation utilities"""
    create_on_mesh = """
import bpy
bpy.ops.mesh.primitive_plane_add(location=(0., 0., 0))
obj = bpy.data.objects[0]
obj.shape_key_add()
obj.shape_key_add()
obj.shape_key_add()
keys = bpy.data.shape_keys[0]
key0 = keys.key_blocks[0]
key0.data[0].co[2] = 1.
key1 = keys.key_blocks[1]
key1.value = 0.1
key2 = keys.key_blocks[2]
key2.value = 0.2
"""
    return create_on_mesh


def test_shape_key_create_mesh(shape_key_setup, generic_blender_instances):
    """Test creating shape keys on mesh objects"""
    instance = generic_blender_instances[0]

    instance.send_string(shape_key_setup)
    instance.end_test()


def test_shape_key_rename(shape_key_setup, generic_blender_instances):
    """Test renaming shape keys"""
    instance = generic_blender_instances[0]

    instance.send_string(shape_key_setup)

    action = """
import bpy
obj = bpy.data.objects[0]
keys = bpy.data.shape_keys[0]
key0 = keys.key_blocks[0]
key0.name = "plop"
key0.data[0].co[2] = key0.data[0].co[2]
"""
    instance.send_string(action)
    instance.end_test()


def test_shape_key_relative(shape_key_setup, generic_blender_instances):
    """Test shape key relative relationships"""
    instance = generic_blender_instances[0]

    instance.send_string(shape_key_setup)

    action = """
import bpy
obj = bpy.data.objects[0]
keys = bpy.data.shape_keys[0]
keys.key_blocks[2].relative_key = keys.key_blocks[1]
"""
    instance.send_string(action)
    instance.end_test()


def test_shape_key_remove(shape_key_setup, generic_blender_instances):
    """Test removing shape keys"""
    instance = generic_blender_instances[0]

    instance.send_string(shape_key_setup)

    action = """
import bpy
obj = bpy.data.objects[0]
keys = bpy.data.shape_keys[0]
key1 = keys.key_blocks[1]
obj.shape_key_remove(key1)
"""
    instance.send_string(action)
    instance.end_test()


def test_custom_properties_create(generic_blender_instances):
    """Test creating custom properties on objects"""
    instance = generic_blender_instances[0]

    create = """
import bpy
bpy.ops.mesh.primitive_plane_add(location=(0., 0., 0))
obj = bpy.data.objects[0]
bpy.context.view_layer.objects.active = obj
bpy.ops.wm.properties_add(data_path="active_object")
"""
    instance.send_string(create)
    instance.end_test()


def test_custom_properties_update(generic_blender_instances):
    """Test updating custom properties on objects"""
    instance = generic_blender_instances[0]

    create = """
import bpy
bpy.ops.mesh.primitive_plane_add(location=(0., 0., 0))
obj = bpy.data.objects[0]
bpy.context.view_layer.objects.active = obj
bpy.ops.wm.properties_add(data_path="active_object")
"""
    instance.send_string(create)

    update = """
import bpy
obj = bpy.data.objects[0]
rna_ui = obj["_RNA_UI"]
key = list(rna_ui.keys())[0]
rna_ui[key]["description"]= "the tooltip"
# trigger update
obj.location[0] += 1
"""
    instance.send_string(update)
    instance.end_test()


def test_custom_properties_remove(generic_blender_instances):
    """Test removing custom properties from objects"""
    instance = generic_blender_instances[0]

    create = """
import bpy
bpy.ops.mesh.primitive_plane_add(location=(0., 0., 0))
obj = bpy.data.objects[0]
bpy.context.view_layer.objects.active = obj
bpy.ops.wm.properties_add(data_path="active_object")
"""
    instance.send_string(create)

    remove = """
import bpy
obj = bpy.data.objects[0]
rna_ui = obj["_RNA_UI"]
key = list(rna_ui.keys())[0]
bpy.ops.wm.properties_remove(data_path='active_object', property=key)
"""
    instance.send_string(remove)
    instance.end_test()


def test_image_from_file(generic_blender_instances):
    """Test loading images from file paths"""
    instance = generic_blender_instances[0]

    path = str(files_folder() / "image_a.png")
    create = f"""
import bpy
bpy.data.images.load(r"{path}")
"""
    instance.send_string(create)
    instance.end_test()
