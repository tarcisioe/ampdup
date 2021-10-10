"""Tests for the connection module."""
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import AsyncContextManager, AsyncIterator, Callable, Coroutine, List

import pytest
from anyio.abc import Listener, ObjectReceiveStream, SocketStream
from typing_extensions import Protocol

from ampdup.connection import Connection, ConnectionFailedError, Socket

SocketHandler = Callable[[SocketStream], Coroutine[None, None, None]]


class ServeFunction(Protocol):
    """Callable that makes a server serve as an AsyncContextManager."""

    def __call__(self, *, receive: bool = True) -> AsyncContextManager[None]:
        ...


class ListenerFactory(Protocol):
    """Callable that produces a ServerData object, as an AsyncContextManager."""

    async def __call__(self) -> Listener:
        ...


class ClientSocketFactory(Protocol):
    """Callable that produces a SocketStream that is a client of a test server."""

    async def __call__(self) -> Socket:
        ...


@dataclass
class ConfigurableSendingHandler:
    """Configurable handler for sending different kinds of data to socket clients."""

    data: List[bytes]

    async def handle(self, client: SocketStream):
        """Send data to a client."""
        for d in self.data:
            await client.send(d)


@dataclass(frozen=True)
class ServerTestData:
    """Aggregate base for the *_unix_server fixtures."""

    make_client: ClientSocketFactory
    serve: ServeFunction
    received: ObjectReceiveStream
    handler: ConfigurableSendingHandler


@dataclass(frozen=True)
class ServerFactory:
    """Aggregate class for functions to create an anyio server and connect to it."""

    make_listener: ListenerFactory
    make_client: ClientSocketFactory

    @asynccontextmanager
    async def make_test_server(self) -> AsyncIterator[ServerTestData]:
        """Create a temporary unix server."""
        from anyio import create_memory_object_stream, create_task_group
        from anyio.streams.buffered import BufferedByteReceiveStream
        from anyio.streams.stapled import StapledObjectStream

        received = StapledObjectStream(*create_memory_object_stream())

        sending_handler = ConfigurableSendingHandler([b'Test data.\n'])

        async def receive_handler(client: SocketStream):
            buffered = BufferedByteReceiveStream(client)
            while True:
                await received.send(await buffered.receive_until(b'\n', 0xFFFFFFFF))

        async def handle(client: SocketStream, *, receive: bool):
            async with client:
                async with create_task_group() as tg:
                    if receive:
                        tg.start_soon(receive_handler, client)
                    tg.start_soon(sending_handler.handle, client)

        async with await self.make_listener() as server:

            @asynccontextmanager
            async def serve_task(receive: bool = True):
                async with create_task_group() as tg:
                    tg.start_soon(server.serve, partial(handle, receive=receive))
                    yield
                    tg.cancel_scope.cancel()

            yield ServerTestData(
                self.make_client,
                serve_task,
                received,
                sending_handler,
            )


@pytest.fixture(params=['unix', 'tcp'])
async def testing_server(tmp_path: Path, request) -> AsyncIterator[ServerTestData]:
    """Fixture for creating different, parameterized, server factories."""

    from anyio import create_tcp_listener, create_unix_listener

    from ._test_util import is_asyncio, is_windows

    if request.param == 'unix' and (is_windows() or is_asyncio()):
        pytest.skip()

    sock_path = tmp_path / 'testserver'

    address, port = '127.0.0.1', 12345

    server_factory = {
        'unix': ServerFactory(
            make_listener=partial(create_unix_listener, sock_path),
            make_client=partial(Socket.connect_unix, sock_path),
        ),
        'tcp': ServerFactory(
            make_listener=partial(
                create_tcp_listener,
                local_host=address,
                local_port=port,
            ),
            make_client=partial(Socket.connect_tcp, address, port),
        ),
    }[request.param]

    async with server_factory.make_test_server() as server_data:
        yield server_data


@pytest.mark.anyio
async def test_socket_write(testing_server: ServerTestData):
    """Test for the socket.write method."""

    test_data = b'A line of data\n'

    async with AsyncExitStack() as s:
        await s.enter_async_context(testing_server.serve())
        socket = await s.enter_async_context(
            await testing_server.make_client(),
        )

        await socket.write(test_data)
        assert await testing_server.received.receive() == test_data.strip()


@pytest.mark.anyio
async def test_socket_readline(testing_server: ServerTestData):
    """Test for the socket.readline method."""
    async with AsyncExitStack() as s:
        await s.enter_async_context(testing_server.serve())
        socket = await s.enter_async_context(
            await testing_server.make_client(),
        )

        assert await socket.readline() == b'Test data.'


