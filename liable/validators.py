import os
from itertools import filterfalse
from typing import Iterable

from . import strings
from .utils import is_python_module


def validate_paths(paths: Iterable[str]) -> None:
    non_existent_paths = list(filterfalse(os.path.exists, paths))

    if not non_existent_paths:
        return

    non_existent_paths_str = strings.join(map(strings.wrap_with_quotes,
                                              non_existent_paths))
    err_msg = ('Next paths not found on file system:\n'
               '{paths}.'
               .format(paths=non_existent_paths_str))
    raise FileNotFoundError(err_msg)


def validate_modules_paths(paths: Iterable[str]) -> None:
    invalid_paths = list(filterfalse(is_python_module, paths))

    if invalid_paths:
        err_msg = ('Next paths are not valid Python modules:\n'
                   '{paths}'.format(paths=strings.join(invalid_paths)))
        raise OSError(err_msg)
