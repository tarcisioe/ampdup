"""Module for connection-related functionality."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

from anyio import connect_tcp, connect_unix
from anyio.abc import SocketStream
from anyio.streams.buffered import BufferedByteReceiveStream

from .errors import ConnectionFailedError


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
        return await self.buffered.receive_until(b'\n', 0xFFFFFFFF)

    async def close(self):
        """Close the socket."""
        await self.sock.aclose()


@dataclass(frozen=True)
class TCPConnector:
    """Factory for TCP-based connections."""

    address: str
    port: int

    async def connect(self) -> Socket:
        """Open a socket using a TCP connection."""
        return Socket(await connect_tcp(self.address, self.port))


@dataclass
class UnixConnector:
    """Factory for Unix-socket-based connections."""

    path: Path

    async def connect(self) -> Socket:
        """Open a Unix socket."""
        path = str(self.path.expanduser().absolute())
        return Socket(await connect_unix(path))


Connector = Union[TCPConnector, UnixConnector]


@dataclass
class Connection:
    """Abstraction for a connection to MPD"""

    connector: Connector
    connection: Optional[Socket] = None

    async def connect(self):
        """Connect to the MPD server."""
        try:
            self.connection = await self.connector.connect()
        except OSError as e:
            raise ConnectionFailedError('Could not connect to MPD') from e

        result = await self.read_line()

        if not result.startswith('OK MPD'):
            raise ConnectionFailedError('Got wrong response from MPD.')

    async def write_line(self, command: str):
        """Send a line through the connection."""
        if self.connection is not None:
            await self.connection.write(command.encode() + b'\n')
            return
        raise ConnectionFailedError('Not connected.')

    async def read_line(self) -> str:
        """Read a line from the connection."""
        if self.connection is not None:
            line = await self.connection.readline()
            return line.decode().strip('\n')
        raise ConnectionFailedError('Not connected.')

    async def close(self):
        """Close the connection."""
        if self.connection is not None:
            await self.connection.close()
