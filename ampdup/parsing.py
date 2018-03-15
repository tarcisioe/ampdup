'''MPD output parsing utilities.'''
from typing import List, Tuple

from .util import from_json_like


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
        name: A key/value string in 'key: value' format.

    Returns:
        The (key, value) tuple, with both sides stripped.
    '''
    lhs, rhs = item.split(':', maxsplit=1)
    return lhs.strip(), rhs.strip()


def from_lines(cls: type, lines: List[str]):
    '''Make a `cls` object from a list of lines in MPD output format.'''
    values = (split_item(l) for l in lines)
    normalized = {normalize(k): v for k, v in values}
    return from_json_like(cls, normalized)
