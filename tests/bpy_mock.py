"""
Direct bpy execution for uv-based Blender testing
Mock subprocess/socket communication with direct bpy execution
"""
import time
import importlib
from typing import Optional, Dict, Any


class DirectBpyApp:
    """Execute Blender commands directly in the current bpy context"""

    def __init__(self, port: int = 8081):
        self.port = port
        self._bpy = None
        self._server_thread = None
        self._response_buffer = []

        # Try to import bpy - if this fails, tests will need proper bpy setup
        try:
            self._bpy = importlib.import_module('bpy')
        except ImportError:
            print("WARNING: bpy not available. Tests require bpy to be installed (uv install bpy)")
            raise MissingBpyError("bpy package not available. Install with: uv install bpy==4.5.2")

        # Initialize basic Blender scene for testing
        self._initialize_blender_scene()

    def _initialize_blender_scene(self):
        """Set up a basic Blender scene for testing"""
        if self._bpy is None:
            return

        # Ensure we have a basic scene
        if len(self._bpy.data.scenes) == 0:
            self._bpy.data.scenes.new("Scene")
            self._bpy.data.scenes[0].view_layers.new("View Layer")

        # Set the active scene
        if not self._bpy.context.scene:
            self._bpy.context.window.scene = self._bpy.data.scenes[0]

    def execute_blender_code(self, code: str, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
        """Execute Python code directly in the Blender context"""
        if self._bpy is None:
            raise MissingBpyError("bpy not available for direct execution")

        try:
            # Prepare execution environment
            exec_globals = {
                'bpy': self._bpy,
                '__builtins__': __builtins__,
                'time': time,
                # Add other commonly used modules as needed
            }
            exec_locals = {}

            # Execute the code
            compiled_code = compile(code, '<test_code>', 'exec')
            exec(compiled_code, exec_globals, exec_locals)

            return exec_locals

        except Exception as e:
            # Provide helpful error messages for test debugging
            error_msg = f"Error executing Blender code: {e}\nCode:\n{code}"
            raise BlenderExecutionError(error_msg) from e

    def send_string(self, s: str, sleep: float = 0.5):
        """Mock socket send_string - execute code directly"""
        result = self.execute_blender_code(s)
        time.sleep(sleep)  # Maintain timing for test compatibility
        return result

    def send_function(self, f, *args, **kwargs):
        """Mock socket send_function - execute function directly"""
        # Convert function to string and execute
        import inspect
        source = inspect.getsource(f)

        # Prepare argument string
        all_args = [repr(arg) for arg in args]
        all_args.extend([f"{k}={repr(v)}" for k, v in kwargs.items()])

        # Build execution code
        exec_code = "import time\n" + source + "\n" + f.__name__ + f"({', '.join(all_args)})"

        return self.execute_blender_code(exec_code)

    def setup(self, blender_args=None, env=None):
        """Mock setup - create fake server thread"""
        # In direct execution mode, no subprocess setup needed
        # Just initialize bpy if not already done
        if self._bpy is None:
            raise MissingBpyError("Cannot setup: bpy not available")

    def connect(self):
        """Mock connection - no socket needed"""
        pass  # Already connected to local bpy

    def quit(self):
        """Mock quit - no subprocess to quit"""
        pass  # Local bpy context doesn't need cleanup

    def wait(self, timeout=None):
        """Mock wait - return fake status"""
        # Return 0 to indicate "success" (fake subprocess)
        return 0 if timeout else None

    def kill(self):
        """Mock kill - no subprocess to kill"""
        pass

    def close(self):
        """Mock close - no socket to close"""
        pass


class MissingBpyError(Exception):
    """Raised when bpy package is not available"""
    pass


class BlenderExecutionError(Exception):
    """Raised when Blender code execution fails"""
    pass


# Global registry to track bpy instances for cleanup
_bpy_instances = []


def create_bpy_app(port: int = 8081) -> DirectBpyApp:
    """Factory function to create a Direct bpy app"""
    app = DirectBpyApp(port)
    _bpy_instances.append(app)
    return app


def cleanup_bpy_instances():
    """Clean up all bpy instances (call in test teardown)"""
    global _bpy_instances
    for instance in _bpy_instances:
        try:
            instance.close()
        except:
            pass  # Ignore cleanup errors
    _bpy_instances.clear()


# Provide a mock server class that returns DirectBpyApp
class MockBlenderServer:
    """Mock server that returns DirectBpyApp instances"""

    def __init__(self, port, ptvsd_port=None, wait_for_debugger=False):
        self.port = port
        self.ptvsd_port = ptvsd_port
        self.wait_for_debugger = wait_for_debugger
        self._app = None

    def start(self, blender_args=None, env_override=None):
        """Mock start - create DirectBpyApp"""
        self._app = create_bpy_app(self.port)

    def connect(self):
        """Mock connect - DirectBpyApp is always connected"""
        if self._app:
            self._app.connect()

    def send_string(self, code: str):
        """Forward to DirectBpyApp"""
        if self._app:
            return self._app.send_string(code)

    def send_function(self, f, *args, **kwargs):
        """Forward to DirectBpyApp"""
        if self._app:
            return self._app.send_function(f, *args, **kwargs)

    def quit(self):
        """Forward to DirectBpyApp"""
        if self._app:
            self._app.quit()

    def close(self):
        """Forward to DirectBpyApp"""
        if self._app:
            self._app.close()


class MockBlenderProcess:
    """Mock process that returns MockBlenderServer"""

    def __init__(self):
        self._process = None
        self.command_line = "direct bpy execution (mock)"

    def start(self, args, kwargs):
        """Do nothing - no subprocess needed"""
        self._process = MockBlenderServer(args[0] if args else 8081)

    def wait(self, timeout=None):
        """Return fake success"""
        return 0

    def kill(self):
        """No process to kill"""
        pass
