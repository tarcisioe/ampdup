'''Song metadata representation.'''
from typing import NamedTuple


class Song(NamedTuple):
    '''Type representing the static data about a playable song in MPD.'''
    file: str
    last_modified: str
    time: int
    duration: float
    pos: int
    id: int
    artist: str = ''
    albumartist: str = ''
    title: str = ''
    album: str = ''
    genre: str = ''
    disc: int = None
    track: int = None
    date: int = None