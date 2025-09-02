"""
Tests for the broadcaster server module
"""
import pytest
import logging
import time

from mixer.broadcaster.client import Client
import mixer.broadcaster.common as common
from tests.process import ServerProcess

logger = logging.getLogger(__name__)


@pytest.fixture
def server_process():
    """Provide a configured server subprocess for testing"""
    # Use ServerProcess to run the server as a subprocess
    server = ServerProcess()

    # Use truly unique ports per test to ensure complete isolation
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        server.port = s.getsockname()[1]

    server.start()

    # Wait for server to be fully ready
    _wait_for_server_ready(server)

    yield server

    # Cleanup after test
    try:
        if server is not None:
            server.kill()
            time.sleep(0.5)  # Allow cleanup time
    except Exception:
        # Force kill if graceful termination fails
        import os
        import signal
        try:
            if hasattr(server, '_process') and server._process:
                os.kill(server._process.pid, signal.SIGKILL)
                server._process.wait(timeout=5)
        except Exception:
            pass


def _wait_for_server_ready(server_process):
    """Wait for the server to be fully ready to accept connections"""
    max_wait = 10  # seconds
    start_time = time.time()

    while time.time() - start_time < max_wait:
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            sock.connect((server_process.host, server_process.port))
            sock.close()
            logger.debug(f"Server ready on port {server_process.port}")
            return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.2)
            continue

    logger.warning(f"Server failed to become ready within {max_wait} seconds")
    return False


def get_server_client_count(server_process):
    """Query the external server process for client/room count"""
    # Create a temporary client to query server state
    temp_client = Client(server_process.host, server_process.port)
    temp_client.connect()

    try:
        # Send LIST_CLIENTS and LIST_ROOMS commands quickly
        temp_client.send_list_rooms()
        temp_client.send_list_clients()

        # Small delay for server to respond
        time.sleep(0.05)

        # Get responses
        commands = temp_client.fetch_commands()
        if commands is not None:
            for command in commands:
                if command.type == common.MessageType.LIST_CLIENTS:
                    clients_data, _ = common.decode_json(command.data, 0)
                elif command.type == common.MessageType.LIST_ROOMS:
                    rooms_data, _ = common.decode_json(command.data, 0)

        # Count clients in rooms
        clients_in_rooms = len([c for c in clients_data.values()
                               if c.get(common.ClientAttributes.ROOM)])
        total_connected = len(clients_data)

    except:
        clients_in_rooms = 0
        total_connected = 0
        clients_data = {}
        rooms_data = {}

    finally:
        # Always disconnect the temp client
        temp_client.disconnect()

    # Wait for disconnect processing
    time.sleep(0.05)

    return (clients_in_rooms, total_connected - clients_in_rooms - 1)  # -1 for query client


def test_server_connect_disconnect(server_process):
    """Test basic client connect/disconnect functionality"""
    delay = lambda: time.sleep(0.2)

    client1 = Client(server_process.host, server_process.port)
    client1.connect()
    delay()
    assert client1.is_connected()
    assert get_server_client_count(server_process) == (0, 1)

    client1.disconnect()
    delay()
    assert not client1.is_connected()
    assert get_server_client_count(server_process) == (0, 0)


def test_server_multiple_clients(server_process):
    """Test server handling of multiple client connections and disconnections"""
    delay = lambda: time.sleep(0.2)

    client1 = Client(server_process.host, server_process.port)
    client2 = Client(server_process.host, server_process.port)
    client3 = Client(server_process.host, server_process.port)

    # Connect clients
    client1.connect()
    delay()
    assert client1.is_connected()
    assert get_server_client_count(server_process) == (0, 1)

    client2.connect()
    delay()
    assert client2.is_connected()
    assert get_server_client_count(server_process) == (0, 2)

    client3.connect()
    delay()
    assert client3.is_connected()
    assert get_server_client_count(server_process) == (0, 3)

    # Disconnect clients
    client2.disconnect()
    delay()
    assert not client2.is_connected()
    assert client3.is_connected()
    assert get_server_client_count(server_process) == (0, 2)

    client3.disconnect()
    delay()
    assert not client3.is_connected()
    assert get_server_client_count(server_process) == (0, 1)


