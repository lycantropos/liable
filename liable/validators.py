import importlib.util
import operator
import os
from functools import partial
from itertools import filterfalse
from typing import Iterable

from . import (strings,
               catalog)
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


def validate_modules(names: Iterable[str]) -> None:
    missing_modules = set(filterfalse(module_accessible, names))

    if not missing_modules:
        return

    missing_modules_str = strings.join(map(strings.wrap_with_quotes,
                                           missing_modules))
    err_msg = ('Next modules not found:\n'
               '{modules}.'
               .format(modules=missing_modules_str))
    raise ModuleNotFoundError(err_msg)


def module_accessible(name: str,
                      *,
                      sep: str = catalog.SEPARATOR) -> bool:
    first_sub_module_name, *rest_sub_modules_names = iter(name.split(sep))
    add_sep_prefix = partial(operator.add, sep)
    sub_modules_names = ([first_sub_module_name]
                         + list(map(add_sep_prefix, rest_sub_modules_names)))
    modules_paths = strings.iterative_join('', *sub_modules_names)
    for sub_module_name, module_path in zip(sub_modules_names,
                                            modules_paths):
        spec = importlib.util.find_spec(name=sub_module_name,
                                        package=module_path)
        if spec is None:
            return False
    return True
