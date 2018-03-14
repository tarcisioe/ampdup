'''MPD Client module.'''
from .base_client import BaseMPDClient
from .errors import ClientTypeError, NoCurrentSongError
from .song import Song
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
            Song: The same song that is identified in status.
        '''
        result = await self.run_command('currentsong')

        if not result:
            raise NoCurrentSongError('There is no current song playing.')

        return Song.from_lines(result)
