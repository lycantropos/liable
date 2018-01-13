import builtins
import enum
import inspect
import operator
import os
from collections import defaultdict
from itertools import filterfalse
from typing import (Optional,
                    Iterable,
                    Iterator,
                    NamedTuple,
                    Dict,
                    Set,
                    List)

from . import strings

SEPARATOR = '.'


class PathType(enum.IntEnum):
    inner = 0
    absolute = 1
    relative = 2


IMPORTS_TEMPLATES = {PathType.absolute: 'import {module}\n',
                     PathType.relative: 'from {module} import {objects}\n'}

BUILT_IN_MODULE_NAME = builtins.__name__


class ObjectPath(NamedTuple):
    module: Optional[str]
    object: Optional[str]
    type: PathType

    def __str__(self):
        if self.object is None:
            return self.module
        elif is_built_in(self):
            return self.object
        else:
            return self.module + SEPARATOR + self.object


def is_absolute(object_path: ObjectPath) -> bool:
    return object_path.type == PathType.absolute


def is_built_in(object_path: ObjectPath) -> bool:
    return object_path.module == BUILT_IN_MODULE_NAME


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
            modules_names_str = strings.join('"' + name + '"'
                                             for name in modules_names)
            err_msg = ('Found modules paths for different modules: '
                       '{modules}.'
                       .format(modules=modules_names_str))
        else:
            err_msg = 'No modules paths found.'
        raise ValueError(err_msg) from err

    if is_built_in(module_paths[0]):
        return

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
                          ) -> Dict[str, Set[ObjectPath]]:
    result = defaultdict(list)
    for object_path in objects_paths:
        result[object_path.module].append(object_path)
    return dict(zip(result.keys(), map(set, result.values())))
