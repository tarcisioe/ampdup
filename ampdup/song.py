'''Song metadata representation.'''
from typing import NamedTuple


class SongId(int):
    '''Strong alias for song ids.'''
    pass


class Song(NamedTuple):
    '''Type representing the static data about a playable song in MPD.'''
    file: str
    last_modified: str
    time: int
    duration: float
    pos: int
    id: SongId
    artist: str = ''
    artistsort: str = ''
    albumartist: str = ''
    albumartistsort: str = ''
    title: str = ''
    album: str = ''
    albumsort: str = ''
    genre: str = ''
    disc: int = None
    track: int = None
    date: int = None
