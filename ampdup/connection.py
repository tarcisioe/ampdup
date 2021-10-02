"""Module for connection-related functionality."""
import asyncio
from asyncio import StreamReader, StreamWriter
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from .errors import ConnectionFailedError


@dataclass(frozen=True)
class Socket:
    """An async socket model based on asyncio."""

    reader: StreamReader
    writer: StreamWriter

    async def write(self, data: bytes):
        """Write data to the socket."""
        self.writer.write(data)
        try:
            await self.writer.drain()
        except Exception as e:
            raise ConnectionFailedError() from e

    async def readline(self) -> bytes:
        """Read from the socket up to a newline."""
        x = await self.reader.readline()
        if not x.endswith(b'\n'):
            raise ConnectionFailedError('Connection aborted while reading.')
        return x

    async def close(self):
        """Close the socket."""
        self.writer.close()
        try:
            await self.writer.wait_closed()
        except BrokenPipeError:
            pass


@dataclass(frozen=True)
class TCPConnector:
    """Factory for TCP-based connections."""

    address: str
    port: int

    async def connect(self) -> Socket:
        """Open a socket using a TCP connection."""
        return Socket(*await asyncio.open_connection(self.address, self.port))


@dataclass
class UnixConnector:
    """Factory for Unix-socket-based connections."""

    path: Path

    async def connect(self) -> Socket:
        """Open a Unix socket."""
        path = str(self.path.expanduser().absolute())
        return Socket(*await asyncio.open_unix_connection(path))


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
