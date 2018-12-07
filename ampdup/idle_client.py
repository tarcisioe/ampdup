'''Idle client module.'''

from typing import List

from .base_client import BaseMPDClient
from .errors import ClientTypeError
from .parsing import split_item
from .types import Subsystem
from .util import has_any_prefix


class IdleMPDClient(BaseMPDClient):
    '''Client that is only capable of running the idle command.

    More information in the idle() method docstring.
    '''
    async def run_command(self, command: str):
        if not has_any_prefix(command, ('idle', 'noidle')):
            raise ClientTypeError(
                'Use an MPDClient to run commands other than idle and noidle.'
            )

        return await super().run_command(command)

    async def idle(self,
                   *subsystems: Subsystem) -> List[Subsystem]:
        '''Run the idle command, fetching events from the player.

        Args:
            *subsystems (Subsystem):
                Subsystems to listen to (variadic). If empty or omitted listens
                to all systems.

        Returns:
            List[Subsystem]: subsystems that changed since the command was
                             called.
        '''
        subsystem_names = [s.value for s in subsystems]
        command = ' '.join(['idle', *subsystem_names])

        changed = (split_item(i) for i in await self.run_command(command))

        return [Subsystem(s) for _, s in changed]

    async def noidle(self):
        '''Cancel the current idle command.'''
        return await self.connection.connection.write_line('noidle')
