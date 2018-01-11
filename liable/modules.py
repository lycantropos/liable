import importlib.util
import inspect
import os
import sys
from importlib._bootstrap_external import (SOURCE_SUFFIXES,
                                           SourceFileLoader)
from types import ModuleType
from typing import (Any,
                    Dict,
                    Tuple)

from . import catalog


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
    module_name = catalog.to_import(catalog.to_relative(path))
    loader = SourceFileLoader(module_name,
                              path=path)
    spec = importlib.util.spec_from_loader(module_name,
                                           loader=loader)
    return importlib.util.module_from_spec(spec)


def load(module: ModuleType,
         *,
         cache: Dict[str, ModuleType]) -> ModuleType:
    cached_module = cache.get(module.__name__, None)
    if cached_module is None:
        module.__loader__.exec_module(module)
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


def path_to_name(path: str,
                 *,
                 source_suffixes: Tuple[str] = tuple(SOURCE_SUFFIXES)) -> str:
    if os.path.isabs(path):
        err_msg = ('Invalid path: "{path}", '
                   'should be relative.'
                   .format(path=path))
        raise ValueError(err_msg)
    if path.endswith(source_suffixes):
        path, _ = os.path.splitext(path)
    return os.path.normpath(path).replace(os.sep, '.')
