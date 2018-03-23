'''MPD Client module.'''
from typing import List, Tuple, Union, Optional

from .base_client import BaseMPDClient
from .errors import ClientTypeError, NoCurrentSongError
from .song import Song, SongId
from .parsing import from_lines, parse_playlist, parse_single
from .stats import Stats
from .status import Status
from .util import has_any_prefix


PositionOrRange = Union[int, Tuple[int, int]]


def position_or_range_arg(arg: Optional[PositionOrRange]) -> str:
    '''Make argument string for commands that may take a position or a range.

    Args:
        arg: Either a position as an int or a range as a tuple.

    Returns:
        The correspondent string to the argument.
    '''
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
            position_or_range: Optional[PositionOrRange] = None,
    ) -> List[Song]:
        '''Get information about every song in the current playlist.

        Args:
            position_or_range: either an integer pointing to a specific
                               position in the playlist or an interval.
                               If ommited, returns the whole playlist.

        Returns:
            A list of Song objects representing the current playlist.
        '''
        arg = position_or_range_arg(position_or_range)

        result = await self.run_command(f'playlistinfo{arg}')
        return parse_playlist(result)

    async def clear(self):
        '''Clears the current playlist.'''
        await self.run_command('clear')

    async def add(self, uri: str):
        '''Add a directory or a file to the current playlist.

        Args:
            uri: The URI of what to add. Directories are added recursively.
        '''
        await self.run_command(f'add "{uri}"')

    async def add_id(self, song_uri: str, position: int = None) -> SongId:
        '''Add a directory or a file to the current playlist.

        Args:
            song_uri: The URI of the song to add. Must be a single file.
            position: Position on the playlist where to add. End of playlist if
                      omitted.

        Returns:
            The id of the added song.
        '''
        pos = '' if position is None else f' {position}'

        result = await self.run_command(f'addid "{song_uri}"{pos}')
        return parse_single(result, SongId)

    async def delete(
            self,
            position_or_range: PositionOrRange,
    ):
        '''Delete songs from the playlist.

        Args:
            position_or_range: either an integer pointing to a specific
                               position in the playlist or an interval.
        '''
        arg = position_or_range_arg(position_or_range)

        await self.run_command(f'delete{arg}')

    async def delete_id(self, song_id: SongId):
        '''Delete a song by its id.

        Args
            id: a song id.
        '''
        await self.run_command(f'deleteid {song_id}')

    async def update(self, uri: str = None) -> int:
        '''Update the database.

        Args:
            uri: An optional URI to specify which file or directory to update.
                 If omitted, everything is updated.

        Returns:
            The id of the update job.
        '''
        result = await self.run_command(f'update "{uri}"')
        return parse_single(result, int)

    async def rescan(self, uri: str = None) -> int:
        '''Update the database rescanning unmodified files as well.

        Args:
            uri: An optional URI to specify which file or directory to update.
                 If omitted, everything is updated.

        Returns:
            The id of the update job.
        '''
        result = await self.run_command(f'rescan "{uri}"')
        return parse_single(result, int)
