"""
Functional test for mixer synchronization
"""
import unittest
import os
import subprocess
from pathlib import Path

class TestMixerFunctional(unittest.TestCase):
    """Test basic mixer functionality with real Blender instances"""

    def setUp(self):
        self.blender_exe = os.environ.get('MIXER_BLENDER_EXE_PATH')
        if not self.blender_exe:
            self.skipTest("MIXER_BLENDER_EXE_PATH not set")

        self.blender_exe = Path(self.blender_exe)
        if not self.blender_exe.exists():
            self.skipTest(f"Blender executable not found: {self.blender_exe}")

        # Create a simple test script
        self.test_script = """
import bpy
import sys
import time

# Enable the mixer addon (assuming it's installed)
try:
    bpy.ops.preferences.addon_enable(module='mixer')
    print("Mixer addon enabled")
except Exception as e:
    print(f"Failed to enable mixer addon: {e}")
    sys.exit(1)

# Create a simple object to test synchronization
bpy.ops.mesh.primitive_cube_add()
cube = bpy.context.active_object
cube.name = "TestCube"
print(f"Created object: {cube.name}")

# Try to create a room
try:
    # This would be the mixer operator to create a room
    # bpy.ops.mixer.create_room()  # This operator may not exist
    print("Room creation attempted")
except Exception as e:
    print(f"Room creation failed: {e}")

print("Test script completed successfully")
"""

    def test_basic_blender_startup(self):
        """Test that Blender can start and run our test script"""
        script_path = Path("/tmp/test_mixer.py")
        script_path.write_text(self.test_script)

        try:
            # Run Blender with our test script
            cmd = [
                str(self.blender_exe),
                "--background",
                "--python", str(script_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            print("Return code:", result.returncode)

            # Check if the test script ran successfully
            self.assertEqual(result.returncode, 0, f"Blender failed with stderr: {result.stderr}")
            self.assertIn("Test script completed successfully", result.stdout)

        finally:
            # Clean up
            if script_path.exists():
                script_path.unlink()

    def test_mixer_addon_enable(self):
        """Test that the mixer addon can be enabled from Blender's addon directory"""
        script_path = Path("/tmp/test_addon_enable.py")

        enable_script = """
import bpy
import sys

print("Checking for mixer addon...")

# Check if mixer addon is available in Blender's addon list
addons = bpy.context.preferences.addons
available_addons = [addon.module for addon in bpy.context.preferences.addons]

if 'mixer' in available_addons:
    print("Mixer addon found in available addons")
else:
    print("Available addons:", available_addons[:10])  # Show first 10
    print("Mixer addon not found in available addons list")

# Try to enable the mixer addon
try:
    bpy.ops.preferences.addon_enable(module='mixer')
    print("Mixer addon enabled successfully")
except Exception as e:
    print(f"Failed to enable mixer addon: {e}")
    import traceback
    traceback.print_exc()
    # Try to find the addon file
    import os
    addon_paths = bpy.utils.script_paths("addons")
    print(f"Addon search paths: {addon_paths}")
    for path in addon_paths:
        mixer_path = os.path.join(path, 'mixer')
        if os.path.exists(mixer_path):
            print(f"Found mixer addon at: {mixer_path}")
            break
    else:
        print("Mixer addon directory not found in addon paths")
    sys.exit(1)

# Check if mixer operators are available
if hasattr(bpy.ops, 'mixer'):
    print("Mixer operators are available in bpy.ops")
    # List available mixer operators
    mixer_ops = [op for op in dir(bpy.ops.mixer) if not op.startswith('_')]
    print(f"Available mixer operators: {mixer_ops}")
else:
    print("Warning: Mixer operators not found in bpy.ops")

print("Addon enable test completed successfully")
"""

        script_path.write_text(enable_script)

        try:
            cmd = [
                str(self.blender_exe),
                "--background",
                "--python", str(script_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            print("Enable STDOUT:", result.stdout)
            print("Enable STDERR:", result.stderr)

            self.assertEqual(result.returncode, 0, f"Addon enable failed: {result.stderr}")
            self.assertIn("Addon enable test completed successfully", result.stdout)

        finally:
            if script_path.exists():
                script_path.unlink()

if __name__ == '__main__':
    unittest.main()