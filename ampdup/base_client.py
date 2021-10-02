"""Base client for MPD."""
from asyncio import (  # pylint:disable=unused-import
    CancelledError,
    Future,
    Queue,
    Task,
    create_task,
    get_running_loop,
)
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncGenerator, List, Optional, Union

from .connection import Connection, Connector, TCPConnector, UnixConnector
from .errors import CommandError, ConnectionFailedError
from .parsing import parse_error
from .util import asynccontextmanager


@dataclass
class MPDConnection:
    """A high-level connection to an MPD server."""

    pending_commands: 'Queue[Future[List[str]]]' = field(default_factory=Queue)
    connection: Optional[Connection] = None
    loop: Optional[Task] = None

    async def _connect(self):
        await self.connection.connect()
        self._start_loop()

    async def _disconnect(self):
        if self.connection is not None:
            await self.connection.close()

        if self.loop is not None:
            self.loop.cancel()

        self.loop = None

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

        p: 'Future[List[str]]' = get_running_loop().create_future()
        await self.pending_commands.put(p)

        await self.connection.write_line(command)

        result = await p

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
        self.loop = create_task(self._reply_loop())

    async def _reply_loop(self):
        try:
            while True:
                pending = await self.pending_commands.get()
                try:
                    reply = await self._read_response()
                except CancelledError:
                    pending.set_exception(ConnectionFailedError())
                    raise
                except Exception as e:  # pylint: disable=broad-except
                    pending.set_exception(e)
                else:
                    pending.set_result(reply)
                self.pending_commands.task_done()
        except CancelledError:
            return


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
        c = cls()
        await c.connect(address, port)
        yield c
        await c.disconnect()

    @classmethod
    @asynccontextmanager
    async def make_unix(cls, socket: Path) -> AsyncGenerator:
        """Create a BaseMPDClient using a Unix socket.

        This should be used instead of instantiating the class directly.
        """
        c = cls()
        await c.connect_unix(socket)
        yield c
        await c.disconnect()

    async def connect(self, address: str, port: int):
        """Connect to the MPD client using TCP."""
        self.connection = MPDConnection()

        await self.connection.connect(TCPConnector(address, port))

    async def connect_unix(self, path: Path):
        """Connect to the MPD client using Unix socket."""
        self.connection = MPDConnection()

        await self.connection.connect(UnixConnector(Path(path)))

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
