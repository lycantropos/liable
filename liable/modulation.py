import importlib._bootstrap_external
import importlib.util
from types import ModuleType

from . import catalog

SEPARATOR = '.'


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
