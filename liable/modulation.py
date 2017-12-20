import importlib._bootstrap_external
import importlib.util
from types import ModuleType
from typing import (Any,
                    Iterable,
                    Dict)

from . import catalog

SEPARATOR = '.'

MODULE_UTILITY_FIELDS = ['__name__', '__doc__', '__package__',
                         '__loader__', '__spec__',
                         '__file__', '__path__', '__cached__',
                         '__builtins__', '__all__']


def from_name(name: str) -> ModuleType:
    spec = importlib.util.find_spec(name)
    return importlib.util.module_from_spec(spec)


def from_path(path: str) -> ModuleType:
    module_name = catalog.to_import(catalog.to_relative(path))
    loader = importlib._bootstrap_external.SourceFileLoader(module_name,
                                                            path=path)
    spec = importlib.util.spec_from_loader(module_name,
                                           loader=loader)
    return importlib.util.module_from_spec(spec)


def load(module: ModuleType) -> None:
    module.__loader__.exec_module(module)


def to_namespace(module: ModuleType,
                 *,
                 utility_fields: Iterable[str] = MODULE_UTILITY_FIELDS
                 ) -> Dict[str, Any]:
    result = dict(vars(module))
    for field in utility_fields:
        result.pop(field, None)
    return result
