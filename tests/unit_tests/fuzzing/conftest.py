# Configuration for fuzzing tests

import pytest
import bpy

@pytest.fixture(scope="session", autouse=True)
def setup_blender():
    """Set up Blender environment for fuzzing tests."""
    # Clear any existing data
    bpy.ops.wm.read_homefile(use_empty=True)

    yield

    # Clean up after tests
    bpy.ops.wm.read_homefile(use_empty=True)

@pytest.fixture
def clean_blender_scene():
    """Provide a clean Blender scene for each test."""
    # Store original state
    original_objects = list(bpy.data.objects)
    original_meshes = list(bpy.data.meshes)
    original_materials = list(bpy.data.materials)

    yield

    # Clean up created objects
    for obj in bpy.data.objects:
        if obj not in original_objects:
            bpy.data.objects.remove(obj)

    for mesh in bpy.data.meshes:
        if mesh not in original_meshes:
            bpy.data.meshes.remove(mesh)

    for mat in bpy.data.materials:
        if mat not in original_materials:
            bpy.data.materials.remove(mat)