import asyncio
from asyncio import StreamReader, StreamWriter
from pathlib import Path
from typing import Awaitable, Callable, Optional, NamedTuple, Tuple, Union

from dataclasses import dataclass

from .errors import ConnectionFailedError


class Socket(NamedTuple):
    reader: StreamReader
    writer: StreamWriter

    async def write(self, data: bytes):
        self.writer.write(data)
        try:
            await self.writer.drain()
        except Exception as e:
            raise ConnectionFailedError() from e

    async def readline(self) -> bytes:
        x = await self.reader.readline()
        if not x.endswith(b'\n'):
            raise ConnectionFailedError('Connection aborted while reading.')
        return x

    async def close(self):
        self.writer.close()
        try:
            await self.writer.wait_closed()
        except BrokenPipeError:
            pass


@dataclass
class TCPConnector:
    address: str
    port: int

    async def connect(self) -> Socket:
        return Socket(*await asyncio.open_connection(self.address, self.port))


@dataclass
class UnixConnector:
    path: Path

    async def connect(self) -> Socket:
        path = str(self.path.expanduser().absolute())
        return Socket(*await asyncio.open_unix_connection(path))


Connector = Union[TCPConnector, UnixConnector]


@dataclass
class Connection:
    connector: Connector
    connection: Optional[Socket] = None

    async def connect(self):
        try:
            self.connection = await self.connector.connect()
        except OSError as e:
            raise ConnectionFailedError('Could not connect to MPD') from e

        result = await self.read_line()

        if not result.startswith('OK MPD'):
            raise ConnectionFailedError('Got wrong response from MPD.')

    async def write_line(self, command: str):
        if self.connection is not None:
            await self.connection.write(command.encode() + b'\n')
            return
        raise ConnectionFailedError('Not connected.')

    async def read_line(self) -> str:
        if self.connection is not None:
            line = await self.connection.readline()
            return line.decode().strip('\n')
        raise ConnectionFailedError('Not connected.')

    async def close(self):
        if self.connection is not None:
            await self.connection.close()
