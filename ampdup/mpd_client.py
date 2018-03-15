'''MPD Client module.'''
from .base_client import BaseMPDClient
from .errors import ClientTypeError, NoCurrentSongError
from .song import Song
from .parsing import from_lines
from .status import Status
from .util import has_any_prefix


class MPDClient(BaseMPDClient):
    '''An async MPD Client object for any operations except idle/noidle.'''

    async def run_command(self, command: str):
        if has_any_prefix(command, ('idle', 'noidle')):
            raise ClientTypeError('Use an IdleClient to use the idle command.')

        return await super().run_command(command)

    async def current_song(self) -> Song:
        '''Displays the song info of the current song.

        Returns:
            The metadata of the song that is identified in status.
        '''
        result = await self.run_command('currentsong')

        if not result:
            raise NoCurrentSongError('There is no current song playing.')

        return from_lines(Song, result)

    async def status(self) -> Status:
        '''Get the current player status.

        Returns:
            The current player status.
        '''
        result = await self.run_command('status')
        return from_lines(Status, result)
