import os
from typing import Any

from . import arboretum


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
        arboretum.from_source(source,
                              file_name=path)
    except SyntaxError:
        return False
    else:
        return True
