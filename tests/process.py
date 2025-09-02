import inspect
import logging
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from typing import Any, Callable, Iterable, List, Mapping, Optional

import tests.blender_lib as blender_lib

from mixer.broadcaster.common import DEFAULT_PORT, encode_int

# Try to import bpy mock classes for direct execution
try:
    from tests.bpy_mock import DirectBpyApp, MockBlenderServer, MissingBpyError
    _bpy_available = True
    print("✅ bpy available - using direct execution mode")
except ImportError as e:
    _bpy_available = False
    print(f"⚠️  bpy not available - falling back to subprocess mode: {e}")

"""
The idea is to automate Blender / Blender tests

Sender Blender executes the test script
- join a room
- load a file
- perform changes (core of the tests)
- save the file
- do not leave the room

Receiver Blender
- join the room after Sender
- "wait" for the changes
- save the file

Diff the scenes
"""

logger = logging.getLogger(__name__)

current_dir = Path(__file__).parent

# HACKS for io redirection
# - with xmlrunner (used on Gitlab), stdout will be a xmlrunner.result._DuplicateWriter
# and redirecting onto it raises "io.UnsupportedOperation: fileno"
# so use stderr
# - with VScode Test UI (Test Explorer UI), redirecting to stderr causes a deadlock
# between Blender an the unittest during room grabbing.
#
# So redirect to stderr if we believe that we run in a Gitlab runner.
# Better ideas welcome

if os.getenv("CI_RUNNER_VERSION"):
    _popen_redirect = {
        "stdout": sys.stderr,
        "stderr": sys.stderr,
    }
else:
    _popen_redirect = {}


def blender_exe_path() -> str:
    # When using bpy from uv, we don't need a separate Blender executable
    # The bpy package provides the Blender API directly in our Python environment
    import bpy
    return None


class Process:
    """
    Simple wrapper around subprocess.Popen
    """

    def __init__(self):
        self._process: subprocess.Popen = None
        self.command_line: str = None

    def start(self, args, kwargs):
        logger.info("Running subprocess.Popen()")
        logger.info(f"args:   {args}")
        logger.info(f"kwargs: {kwargs}")
        self.command_line = " ".join(args)
        logger.info(f"command line: {self.command_line}")
        try:
            self._process = subprocess.Popen(args, **kwargs)
            logger.info("subprocess.popen: success")
        except Exception as e:
            logger.error("Python.start(): Exception raised during subprocess.Popen(): ")
            logger.error(f"{e!r}")
            logger.error(f"args:   {args}")
            logger.error(f"kwargs: {kwargs}")
            logger.error(f"command line: {self.command_line}")
            raise

    def wait(self, timeout: float = None):
        try:
            return self._process.wait(timeout)
        except subprocess.TimeoutExpired:
            return None

    def kill(self, timeout: float = None):
        if self._process is None:
            return
        self._process.kill()
        self.wait(timeout)
        self._process = None


class BlenderProcess(Process):
    """
    Work with the bpy process in the same Python environment
    When using bpy from uv, we're already running in Blender's context
    """

    def __init__(self):
        super().__init__()
        self._cmd_args = []
        self._use_in_process_bpy = True  # When using bpy from uv

        # Use DirectBpyApp if available (uv + bpy setup)
        if _bpy_available:
            self._bpy_app = DirectBpyApp()
        else:
            self._bpy_app = None

    def start(
        self,
        python_script_path: str = None,
        script_args: Optional[List[Any]] = None,
        blender_args: Optional[List[str]] = None,
        env: Optional[List[str]] = None,
    ):
        # When using bpy from uv, we're already in Blender context
        # No need to start separate processes
        if blender_exe_path() is None:
            # Using bpy from uv - already in Blender context
            return

        # Fallback for when using external Blender executable
        popen_args = [blender_exe_path()]
        popen_args.extend(self._cmd_args)
        if blender_args is not None:
            popen_args.extend(blender_args)
        if python_script_path is not None:
            popen_args.extend(["--python", str(python_script_path)])
        if script_args is not None:
            popen_args.append("--")
            popen_args.extend([str(arg) for arg in script_args])

        popen_kwargs = {
            "shell": False,
            "env": env,
        }

        if os.name == 'nt':
            popen_kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE

        popen_kwargs.update(_popen_redirect)
        super().start(popen_args, popen_kwargs)


