'''Player state representation.'''
from typing import NamedTuple

from enum import Enum

from .song import SongId


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
    volume: int = None
    song: int = None
    songid: SongId = None
    time: str = None
    elapsed: float = None
    bitrate: int = None
    duration: float = None
    audio: str = None
    nextsong: int = None
    nextsongid: SongId = None
    error: str = None
    mixrampdelay: int = None
    updating_db: int = None
    xfade: int = None
