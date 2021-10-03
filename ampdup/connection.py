"""Module for connection-related functionality."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Coroutine, Optional

from anyio import IncompleteRead, connect_tcp, connect_unix
from anyio.abc import SocketStream
from anyio.streams.buffered import BufferedByteReceiveStream
from typing_extensions import Protocol

from .errors import ConnectionFailedError, ReceiveError


@dataclass
class Socket:
    """An async socket higher-level abstraction."""

    sock: SocketStream
    buffered: BufferedByteReceiveStream = field(init=False)

    def __post_init__(self):
        self.buffered = BufferedByteReceiveStream(self.sock)

    async def write(self, data: bytes):
        """Write data to the socket."""
        await self.sock.send(data)

    async def readline(self) -> bytes:
        """Read from the socket up to a newline."""
        try:
            return await self.buffered.receive_until(b'\n', 0xFFFFFFFF)
        except IncompleteRead as e:
            raise ReceiveError('Connection closed before a newline was sent.') from e

    @staticmethod
    async def connect_tcp(address: str, port: int) -> 'Socket':
        """Create a socket with a TCP socket stream."""
        return Socket(await connect_tcp(address, port))

    @staticmethod
    async def connect_unix(path: Path) -> 'Socket':
        """Create a socket with a Unix-socket stream."""
        return Socket(await connect_unix(path.expanduser().absolute()))

    async def aclose(self):
        """Close the socket."""
        await self.sock.aclose()


class Connector(Protocol):
    """A"""

    def __call__(self) -> Coroutine[None, None, Socket]:
        ...


@dataclass
class Connection:
    """Abstraction for a connection to MPD"""

    connector: Connector
    socket: Optional[Socket] = None

    async def connect(self):
        """Connect to the MPD server."""
        try:
            self.socket = await self.connector()
        except OSError as e:
            raise ConnectionFailedError('Could not connect to MPD') from e

        result = await self.read_line()

        if not result.startswith('OK MPD'):
            raise ConnectionFailedError('Got wrong response from MPD.')

    async def write_line(self, command: str):
        """Send a line through the connection."""
        if self.socket is not None:
            await self.socket.write(command.encode() + b'\n')
            return
        raise ConnectionFailedError('Not connected.')

    async def read_line(self) -> str:
        """Read a line from the connection."""
        if self.socket is not None:
            line = await self.socket.readline()
            return line.decode().strip('\n')
        raise ConnectionFailedError('Not connected.')

    async def aclose(self):
        """Close the connection."""
        if self.socket is not None:
            await self.socket.aclose()