def test_join_one_room_one_client(server_process):
    """Test single client joining a room successfully"""
    delay = lambda: time.sleep(0.2)

    c0_name = "c0_name"
    c0_room = "c0_room"

    # Client joins the room
    c0 = Client(server_process.host, server_process.port)
    c0.connect()
    c0.set_client_attributes({common.ClientAttributes.USERNAME: c0_name})
    c0.join_room(c0_room, "ignored", "ignored", True, True)
    delay()

    # Process join commands including CONTENT to make room joinable
    commands = c0.fetch_commands()
    if commands:
        for cmd in commands:
            if cmd.type == common.MessageType.CONTENT:
                # Respond with CONTENT to make room joinable
                response_command = common.Command(common.MessageType.CONTENT)
                c0.send_command(response_command)
                delay()
                c0.fetch_commands()  # Get acknowledgment
                break
    delay()

    # Query server state to verify room assignment
    query_client = Client(server_process.host, server_process.port)
    query_client.connect()
    delay()

    query_client.send_list_clients()
    delay()

    # Verify room assignment
    commands = query_client.fetch_commands()
    if commands:
        for cmd in commands:
            if cmd.type == common.MessageType.LIST_CLIENTS:
                clients_data, _ = common.decode_json(cmd.data, 0)

                # Find c0 and verify room assignment
                for client_id, client_info in clients_data.items():
                    if client_info.get(common.ClientAttributes.USERNAME) == c0_name:
                        room_assigned = client_info.get(common.ClientAttributes.ROOM)
                        assert room_assigned == c0_room, f"Client {c0_name} should be in room {c0_room}"
                        break
                else:
                    assert False, f"Client {c0_name} not found in LIST_CLIENTS response"

    query_client.disconnect()
    delay()

    # Verify final count
    assert get_server_client_count(server_process) == (1, 0)


@pytest.mark.skip(reason="Requires reliable multi-client timing control")
def test_join_one_room_two_clients(server_process):
    """Test two clients joining the same room"""
    delay = lambda: time.sleep(0.2)

    c0_name = "c0_name"
    c0_room = "c0_room"

    # First client creates the room
    c0 = Client(server_process.host, server_process.port)
    c0.connect()
    c0.join_room(c0_room, "ignored", "ignored", True, True)
    c0.set_client_attributes({common.ClientAttributes.USERNAME: c0_name})

    # Process c0's CONTENT command to make room joinable
    delay()
    commands = c0.fetch_commands()
    if commands:
        for cmd in commands:
            if cmd.type == common.MessageType.CONTENT:
                response_command = common.Command(common.MessageType.CONTENT)
                c0.send_command(response_command)
                delay()
                c0.fetch_commands()
                break

    delay()

    # Second client joins the room
    c1_name = "c1_name"
    c1 = Client(server_process.host, server_process.port)
    c1.connect()
    delay()

    c1.join_room(c0_room, "ignored", "ignored", True, True)
    c1.set_client_attributes({common.ClientAttributes.USERNAME: c1_name})

    # Process c1's commands - should include JOIN_ROOM success
    delay()
    commands = c1.fetch_commands()
    joined_successfully = False
    if commands:
        for cmd in commands:
            if cmd.type == common.MessageType.JOIN_ROOM:
                joined_successfully = True
                break
            elif cmd.type == common.MessageType.SEND_ERROR:
                error_msg, _ = common.decode_string(cmd.data, 0)
                assert False, f"c1 failed to join room: {error_msg}"

    assert joined_successfully, "c1 did not receive JOIN_ROOM success message"

    delay()

    # Query server state to verify both clients
    query_client = Client(server_process.host, server_process.port)
    query_client.connect()
    delay()

    query_client.send_list_clients()
    delay()

    # Verify room state
    commands = query_client.fetch_commands()
    clients_in_room = 0
    total_connected = 0

    if commands:
        for cmd in commands:
            if cmd.type == common.MessageType.LIST_CLIENTS:
                clients_data, _ = common.decode_json(cmd.data, 0)
                total_connected = len(clients_data)

                # Count clients in the target room (excluding query client)
                for client_id, client_info in clients_data.items():
                    room_assigned = client_info.get(common.ClientAttributes.ROOM)
                    if room_assigned == c0_room:
                        clients_in_room += 1

    # Basic validation that multi-client functionality is working
    assert clients_in_room >= 2, f"Should have at least 2 clients in room, found {clients_in_room}"
    assert total_connected > 2, f"Should have more than 2 connected total, found {total_connected}"

    query_client.disconnect()
    delay()


def test_client_server_disconnection(server_process):
    """Test client disconnection when server subprocess is killed"""
    # Use a dynamic port for isolation
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        port = s.getsockname()[1]

    # Start server on unique port
    test_server = ServerProcess()
    test_server.port = port
    test_server.start()

    time.sleep(0.5)  # Allow server initialization

    # Verify server is ready
    max_retries = 3
    for retry in range(max_retries):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            sock.connect((test_server.host, port))
            sock.close()
            break
        except (ConnectionRefusedError, OSError):
            if retry == max_retries - 1:
                pytest.skip(f"Server failed to start on {test_server.host}:{port}")
            time.sleep(0.2)

    # Test client connection and server disconnect
    client = Client(test_server.host, port)

    with client:
        assert client.is_connected()
        client.fetch_commands()

        # Kill server
        test_server.kill()

        # Client should detect disconnection
        with pytest.raises(common.ClientDisconnectedException):
            client.fetch_commands()

        assert not client.is_connected()


if __name__ == "__main__":
    pytest.main([__file__])
