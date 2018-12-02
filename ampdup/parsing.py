'''MPD output parsing utilities.'''
import re

from typing import (
    overload, Callable, Iterable, List, Tuple, TypeVar, Type, Union
)

from .errors import CommandError, ErrorCode, get_error_constructor
from .types import Song
from .util import from_json_like, split_on


__all__ = [
    'normalize',
    'split_item',
    'from_lines',
    'parse_single',
    'parse_playlist',
    'parse_error',
]


T = TypeVar('T')


class IncompatibleErrorMessage(Exception):
    '''Exception in case MPD sends an error in a different format somehow.'''


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


def from_lines(cls: Type[T], lines: Iterable[str]) -> T:
    '''Make a `cls` object from a list of lines in MPD output format.'''
    values = (split_item(l) for l in lines)
    normalized = {normalize(k): v for k, v in values}
    return from_json_like(cls, normalized)


def parse_error(error_line: str, partial: List[str]) -> CommandError:
    '''Parse an error from MPD.

    Errors are of format

    `ACK [CODE@LINE] {COMMAND} MESSAGE`

    Args:
        error_line: an ACK line from MPD.

    Returns:
        A CommandError (or subclass) object with the error data.
    '''
    match = ERROR_RE.match(error_line)

    if match is None:
        raise IncompatibleErrorMessage(error_line)

    code, line, command, message = match.groups()
    error_code = ErrorCode(int(code))
    return get_error_constructor(error_code)(int(line),
                                             command,
                                             message,
                                             partial)


@overload
def parse_single(
        lines: Iterable[str]  # pylint: disable=unused-argument
) -> str:
    '''Overload.'''


@overload  # noqa: F811
def parse_single(  # pylint: disable=function-redefined
        lines: Iterable[str],  # pylint: disable=unused-argument
        cast: Callable[[str], T]  # pylint: disable=unused-argument
) -> T:
    '''Overload.'''


def parse_single(  # noqa: F811, pylint: disable=function-redefined
        lines: Iterable[str],
        cast: Callable[[str], T] = None
) -> Union[str, T]:
    '''Parse a single return value and discard its name.

    Args:
        lines: The return from MPD as a list of a single line.
        cast: An optional function to read the string into another type.

    Returns:
        The value as a string or converted into the chosen type.
    '''
    result, = lines
    _, value = split_item(result)
    if cast is None:
        return value
    return cast(value)


def is_file(line: str) -> bool:
    '''Check if a return line is a song file.'''
    return line.startswith('file:')


def parse_playlist(lines: Iterable[str]) -> List[Song]:
    '''Parse playlist information into a list of songs.'''
    split = split_on(is_file, lines)
    return [from_lines(Song, song_info) for song_info in split]


ERROR_RE = re.compile(r'ACK\s+\[(\d+)@(\d+)\]\s+\{(.*)\}\s+(.*)')
