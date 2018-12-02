'''This module mimics some functionality from typing-inspect.

Original code can be found at github.com/ilevkivskyi/typing_inspect.

Until typing-inspect stops being experimental or gets standardized (one can
dream), this simpler version will be used. Notice this only needs to support
Python 3.7+.
'''

# The original typing-inspect module is published on PyPI under the MIT
# license.
# There was no proper license notice on github, except for setup.py.
# License follows:
#
# Copyright 2018 Ivan Levkivskyi
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from typing import Callable

from typing import (  # type: ignore
    ClassVar, Generic, Tuple, Type, Union, _GenericAlias
)


def is_union_type(tp: Type) -> bool:
    '''Test if the type is a union type. Examples::
        is_union_type(int) == False
        is_union_type(Union) == True
        is_union_type(Union[int, int]) == False
        is_union_type(Union[T, int]) == True
    '''
    return (tp is Union or
            isinstance(tp, _GenericAlias) and tp.__origin__ is Union)


def get_origin(tp):
    '''Get the unsubscripted version of a type. Supports generic types, Union,
    Callable, and Tuple. Returns None for unsupported types. Examples::
        get_origin(int) == None
        get_origin(ClassVar[int]) == None
        get_origin(Generic) == Generic
        get_origin(Generic[T]) == Generic
        get_origin(Union[T, int]) == Union
        get_origin(List[Tuple[T, T]][int]) == list  # List prior to Python 3.7
    '''
    if isinstance(tp, _GenericAlias):
        return tp.__origin__ if tp.__origin__ is not ClassVar else None
    if tp is Generic:
        return Generic
    return None


def get_args(tp: Type) -> Tuple:
    '''Get type arguments with all substitutions performed. For unions,
    basic simplifications used by Union constructor are performed.
    On versions prior to 3.7 if `evaluate` is False (default),
    report result as nested tuple, this matches
    the internal representation of types. If `evaluate` is True
    (or if Python version is 3.7 or greater), then all
    type parameters are applied (this could be time and memory expensive).
    Examples::
        get_args(int) == ()
        get_args(Union[int, Union[T, int], str][int]) == (int, str)
        get_args(Union[int, Tuple[T, int]][str]) == (int, (Tuple, str, int))
        get_args(Union[int, Tuple[T, int]][str], evaluate=True) == \
                 (int, Tuple[str, int])
        get_args(Dict[int, Tuple[T, T]][Optional[int]], evaluate=True) == \
                 (int, Tuple[Optional[int], Optional[int]])
        get_args(Callable[[], T][int], evaluate=True) == ([], int,)
    '''
    if isinstance(tp, _GenericAlias):
        res = tp.__args__
        if get_origin(tp) is Callable and res[0] is not Ellipsis:
            res = (list(res[:-1]), res[-1])
        return res
    return ()


def is_optional_type(tp: Type) -> bool:
    '''Returns `True` if the type is `type(None)`, or is a direct `Union` to
       `type(None)`, such as `Optional[T]`.

    NOTE: this method inspects nested `Union` arguments but not `TypeVar`
    definitions (`bound`/`constraint`). So it will return `False` if
     - `tp` is a `TypeVar` bound, or constrained to, an optional type
     - `tp` is a `Union` to a `TypeVar` bound or constrained to an optional
       type,
     - `tp` refers to a *nested* `Union` containing an optional type or one of
       the above.
    Users wishing to check for optionality in types relying on type variables
    might wish to use this method in  combination with `get_constraints` and
    `get_bound`
    '''

    if tp is type(None):  # noqa
        return True
    if is_union_type(tp):
        return any(is_optional_type(t) for t in get_args(tp))
    return False
