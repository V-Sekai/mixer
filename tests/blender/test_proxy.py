import pytest
# Create a pytest-compatible wrapper for MixerTestCase
from tests.mixer_testcase import MixerTestCase as BaseMixerTestCase
from tests.mixer_testcase import BlenderDesc


class MixerTestCaseWrapper(BaseMixerTestCase):
    """Pytest-compatible wrapper for MixerTestCase"""

    def __init__(self):
        # Initialize the base class directly
        super().__init__()
        # Add pytest-compatible assertion methods
        self.failureException = AssertionError

    def setup_method(self):
        # Call the base setup_method with Blender configurations
        sender_blendfile = None  # Use default Blender file
        receiver_blendfile = None  # Use same for receiver
        sender = BlenderDesc(load_file=sender_blendfile, wait_for_debugger=False)
        receiver = BlenderDesc(load_file=receiver_blendfile, wait_for_debugger=False)
        blenderdescs = [sender, receiver]
        super().setup_method(blenderdescs=blenderdescs, join=True)

    def teardown_method(self):
        # Clean up blender instances
        super().teardown_method()


class TestBpyProxy(MixerTestCaseWrapper):
    def force_sync(self):
        action = """
import bpy
bpy.data.scenes[0].use_gravity = not bpy.data.scenes[0].use_gravity
"""
        self.send_string(action)

    def test_just_join(self):
        self.end_test()

    def test_duplicate_uuid_metaball(self):
        # with metaballs the effect of duplicate uuids is visible as they are not
        # handled by the VRtist protocol
        action = """
import bpy
bpy.ops.object.metaball_add(type='BALL', location=(0,0,0))
obj = bpy.context.active_object
"""
        self.send_string(action)

        action = """
import bpy
D = bpy.data
bpy.ops.object.duplicate()
bpy.ops.transform.translate(value=(0, 4, 0))
"""
        self.send_string(action)

        self.force_sync()

        self.end_test()


class TestStructCollectionProxy(MixerTestCaseWrapper):
    def test_light_falloff_curve_add_point(self):
        action = """
import bpy
bpy.ops.object.light_add(type='POINT')
"""
        self.send_string(action)

        # HACK it seems that we do not receive the depsgraph update
        # for light.falloff_curve.curves[0].points so add a Light member update

        action = """
import bpy
light = bpy.data.lights['Point']
light.falloff_curve.curves[0].points.new(0.5, 0.5)
light.distance = 20
"""
        self.send_string(action)

        self.end_test()

    def test_scene_render_view_add_remove(self):
        action = """
import bpy
views = bpy.data.scenes[0].render.views
bpy.ops.scene.render_view_add()
index = views.active_index
views[2].use = False
views.remove(views[0])
"""
        self.send_string(action)

        self.end_test()

    @pytest.mark.skip(reason="see internal issue #298")
    def test_scene_color_management_curve(self):
        action = """
import bpy
settings = bpy.data.scenes[0].view_settings
settings.use_curve_mapping = True
rgb = settings.curve_mapping.curves[3]
points = rgb.points
points.new(0.2, 0.8)
points.new(0.7, 0.3)
"""
        self.send_string(action)

        self.end_test()


if __name__ == "__main__":
    pytest.main([__file__])
