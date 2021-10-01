from ampdup.util import enumerate_on


def test_enumerate_empty_list():
    '''Enumerate an empty list returns an empty iterable.'''
    enumerated = enumerate_on(lambda x: True, [])

    assert list(enumerated) == []


def test_enumerate_on_even_numbers():
    '''Enumerate on a list of numbers, incrementing on even ones.'''
    numbers = [1, 2, 3, 4, 5, 6, 7, 9, 11, 12]

    enumerated = enumerate_on(lambda x: x % 2 == 0, numbers)

    expected = [
        (0, 1),
        (1, 2),
        (1, 3),
        (2, 4),
        (2, 5),
        (3, 6),
        (3, 7),
        (3, 9),
        (3, 11),
        (4, 12)
    ]

    assert list(enumerated) == expected
