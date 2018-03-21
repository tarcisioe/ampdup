'''MPD output parsing utilities.'''
import re

from typing import Iterable, List, Tuple

from .errors import ErrorCode, get_error_constructor
from .song import Song
from .util import from_json_like, split_on


__all__ = [
    'normalize',
    'split_item',
    'from_lines',
    'parse_playlist',
    'parse_error',
]


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


ERROR_RE = re.compile(r'ACK\s+\[(\d+)@(\d+)\]\s+\{(.*)\}\s+(.*)')


def parse_error(error_line: str, partial: List[str]):
    '''Parse an error from MPD.

    Errors are of format

    `ACK [CODE@LINE] {COMMAND} MESSAGE`

    Args:
        error_line: an ACK line from MPD.

    Returns:
        A CommandError (or subclass) object with the error data.
    '''
    code, line, command, message = ERROR_RE.match(error_line).groups()
    error_code = ErrorCode(int(code))
    return get_error_constructor(error_code)(int(line),
                                             command,
                                             message,
                                             partial)
