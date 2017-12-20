import os
from typing import (Any,
                    Iterable,
                    Sequence)

from .arboterum import to_tree

STRINGS_SEPARATOR = ',\n'


def join_strings(strings: Iterable[str],
                 *,
                 sep: str = STRINGS_SEPARATOR) -> str:
    return sep.join(strings)


def join_with_wrapping(strings: Sequence[str],
                       *,
                       sep: str) -> str:
    if len(strings) == 1:
        string, = strings
        return string
    return '(' + sep.join(strings) + ')'


def wrap_with_quotes(string: str) -> Any:
    quote_character = '"'
    return quote_character + string + quote_character


def to_name(object_: Any) -> str:
    try:
        return object_.__qualname__
    except AttributeError:
        try:
            return object_.__name__
        except AttributeError:
            return str(object_)


def is_python_module(path: str) -> bool:
    if not os.path.isfile(path):
        return False
    with open(path) as source_file:
        source = source_file.read()

    try:
        to_tree(source,
                file_name=path)
    except SyntaxError:
        return False
    else:
        return True
