#!/usr/bin/env python3
"""
Validation script for Mixer Blender extension.

This script validates the extension structure and ensures all components
are properly configured for Blender 4.2+ extension system.
"""

import logging
import sys
import traceback
from pathlib import Path


def validate_extension_structure():
    """Validate that the extension has the required structure."""
    print("🔍 Validating extension structure...")

    extension_dir = Path(__file__).parent
    required_files = [
        "blender_manifest.toml",
        "__blender_manifest__.py",
        "__init__.py",
        "share_data.py",
    ]

    missing_files = []
    for file_name in required_files:
        file_path = extension_dir / file_name
        if not file_path.exists():
            missing_files.append(file_name)
        else:
            print(f"✅ {file_name} exists")

    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False

    print("✅ Extension structure validation passed")
    return True


def validate_manifest_import():
    """Validate that the extension manifest can be imported."""
    print("\n🔍 Validating manifest import...")

    try:
        # Test import of __blender_manifest__
        sys.path.insert(0, str(Path(__file__).parent))

        import __blender_manifest__

        # Verify required manifest attributes
        required_attrs = ["__blender_manifest__"]
        for attr in required_attrs:
            if hasattr(__blender_manifest__, attr):
                print(f"✅ {attr} found in __blender_manifest__")
            else:
                print(f"❌ {attr} missing from __blender_manifest__")
                return False

        # Verify manifest structure
        manifest = __blender_manifest__.__blender_manifest__
        required_fields = ["type", "name", "version", "blender", "description"]
        for field in required_fields:
            if field in manifest:
                print(f"✅ Manifest field '{field}' present")
            else:
                print(f"❌ Manifest field '{field}' missing")
                return False

        # Verify Blender version requirements
        blender_version = manifest.get("blender")
        if blender_version and isinstance(blender_version, tuple) and len(blender_version) >= 2:
            major, minor = blender_version[:2]
            if major >= 4 and minor >= 2:
                print(f"✅ Blender version requirement satisfied: {blender_version}")
            else:
                print(f"⚠️  Blender version {blender_version} may be too old for modern extension system")
        else:
            print("❌ Invalid Blender version specification")

        print("✅ Manifest import validation passed")
        return True

    except Exception as e:
        print(f"❌ Manifest import failed: {e}")
        traceback.print_exc()
        return False


def validate_addon_imports():
    """Validate that addon modules can be imported."""
    print("\n🔍 Validating addon imports...")

    import sys
    import importlib
    from pathlib import Path

    # Add the addon directory to Python path
    addon_dir = Path(__file__).parent
    sys.path.insert(0, str(addon_dir))

    modules_to_test = [
        "mixer",
        "mixer.share_data",
    ]

    failed_imports = []

    for module_name in modules_to_test:
        try:
            importlib.import_module(module_name)
            print(f"✅ {module_name} imported successfully")
        except Exception as e:
            print(f"❌ Failed to import {module_name}: {e}")
            failed_imports.append(module_name)

    if failed_imports:
        print(f"❌ Some modules failed to import: {failed_imports}")
        return False

    print("✅ Addon import validation passed")
    return True


def validate_extension_callbacks():
    """Validate that extension callbacks are properly defined."""
    print("\n🔍 Validating extension callbacks...")

    try:
        import __blender_manifest__

        manifest = __blender_manifest__.__blender_manifest__

        # Check for extension callbacks
        possible_callbacks = [
            "activate",
            "deactivate",
            "register",
            "unregister",
            "register_extension",
            "unregister_extension",
            "activate_extension",
            "deactivate_extension"
        ]

        found_callbacks = []
        for callback in possible_callbacks:
            if callback in manifest:
                callback_func_code = f"""
def {callback}():
    return True
"""
                print(f"✅ Extension callback '{callback}' defined in manifest")
                found_callbacks.append(callback)

        if not found_callbacks:
            print("⚠️  No extension callbacks found - this may work as a traditional addon")
            return True  # Not critical for traditional addon installs

        print(f"✅ Extension callbacks validation passed (found: {len(found_callbacks)} callbacks)")
        return True

    except Exception as e:
        print(f"❌ Extension callback validation failed: {e}")
        return False


def run_validation():
    """Run all validation checks."""
    print("=" * 60)
    print("🎯 MIXER BLENDER EXTENSION VALIDATION")
    print("=" * 60)

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    results = []
    results.append(("Extension Structure", validate_extension_structure()))
    results.append(("Manifest Import", validate_manifest_import()))
    results.append(("Addon Imports", validate_addon_imports()))
    results.append(("Extension Callbacks", validate_extension_callbacks()))

    print("\n" + "=" * 60)
    print("📊 VALIDATION RESULTS")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<25} {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)

    if all_passed:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("The Mixer extension should be compatible with Blender 4.2+")
        print("\n📋 Next steps:")
        print("1. Install Blender 4.2+ or later")
        print("2. Install the extension via Extensions > Install from Disk")
        print("3. Enable the 'Mixer' extension")
        print("4. Configure network settings if needed")
        return 0
    else:
        print("❌ SOME VALIDATIONS FAILED")
        print("The extension may require additional fixes before installation")
        return 1


if __name__ == "__main__":
    exit_code = run_validation()
    sys.exit(exit_code)