class BlenderServer(BlenderProcess):
    """
    Starts a Blender process that runs a python server. The Blender can be controlled
    by sending python source code.

    When bpy is available (uv + bpy setup), this creates a MockBlenderServer that
    delegates to DirectBpyApp for direct code execution.
    """

    def __init__(self, port: int, ptvsd_port: int = None, wait_for_debugger=False):
        if _bpy_available:
            # Use mock server for direct bpy execution
            self._mock_server = MockBlenderServer(port, ptvsd_port, wait_for_debugger)
            self._use_mock = True
        else:
            # Use subprocess/socket approach
            super().__init__()
            self._port = port
            self._ptvsd_port = ptvsd_port
            self._wait_for_debugger = wait_for_debugger
            self._path = str(current_dir / "python_server.py")
            self._sock: socket.socket = None
            self._use_mock = False

    def start(self, blender_args: List = None, env_override: Optional[Mapping[str, str]] = None):
        if self._use_mock:
            # Use mock server for direct bpy execution
            return self._mock_server.start(blender_args, env_override)

        # Original subprocess approach
        args = [f"--port={self._port}"]
        if self._ptvsd_port is not None:
            args.append(f"--ptvsd={self._ptvsd_port}")
        if self._wait_for_debugger:
            args.append("--wait_for_debugger")

        env = os.environ.copy()
        if env_override is not None:
            env.update(env_override)

        # The testcase will start its own server and control its configuration.
        # If it fails we want to know and not have Blender silently start a misconfigured one
        env["MIXER_NO_START_SERVER"] = "1"

        super().start(self._path, args, blender_args, env=env)

    def connect(self):
        if self._use_mock:
            return self._mock_server.connect()

        # Original socket connection approach
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setblocking(True)
        connected = False

        # anti-virus might delay if Blender is launched for the first time
        # allow time to attach debugger
        if self._wait_for_debugger:
            max_wait = sys.maxsize
        else:
            max_wait = 20

        start = time.monotonic()
        while not connected and time.monotonic() - start < max_wait:
            try:
                self._sock.connect(("127.0.0.1", self._port))
                connected = True
            except ConnectionRefusedError:
                pass

        if not connected:
            message = (
                f"Cannot connect to Blender at 127.0.0.1:{self._port} after {int(time.monotonic() - start)} seconds.\n"
                + f"Command line was: {self.command_line}"
            )

            raise RuntimeError(message)

    def close(self):
        if self._use_mock:
            return self._mock_server.close()

        # Original socket shutdown
        if self._sock is not None:
            self._sock.close()

    def send_string(self, script: str):
        if self._use_mock:
            return self._mock_server.send_string(script)

        # Original socket communication
        # ensure that Blender processes the scripts one by one,
        # otherwise they get buffered here on startup and Blender gets all the scripts at once before
        # the initial synchronization is done
        buffer = script.encode("utf-8")
        length_buffer = encode_int(len(buffer))
        self._sock.send(length_buffer)
        self._sock.send(buffer)

    def send_function(self, f: Callable, *args, **kwargs):
        if self._use_mock:
            return self._mock_server.send_function(f, *args, **kwargs)

        # Original socket-based function execution
        """
        Remotely execute a function.

        Extracts the source code from the function f.
        The def statement must not be indented (no local function)
        """
        src = inspect.getsource(f)
        kwargs_ = [f"{key}={repr(value)}" for key, value in kwargs.items()]
        args_ = [f"{repr(arg)}" for arg in args]
        args_.extend(kwargs_)
        arg_string = "" if args_ is None else ",".join(args_)
        source = f"{src}\n{f.__name__}({arg_string})\n"
        self.send_string(source)

    def quit(self):
        if self._use_mock:
            return self._mock_server.quit()

        # Original quit via socket
        self.send_function(blender_lib.quit)


class PythonProcess(Process):
    """
    Starts a Blender python process that runs a script
    """

    def __init__(self):
        super().__init__()
        # Use the same Python interpreter as the parent process
        import sys
        self._python_path = sys.executable
        logger.info(f"Using python : {self._python_path}")

    def start(self, args: Optional[Iterable[Any]] = ()) -> str:
        popen_args = [self._python_path]
        popen_args.extend([str(arg) for arg in args])

        # stdout will be a xmlrunner.result._DuplicateWriter
        # and redirecting onto it raises "io.UnsupportedOperation: fileno"
        popen_kwargs = {
            "shell": False,
        }

        # Only add this flag if the OS is Windows
        if os.name == 'nt':
            popen_kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE

        # Pass PYTHONPATH to subprocess so it can import mixer modules
        env = os.environ.copy()
        current_pythonpath = env.get('PYTHONPATH', '')
        if current_pythonpath:
            env['PYTHONPATH'] = current_pythonpath + os.pathsep + os.getcwd()
        else:
            env['PYTHONPATH'] = os.getcwd()

        popen_kwargs["env"] = env

        popen_kwargs.update(_popen_redirect)

        return super().start(popen_args, popen_kwargs)

class ServerProcess(PythonProcess):
    """
    Starts a broadcaster process
    """

    def __init__(self):
        super().__init__()
        self.port: int = int(os.environ.get("VRTIST_PORT", DEFAULT_PORT))
        self.host: str = "127.0.0.1"

    def start(self, server_args: Optional[List[str]] = None):
        # do not use an existing server, since it might not be ours and might not be setup
        # the way we want (throttling)
        try:
            self._test_connect(None)
        except ConnectionRefusedError:
            pass
        else:
            raise RuntimeError(f"A server listening at {self.host}:{self.port} already exists. Aborting")

        args = ["-m", "mixer.broadcaster.apps.server"]
        args.extend(["--port", str(self.port)])
        args.extend(["--log-level", "WARNING"])
        if server_args:
            args.extend(server_args)
        super().start(args)
        self._test_connect(timeout=4)

    def _test_connect(self, timeout: float = 0.0):
        waited = 0.0
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self.host, self.port))
        except ConnectionRefusedError as e:
            if timeout is None:
                raise
            if waited >= timeout:
                message = f"Cannot connect to broadcaster at {self.host}{self.port} after {waited} seconds.\n"
                f"Exception: {e!r}\n"
                f"Command line was: {self.command_line}"
                raise RuntimeError(message)
            delay = 0.2
            time.sleep(delay)
            waited += delay
        finally:
            sock.close()
