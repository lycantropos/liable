import operator
import os
from functools import partial
from itertools import chain
from typing import (Any,
                    Hashable,
                    Mapping)

import autopep8

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


def merge_mappings(*mappings: Mapping[Hashable, Any]) -> dict:
    items = chain.from_iterable(map(operator.methodcaller('items'), mappings))
    return dict(items)


fix_code = partial(autopep8.fix_code,
                   options={'aggressive': True,
                            'max_line_length': 79})
