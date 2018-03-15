'''Song metadata representation.'''
from typing import NamedTuple


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
