'''Player statistics.'''
from typing import NamedTuple


class Stats(NamedTuple):
    '''Statistics about the player.'''
    uptime: int
    playtime: int
    artists: int
    albums: int
    songs: int
    db_playtime: int
    db_update: int
