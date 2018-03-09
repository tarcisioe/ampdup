import re

from typing import AsyncGenerator, List

from dataclasses import dataclass, field

from curio.promise import Promise
from curio.queue import Queue
from curio.task import spawn, Task, TaskCancelled

from .connection import Connection
from .errors import CommandError
from .util import asynccontextmanager


ERROR_RE = re.compile(r'ACK\s+\[(\d+)@(\d+)\]\s+\{(.*)\}\s+(.*)')


def parse_error(error_line: str, partial: List[str]):
    code, line, command, message = ERROR_RE.match(error_line).groups()
    return CommandError(int(code), int(line), command, message, partial)


@dataclass
class BaseMPDClient:
    pending_commands: Queue = field(default_factory=Queue)
    connection: Connection = None
    loop: Task = None

    @classmethod
    @asynccontextmanager
    async def make(cls, address: str, port: int) -> AsyncGenerator:
        c = cls()
        await c.connect(address, port)
        yield c
        await c.stop()

    async def connect(self, address: str, port: int):
        self.connection = Connection()
        await self.connection.connect(address, port)
        await self._start_loop()

    async def run_command(self, command: str) -> List[str]:
        p = Promise()
        await self.pending_commands.put(p)

        await self.connection.write_line(command)

        result = await p.get()

        if isinstance(result, Exception):
            raise result

        return result

    async def stop(self):
        if self.loop:
            await self.loop.cancel()

    async def _read_response(self) -> List[str]:
        lines: List[str] = []

        while True:
            line = await self.connection.read_line()

            if line.startswith('OK'):
                break
            if line.startswith('ACK'):
                return parse_error(line, lines)

            lines.append(line)

        return lines

    async def _reply_loop(self):
        try:
            while True:
                reply = await self._read_response()
                pending = await self.pending_commands.get()
                await pending.set(reply)
        except TaskCancelled:
            return

    async def _start_loop(self):
        self.loop = await spawn(self._reply_loop())
