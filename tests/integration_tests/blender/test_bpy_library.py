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
            self.fail("bpy not available - required for library context testing")

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

class TestBpyRequirement(unittest.TestCase):
    """Test that bpy is available as required"""

    def test_bpy_must_be_available(self):
        """Test that bpy import succeeds - this is a requirement"""
        if not HAS_BPY:
            self.fail("bpy library is required but not available. Install bpy==5.0.1")
        self.assertIsNotNone(bpy)

if __name__ == '__main__':
    unittest.main()