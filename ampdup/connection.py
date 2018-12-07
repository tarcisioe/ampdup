from asyncio import open_connection, StreamReader, StreamWriter
from typing import Optional, NamedTuple

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
        await self.writer.wait_closed()


@dataclass
class Connection:
    connection: Optional[Socket] = None

    async def connect(self, address: str, port: int):
        try:
            self.connection = Socket(*await open_connection(address, port))
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
