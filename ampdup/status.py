'''Player state representation.'''
from typing import NamedTuple

from enum import Enum


class Single(Enum):
    '''"single" setting state.'''
    DISABLED = 0
    ENABLED = 1
    ONESHOT = 2


class State(Enum):
    '''Player state.'''
    PLAY = 'play'
    STOP = 'stop'
    PAUSE = 'pause'


class Status(NamedTuple):
    '''Type representing the static data about a playable song in MPD.'''
    volume: int
    repeat: bool
    random: bool
    single: Single
    consume: bool
    playlist: int
    playlistlength: int
    mixrampdb: float
    state: State
    song: int
    songid: int
    time: str
    elapsed: float
    bitrate: int
    duration: float
    audio: str
    nextsong: int
    nextsongid: int
    error: str = None
    mixrampdelay: int = None
    updating_db: int = None
    xfade: int = None
