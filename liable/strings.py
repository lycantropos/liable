from typing import (Any,
                    Iterable,
                    Sequence)

STRINGS_SEPARATOR = ',\n'


def join_strings(strings: Iterable[str],
                 *,
                 sep: str = STRINGS_SEPARATOR) -> str:
    return sep.join(strings)


def join_with_wrapping(strings: Sequence[str],
                       *,
                       sep: str = STRINGS_SEPARATOR) -> str:
    if len(strings) == 1:
        string, = strings
        return string
    return '(' + sep.join(strings) + ')'


def wrap_with_quotes(string: str) -> Any:
    quote_character = '"'
    return quote_character + string + quote_character
