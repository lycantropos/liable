import importlib.util
import inspect
from types import ModuleType
from typing import (Any,
                    Dict)

from . import (catalog,
               file_system)
from .catalog import ObjectPathType


def from_module_path(module_path: catalog.ModulePath) -> ModuleType:
    full_name = str(module_path)
    return importlib.import_module(full_name)


def from_path(path: str) -> ModuleType:
    object_path = catalog.path_to_module_path(file_system.to_relative(path))
    return from_module_path(object_path)


def skeleton_from_name(name: str) -> ModuleType:
    spec = importlib.util.find_spec(name)
    return importlib.util.module_from_spec(spec)


def search(object_path: ObjectPathType,
           *,
           modules: Dict[catalog.ModulePath, ModuleType]) -> Any:
    if isinstance(object_path, catalog.ModulePath):
        return modules[object_path]
    module = modules[object_path.module]
    if object_path.object is None:
        err_msg = ('Invalid content path: '
                   'object should not be "None".')
        raise ValueError(err_msg)
    return getattr(module, object_path.object)


def is_built_in(module: ModuleType) -> bool:
    return not hasattr(module, '__file__')


def is_object_from_module(object_: Any,
                          *,
                          module: ModuleType) -> bool:
    return inspect.getmodule(object_) is module
