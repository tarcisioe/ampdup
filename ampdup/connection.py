from asyncio import open_connection, StreamReader, StreamWriter
from typing import Optional, NamedTuple

from dataclasses import dataclass

from .errors import ConnectionFailedError


class Socket(NamedTuple):
    reader: StreamReader
    writer: StreamWriter

    async def write(self, data: bytes):
        self.writer.write(data)
        await self.writer.drain()

    async def readline(self) -> bytes:
        return await self.reader.readline()


class NotConnectedError(Exception):
    pass


@dataclass
class Connection:
    connection: Optional[Socket] = None

    async def connect(self, address: str, port: int):
        self.connection = Socket(*await open_connection(address, port))
        result = await self.read_line()
        if not result.startswith('OK MPD'):
            raise ConnectionFailedError

    async def write_line(self, command: str):
        if self.connection is not None:
            await self.connection.write(command.encode() + b'\n')
            return
        raise NotConnectedError()

    async def read_line(self) -> str:
        if self.connection is not None:
            line = await self.connection.readline()
            return line.decode().strip('\n')
        raise NotConnectedError()
