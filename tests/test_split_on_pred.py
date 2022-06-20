"""Tests for the split_on function."""
from typing import List

from ampdup.util import split_on


def test_split_empty_list() -> None:
    """Enumerate an empty list returns an empty iterable."""
    empty: List[int] = []
    split = split_on(lambda x: True, empty)

    assert not list(split)


def test_split_on_even_numbers() -> None:
    """Enumerate on a list of numbers, incrementing on even ones."""
    numbers = [1, 2, 3, 4, 5, 6, 7, 9, 11, 12]

    split = split_on(lambda x: x % 2 == 0, numbers)

    expected = [
        [1],
        [2, 3],
        [4, 5],
        [6, 7, 9, 11],
        [12],
    ]

    assert list(list(g) for g in split) == expected