@pytest.mark.anyio
async def test_socket_readline_timeout(testing_server: ServerTestData):
    """Test for the socket.readline method in case no newline ever comes."""
    from ampdup.errors import ReceiveError

    testing_server.handler.data = [b'No newline :(']

    async with AsyncExitStack() as s:
        await s.enter_async_context(testing_server.serve())
        socket = await s.enter_async_context(
            await testing_server.make_client(),
        )

        with pytest.raises(ReceiveError):
            await socket.readline(timeout_seconds=0.1)


@pytest.mark.anyio
async def test_socket_readline_no_newline(testing_server: ServerTestData):
    """Test for the socket.readline method in case no newline ever comes."""
    from ampdup.errors import ReceiveError

    testing_server.handler.data = [b'No newline :(']

    async with AsyncExitStack() as s:
        await s.enter_async_context(testing_server.serve(receive=False))
        socket = await s.enter_async_context(
            await testing_server.make_client(),
        )

        with pytest.raises(ReceiveError):
            await socket.readline()


@pytest.mark.anyio
async def test_socket_readline_many_lines(testing_server: ServerTestData):
    """Test for the socket.readline method in case no newline ever comes."""
    from textwrap import dedent

    testing_server.handler.data = [
        dedent(
            '''\
            Line 1
            Line 2
            Line 3
            '''
        ).encode(),
    ]

    async with AsyncExitStack() as s:
        await s.enter_async_context(testing_server.serve())
        socket = await s.enter_async_context(await testing_server.make_client())

        assert await socket.readline() == b'Line 1'
        assert await socket.readline() == b'Line 2'
        assert await socket.readline() == b'Line 3'


@pytest.mark.anyio
async def test_socket_aclose(testing_server: ServerTestData):
    """Test for the socket.readline method in case no newline ever comes."""
    async with AsyncExitStack() as s:
        await s.enter_async_context(testing_server.serve())
        socket = await s.enter_async_context(
            await testing_server.make_client(),
        )

        await socket.aclose()


async def fail_to_make_connector() -> Socket:  # pragma: no cover
    """A Connector that always fails to create a socket."""
    raise AssertionError('This connector always fails.')


@pytest.mark.anyio
async def test_connection_write_line_disconnected():
    """Test that write_line signals error if there is no established connection."""
    connection = Connection(fail_to_make_connector)

    with pytest.raises(ConnectionFailedError):
        await connection.write_line('Test.')


@pytest.mark.anyio
async def test_connection_read_line_disconnected():
    """Test that write_line signals error if there is no established connection."""
    connection = Connection(fail_to_make_connector)

    with pytest.raises(ConnectionFailedError):
        _ = await connection.read_line()


@pytest.mark.anyio
async def test_connection_connect(testing_server: ServerTestData):
    """Test the Connection.connect method through the contextmanager interface."""
    async with AsyncExitStack() as s:
        await s.enter_async_context(testing_server.serve())

        testing_server.handler.data = [b'OK MPD\n']

        connection = Connection(testing_server.make_client)
        await connection.connect()
        await connection.aclose()


@pytest.mark.anyio
async def test_connection_connect_fail_if_server_replies_wrong_data(
    testing_server: ServerTestData,
):
    """Test that Connection fails to connect if server replies with wrong data."""
    async with AsyncExitStack() as s:
        await s.enter_async_context(testing_server.serve())

        testing_server.handler.data = [b'NOT OK MPD\n']

        with pytest.raises(ConnectionFailedError):
            _ = await s.enter_async_context(Connection(testing_server.make_client))


@pytest.mark.anyio
async def test_connection_connect_context_manager(testing_server: ServerTestData):
    """Test the Connection.connect method through the contextmanager interface."""
    async with AsyncExitStack() as s:
        await s.enter_async_context(testing_server.serve())

        testing_server.handler.data = [b'OK MPD\n']

        _ = await s.enter_async_context(Connection(testing_server.make_client))


@pytest.mark.anyio
async def test_connection_read_line(testing_server: ServerTestData):
    """Test the Connection.connect method through the contextmanager interface."""
    async with AsyncExitStack() as s:
        await s.enter_async_context(testing_server.serve())

        testing_server.handler.data = [b'OK MPD\n', b'abcdefg\n']

        connection = await s.enter_async_context(Connection(testing_server.make_client))

        assert await connection.read_line() == 'abcdefg'


@pytest.mark.anyio
async def test_connection_write_line(testing_server: ServerTestData):
    """Test the Connection.connect method through the contextmanager interface."""
    async with AsyncExitStack() as s:
        await s.enter_async_context(testing_server.serve())

        testing_server.handler.data = [b'OK MPD\n']

        connection = await s.enter_async_context(Connection(testing_server.make_client))

        await connection.write_line('abcdefg')
