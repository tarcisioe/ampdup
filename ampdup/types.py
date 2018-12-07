'''Types for MPD information.'''
from enum import Enum
from typing import NamedTuple, Optional, Tuple, NewType


TimeRange = NewType('TimeRange', Tuple[Optional[float], Optional[float]])


class SongId(int):
    '''Strong alias for song ids.'''


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
    label: str = ''
    format: Optional[str] = None
    disc: Optional[int] = None
    track: Optional[int] = None
    date: Optional[int] = None
    range: Optional[TimeRange] = None
    pos: Optional[int] = None
    id: Optional[SongId] = None
    prio: Optional[int] = None


class SearchType(Enum):
    '''Special types for searching the database.'''
    ANY = 'any'
    FILE = 'file'
    BASE = 'base'
    MODIFIED_SINCE = 'modified-since'


class Single(Enum):
    '''"single" setting state.'''
    DISABLED = '0'
    ENABLED = '1'
    ONESHOT = 'oneshot'


class State(Enum):
    '''Player state.'''
    PLAY = 'play'
    STOP = 'stop'
    PAUSE = 'pause'


class Status(NamedTuple):
    '''Type representing the static data about a playable song in MPD.'''
    repeat: bool
    random: bool
    single: Single
    consume: bool
    playlist: int
    playlistlength: int
    mixrampdb: float
    state: State
    volume: Optional[int] = None
    song: Optional[int] = None
    songid: Optional[SongId] = None
    time: Optional[str] = None
    elapsed: Optional[float] = None
    bitrate: Optional[int] = None
    duration: Optional[float] = None
    audio: Optional[str] = None
    nextsong: Optional[int] = None
    nextsongid: Optional[SongId] = None
    error: Optional[str] = None
    mixrampdelay: Optional[int] = None
    updating_db: Optional[int] = None
    xfade: Optional[int] = None


class Stats(NamedTuple):
    '''Statistics about the player.'''
    uptime: int
    playtime: int
    artists: int
    albums: int
    songs: int
    db_playtime: int
    db_update: int


class Subsystem(Enum):
    '''Enumeration of available subsystems for idle to listen to.'''
    DATABASE = 'database'
    UPDATE = 'update'
    STORED_PLAYLIST = 'stored_playlist'
    PLAYLIST = 'playlist'
    PLAYER = 'player'
    MIXER = 'mixer'
    OUTPUT = 'output'
    OPTIONS = 'options'
    PARTITION = 'partition'
    STICKER = 'sticker'
    SUBSCRIPTION = 'subscription'
    MESSAGE = 'message'


class Tag(Enum):
    '''Tags supported by MPD.'''
    ARTIST = 'artist'
    ARTISTSORT = 'artistsort'
    ALBUM = 'album'
    ALBUMSORT = 'albumsort'
    ALBUMARTIST = 'albumartist'
    ALBUMARTISTSORT = 'albumartistsort'
    TITLE = 'title'
    TRACK = 'track'
    NAME = 'name'
    GENRE = 'genre'
    DATE = 'date'
    COMPOSER = 'composer'
    PERFORMER = 'performer'
    COMMENT = 'comment'
    DISC = 'disc'
    MUSICBRAINZ_ARTISTID = 'musicbrainz_artistid'
    MUSICBRAINZ_ALBUMID = 'musicbrainz_albumid'
    MUSICBRAINZ_ALBUMARTISTID = 'musicbrainz_albumartistid'
    MUSICBRAINZ_TRACKID = 'musicbrainz_trackid'
    MUSICBRAINZ_RELEASETRACKID = 'musicbrainz_releasetrackid'
    MUSICBRAINZ_WORKID = 'musicbrainz_workid'


__all__ = [
    'SearchType',
    'Single',
    'Song',
    'SongId',
    'State',
    'Stats',
    'Status',
    'Subsystem',
    'Tag',
    'TimeRange',
]
