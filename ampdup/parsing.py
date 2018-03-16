'''MPD output parsing utilities.'''
from typing import Iterable, List, Tuple

from .song import Song
from .util import from_json_like, split_on


def normalize(name: str) -> str:
    '''Normalize a value name to a valid Python (PEP8 compliant) identifier.

    Args:
        name: The name of a value returned by MPD.

    Returns:
        The normalized name, in all lowercase with - replaced by _.
    '''
    return name.lower().replace('-', '_')


def split_item(item: str) -> Tuple[str, str]:
    '''Split a key/value pair in a string into a tuple (key, value).

    This also strips space from both sides of either.

    Args:
        item: A key/value string in 'key: value' format.

    Returns:
        The (key, value) tuple, with both sides stripped.
    '''
    lhs, rhs = item.split(':', maxsplit=1)
    return lhs.strip(), rhs.strip()


def from_lines(cls: type, lines: Iterable[str]):
    '''Make a `cls` object from a list of lines in MPD output format.'''
    values = (split_item(l) for l in lines)
    normalized = {normalize(k): v for k, v in values}
    return from_json_like(cls, normalized)


def is_file(line: str) -> bool:
    '''Check if a return line is a song file.'''
    return line.startswith('file:')


def parse_playlist(lines: Iterable[str]) -> List[Song]:
    '''Parse playlist information into a list of songs.'''
    split = split_on(is_file, lines)
    return [from_lines(Song, song_info) for song_info in split]
