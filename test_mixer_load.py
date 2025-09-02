#!/usr/bin/env python3
"""
Test script to load the Mixer addon and verify it works.
"""
import sys
import os
from pathlib import Path

# Add the addons directory to the Python path
project_root = Path(__file__).parent
addons_path = project_root / 'addons'
sys.path.insert(0, str(addons_path))

print("🔍 Testing Mixer addon loading...")
print(f"Python path: {sys.path[0]}")

try:
    # Import the mixer module
    import mixer

    print("🎉 Mixer addon loaded successfully!")

    # Test basic attributes
    print(f"Addon version: {mixer.__version__}")
    print(f"Display version: {mixer.display_version}")

    # Test bl_info
    bl_info = mixer.bl_info
    print(f"Addon name: {bl_info['name']}")
    print(f"Description: {bl_info['description']}")
    print(f"Version: {bl_info['version']}")
    print(f"Blender version: {bl_info['blender']}")

    # Test share_data
    from mixer.share_data import share_data
    print(f"Share data initialized: {share_data is not None}")
    print(f"Local server process: {share_data.local_server_process}")

    print("\n✅ All tests passed! Mixer addon is functional.")

except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
