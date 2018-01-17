import importlib.util
import inspect
from types import ModuleType
from typing import (Any,
                    Dict)

from . import (catalog,
               file_system)
from .catalog import ObjectPathType


def from_module_path(module_path: catalog.ModulePath) -> ModuleType:
    if module_path.type == catalog.PathType.relative:
        sup_module_full_name = str(module_path.module)
        sup_module = importlib.import_module(sup_module_full_name)
        return getattr(sup_module, module_path.object)
    module_full_name = str(module_path)
    return importlib.import_module(module_full_name)


def from_path(path: str) -> ModuleType:
    object_path = catalog.path_to_module_path(file_system.to_relative(path))
    return from_module_path(object_path)


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
    return inspect.getmodule(object_) is module and object_ is not module
