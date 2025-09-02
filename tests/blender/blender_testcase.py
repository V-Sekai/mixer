"""
Test case for the Full Blender protocol
"""
import logging
import sys

from tests import files_folder
from tests.mixer_testcase import BlenderDesc, MixerTestCase


logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
logger = logging.getLogger(__name__)


class BlenderTestCase(MixerTestCase):
    """
    Test case for the Full Blender protocol
    """

    def __init__(self, *args, **kwargs):
        # in case @parameterized_class is missing
        if not hasattr(self, "vrtist_protocol"):
            self.vrtist_protocol = False
        super().__init__(*args, **kwargs)

        # Add failureException for unittest compatibility
        self.failureException = AssertionError

    def setup_method(self, method):
        super().setup_method()


def create_basic_blender_setup(join=True):
    """Helper function to create basic Blender setup"""
    sender_blendfile = files_folder() / "empty.blend"
    receiver_blendfile = files_folder() / "empty.blend"
    sender = BlenderDesc(load_file=sender_blendfile, wait_for_debugger=False)
    receiver = BlenderDesc(load_file=receiver_blendfile, wait_for_debugger=False)
    blenderdescs = [sender, receiver]
    return blenderdescs


class TestGeneric(BlenderTestCase):
    """Test that joins a room before message creation"""

    def setup_method(self, method):
        blenderdescs = create_basic_blender_setup(join=True)
        super().setup_method(blenderdescs=blenderdescs, server_args=None, join=True)


class TestGenericJoinBefore(TestGeneric):
    """Test that joins a room before message creation"""

    def setup_method(self, method):
        blenderdescs = create_basic_blender_setup(join=True)
        super().setup_method(blenderdescs=blenderdescs, server_args=None, join=True)


class TestGenericJoinAfter(TestGeneric):
    """Test that does not join a room before message creation"""

    def setup_method(self, method):
        blenderdescs = create_basic_blender_setup(join=False)
        super().setup_method(blenderdescs=blenderdescs, server_args=None, join=False)
