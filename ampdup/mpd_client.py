'''MPD Client module.'''
from typing import NamedTuple

from .base_client import BaseMPDClient
from .errors import ClientTypeError
from .util import has_any_prefix, from_json_like


class Song(NamedTuple):
    '''Type representing the static data about a playable song in MPD.'''
    file: str
    last_modified: str
    artist: str
    title: str
    album: str
    track: int
    date: int
    genre: str
    time: int
    duration: float
    pos: int
    id: int


def normalize(s: str) -> str:
    '''normalize'''
    return s.lower().replace('-', '_')


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
        values = (r.split(': ') for r in result)
        normalized = {normalize(k): v for k, v in values}
        return from_json_like(Song, normalized)
