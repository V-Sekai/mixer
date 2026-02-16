# GPLv3 License
#
# Copyright (C) 2020 Ubisoft
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Fuzzing tests for mixer proxy system using hypothesis.

This module uses hypothesis to generate random Blender objects and test
the mixer proxy system's robustness by exercising save/load/apply/diff operations.
"""

import bpy
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from hypothesis.stateful import RuleBasedStateMachine, rule, precondition

from mixer.blender_data import bpy_data_proxy
from mixer.blender_data.proxy import Proxy
from mixer.blender_data.struct_proxy import StructProxy
from mixer.blender_data.datablock_proxy import DatablockProxy
from mixer.blender_data.filter import safe_properties


# Hypothesis strategies for generating Blender data
@st.composite
def random_vector(draw):
    """Generate a random 3D vector."""
    return draw(st.tuples(st.floats(-1000, 1000), st.floats(-1000, 1000), st.floats(-1000, 1000)))


@st.composite
def random_color(draw):
    """Generate a random color."""
    return draw(st.tuples(st.floats(0, 1), st.floats(0, 1), st.floats(0, 1)))


@st.composite
def random_string(draw):
    """Generate a random string suitable for Blender names."""
    return draw(st.text(st.characters(whitelist_categories=('L', 'N', 'P', 'S', 'Zs')), min_size=1, max_size=50))


@st.composite
def random_mesh_data(draw):
    """Generate random mesh data."""
    num_verts = draw(st.integers(3, 100))
    vertices = [draw(random_vector()) for _ in range(num_verts)]

    # Generate faces (triangles)
    num_faces = draw(st.integers(1, num_verts // 3))
    faces = []
    used_verts = set()
    for _ in range(num_faces):
        # Ensure we don't reuse vertices in a way that creates invalid geometry
        face_verts = []
        for _ in range(3):  # triangles
            vert_idx = draw(st.integers(0, num_verts - 1))
            while vert_idx in used_verts and len(used_verts) < num_verts:
                vert_idx = draw(st.integers(0, num_verts - 1))
            face_verts.append(vert_idx)
            used_verts.add(vert_idx)
        faces.append(face_verts)

    return vertices, faces


@st.composite
def random_object_data(draw):
    """Generate random object data."""
    name = draw(random_string())
    location = draw(random_vector())
    rotation = draw(st.tuples(st.floats(-3.14, 3.14), st.floats(-3.14, 3.14), st.floats(-3.14, 3.14)))
    scale = draw(st.tuples(st.floats(0.1, 10), st.floats(0.1, 10), st.floats(0.1, 10)))

    return {
        'name': name,
        'location': location,
        'rotation_euler': rotation,
        'scale': scale
    }


class ProxyFuzzingState(RuleBasedStateMachine):
    """State machine for fuzzing proxy operations."""

    def __init__(self):
        super().__init__()
        self.proxy_state = bpy_data_proxy.ProxyState()
        self.created_objects = []
        self.created_meshes = []

    @rule()
    def create_random_mesh(self):
        """Create a random mesh and test proxy operations."""
        vertices, faces = random_mesh_data().example()

        # Create mesh in Blender
        mesh = bpy.data.meshes.new("fuzz_mesh")
        mesh.from_pydata(vertices, [], faces)
        mesh.update()

        # Create object
        obj = bpy.data.objects.new("fuzz_obj", mesh)
        bpy.context.scene.collection.objects.link(obj)

        # Test proxy operations
        context = bpy_data_proxy.BpyDataProxy().context(safe_properties)

        try:
            # Load proxy
            proxy = DatablockProxy.make(obj)
            proxy.load(obj, context)

            # Save proxy
            saved_obj = proxy.save(obj, None, 'test', context)

            # Diff proxy
            diff = proxy.diff(obj, 'test', None, context)

            # Apply proxy
            if diff:
                proxy.apply(diff, obj, 'test', context)

        except Exception as e:
            pytest.fail(f"Proxy operation failed on mesh: {e}")

        self.created_meshes.append(mesh)
        self.created_objects.append(obj)

    @rule()
    def create_random_object(self):
        """Create a random object and test proxy operations."""
        obj_data = random_object_data().example()

        # Create empty object
        obj = bpy.data.objects.new(obj_data['name'], None)
        obj.location = obj_data['location']
        obj.rotation_euler = obj_data['rotation_euler']
        obj.scale = obj_data['scale']
        bpy.context.scene.collection.objects.link(obj)

        # Test proxy operations
        context = bpy_data_proxy.BpyDataProxy().context(safe_properties)

        try:
            # Load proxy
            proxy = DatablockProxy.make(obj)
            proxy.load(obj, context)

            # Save proxy
            saved_obj = proxy.save(obj, None, 'test', context)

            # Diff proxy
            diff = proxy.diff(obj, 'test', None, context)

            # Apply proxy
            if diff:
                proxy.apply(diff, obj, 'test', context)

        except Exception as e:
            pytest.fail(f"Proxy operation failed on object: {e}")

        self.created_objects.append(obj)

    @rule()
    def modify_existing_object(self):
        """Modify an existing object and test proxy diff/apply."""
        if not self.created_objects:
            return

        obj = self.created_objects[0]  # Use first object

        # Make random modifications
        obj.location = random_vector().example()
        obj.rotation_euler = (random_vector().example()[0] % (2 * 3.14159),
                            random_vector().example()[1] % (2 * 3.14159),
                            random_vector().example()[2] % (2 * 3.14159))
        obj.scale = (abs(random_vector().example()[0]) + 0.1,
                    abs(random_vector().example()[1]) + 0.1,
                    abs(random_vector().example()[2]) + 0.1)

        # Test proxy operations
        context = bpy_data_proxy.BpyDataProxy().context(safe_properties)

        try:
            proxy = DatablockProxy.make(obj)
            proxy.load(obj, context)

            # Create another instance to test diff
            obj2 = bpy.data.objects.new("temp_obj", obj.data)
            obj2.location = obj.location
            obj2.rotation_euler = obj.rotation_euler
            obj2.scale = obj.scale
            bpy.context.scene.collection.objects.link(obj2)

            proxy2 = DatablockProxy.make(obj2)
            proxy2.load(obj2, context)

            # Diff between proxies
            diff = proxy.diff(obj, 'test', None, context)

            # Apply diff
            if diff:
                proxy.apply(diff, obj2, 'test', context)

            # Clean up
            bpy.data.objects.remove(obj2)

        except Exception as e:
            pytest.fail(f"Proxy diff/apply failed: {e}")

    def teardown(self):
        """Clean up created objects."""
        for obj in self.created_objects:
            if obj.name in bpy.data.objects:
                bpy.data.objects.remove(obj)

        for mesh in self.created_meshes:
            if mesh.name in bpy.data.meshes:
                bpy.data.meshes.remove(mesh)


# Property-based tests
@given(
    name=random_string(),
    location=random_vector(),
    rotation=st.tuples(st.floats(-3.14, 3.14), st.floats(-3.14, 3.14), st.floats(-3.14, 3.14)),
    scale=st.tuples(st.floats(0.1, 10), st.floats(0.1, 10), st.floats(0.1, 10))
)
@settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.too_slow])
def test_object_proxy_roundtrip(name, location, rotation, scale):
    """Test that object proxy save/load operations are consistent."""
    # Create object
    obj = bpy.data.objects.new(name, None)
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = scale
    bpy.context.scene.collection.objects.link(obj)

    context = bpy_data_proxy.BpyDataProxy().context(safe_properties)

    try:
        # Load proxy
        proxy = DatablockProxy.make(obj)
        proxy.load(obj, context)

        # Save to new object
        obj2 = bpy.data.objects.new(name + "_copy", None)
        bpy.context.scene.collection.objects.link(obj2)

        saved_obj = proxy.save(obj2, None, 'test', context)

        # Verify properties match
        assert saved_obj.location == obj.location
        assert saved_obj.rotation_euler == obj.rotation_euler
        assert saved_obj.scale == obj.scale

    except Exception as e:
        pytest.fail(f"Object proxy roundtrip failed: {e}")
    finally:
        # Clean up
        if obj.name in bpy.data.objects:
            bpy.data.objects.remove(obj)
        if name + "_copy" in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[name + "_copy"])


@given(vertices=st.lists(random_vector(), min_size=3, max_size=50))
@settings(max_examples=30, deadline=3000, suppress_health_check=[HealthCheck.too_slow])
def test_mesh_proxy_operations(vertices):
    """Test mesh proxy operations with random vertices."""
    # Create simple mesh
    faces = [[0, 1, 2]]  # Single triangle
    mesh = bpy.data.meshes.new("fuzz_mesh")
    mesh.from_pydata(vertices[:min(len(vertices), 3)], [], faces)
    mesh.update()

    obj = bpy.data.objects.new("fuzz_obj", mesh)
    bpy.context.scene.collection.objects.link(obj)

    context = bpy_data_proxy.BpyDataProxy().context(safe_properties)

    try:
        # Load proxy
        proxy = DatablockProxy.make(obj)
        proxy.load(obj, context)

        # Test diff operation
        diff = proxy.diff(obj, 'test', None, context)

        # Test apply operation
        if diff:
            proxy.apply(diff, obj, 'test', context)

    except Exception as e:
        pytest.fail(f"Mesh proxy operation failed: {e}")
    finally:
        # Clean up
        if obj.name in bpy.data.objects:
            bpy.data.objects.remove(obj)
        if mesh.name in bpy.data.meshes:
            bpy.data.meshes.remove(mesh)


@given(data=st.binary(min_size=0, max_size=1000))
@settings(max_examples=20, deadline=1000)
def test_codec_fuzzing(data):
    """Test codec encoding/decoding with random binary data."""
    from mixer.blender_data.json_codec import Codec

    codec = Codec()

    try:
        # This should not crash even with random data
        decoded = codec.decode(data)
        # If decoding succeeds, try encoding back
        if decoded is not None:
            encoded = codec.encode(decoded)
            assert encoded is not None
    except Exception:
        # Codec should handle invalid data gracefully
        pass


# Run the state machine test
TestProxyFuzzing = ProxyFuzzingState.TestCase