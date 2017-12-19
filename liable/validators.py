import importlib.util
import os
from itertools import filterfalse
from typing import Iterable

from .utils import (join_strings,
                    wrap_with_quotes)


def validate_paths(paths: Iterable[str]) -> None:
    non_existent_paths = list(filterfalse(os.path.exists, paths))

    if not non_existent_paths:
        return

    non_existent_paths_str = join_strings(map(wrap_with_quotes,
                                              non_existent_paths))
    err_msg = ('Next paths not found on file system:\n'
               '{paths}.'
               .format(paths=non_existent_paths_str))
    raise FileNotFoundError(err_msg)


def validate_modules(names: Iterable[str]) -> None:
    missing_modules = set(filterfalse(module_accessible, names))

    if not missing_modules:
        return

    missing_modules_str = join_strings(map(wrap_with_quotes,
                                           missing_modules))
    err_msg = ('Next modules not found:\n'
               '{modules}.'
               .format(modules=missing_modules_str))
    raise ModuleNotFoundError(err_msg)


def module_accessible(name: str,
                      *,
                      sep: str = '.') -> bool:
    sub_modules_names = name.split(sep)
    package = ''
    for sub_module_name in sub_modules_names[:-1]:
        spec = importlib.util.find_spec(sub_module_name, package)
        if spec is None:
            return False
        package += sub_module_name

    return True
