import inspect
import os
from functools import partial
from typing import (Any,
                    Iterable,
                    Iterator)

STRINGS_SEPARATOR = ',\n'


def parse_module_name(path: str) -> str:
    return inspect.getmodulename(path) or os.path.basename(path)


def find_files(path: str,
               *,
               recursive: bool) -> Iterator[str]:
    if os.path.isdir(path):
        yield from directory_files(path,
                                   recursive=recursive)
    else:
        yield path


def directory_files(path: str,
                    *,
                    recursive: bool) -> Iterator[str]:
    if recursive:
        for root, _, files_names in os.walk(path):
            yield from map(partial(os.path.join, root), files_names)
    else:
        yield from filter(os.path.isfile,
                          map(partial(os.path.join, path), os.listdir(path)))


def join_strings(strings: Iterable[str],
                 *,
                 sep: str = STRINGS_SEPARATOR) -> str:
    return sep.join(strings)


def wrap_with_quotes(string: str) -> Any:
    quote_character = '"'
    return quote_character + string + quote_character
