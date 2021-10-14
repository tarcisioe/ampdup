"""An Optional-like type for cases where None is valid."""
from enum import Enum
from typing import TypeVar, Union


class NothingType(Enum):
    """A sentinel type for cases where None is valid."""

    VALUE = 0


_T = TypeVar('_T')
Nothing = NothingType.VALUE
Maybe = Union[_T, NothingType]
