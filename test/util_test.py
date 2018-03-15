from enum import Enum

from pytest import raises

from ampdup.util import underlying_type, EmptyEnumError, NoCommonTypeError


def test_underlying_type_heterogeneous_enum():
    '''Check if underlying_type flags correctly an heterogeneous enum.'''

    class TestEnum(Enum):
        '''Test heterogeneous enumeration.'''
        a = True
        b = 0

    with raises(NoCommonTypeError):
        underlying_type(TestEnum)


def test_underlying_type_empty_enum():
    '''Check if underlying_type flags correctly an empty enum.'''

    class TestEnum(Enum):
        '''Test empty enumeration.'''

    with raises(EmptyEnumError):
        underlying_type(TestEnum)


def test_underlying_type_int_enum():
    '''Check if underlying_type flags correctly an empty enum.'''

    class TestEnum(Enum):
        '''Test empty enumeration of ints.'''
        A = 0
        B = 1

    assert underlying_type(TestEnum) is int


def test_underlying_type_string_enum():
    '''Check if underlying_type flags correctly an empty enum.'''

    class TestEnum(Enum):
        '''Test empty enumeration of strings.'''
        A = 'A'
        B = 'B'

    assert underlying_type(TestEnum) is str
