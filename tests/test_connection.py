"""Tests for the connection module."""
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import AsyncContextManager, AsyncIterator, Callable, Coroutine

import pytest
from anyio import connect_unix, create_memory_object_stream
from anyio.abc import ObjectReceiveStream, SocketStream
from anyio.streams.stapled import StapledObjectStream
from typing_extensions import Protocol

from ampdup.connection import Socket

SocketHandler = Callable[[SocketStream], Coroutine[None, None, None]]


class ServeFunction(Protocol):
    """Callable that makes a server serve.

    Hack because mypy hates callable attributes.
    """

    def __call__(self) -> AsyncContextManager[None]:
        ...


class SocketStreamMaker(Protocol):
    """Callable that produces a SocketStream.

    Hack because mypy hates callable attributes.
    """

    def __call__(self) -> Coroutine[None, None, SocketStream]:
        ...


@asynccontextmanager
async def unix_server(
    sock_path: Path,
    handle: SocketHandler,
) -> AsyncIterator[ServeFunction]:
    """Create a temporary unix server."""
    from anyio import create_task_group, create_unix_listener

    async with await create_unix_listener(sock_path) as server:

        @asynccontextmanager
        async def serve_task():
            async with create_task_group() as tg:
                tg.start_soon(server.serve, handle)
                yield
                tg.cancel_scope.cancel()

        yield serve_task


@asynccontextmanager
async def tcp_server(
    local_host: str,
    local_port: int,
    handle: SocketHandler,
) -> AsyncIterator[ServeFunction]:
    """Create a temporary unix server."""
    from anyio import create_task_group, create_tcp_listener

    async with await create_tcp_listener(
        local_host=local_host, local_port=local_port
    ) as server:

        @asynccontextmanager
        async def serve_task():
            async with create_task_group() as tg:
                tg.start_soon(server.serve, handle)
                yield
                tg.cancel_scope.cancel()

        yield serve_task


@dataclass(frozen=True)
class ServerData:
    """Aggregate base for the *_unix_server fixtures."""

    connect_to_server: SocketStreamMaker
    serve: ServeFunction


@dataclass(frozen=True)
class ReceivingServerData(ServerData):
    """Aggregate for the receiving_unix_server fixture."""

    received: ObjectReceiveStream


@pytest.fixture
async def receiving_unix_server(tmpdir: Path) -> AsyncIterator[ReceivingServerData]:
    """A temporary unix-socket based server."""
    from anyio.streams.buffered import BufferedByteReceiveStream

    received = StapledObjectStream(*create_memory_object_stream())

    sock_path = tmpdir / 'tempsocket'

    async def handle(client: SocketStream):
        buffered = BufferedByteReceiveStream(client)
        async with client:
            await received.send(await buffered.receive_until(b'\n', 0xFFFFFFFF))

    async with unix_server(sock_path, handle) as serve_task:
        yield ReceivingServerData(
            partial(connect_unix, sock_path),
            serve_task,
            received.receive_stream,
        )


@dataclass
class ConfigurableSendingHandler:
    """Configurable handler for sending different kinds of data to socket clients."""

    data: bytes

    async def handle(self, client: SocketStream):
        """Send data to a client."""
        async with client:
            await client.send(self.data)


@dataclass(frozen=True)
class SendingServerData(ServerData):
    """Aggregate for the sending_unix_server fixture."""

    handler: ConfigurableSendingHandler


@pytest.fixture
async def sending_unix_server(tmpdir: Path) -> AsyncIterator[ServerData]:
    """A unix-socket based server which sends data to its clients."""
    sock_path = tmpdir / 'tempsocket'

    handler = ConfigurableSendingHandler(b'Test data.\n')

    async with unix_server(sock_path, handler.handle) as serve_task:
        yield SendingServerData(partial(connect_unix, sock_path), serve_task, handler)


@pytest.mark.anyio
async def test_socket_write(receiving_unix_server: ReceivingServerData):
    """Test for the socket.write method."""

    test_data = b'A line of data\n'

    async with AsyncExitStack() as s:
        await s.enter_async_context(receiving_unix_server.serve())
        socket_stream = await s.enter_async_context(
            await receiving_unix_server.connect_to_server()
        )

        socket = Socket(socket_stream)
        await socket.write(test_data)
        assert await receiving_unix_server.received.receive() == test_data.strip()


@pytest.mark.anyio
async def test_socket_readline(sending_unix_server: SendingServerData):
    """Test for the socket.readline method."""
    async with AsyncExitStack() as s:
        await s.enter_async_context(sending_unix_server.serve())
        socket_stream = await s.enter_async_context(
            await sending_unix_server.connect_to_server()
        )

        socket = Socket(socket_stream)
        assert await socket.readline() == b'Test data.'


@pytest.mark.anyio
async def test_socket_readline_no_newline(sending_unix_server: SendingServerData):
    """Test for the socket.readline method in case no newline ever comes."""
    from ampdup.errors import ReceiveError

    sending_unix_server.handler.data = b'No newline :('

    async with AsyncExitStack() as s:
        await s.enter_async_context(sending_unix_server.serve())
        socket_stream = await s.enter_async_context(
            await sending_unix_server.connect_to_server()
        )

        socket = Socket(socket_stream)
        with pytest.raises(ReceiveError):
            await socket.readline()


@pytest.mark.anyio
async def test_socket_readline_many_lines(sending_unix_server: SendingServerData):
    """Test for the socket.readline method in case no newline ever comes."""
    from textwrap import dedent

    sending_unix_server.handler.data = dedent(
        '''\
        Line 1
        Line 2
        Line 3
        '''
    ).encode()

    async with AsyncExitStack() as s:
        await s.enter_async_context(sending_unix_server.serve())
        socket_stream = await s.enter_async_context(
            await sending_unix_server.connect_to_server()
        )

        socket = Socket(socket_stream)
        assert await socket.readline() == b'Line 1'
        assert await socket.readline() == b'Line 2'
        assert await socket.readline() == b'Line 3'


@pytest.mark.anyio
async def test_socket_aclose(sending_unix_server: SendingServerData):
    """Test for the socket.readline method in case no newline ever comes."""
    async with AsyncExitStack() as s:
        await s.enter_async_context(sending_unix_server.serve())
        socket_stream = await s.enter_async_context(
            await sending_unix_server.connect_to_server()
        )

        socket = Socket(socket_stream)
        await socket.aclose()
