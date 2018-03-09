'''MPD Client module.'''
from .base_client import BaseMPDClient
from .errors import ClientTypeError
from .util import has_any_prefix


class MPDClient(BaseMPDClient):
    '''An async MPD Client object for any operations except idle/noidle.'''
    async def run_command(self, command: str):
        if has_any_prefix(command, ('idle', 'noidle')):
            raise ClientTypeError('Use an IdleClient to use the idle command.')

        return await super().run_command(command)
