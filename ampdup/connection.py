from curio.io import Socket
from curio.network import open_connection

from dataclasses import dataclass

from .errors import ConnectionFailedError
from .typing_local import AsyncBinaryIO


@dataclass
class Connection:
    connection: Socket = None
    stream: AsyncBinaryIO = None

    async def connect(self, address: str, port: int):
        self.connection = await open_connection(address, port)
        self.stream = self.connection.as_stream()
        result = await self.read_line()
        if not result.startswith('OK MPD'):
            raise ConnectionFailedError

    async def write_line(self, command: str):
        await self.stream.write(command.encode() + b'\n')

    async def read_line(self) -> str:
        line = await self.stream.readline()
        return line.decode().strip('\n')
