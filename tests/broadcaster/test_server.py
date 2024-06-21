import threading
import time
import pytest

import itertools
from mixer.broadcaster.apps.server import Server
from mixer.broadcaster.client import Client
import mixer.broadcaster.common as common

from tests.process import ServerProcess


class Delegate:
    def __init__(self):
        self.clear()

    def clear(self):
        self.clients = None
        self.name_room = None

    def update_rooms_attributes(self, data):
        return None

    def update_clients_attributes(self, data):
        return None


def network_consumer(client, delegate):
    received_commands = client.fetch_commands()

    if received_commands is None:
        return

    for command in received_commands:
        if command.type == common.MessageType.LIST_ROOMS:
            delegate.update_rooms_attributes(command.data)
        elif command.type == common.MessageType.LIST_CLIENTS:
            clients_attributes, _ = common.decode_json(command.data, 0)
            delegate.update_clients_attributes(clients_attributes)


port_iter = itertools.count(start=common.DEFAULT_PORT)


@pytest.fixture
def server():
    _delegate = Delegate()
    _server = Server()

    while True:
        try:
            port = next(port_iter)
            server_thread = threading.Thread(target=_server.run, args=(port,))
            server_thread.start()

            time.sleep(0.5)

            yield _server, port
            
            _server.shutdown()

            break
        except Exception as e:
            print(f"Failed to start server on port {port}: {e}")
            continue


@pytest.mark.skip(reason="Temporarily disabled")
def test_connect(server):
    def delay():
        return time.sleep(0.2)

    _server, port = server

    client1 = Client(port=port)
    delay()
    assert not client1.is_connected()
    assert _server.client_count() == 0

    client1.connect()
    delay()
    assert client1.is_connected()
    assert _server.client_count() == 1

    client1.disconnect()
    delay()
    assert not client1.is_connected()
    assert _server.client_count() == 0

    #
    client2 = Client(port=port)
    client2.connect()
    delay()
    assert client2.is_connected()
    assert _server.client_count() == 1

    client3 = Client(port=port)
    client3.connect()
    delay()
    assert client3.is_connected()
    assert _server.client_count() == 2

    client2.disconnect()
    delay()
    assert not client2.is_connected()
    assert client3.is_connected()
    assert _server.client_count() == 1

    client2.disconnect()
    delay()
    assert not client2.is_connected()
    assert client3.is_connected()
    assert _server.client_count() == 1

    client3.disconnect()
    delay()
    assert not client3.is_connected()
    assert _server.client_count() == 0


def test_join_one_room_one_client(server):
    def delay():
        return time.sleep(0.2)

    _server, port = server
    c0_name = "c0_name"
    c0_room = "c0_room"

    d0 = Delegate()
    c0 = Client()
    delay()

    c0.connect()
    c0.set_client_attributes({common.ClientAttributes.USERNAME: c0_name})
    c0.join_room(c0_room, "ignored", "ignored", True, True)
    delay()
    network_consumer(c0, d0)
    assert len(_server._rooms) == 1
    assert c0_room in _server._rooms
    # assert len(d0.name_room) == 1
    # assert expected in d0.name_room


@pytest.mark.skip(reason="Temporarily disabled")
def test_join_one_room_two_clients(server):
    def delay():
        return time.sleep(0.2)

    _server, port = server

    c0_name = "c0_name"
    c0_room = "c0_room"

    c1_name = "c1_name"
    c1_room = c0_room

    d0 = Delegate()
    c0 = Client(port=port)
    c0.connect()
    delay()
    c0.join_room(c0_room, "ignored", "ignored", True, True)
    c0.set_client_attributes({common.ClientAttributes.USERNAME: c0_name})

    d1 = Delegate()
    c1 = Client(port=port)
    c1.connect()
    delay()
    c1.join_room(c1_room, "ignored", "ignored", True, True)
    c1.set_client_attributes({common.ClientAttributes.USERNAME: c1_name})

    delay()

    network_consumer(c0, d0)
    network_consumer(c1, d1)
    expected = [(c0_name, c0_room), (c1_name, c1_room)]
    assert _server.client_count() == 2
    assert len(d0.name_room) == 2
    assert len(d1.name_room) == 2
    assert set(d0.name_room) == set(expected)
    assert set(d1.name_room) == set(expected)


@pytest.mark.skip(reason="Temporarily disabled")
def test_join_one_room_two_clients_leave(server):
    def delay():
        return time.sleep(0.2)

    c0_name = "c0_name"
    c0_room = "c0_room"

    c1_name = "c1_name"
    c1_room = c0_room

    d0 = Delegate()
    c0 = Client()
    c0.connect()
    c0.join_room(c0_room, "ignored", "ignored", True, True)
    c0.set_client_attributes({common.ClientAttributes.USERNAME: c0_name})

    d1 = Delegate()
    c1 = Client()
    c1.connect()
    c1.join_room(c1_room, "ignored", "ignored", True, True)
    c1.set_client_attributes({common.ClientAttributes.USERNAME: c1_name})

    c1.leave_room(c1_room)

    delay()
    network_consumer(c0, d0)
    network_consumer(c1, d1)
    expected = [(c0_name, c0_room)]
    assert server.client_count() == (1, 1)
    assert len(d0.name_room) == 1
    assert set(d0.name_room) == set(expected)
    assert d0.name_room == d1.name_room


@pytest.mark.skip(reason="Temporarily disabled")
def test_client_is_disconnected_when_server_process_is_killed():
    server_process = ServerProcess()
    server_process.start()

    with Client(server_process.host, server_process.port) as client:
        assert client.is_connected()
        client.fetch_commands()

        server_process.kill()

        with pytest.raises(common.ClientDisconnectedException):
            client.fetch_commands()

        assert not client.is_connected()
