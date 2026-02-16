"""
Test demonstrating two Blender instances synchronizing using uv bpy
"""
import unittest
import subprocess
import tempfile
import time
import threading
import socket
from pathlib import Path
from mixer.broadcaster.common import encode_int

class TestTwoBlenderSync(unittest.TestCase):
    """Test demonstrating synchronization between two uv bpy instances"""

    def test_uv_bpy_subprocess_communication(self):
        """Test that uv bpy subprocesses can communicate and execute bpy operations"""

        # Create a simple server script that can execute bpy commands
        server_script = '''
import socket
import bpy
import struct
from mixer.broadcaster.common import encode_int

# Create a simple socket server
HOST = "127.0.0.1"
PORT = 9999

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print(f"Server listening on {HOST}:{PORT}")

client_socket, addr = server_socket.accept()
print(f"Connection from {addr}")

# Receive and execute commands
try:
    # Receive length
    length_data = client_socket.recv(4)
    length = struct.unpack("!I", length_data)[0]

    # Receive command
    command_data = client_socket.recv(length)
    command = command_data.decode("utf-8")
    print(f"Executing: {command[:50]}...")

    # Execute the command
    exec(command)
    response = "OK"

    # Send response back
    response_data = response.encode("utf-8")
    client_socket.send(encode_int(len(response_data)))
    client_socket.send(response_data)

except Exception as e:
    print(f"Error: {e}")
    response = f"ERROR: {e}"
    response_data = response.encode("utf-8")
    client_socket.send(encode_int(len(response_data)))
    client_socket.send(response_data)

client_socket.close()
server_socket.close()
print("Server shutdown")
'''

        # Create a client script that sends a command
        client_script = '''
import socket
import bpy
import struct
from mixer.broadcaster.common import encode_int

HOST = "127.0.0.1"
PORT = 9999

# Connect to server
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

# Send a command to create a cube
command = """
bpy.ops.mesh.primitive_cube_add()
cube = bpy.context.active_object
cube.name = 'TestCube'
print(f'Created cube: {cube.name} at {cube.location}')
"""

command_data = command.encode("utf-8")
sock.send(encode_int(len(command_data)))
sock.send(command_data)

# Receive response
length_data = sock.recv(4)
length = struct.unpack("!I", length_data)[0]
response_data = sock.recv(length)
response = response_data.decode("utf-8")

print(f"Response: {response}")

sock.close()
'''

        # Write scripts to temp files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as server_file:
            server_file.write(server_script)
            server_path = server_file.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as client_file:
            client_file.write(client_script)
            client_path = client_file.name

        try:
            # Start server subprocess
            server_cmd = ["uv", "run", "python", server_path]
            server_proc = subprocess.Popen(
                server_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait a bit for server to start
            time.sleep(2)

            # Start client subprocess
            client_cmd = ["uv", "run", "python", client_path]
            client_proc = subprocess.Popen(
                client_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait for both to complete
            client_stdout, client_stderr = client_proc.communicate(timeout=10)
            server_stdout, server_stderr = server_proc.communicate(timeout=10)

            print("Client stdout:", client_stdout)
            print("Client stderr:", client_stderr)
            print("Server stdout:", server_stdout)
            print("Server stderr:", server_stderr)

            # Check results
            self.assertEqual(client_proc.returncode, 0, f"Client failed: {client_stderr}")
            self.assertEqual(server_proc.returncode, 0, f"Server failed: {server_stderr}")
            self.assertIn("Created cube", server_stdout)
            self.assertIn("TestCube", server_stdout)
            self.assertIn("OK", client_stdout)

        finally:
            # Clean up temp files
            Path(server_path).unlink(missing_ok=True)
            Path(client_path).unlink(missing_ok=True)

if __name__ == '__main__':
    unittest.main()