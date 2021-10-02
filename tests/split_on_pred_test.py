"""Tests for the split_on function."""
from ampdup.util import split_on


def test_split_empty_list():
    """Enumerate an empty list returns an empty iterable."""
    split = split_on(lambda x: True, [])

    assert list(split) == []


def test_split_on_even_numbers():
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
