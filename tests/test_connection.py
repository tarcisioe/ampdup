"""Tests for the connection module."""
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncContextManager, AsyncIterator, Callable, Coroutine, List

import pytest
from anyio.abc import Listener, ObjectReceiveStream, SocketStream
from typing_extensions import Protocol

from ampdup.connection import Connection, ConnectionFailedError, Socket

SocketHandler = Callable[[SocketStream], Coroutine[None, None, None]]


class ServeFunction(Protocol):
    """Callable that makes a server serve as an AsyncContextManager."""

    def __call__(self) -> AsyncContextManager[None]:
        ...


class ListenerFactory(Protocol):
    """Callable that produces a ServerData object, as an AsyncContextManager."""

    async def __call__(self) -> Listener:
        ...


class ClientSocketFactory(Protocol):
    """Callable that produces a SocketStream that is a client of a test server."""

    async def __call__(self) -> Socket:
        ...


@dataclass(frozen=True)
class ServerTestData:
    """Aggregate base for the *_unix_server fixtures."""

    make_client: ClientSocketFactory
    serve: ServeFunction


@dataclass(frozen=True)
class ServerFactory:
    """Aggregate class for functions to create an anyio server and connect to it."""

    make_listener: ListenerFactory
    make_client: ClientSocketFactory

    @asynccontextmanager
    async def make_test_server(
        self, handler: SocketHandler
    ) -> AsyncIterator[ServerTestData]:
        """Create a temporary unix server."""
        from anyio import create_task_group

        async with await self.make_listener() as server:

            @asynccontextmanager
            async def serve_task():
                async with create_task_group() as tg:
                    tg.start_soon(server.serve, handler)
                    yield
                    tg.cancel_scope.cancel()

            yield ServerTestData(self.make_client, serve_task)


@pytest.fixture(params=['unix', 'tcp'])
async def server_factory(tmp_path: Path, request) -> ServerFactory:
    """Fixture for creating different, parameterized, server factories."""

    from functools import partial

    from ._test_util import is_windows

    if request.param == 'unix' and is_windows():
        pytest.skip()

    async def _make_unix_server_factory() -> ServerFactory:
        """Create a temporary unix server."""
        from anyio import create_unix_listener

        sock_path = tmp_path / 'testserver'

        return ServerFactory(
            make_listener=partial(create_unix_listener, sock_path),
            make_client=partial(Socket.connect_unix, sock_path),
        )

    async def _make_tcp_server_factory() -> ServerFactory:
        """Create a temporary TCP server."""
        from anyio import create_tcp_listener

        address = '127.0.0.1'
        port = 12345

        return ServerFactory(
            make_listener=partial(
                create_tcp_listener, local_host=address, local_port=port
            ),
            make_client=partial(Socket.connect_tcp, address, port),
        )

    server_factory = await (
        {
            'unix': _make_unix_server_factory,
            'tcp': _make_tcp_server_factory,
        }[request.param]()
    )

    return server_factory


@dataclass(frozen=True)
class ReceivingServerData(ServerTestData):
    """Aggregate for the receiving_unix_server fixture."""

    received: ObjectReceiveStream


@pytest.fixture
async def receiving_server(
    server_factory: ServerFactory,
) -> AsyncIterator[ReceivingServerData]:
    """A temporary unix-socket based server."""

    from anyio import create_memory_object_stream
    from anyio.streams.buffered import BufferedByteReceiveStream
    from anyio.streams.stapled import StapledObjectStream

    received = StapledObjectStream(*create_memory_object_stream())

    async def handle(client: SocketStream):
        buffered = BufferedByteReceiveStream(client)
        async with client:
            await received.send(await buffered.receive_until(b'\n', 0xFFFFFFFF))

    async with server_factory.make_test_server(handle) as server_data:
        yield ReceivingServerData(
            server_data.make_client,
            server_data.serve,
            received.receive_stream,
        )


@dataclass
class ConfigurableSendingHandler:
    """Configurable handler for sending different kinds of data to socket clients."""

    data: List[bytes]

    async def handle(self, client: SocketStream):
        """Send data to a client."""
        async with client:
            for d in self.data:
                await client.send(d)


