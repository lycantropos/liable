import importlib.util
import inspect
import operator
from functools import partial
from types import ModuleType
from typing import (Any,
                    Dict)

from . import (catalog,
               strings)


def from_name(full_name: str) -> ModuleType:
    return importlib.import_module(full_name)


def from_path(path: str) -> ModuleType:
    full_name = catalog.to_module_full_name(catalog.to_relative(path))
    return from_name(full_name)


def skeleton_from_name(name: str) -> ModuleType:
    spec = importlib.util.find_spec(name)
    return importlib.util.module_from_spec(spec)


def search(object_path: catalog.ObjectPath,
           *,
           modules: Dict[str, ModuleType]) -> Any:
    object_ = modules.get(str(object_path), None)
    if object_ is not None:
        return object_
    module = modules[object_path.module]
    if object_path.object is None:
        object_ = module
    elif object_path.type == catalog.PathType.relative:
        object_ = getattr(module, object_path.object)
    return object_


def is_built_in(module: ModuleType) -> bool:
    return not hasattr(module, '__file__')


def is_object_from_module(object_: Any,
                          *,
                          module: ModuleType) -> bool:
    return inspect.getmodule(object_) is module


def full_name_valid(full_name: str,
                    *,
                    sep: str = catalog.SEPARATOR) -> bool:
    first_sub_module_name, *rest_sub_modules_names = iter(full_name.split(sep))
    add_sep_prefix = partial(operator.add, sep)
    sub_modules_names = ([first_sub_module_name]
                         + list(map(add_sep_prefix, rest_sub_modules_names)))
    modules_paths = strings.iterative_join('', *sub_modules_names)
    for sub_module_name, module_path in zip(sub_modules_names,
                                            modules_paths):
        full_name = importlib.util.resolve_name(name=sub_module_name,
                                                package=module_path)
        try:
            from_name(full_name)
        except ImportError:
            return False
    return True
