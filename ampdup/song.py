'''Song metadata representation.'''
from typing import NamedTuple, Optional, Tuple


class SongId(int):
    '''Strong alias for song ids.'''
    pass


TimeRange = Tuple[Optional[float], Optional[float]]


class Song(NamedTuple):
    '''Type representing the static data about a playable song in MPD.'''
    file: str
    last_modified: str
    time: int
    duration: float
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
    range: TimeRange = None
    pos: int = None
    id: SongId = None
    prio: int = None
