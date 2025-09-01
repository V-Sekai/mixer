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

    def __init__(self):
        # in case @parameterized_class is missing
        if not hasattr(self, "vrtist_protocol"):
            self.vrtist_protocol = False
        super().__init__()

    def setup_method(self, *args, **kwargs):
        super().setup_method(*args, **kwargs)


class TestGeneric(BlenderTestCase):
    """Test that joins a room before message creation"""

    def __init__(self):
        self._join = True  # Default value

    def setup_method(self):
        sender_blendfile = files_folder() / "empty.blend"
        receiver_blendfile = files_folder() / "empty.blend"
        sender = BlenderDesc(load_file=sender_blendfile, wait_for_debugger=False)
        receiver = BlenderDesc(load_file=receiver_blendfile, wait_for_debugger=False)
        blenderdescs = [sender, receiver]
        super().setup_method(blenderdescs=blenderdescs, server_args=None, join=self._join)


class TestGenericJoinBefore(TestGeneric):
    """Test that joins a room before message creation"""

    def __init__(self):
        self._join = True

    def setup_method(self):
        super().setup_method()


class TestGenericJoinAfter(TestGeneric):
    """Test that does not join a room before message creation"""

    def __init__(self):
        self._join = False

    def setup_method(self):
        super().setup_method()
