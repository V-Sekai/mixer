"""
Blender extension manifest bootstrap for Mixer add-on.

This file enables the modern Blender 4.2+ extension system while maintaining
backward compatibility with traditional addon installation.
"""

import logging
import platform
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

import bpy

# Blender globals for the extension system
__blender_manifest__ = {
    "type": "add-on",
    "name": "Mixer",
    "version": (1, 0, 0),
    "blender": (4, 4, 0),
    "description": "Real-time collaborative Blender workflows with synchronization",
    "location": "View3D > Mixer",
    "category": "Collaboration",
    "support": "COMMUNITY",
    "author": "Ubisoft Animation Studio",
    "warning": "Experimental addon, can break your scenes",
    "doc_url": "https://github.com/V-Sekai/mixer",
    "tracker_url": "https://github.com/V-Sekai/mixer/issues",
    "maintainer": "K. S. Ernest (iFire) Lee <dyob@lunaport.net>",
    "wiki_url": "",
    "license": ["SPDX:MIT", "GPL-3.0-or-later"],
    "website": "https://github.com/V-Sekai/mixer",
    "tags": ["Modeling", "Scene", "Animation", "Collaboration", "Synchronization"],

    # Extension system callbacks
    "activate": "activate_extension",
    "deactivate": "deactivate_extension",
    "register": "register_extension",
    "unregister": "unregister_extension",

    # Permissions for network functionality
    "permissions": {
        "network": {
            "enabled": True,
            "direction": ["inbound", "outbound"],
            "domains": ["127.0.0.1", "0.0.0.0"],
            "protocols": ["tcp"],
            "default_port": 12800,
        },
        "files": {
            "enabled": True,
            "paths": ["blender://"],
        }
    },

    # Default preferences
    "preferences": {
        "enhanced_synchronization": True,
        "collaborative_panels": True,
        "network.auto_discovery": False,
        "network.default_port": 12800,
        "logging.verbose_mode": False,
    }
}

logger = logging.getLogger(__name__)


def _activate_extension(context: bpy.types.Context) -> bool:
    """
    Called when the extension is first activated after installation.

    Args:
        context: Blender context

    Returns:
        True if activation successful
    """
    try:
        logger.info("Activating Mixer extension...")

        # Register the addon functionality
        import mixer

        # Store extension state
        bpy.context.preferences.addons["mixer"].preferences.set("extension_active", True)

        logger.info("Mixer extension activated successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to activate Mixer extension: {e}")
        return False


def _deactivate_extension(context: bpy.types.Context) -> bool:
    """
    Called when the extension is deactivated (not during Blender shutdown).

    Args:
        context: Blender context

    Returns:
        True if deactivation successful
    """
    try:
        logger.info("Deactivating Mixer extension...")

        # Store extension state
        bpy.context.preferences.addons["mixer"].preferences.set("extension_active", False)

        logger.info("Mixer extension deactivated successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to deactivate Mixer extension: {e}")
        return False


def _register_extension() -> None:
    """Called when the extension module is loaded."""
    try:
        logger.info("Registering Mixer addon components...")

        # Import and register addon components
        import mixer

        # Register the core functionality
        mixer.register()

        logger.info("Mixer addon registered successfully")

    except Exception as e:
        logger.error(f"Failed to register Mixer addon: {e}")
        raise


def _unregister_extension() -> None:
    """Called when the extension module is unloaded."""
    try:
        logger.info("Unregistering Mixer addon components...")

        # Import and unregister addon components
        import mixer

        # Unregister the core functionality
        mixer.unregister()

        logger.info("Mixer addon unregistered successfully")

    except Exception as e:
        logger.error(f"Failed to unregister Mixer addon: {e}")
        raise


def register() -> None:
    """
    Alternative register function for traditional addon compatibility.
    Delegates to _register_extension() for modern extension system.
    """
    _register_extension()


def unregister() -> None:
    """
    Alternative unregister function for traditional addon compatibility.
    Delegates to _unregister_extension() for modern extension system.
    """
    _unregister_extension()


# For backward compatibility with traditional addon installation
if __name__ != "__main__":
    # Only register if we're being loaded as an addon (not directly run)
    try:
        register()
    except Exception as e:
        logger.error(f"Failed to auto-register Mixer addon: {e}")
        # Continue to allow manual registration if auto-registration fails
