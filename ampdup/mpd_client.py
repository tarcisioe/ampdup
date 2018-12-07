'''MPD Client module.'''
from typing import List, Tuple, Union, Optional

from .base_client import BaseMPDClient
from .errors import ClientTypeError, NoCurrentSongError
from .parsing import from_lines, parse_playlist, parse_single
from .util import has_any_prefix

from .types import (
    Song, SongId, Stats, Status, Single, Tag, SearchType, TimeRange
)

Range = Tuple[int, int]
PositionOrRange = Union[int, Range]


AnySearchType = Union[Tag, SearchType]


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


def find_args(
        queries: List[Tuple[AnySearchType, str]]
) -> str:
    '''Make argument string for find and search.

    Args:
        queries: A list of queries (type and what).

    Returns:
        An argument string.
    '''
    return ' '.join(f'{type.value} "{what}"' for type, what in queries)


class MPDClient(BaseMPDClient):
    '''An async MPD Client object for any operations except idle/noidle.'''

    async def run_command(self, command: str) -> List[str]:
        if has_any_prefix(command, ('idle', 'noidle')):
            raise ClientTypeError('Use an IdleClient to use the idle command.')

        return await super().run_command(command)

    # MPD status

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

    # Playback options

    async def consume(self, state: bool):
        '''Enable or disable consume.

        When consume is enabled, played songs are removed from the playlist.

        Args:
            state: True for consume, otherwise False.
        '''
        await self.run_command(f'consume {int(state)}')

    async def single(self, mode: Single):
        '''Enable, disable or set to oneshot single playback.

        Args:
            mode: True for random, False for sequential.
        '''
        await self.run_command(f'single {mode.value}')

    async def random(self, state: bool):
        '''Enable or disable random playback.

        Args:
            state: True for random, False for sequential.
        '''
        await self.run_command(f'random {int(state)}')

    async def repeat(self, state: bool):
        '''Enable or disable repeat.

        Args:
            state: True to repeat, False to play once.
        '''
        await self.run_command(f'repeat {int(state)}')

    async def setvol(self, amount: int):
        '''Set volume.

        Args:
            amount: The new volume, from 0 to 100.
        '''
        await self.run_command(f'setvol {amount}')

    # Playback control

    async def next(self):
        '''Play next song in the playlist.'''
        await self.run_command(f'next')

    async def pause(self, pause: bool):
        '''Pause or resume playback.

        Args:
            pause: Whether to pause (`True`) or resume (`False`).
        '''
        await self.run_command(f'pause {int(pause)}')

    async def play(self, pos: Optional[int] = None):
        '''Begin playback. If supplied, start at `pos` in the playlist.

        Args:
            pos: The position in the playlist where to begin playback.
                 If omitted and playback is paused, resume it.
                 If playback was stopped, start from the beginning.
        '''
        arg = '' if pos is None else f' {pos}'
        await self.run_command(f'play{arg}')

    async def play_id(self, song_id: Optional[SongId] = None):
        '''Begin playback. If supplied, start at the song with id `song_id`.

        Args:
            song_id: The id of the song in the playlist where to begin
                     playback. If omitted and playback is paused, resume it.
                     If playback was stopped, start from the beginning.
        '''
        arg = '' if song_id is None else f' {song_id}'
        await self.run_command(f'playid{arg}')

    async def previous(self):
        '''Play previous song in the playlist.'''
        await self.run_command(f'previous')

    async def seek(self, pos: int, time: float):
        '''Seek to a certain time of the `pos` entry in the playlist.

        Args:
            pos: The position in the playlist of the song to seek.
            time: The timestamp to seek to in seconds (fractions allowed).
        '''
        await self.run_command(f'seek {pos} {time}')

    async def seek_id(self, song_id: SongId, time: float):
        '''Seek to a certain time of the song with id `song_id` in the playlist.

        Args:
            song_id: The id of the song in the playlist to seek.
            time: The timestamp to seek to in seconds (fractions allowed).
        '''
        await self.run_command(f'seekid {song_id} {time}')

    async def seek_cur_abs(self, time: float):
        '''Seek to a certain time of the current song.

        Args:
            time: The timestamp to seek to in seconds (fractions allowed).
        '''
        time = time if time >= 0 else 0
        await self.run_command(f'seekcur {time}')

    async def seek_cur_rel(self, time: float):
        '''Seek to a time relative to the current time in the current song.

        Args:
            time: The time delta to apply to the current time (fractions
                  allowed).
        '''
        await self.run_command(f'seekcur {time:+}')

    async def stop(self):
        '''Stop playback.'''
        await self.run_command(f'stop')

    # Current playlist

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

    async def clear(self):
        '''Clears the current playlist.'''
        await self.run_command('clear')

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

    async def move(self, what: PositionOrRange, to: int):
        '''Move a song or a range to another position in the playlist.

        Args:
            what: A position or range of songs to move.
            to: The position on the current state of the playlist where the
                songs should be moved to.
        '''
        what_arg = position_or_range_arg(what)

        await self.run_command(f'move {what_arg} {to}')

    async def move_id(self, song_id: SongId, to: int):
        '''Move a song by its id to a position in the playlist.

        If to is negative, it is relative to the current song in the playlist
        (if there is one).

        Args:
            song_id: An id of a song in the playlist.
            to: The position on the current state of the playlist where the
                songs should be moved to.
        '''
        await self.run_command(f'moveid {song_id} {to}')

    async def playlist_find(self, tag: Tag, needle: str) -> List[Song]:
        '''Search strictly for `needle` among the `tag` values.

        Args:
            tag: Which tag to search for.
            needle: What to search for.

        Returns:
        '''
        result = await self.run_command(
            f'playlistfind {tag.value} "{needle}"'
        )
        return parse_playlist(result)

    async def playlist_id(
            self,
            song_id: Optional[SongId] = None
    ) -> List[Song]:
        '''Get information about a particular song in the playlist.

        Args:
            song_id: The id of the song to search for. If omitted,
                     returns the whole playlist, like `playlist_info`.

        Returns:
            A list of Song objects representing the current playlist.
        '''
        arg = f' {song_id}' if song_id else ''

        result = await self.run_command(f'playlistid{arg}')
        return parse_playlist(result)

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

    async def playlist_search(self, tag: Tag, needle: str) -> List[Song]:
        '''Search case-insensitively for `needle` among the `tag` values.

        Args:
            tag: Which tag to search for.
            needle: What to search for.

        Returns:
        '''
        result = await self.run_command(
            f'playlistsearch {tag.value} "{needle}"'
        )
        return parse_playlist(result)

    async def prio(self, priority: int, song_range: Range):
        '''Set a song priority for random playback.

        Args:
            priority: A value between 0 and 255.
            song_range: The range of songs in the playlist to change.
        '''
        start, end = song_range
        start_arg = '' if start is None else f'{start}'
        end_arg = '' if end is None else f'{end}'
        result = await self.run_command(
            f'prio {priority} {start_arg}:{end_arg}'
        )
        return parse_playlist(result)

    async def prio_id(self, priority: int, song_id: SongId):
        '''Set a song priority for random playback.

        Args:
            priority: A value between 0 and 255.
            song_range: The range of songs in the playlist to change.
        '''
        result = await self.run_command(f'prioid {priority} {song_id}')
        return parse_playlist(result)

    async def range_id(
            self,
            song_id: SongId,
            time_range: TimeRange = TimeRange((None, None)),
    ):
        '''Specify the portion of the song that shall be played.

        Args:
            song_id: The id of the target song.
            time_range: A pair of offsets in seconds (fractions allowed).
                        If omitted, removes any range,
        '''
        start, end = time_range
        start_arg = '' if start is None else f'{start}'
        end_arg = '' if end is None else f'{end}'
        await self.run_command(f'rangeid {song_id} {start_arg}:{end_arg}')

    async def shuffle(self, shuffle_range: Optional[Range] = None):
        '''Shuffle the current playlist.

        Args:
            shuffle_range: An optional range to shuffle. If ommitted, shuffles
                           the whole playlist.
        '''
        arg = position_or_range_arg(shuffle_range)

        await self.run_command(f'shuffle{arg}')

    async def swap(self, s1: int, s2: int):
        '''Swap two songs.

        Args:
            s1: the first song's position.
            s2: the second song's position.
        '''
        await self.run_command(f'swap {s1} {s2}')

    async def swap_id(self, s1: SongId, s2: SongId):
        '''Swap two songs by id.

        Args:
            s1: the first song's id.
            s2: the second song's id.
        '''
        await self.run_command(f'swapid {s1} {s2}')

    # Music database

    async def find(
            self,
            queries: List[Tuple[AnySearchType, str]]
    ) -> List[Song]:
        '''Search strictly in the music database.

        Args:
        Returns:
        '''
        result = await self.run_command(f'find {find_args(queries)}')
        return parse_playlist(result)

    async def search(
            self,
            queries: List[Tuple[AnySearchType, str]]
    ) -> List[Song]:
        '''Search case-insensitively in the music database.

        Args:
        Returns:
        '''
        result = await self.run_command(f'search {find_args(queries)}')
        return parse_playlist(result)

    async def update(self, uri: str = None) -> int:
        '''Update the database.

        Args:
            uri: An optional URI to specify which file or directory to update.
                 If omitted, everything is updated.

        Returns:
            The id of the update job.
        '''
        arg = f' "{uri}"' if uri else ''

        result = await self.run_command(f'update{arg}')
        return parse_single(result, int)

    async def rescan(self, uri: str = None) -> int:
        '''Update the database rescanning unmodified files as well.

        Args:
            uri: An optional URI to specify which file or directory to update.
                 If omitted, everything is updated.

        Returns:
            The id of the update job.
        '''
        arg = f' "{uri}"' if uri else ''

        result = await self.run_command(f'rescan{arg}')
        return parse_single(result, int)
