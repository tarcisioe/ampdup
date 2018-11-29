from typing import AsyncGenerator, List, Optional, Union

from dataclasses import dataclass, field

from asyncio import Future, AbstractEventLoop  # pylint: disable=unused-import
from asyncio import Queue
from asyncio import get_event_loop, Task, CancelledError

from .connection import Connection, NotConnectedError
from .errors import CommandError
from .parsing import parse_error
from .util import asynccontextmanager


@dataclass
class BaseMPDClient:
    pending_commands: 'Queue[Future[List[str]]]' = field(default_factory=Queue)
    connection: Optional[Connection] = None
    loop: Optional[Task] = None
    event_loop: AbstractEventLoop = field(
        default_factory=get_event_loop
    )

    @classmethod
    @asynccontextmanager
    async def make(cls, address: str, port: int) -> AsyncGenerator:
        c = cls()
        await c.connect(address, port)
        yield c
        await c.stop_loop()

    async def connect(self, address: str, port: int):
        self.connection = Connection()
        await self.connection.connect(address, port)
        await self._start_loop()

    async def run_command(self, command: str) -> List[str]:
        if self.connection is None:
            raise NotConnectedError()

        p: 'Future[List[str]]' = self.event_loop.create_future()
        await self.pending_commands.put(p)

        await self.connection.write_line(command)

        result = await p

        if isinstance(result, Exception):
            raise result

        return result

    async def stop_loop(self):
        if self.loop:
            self.loop.cancel()

    async def _read_response(self) -> Union[List[str], CommandError]:
        if self.connection is None:
            raise NotConnectedError()

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
                pending.set_result(reply)
        except CancelledError:
            return

    async def _start_loop(self):
        self.loop = self.event_loop.create_task(self._reply_loop())
