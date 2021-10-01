'''Utility module.'''
from contextlib import asynccontextmanager
from enum import Enum, EnumMeta
from functools import lru_cache
from itertools import groupby
from operator import itemgetter
from typing import Any, Callable, Iterable, List, Sequence, Tuple, Type, TypeVar

from .types import TimeRange
from .typing_inspect import get_args, is_optional_type

__all__ = [
    'asynccontextmanager',
]


class NoCommonTypeError(Exception):
    '''Happens when values in an Enum are not of the same type.'''


class EmptyEnumError(Exception):
    '''Happens when an enum has no value.'''


@lru_cache()
def underlying_type(enum_type: EnumMeta) -> Type:
    '''Get the underlying type of an enum.

    Returns:
        The type of every value in the enum if it is the same.

    Raises:
        NoCommonTypeError: If the values in the enum are not of the same type.
        EmptyEnumError: If the enum has no value.
    '''
    try:
        first: Any = next(iter(enum_type))
    except StopIteration:
        raise EmptyEnumError('No value in enum.')

    t = type(first.value)

    if any(not isinstance(v.value, t) for v in enum_type):  # type: ignore
        raise NoCommonTypeError('No common type in enum.')

    return t


def is_namedtuple(cls: Type) -> bool:
    '''Checks if a type inherits typing.NamedTuple.

    Checking inspects the type and looks for the `_field_types`
    attribute.

    Args:
        cls: Type to inspect.

    Returns:
        Whether or not the type was generated by NamedTuple.
    '''
    return hasattr(cls, '_fields') and hasattr(cls, '__annotations__')


def from_list(list_type, v) -> List[Any]:
    '''Make a list of typed objects from a JSON-like list, based on type hints.

    Args:
        list_type: A `List[T]`-like type to instantiate .
        v: A JSON-like list.

    Returns:
        list_type: An object of type `list_type`.
    '''
    (inner_type,) = list_type.__args__
    return [from_json_like(inner_type, value) for value in v]


T = TypeVar('T')


def from_dict(cls: Type[T], d) -> T:
    '''Make an object from a dict, recursively, based on type hints.

    Args:
        cls: The type to instantiate.
        d: a dict of property names to values.

    Returns:
        cls: An object of type `cls`.
    '''
    # pylint:disable=protected-access
    if hasattr(cls, '_renames'):
        for k in d:
            if k in cls._renames:  # type: ignore
                d[cls._renames[k]] = d.pop(k)  # type: ignore
    return cls(
        **{
            i: from_json_like(cls.__annotations__[i], v)  # type: ignore
            for i, v in d.items()
        }
    )


def time_range(s: str) -> TimeRange:
    '''Parse a time range from a song metadata.

    Args:
        s: The time range as a string.

    Returns:
        A (float, float) tuple with offsets in seconds.
    '''
    start, end = s.split('-')
    return TimeRange((float(start), float(end)))


def from_json_like(cls: Type[T], j) -> T:
    '''Make an object from a JSON-like value, recursively, based on type hints.

    Args:
        cls: The type to instantiate.
        j: the JSON-like object.

    Returns:
        cls: An object of type `cls`.
    '''
    if cls is bool:
        return cls(int(j))  # type: ignore
    if is_optional_type(cls):
        for t in get_args(cls):
            if t is type(None):  # noqa
                continue
            try:
                return from_json_like(t, j)
            except TypeError:
                continue
        raise TypeError(f'{j} cannot be converted into {cls}.')
    if cls is str:
        return j
    if cls is TimeRange:
        return time_range(j)  # type: ignore
    if any(issubclass(cls, t) for t in (int, float)):
        return cls(j)  # type: ignore
    if issubclass(cls, Enum):
        return cls(underlying_type(cls)(j))  # type: ignore
    if issubclass(cls, List):
        return from_list(cls, j)  # type: ignore
    if is_namedtuple(cls):
        return from_dict(cls, j)
    raise TypeError(f'{j} cannot be converted into {cls}.')


def has_any_prefix(s: str, prefixes: Sequence[str]) -> bool:
    '''Checks if a string has any of the provided prefixes.

    Args:
        s: The string to check.
        prefixes: A sequence of prefixes to check.

    Returns:
        Whether the string matches any of the prefixes.
    '''
    return any(s.startswith(prefix) for prefix in prefixes)


Predicate = Callable[[T], bool]


def enumerate_on(
    pred: Predicate, iterable: Iterable[T], begin: int = 0
) -> Iterable[Tuple[int, T]]:
    '''Generate enumerated tuples based on sentinel elements in an iterable.

    A sentinel element is one for which `pred` is `True`. From it onwards the
    enumeration is incremented.

    Args:
        pred: A predicate identifying a sentinel element.
        iterable: An iterable to enumerate.
        begin: where to begin the enumeration.

    Returns:
        The enumerated iterable of tuples.
    '''
    i = begin

    it = iter(iterable)

    try:
        first = next(it)
    except StopIteration:
        return

    yield i, first

    for e in it:
        if pred(e):
            i += 1
        yield i, e


def split_on(pred: Predicate, iterable: Iterable[T]) -> Iterable[Iterable[T]]:
    '''Split an iterable based on sentnel elements.

    A sentinel element is one for which `pred` is `True`. From it onwards a
    new split is made.

    Args:
        pred: A predicate identifying a sentinel element.
        iterable: An iterable to enumerate.

    Returns:
        An iterable with an iterable for each split.
    '''

    enumerated = enumerate_on(pred, iterable)

    return (
        (line for _, line in group)
        for _, group in groupby(enumerated, key=itemgetter(0))
    )