@dataclass(frozen=True)
class SendingServerData(ServerTestData):
    """Aggregate for the sending_unix_server fixture."""

    handler: ConfigurableSendingHandler


@pytest.fixture
async def sending_server(
    server_factory: ServerFactory,
) -> AsyncIterator[SendingServerData]:
    """A unix-socket based server which sends data to its clients."""
    handler = ConfigurableSendingHandler([b'Test data.\n'])

    async with server_factory.make_test_server(handler.handle) as server_data:
        yield SendingServerData(
            server_data.make_client,
            server_data.serve,
            handler,
        )


@pytest.mark.anyio
async def test_socket_write(receiving_server: ReceivingServerData):
    """Test for the socket.write method."""

    test_data = b'A line of data\n'

    async with AsyncExitStack() as s:
        await s.enter_async_context(receiving_server.serve())
        socket = await s.enter_async_context(
            await receiving_server.make_client(),
        )

        await socket.write(test_data)
        assert await receiving_server.received.receive() == test_data.strip()


@pytest.mark.anyio
async def test_socket_readline(sending_server: SendingServerData):
    """Test for the socket.readline method."""
    async with AsyncExitStack() as s:
        await s.enter_async_context(sending_server.serve())
        socket = await s.enter_async_context(
            await sending_server.make_client(),
        )

        assert await socket.readline() == b'Test data.'


@pytest.mark.anyio
async def test_socket_readline_no_newline(sending_server: SendingServerData):
    """Test for the socket.readline method in case no newline ever comes."""
    from ampdup.errors import ReceiveError

    sending_server.handler.data = [b'No newline :(']

    async with AsyncExitStack() as s:
        await s.enter_async_context(sending_server.serve())
        socket = await s.enter_async_context(
            await sending_server.make_client(),
        )

        with pytest.raises(ReceiveError):
            await socket.readline()


@pytest.mark.anyio
async def test_socket_readline_many_lines(sending_server: SendingServerData):
    """Test for the socket.readline method in case no newline ever comes."""
    from textwrap import dedent

    sending_server.handler.data = [
        dedent(
            '''\
            Line 1
            Line 2
            Line 3
            '''
        ).encode(),
    ]

    async with AsyncExitStack() as s:
        await s.enter_async_context(sending_server.serve())
        socket = await s.enter_async_context(await sending_server.make_client())

        assert await socket.readline() == b'Line 1'
        assert await socket.readline() == b'Line 2'
        assert await socket.readline() == b'Line 3'


@pytest.mark.anyio
async def test_socket_aclose(sending_server: SendingServerData):
    """Test for the socket.readline method in case no newline ever comes."""
    async with AsyncExitStack() as s:
        await s.enter_async_context(sending_server.serve())
        socket = await s.enter_async_context(
            await sending_server.make_client(),
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
async def test_connection_connect(sending_server: SendingServerData):
    """Test the Connection.connect method through the contextmanager interface."""
    async with AsyncExitStack() as s:
        await s.enter_async_context(sending_server.serve())

        sending_server.handler.data = [b'OK MPD\n']

        connection = Connection(sending_server.make_client)
        await connection.connect()
        await connection.aclose()


@pytest.mark.anyio
async def test_connection_connect_fail_if_server_replies_wrong_data(
    sending_server: SendingServerData,
):
    """Test that Connection fails to connect if server replies with wrong data."""
    async with AsyncExitStack() as s:
        await s.enter_async_context(sending_server.serve())

        sending_server.handler.data = [b'NOT OK MPD\n']

        with pytest.raises(ConnectionFailedError):
            _ = await s.enter_async_context(Connection(sending_server.make_client))


@pytest.mark.anyio
async def test_connection_connect_context_manager(sending_server: SendingServerData):
    """Test the Connection.connect method through the contextmanager interface."""
    async with AsyncExitStack() as s:
        await s.enter_async_context(sending_server.serve())

        sending_server.handler.data = [b'OK MPD\n']

        _ = await s.enter_async_context(Connection(sending_server.make_client))
