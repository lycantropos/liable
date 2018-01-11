import importlib.util
import inspect
import sys
from importlib._bootstrap_external import SourceFileLoader
from types import ModuleType
from typing import (Any,
                    Dict)

from . import (catalog,
               strings)


def from_name(name: str,
              *,
              cache: Dict[str, ModuleType] = sys.modules) -> ModuleType:
    skeleton = skeleton_from_name(name)
    return load(skeleton,
                cache=cache)


def from_path(path: str,
              *,
              cache: Dict[str, ModuleType] = sys.modules) -> ModuleType:
    skeleton = skeleton_from_path(path)
    return load(skeleton,
                cache=cache)


def skeleton_from_name(name: str) -> ModuleType:
    spec = importlib.util.find_spec(name)
    return importlib.util.module_from_spec(spec)


def skeleton_from_path(path: str) -> ModuleType:
    module_full_name = catalog.to_module_full_name(catalog.to_relative(path))
    loader = SourceFileLoader(module_full_name,
                              path=path)
    spec = importlib.util.spec_from_loader(module_full_name,
                                           loader=loader)
    return importlib.util.module_from_spec(spec)


def load(module: ModuleType,
         *,
         cache: Dict[str, ModuleType]) -> ModuleType:
    module_full_name = module.__name__
    cached_module = cache.get(module_full_name, None)
    if cached_module is None:
        module.__loader__.exec_module(module)
        cache[module_full_name] = module
        return module
    return cached_module


def search(object_path: catalog.ObjectPath,
           *,
           modules: Dict[str, ModuleType]) -> Any:
    module = modules[object_path.module]
    if object_path.object is None:
        object_ = module
    else:
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
