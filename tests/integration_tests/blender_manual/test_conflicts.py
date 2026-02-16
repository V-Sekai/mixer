"""
Tests for conflicting operations that are sensitive to network timings,
for instance rename a collection on one side and add to collection on the other side.

Such conflits need a server with throttling control to reproduce the problem reliably.

So far, the tests cannot really be automated on CI/CD since they require lengthy wait
until all the messages are flushed and processed at the end before grabbing
the messages from all Blender
"""
from pathlib import Path
import unittest
import time

from tests.integration_tests.blender.blender_testcase import BlenderTestCase
from tests.test_helpers.mixer_testcase import BlenderDesc


class ThrottledTestCase(BlenderTestCase):
    def setUp(self, startup_file: str = "file2.blend"):
        try:
            files_folder = Path(__file__).parent / "files"
            file = files_folder / startup_file
            blenderdesc = BlenderDesc(load_file=file)
            blenderdescs = [blenderdesc, BlenderDesc()]

            self.latency = 1
            latency_ms = 1000 * self.latency
            server_args = ["--latency", str(latency_ms)]
            super().setUp(blenderdescs=blenderdescs, server_args=server_args)

        except Exception:
            self.shutdown()
            raise

    def assert_matches(self):
        # Wait for the messages to reach the destination
        # TODO What os just enough ?
        time.sleep(5 * self.latency)
        super().assert_matches()


if __name__ == "__main__":
    unittest.main()
