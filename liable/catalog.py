import enum
import inspect
import operator
import os
import sys
from collections import defaultdict
from itertools import filterfalse
from typing import (Optional,
                    Iterable,
                    Iterator,
                    NamedTuple,
                    Dict,
                    List)

from . import strings

SEPARATOR = '.'


class PathType(enum.IntEnum):
    inner = 0
    absolute = 1
    relative = 2


IMPORTS_TEMPLATES = {PathType.absolute: 'import {module}\n',
                     PathType.relative: 'from {module} import {objects}\n'}


class ObjectPath(NamedTuple):
    module: Optional[str]
    object: Optional[str]
    type: PathType

    def __str__(self):
        if is_absolute(self):
            return self.module
        elif self.module is None:
            return self.object
        else:
            return self.module + SEPARATOR + self.object


def is_absolute(object_path: ObjectPath) -> bool:
    return object_path.type == PathType.absolute


def to_relative(path: str,
                *,
                system_paths: Iterable[str] = sys.path) -> str:
    try:
        root_path = max((system_path
                         for system_path in system_paths
                         if path.startswith(system_path)),
                        key=len)
    except ValueError as err:
        err_msg = ('Invalid module path: "{path}". '
                   'No root path found in `Python` system paths.'
                   .format(path=path))
        raise ModuleNotFoundError(err_msg) from err
    return os.path.normpath(os.path.relpath(path, root_path))


def to_module_full_name(path: str) -> str:
    path_parts = path.split(os.sep)
    path_parts = normalize_path_parts(path_parts)
    return SEPARATOR.join(path_parts)


def normalize_path_parts(parts: List[str]) -> List[str]:
    module_file_name = parts[-1]
    module_name = inspect.getmodulename(module_file_name)
    if module_name:
        if module_name == '__init__':
            return parts[:-1]
        else:
            return [*parts[:-1], module_name]
    return parts


def to_imports(*module_paths: ObjectPath) -> Iterator[str]:
    modules_names = set(map(operator.attrgetter('module'), module_paths))
    try:
        module_name, = modules_names
    except ValueError as err:
        if modules_names:
            err_msg = ('Found modules paths for different modules: '
                       '{modules}.'
                       .format(modules=strings.join(modules_names)))
        else:
            err_msg = 'No modules paths found.'
        raise ValueError(err_msg) from err


    non_absolute_paths = list(filterfalse(is_absolute, module_paths))
    if non_absolute_paths:
        objects_names = list(map(operator.attrgetter('object'),
                                 non_absolute_paths))
        objects_names_str = strings.join_with_wrapping(objects_names)
        yield (IMPORTS_TEMPLATES[PathType.relative]
               .format(module=module_name,
                       objects=objects_names_str))
    absolute_path = next(filter(is_absolute, module_paths), None)
    if absolute_path is not None:
        yield (IMPORTS_TEMPLATES[PathType.absolute]
               .format(module=module_name))


def modules_objects_paths(objects_paths: Iterable[ObjectPath]
                          ) -> Dict[str, List[ObjectPath]]:
    result = defaultdict(list)
    for object_path in objects_paths:
        result[object_path.module].append(object_path)
    return result
