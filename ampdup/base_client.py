"""Base client for MPD."""
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import AsyncGenerator, List, Optional, Union

from anyio import create_memory_object_stream, create_task_group
from anyio.abc import ObjectStream, TaskGroup
from anyio.streams.stapled import StapledObjectStream

from .connection import Connection, Connector, Socket
from .errors import CommandError, ConnectionFailedError
from .parsing import parse_error
from .util import asynccontextmanager


def make_object_stream() -> ObjectStream:
    """Create a stapled object stream."""
    return StapledObjectStream(*create_memory_object_stream())


@dataclass
class MPDConnection:
    """A high-level connection to an MPD server."""

    task_group: TaskGroup
    pending_commands: 'ObjectStream[ObjectStream[List[str]]]' = field(
        default_factory=make_object_stream
    )
    connection: Optional[Connection] = None

    async def _connect(self):
        await self.connection.connect()
        self._start_loop()

    async def _disconnect(self):
        if self.connection is not None:
            await self.connection.close()

        self.task_group.cancel_scope.cancel()

    async def connect(self, connector: Connector):
        """Connect to the MPD server using a connector."""
        self.connection = Connection(connector)
        await self._connect()

    async def disconnect(self):
        """Disconnect from the MPD server."""
        await self._disconnect()
        self.connection = None

    async def reconnect(self):
        """Reconnect to the MPD server."""
        await self._disconnect()
        await self._connect()

    async def run_command(self, command: str) -> List[str]:
        """Run a command on the MPD server."""
        if self.connection is None:
            raise ConnectionFailedError()

        p = make_object_stream()
        await self.pending_commands.send(p)

        await self.connection.write_line(command)

        result = await p.receive()

        return result

    async def _read_response(self) -> Union[List[str], CommandError]:
        if self.connection is None:
            raise ConnectionFailedError()

        lines: List[str] = []

        while True:
            line = await self.connection.read_line()

            if line.startswith('OK'):
                break
            if line.startswith('ACK'):
                return parse_error(line, lines)

            lines.append(line)

        return lines

    def _start_loop(self):
        self.task_group.start_soon(self._reply_loop)

    async def _reply_loop(self):
        while True:
            pending = await self.pending_commands.receive()
            try:
                reply = await self._read_response()
            except Exception as e:  # pylint: disable=broad-except
                await pending.send(e)
            else:
                await pending.send(reply)


@dataclass
class BaseMPDClient:
    """Base class for MPD clients."""

    connection: Optional[MPDConnection] = None

    @classmethod
    @asynccontextmanager
    async def make(cls, address: str, port: int) -> AsyncGenerator:
        """Create a BaseMPDClient using a TCP connection.

        This should be used instead of instantiating the class directly.
        """
        async with create_task_group() as tg:
            c = cls()
            await c.connect(address, port, tg)
            yield c
            await c.disconnect()

    @classmethod
    @asynccontextmanager
    async def make_unix(cls, socket: Path) -> AsyncGenerator:
        """Create a BaseMPDClient using a Unix socket.

        This should be used instead of instantiating the class directly.
        """
        async with create_task_group() as tg:
            c = cls()
            await c.connect_unix(socket, tg)
            yield c
            await c.disconnect()

    async def connect(self, address: str, port: int, tg: TaskGroup):
        """Connect to the MPD client using TCP."""
        self.connection = MPDConnection(tg)

        await self.connection.connect(partial(Socket.connect_tcp, address, port))

    async def connect_unix(self, path: Path, tg: TaskGroup):
        """Connect to the MPD client using Unix socket."""
        self.connection = MPDConnection(tg)

        await self.connection.connect(partial(Socket.connect_unix, path))

    async def disconnect(self):
        """Disconnect from the MPD server."""
        if self.connection is not None:
            await self.connection.disconnect()

    async def reconnect(self):
        """Reconnect to the MPD server.

        Must be connected to succeed.
        """
        if self.connection is None:
            raise ConnectionFailedError('Cannot reconnect if not previously connected.')

        await self.connection.reconnect()

    async def run_command(self, command: str) -> List[str]:
        """Run a command on the MPD server."""
        if self.connection is None:
            raise ConnectionFailedError('Connection is not established.')

        return await self.connection.run_command(command)
