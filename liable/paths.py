import inspect
import os
import sys
from typing import (Iterable,
                    List)

from . import modulation


def to_relative(path: str,
                *,
                system_paths: Iterable[str] = sys.path) -> str:
    root_path = max((system_path
                     for system_path in system_paths
                     if path.startswith(system_path)),
                    key=len)
    return os.path.normpath(os.path.relpath(path, root_path))


def to_import(path: str) -> str:
    path_parts = path.split(os.sep)
    path_parts = normalize_path_parts(path_parts)
    return modulation.SEPARATOR.join(path_parts)


def normalize_path_parts(parts: List[str]) -> List[str]:
    module_file_name = parts[-1]
    module_name = inspect.getmodulename(module_file_name)
    if module_name:
        if module_name == '__init__':
            return parts[:-1]
        else:
            return [*parts[:-1], module_name]
    return parts
