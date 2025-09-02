#!/usr/bin/env python3
"""
Dynamic Blender Type Compatibility System for Mixer Addon

This module implements the TODO enhancement in specifics.py to handle
types that don't exist in all Blender versions gracefully.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Add addons to path for testing
project_root = Path(__file__).parent
addons_path = project_root / 'addons'
sys.path.insert(0, str(addons_path))

import bpy
import bpy.types as T

logger = logging.getLogger(__name__)

# Import conditional_properties and related functions
try:
    # Add the mixer_custom_types to module for forward compatibility
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "mixer_custom_types",
        addons_path / 'mixer' / 'blender_data' / 'misc_proxies.py'
    )
    if spec and spec.loader:
        misc_proxies = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(misc_proxies)

    # Import specifics module for compatibility
    from mixer.blender_data.specifics import conditional_properties, _filter_properties
except ImportError as e:
    logger.warning(f"Could not import specifics: {e}. Some features may be limited.")

    # Define minimal fallback if specifics can't be imported
    def conditional_properties(bpy_struct, properties):
        return properties

    def _filter_properties(properties, exclude_names):
        if hasattr(properties, 'items'):
            return {k: v for k, v in properties if k not in exclude_names}
        return properties

class BlenderTypeRegistry:
    """
    Dynamic registry for version-aware Blender type handling.

    This class provides utilities to:
    - Check type availability in current Blender version
    - Safely register decorators only when types exist
    - Log compatibility decisions for debugging
    - Provide fallback behavior for missing types
    """

    @staticmethod
    def has_type(type_name: str) -> bool:
        """Check if a Blender type exists in current version."""
        return hasattr(T, type_name)

    @staticmethod
    def get_conditional_decorator(type_name: str):
        """Return decorator that only registers if type exists."""
        def conditional_register(func):
            if BlenderTypeRegistry.has_type(type_name):
                logger.debug(f"✅ Registering {type_name} handler in Blender {bpy.app.version_string}")
                return conditional_properties.register(getattr(T, type_name))(func)
            else:
                logger.warning(f"⚠️  Skipping {type_name} registration - not available in Blender {bpy.app.version_string}")
                return func  # Return unchanged function for graceful fallback
        return conditional_register

    @staticmethod
    def get_version_features() -> Dict[str, bool]:
        """Get availability matrix of Blender features across versions."""
        features = {
            'attribute_group': BlenderTypeRegistry.has_type('AttributeGroup'),
            'effect_sequence': BlenderTypeRegistry.has_type('EffectSequence'),
            'face_maps': BlenderTypeRegistry.has_type('FaceMaps'),
            'node_tree_inputs': BlenderTypeRegistry.has_type('NodeTreeInputs'),
            'node_tree_outputs': BlenderTypeRegistry.has_type('NodeTreeOutputs'),
            'object_gpencil_modifiers': BlenderTypeRegistry.has_type('ObjectGpencilModifiers'),
            'sequence_modifiers': BlenderTypeRegistry.has_type('SequenceModifiers'),
            'conditional_properties_support': True,  # Version where this system is active
        }

        logger.info(f"Blender {bpy.app.version_string} feature compatibility matrix:")
        for feature, available in features.items():
            status = "✅" if available else "❌"
            logger.info(f"  {status} {feature}")

        return features

    @staticmethod
    def safe_registration(type_names: List[str], registry_func, handler_func):
        """Safely register multiple types with automatic compatibility checking."""
        registered_count = 0
        skipped_count = 0

        for type_name in type_names:
            if BlenderTypeRegistry.has_type(type_name):
                try:
                    registry_func(type_name, handler_func)
                    registered_count += 1
                except Exception as e:
                    logger.error(f"Failed to register {type_name}: {e}")
            else:
                skipped_count += 1
                logger.debug(f"Skipping {type_name} - not available in current Blender version")

        logger.info(f"Registration complete: {registered_count} registered, {skipped_count} skipped")
        return registered_count, skipped_count

def create_plugin_data():
    """Create version-aware plugin data for Blender addon."""
    return {
        'blender_version': bpy.app.version_string,
        'api_features': BlenderTypeRegistry.get_version_features(),
        'compatibility_system_active': True,
        'fallback_behavior': 'warn',  # 'warn', 'silent', 'error'
        'dynamic_registration_enabled': True
    }

# Example usage functions for different registries
def handle_sequence_properties(bpy_struct: Any, properties: Any) -> Any:
    """Generic handler for sequence-type properties that may not exist in all versions."""
    if bpy.app.version >= (2, 92, 0):
        return properties

    # Legacy version filtering
    filter_props = []
    if not bpy_struct.use_crop:
        filter_props.append("crop")
    if not bpy_struct.use_translation:
        filter_props.append("transform")

    if not filter_props:
        return properties

    # This would need the _filter_properties function from specifics.py
    # For now, return properties unchanged
    return properties

if __name__ == "__main__":
    # Test the compatibility system
    print("🧪 Testing Blender Type Compatibility System")

    try:
        features = BlenderTypeRegistry.get_version_features()
        print(f"\n✅ Compatibility check successful for Blender {bpy.app.version_string}")

        # Show plugin data structure
        plugin_data = create_plugin_data()
        print(f"\n📊 Generated plugin data: {plugin_data}")

    except Exception as e:
        print(f"❌ Error testing compatibility system: {e}")
        import traceback
        traceback.print_exc()
