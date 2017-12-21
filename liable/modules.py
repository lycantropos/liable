import importlib._bootstrap_external
import importlib.util
import sys
from types import ModuleType
from typing import Dict

from . import catalog


def from_name(name: str,
              *,
              cache: Dict[str, ModuleType] = sys.modules) -> ModuleType:
    skeleton = skeleton_from_name(name)
    return load(skeleton,
                cache=cache)


def from_path(name: str,
              *,
              cache: Dict[str, ModuleType] = sys.modules) -> ModuleType:
    skeleton = skeleton_from_path(name)
    return load(skeleton,
                cache=cache)


def skeleton_from_name(name: str) -> ModuleType:
    spec = importlib.util.find_spec(name)
    return importlib.util.module_from_spec(spec)


def skeleton_from_path(path: str) -> ModuleType:
    module_name = catalog.to_import(catalog.to_relative(path))
    loader = importlib._bootstrap_external.SourceFileLoader(module_name,
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
