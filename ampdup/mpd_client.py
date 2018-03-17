'''MPD Client module.'''
from typing import List, Tuple, Union

from .base_client import BaseMPDClient
from .errors import ClientTypeError, NoCurrentSongError
from .song import Song
from .parsing import from_lines, parse_playlist
from .stats import Stats
from .status import Status
from .util import has_any_prefix


PlaylistInfoArg = Union[None, int, Tuple[int, int]]


def playlist_info_arg(arg: PlaylistInfoArg) -> str:
    '''Make argument string for playlist_info optional arguments.'''
    if arg is None:
        return ''
    if isinstance(arg, int):
        return f' {arg}'
    start, end = arg
    return f' {start}:{end}'


class MPDClient(BaseMPDClient):
    '''An async MPD Client object for any operations except idle/noidle.'''

    async def run_command(self, command: str) -> List[str]:
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

    async def stats(self) -> Stats:
        '''Get player stats. Refer to the Stats type to see what is available.

        Returns:
            Statistics about the player.
        '''
        result = await self.run_command('stats')
        return from_lines(Stats, result)

    async def playlist_info(
            self,
            position_or_range: PlaylistInfoArg = None
    ) -> List[Song]:
        '''Get information about every song in the current playlist.

        Args:
            position_or_range: either an integer pointing to a specific
                               position in the playlist or an interval.

        Returns:
            A list of Song objects representing the current playlist.
        '''
        arg = ''

        if position_or_range is not None:
            arg = playlist_info_arg(position_or_range)

        result = await self.run_command(f'playlistinfo{arg}')
        return parse_playlist(result)
