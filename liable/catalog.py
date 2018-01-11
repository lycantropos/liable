import enum
import inspect
import os
import sys
from typing import (Optional,
                    Iterable,
                    NamedTuple,
                    List)

SEPARATOR = '.'


class PathType(enum.IntEnum):
    inner = 0
    absolute = 1
    relative = 2


class ObjectPath(NamedTuple):
    module: Optional[str]
    object: Optional[str]
    type: PathType

    def __str__(self):
        if self.object is None:
            return self.module
        elif self.module is None:
            return self.object
        else:
            return self.module + SEPARATOR + self.object


def to_relative(path: str,
                *,
                system_paths: Iterable[str] = sys.path) -> str:
    try:
        root_path = max((system_path
                         for system_path in system_paths
                         if path.startswith(system_path)),
                        key=len)
    except TypeError as err:
        err_msg = ('Invalid module path: "{path}". '
                   'No root path found in `Python` system paths.'
                   .format(path=path))
        raise ModuleNotFoundError(err_msg) from err
    return os.path.normpath(os.path.relpath(path, root_path))


def to_import(path: str) -> str:
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
