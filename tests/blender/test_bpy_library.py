"""
Test bpy library functionality - runs with only bpy, no full Blender
"""
import unittest

try:
    import bpy
    HAS_BPY = True
except ImportError:
    HAS_BPY = False
    bpy = None

class TestBpyLibrary(unittest.TestCase):
    """Test basic bpy functionality in library context"""

    def setUp(self):
        if not HAS_BPY:
            self.skipTest("bpy not available - not running in Blender context")

    def test_bpy_import(self):
        """Test that bpy can be imported"""
        self.assertIsNotNone(bpy)

    def test_bpy_version(self):
        """Test that bpy has version info"""
        self.assertTrue(hasattr(bpy, 'app'))
        self.assertTrue(hasattr(bpy.app, 'version'))
        # Should be at least version 5.0 for bpy==5.0.1
        version = bpy.app.version
        self.assertGreaterEqual(version[0], 5)

    def test_bpy_types_available(self):
        """Test that bpy.types is available"""
        self.assertTrue(hasattr(bpy, 'types'))
        # Check some basic types exist
        self.assertTrue(hasattr(bpy.types, 'Object'))
        self.assertTrue(hasattr(bpy.types, 'Scene'))
        self.assertTrue(hasattr(bpy.types, 'Mesh'))

    def test_bpy_data_available(self):
        """Test that bpy.data is available"""
        self.assertTrue(hasattr(bpy, 'data'))

    def test_bpy_context_available(self):
        """Test that bpy.context is available"""
        self.assertTrue(hasattr(bpy, 'context'))

    def test_bpy_props_available(self):
        """Test that bpy.props is available"""
        self.assertTrue(hasattr(bpy, 'props'))

    def test_bpy_utils_available(self):
        """Test that bpy.utils is available"""
        self.assertTrue(hasattr(bpy, 'utils'))

class TestBpyStandalone(unittest.TestCase):
    """Test bpy library compatibility without Blender"""

    def test_bpy_import_attempt(self):
        """Test that bpy import attempt is handled gracefully"""
        if HAS_BPY:
            self.assertIsNotNone(bpy)
        else:
            # If bpy is not available, that's expected in CI/CD
            self.skipTest("bpy not available - expected in CI/CD environment")

if __name__ == '__main__':
    unittest.main()