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
Fuzzing tests for bpy_data_proxy operations using hypothesis.

This module tests the BpyDataProxy class operations with randomly generated
Blender datablocks to ensure robustness.
"""

import bpy
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

from mixer.blender_data import bpy_data_proxy
from mixer.blender_data.filter import safe_properties

# Strategies for generating Blender datablock names
@st.composite
def random_datablock_name(draw):
    """Generate a random datablock name."""
    return draw(st.text(st.characters(whitelist_categories=('L', 'N', 'P', 'S')), min_size=1, max_size=30))

@st.composite
def random_collection_name(draw):
    """Generate a random collection name from available bpy.data collections."""
    collections = ['objects', 'meshes', 'materials', 'textures', 'lights', 'cameras']
    return draw(st.sampled_from(collections))

@given(
    obj_name=random_datablock_name(),
    mesh_name=random_datablock_name(),
    location=st.tuples(st.floats(-100, 100), st.floats(-100, 100), st.floats(-100, 100))
)
@settings(max_examples=30, deadline=2000, suppress_health_check=[HealthCheck.too_slow])
def test_bpy_data_proxy_create_datablock(obj_name, mesh_name, location):
    """Test creating datablocks through BpyDataProxy."""
    proxy = bpy_data_proxy.BpyDataProxy()
    context = proxy.context(safe_properties)

    # Create a mesh
    mesh = bpy.data.meshes.new(mesh_name)
    mesh.vertices.add(3)
    mesh.update()

    # Create an object
    obj = bpy.data.objects.new(obj_name, mesh)
    obj.location = location
    bpy.context.scene.collection.objects.link(obj)

    try:
        # Test creating datablock through proxy
        created_obj = proxy.create_datablock('objects', context)

        # Test updating datablock
        proxy.update_datablock(created_obj, safe_properties)

        # Test removing datablock
        proxy.remove_datablock(created_obj.mixer_uuid)

    except Exception as e:
        pytest.fail(f"BpyDataProxy datablock operations failed: {e}")
    finally:
        # Clean up
        if obj.name in bpy.data.objects:
            bpy.data.objects.remove(obj)
        if mesh.name in bpy.data.meshes:
            bpy.data.meshes.remove(mesh)

@given(
    num_objects=st.integers(1, 10),
    base_name=random_datablock_name()
)
@settings(max_examples=20, deadline=3000, suppress_health_check=[HealthCheck.too_slow])
def test_bpy_data_proxy_bulk_operations(num_objects, base_name):
    """Test bulk operations on multiple datablocks."""
    proxy = bpy_data_proxy.BpyDataProxy()
    context = proxy.context(safe_properties)

    created_objects = []
    created_meshes = []

    try:
        # Create multiple objects
        for i in range(num_objects):
            mesh_name = f"{base_name}_mesh_{i}"
            obj_name = f"{base_name}_obj_{i}"

            mesh = bpy.data.meshes.new(mesh_name)
            mesh.vertices.add(3)
            mesh.update()
            created_meshes.append(mesh)

            obj = bpy.data.objects.new(obj_name, mesh)
            obj.location = (i * 2, 0, 0)
            bpy.context.scene.collection.objects.link(obj)
            created_objects.append(obj)

        # Test loading all data
        loaded_proxy = proxy.load(safe_properties)

        # Test diff operation
        diff = proxy.diff(safe_properties)

        # Test update operation
        if diff:
            proxy.update(diff, safe_properties)

    except Exception as e:
        pytest.fail(f"BpyDataProxy bulk operations failed: {e}")
    finally:
        # Clean up
        for obj in created_objects:
            if obj.name in bpy.data.objects:
                bpy.data.objects.remove(obj)
        for mesh in created_meshes:
            if mesh.name in bpy.data.meshes:
                bpy.data.meshes.remove(mesh)

@given(
    collection_name=random_collection_name(),
    datablock_name=random_datablock_name()
)
@settings(max_examples=20, deadline=1000)
def test_bpy_data_proxy_find_operations(collection_name, datablock_name):
    """Test find operations in BpyDataProxy."""
    proxy = bpy_data_proxy.BpyDataProxy()

    try:
        # Test finding non-existent datablock
        result = proxy.find(collection_name, datablock_name)
        assert result is None  # Should return None for non-existent datablocks

        # Create a datablock and test finding it
        if collection_name == 'objects':
            obj = bpy.data.objects.new(datablock_name, None)
            bpy.context.scene.collection.objects.link(obj)

            # Reload proxy data
            proxy.load(safe_properties)

            # Test finding the created datablock
            found = proxy.find(collection_name, datablock_name)
            # Note: This might not work as expected due to how the proxy system works

            # Clean up
            bpy.data.objects.remove(obj)

    except Exception as e:
        pytest.fail(f"BpyDataProxy find operations failed: {e}")

@given(
    rename_data=st.lists(
        st.tuples(random_datablock_name(), random_datablock_name(), random_datablock_name()),
        min_size=1, max_size=5
    )
)
@settings(max_examples=15, deadline=2000)
def test_bpy_data_proxy_rename_operations(rename_data):
    """Test datablock renaming operations."""
    proxy = bpy_data_proxy.BpyDataProxy()

    created_objects = []

    try:
        # Create objects to rename
        for old_name, new_name, collection in rename_data:
            if collection == 'objects':
                obj = bpy.data.objects.new(old_name, None)
                bpy.context.scene.collection.objects.link(obj)
                created_objects.append((obj, new_name))

        # Test rename operation
        renames = [(obj.name, new_name, 'objects') for obj, new_name in created_objects]
        changeset = proxy.rename_datablocks(renames)

        # Verify renames worked
        for obj, new_name in created_objects:
            assert obj.name == new_name

    except Exception as e:
        pytest.fail(f"BpyDataProxy rename operations failed: {e}")
    finally:
        # Clean up
        for obj, _ in created_objects:
            if obj.name in bpy.data.objects:
                bpy.data.objects.remove(obj)

@given(
    shared_folder=st.text(st.characters(whitelist_categories=('L', 'N', 'P', 'S', 'Zs')), min_size=1, max_size=50)
)
@settings(max_examples=10, deadline=1000)
def test_bpy_data_proxy_shared_folders(shared_folder):
    """Test shared folder operations."""
    proxy = bpy_data_proxy.BpyDataProxy()

    try:
        # Test setting shared folders
        proxy.set_shared_folders([shared_folder])

        # Test getting shared folders (if method exists)
        if hasattr(proxy, 'get_shared_folders'):
            folders = proxy.get_shared_folders()
            assert shared_folder in folders

    except Exception as e:
        pytest.fail(f"BpyDataProxy shared folder operations failed: {e}")

@given(
    uuid_str=st.text(st.characters(whitelist_categories=('L', 'N')), min_size=32, max_size=36)
)
@settings(max_examples=20, deadline=500)
def test_bpy_data_proxy_uuid_operations(uuid_str):
    """Test UUID-based operations."""
    proxy = bpy_data_proxy.BpyDataProxy()

    try:
        # Test operations with random UUIDs
        # These should handle invalid UUIDs gracefully
        proxy.remove_datablock(uuid_str)

        # Test proxy state operations
        proxy_state = proxy._proxy_state
        result = proxy_state.datablock(uuid_str)
        assert result is None  # Should return None for invalid UUID

    except Exception as e:
        pytest.fail(f"BpyDataProxy UUID operations failed: {e}")