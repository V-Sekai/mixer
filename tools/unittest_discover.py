#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import argparse
import sys
from pathlib import Path
from typing import TextIO
from unittest import TestLoader
from unittest.runner import TextTestRunner

try:
    import bpy
    bpy_available = True
except ImportError:
    bpy_available = False

# Add the addons directory to the path so we can import mixer modules
sys.path.insert(0, str(Path(__file__).parent.parent / "addons"))

def discover_and_run_test_suite(argv: list[str], stream: TextIO) -> int:
    # Check if we're running inside Blender
    if bpy_available and bpy.app.binary_path:
        # Running inside Blender - parse arguments after "--"
        argv = argv[argv.index("--") + 1 :] if "--" in argv else []

    parser = argparse.ArgumentParser(prog=Path(__file__).name)
    parser.add_argument("-f", "--failfast", action="store_true")
    parser.add_argument("-p", "--pattern", default="test*.py")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    test_loader = TestLoader()
    test_suite = test_loader.discover(
        start_dir=str(Path(__file__).parent.parent / "tests"),
        pattern=args.pattern,
    )
    test_runner = TextTestRunner(
        stream=stream,
        failfast=args.failfast,
        verbosity=2 if args.verbose else 1,
    )
    test_result = test_runner.run(test_suite)
    return 0 if test_result.wasSuccessful() else 1

def main(argv: list[str]) -> int:
    if sys.platform == "win32":
        with open(  # noqa: PTH123
            sys.stderr.fileno(), mode="w", encoding="ansi", buffering=1
        ) as windows_stderr:
            return discover_and_run_test_suite(argv, windows_stderr)
    return discover_and_run_test_suite(argv, sys.stderr)

if __name__ == "__main__":
    sys.exit(main(sys.argv))