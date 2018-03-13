'''Song metadata representation.'''
from typing import List, NamedTuple

from .parsing import normalize, split_item
from .util import from_json_like


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

    @staticmethod
    def from_lines(lines: List[str]) -> 'Song':
        '''Make a Song from a list of lines in MPD output format.'''
        values = (split_item(l) for l in lines)
        normalized = {normalize(k): v for k, v in values}
        return from_json_like(Song, normalized)
