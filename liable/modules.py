import importlib.util
from types import ModuleType

from typing import (Any,
                    Iterable,
                    Iterator,
                    Dict,
                    Tuple)

SEPARATOR = '.'

MODULE_UTILITY_FIELDS = ['__name__', '__doc__', '__package__',
                         '__loader__', '__spec__',
                         '__file__', '__path__', '__cached__',
                         '__builtins__', '__all__']


def skeletons(names: Iterable[str]) -> Iterator[Tuple[str, ModuleType]]:
    for module_name in names:
        spec = importlib.util.find_spec(module_name)
        module = importlib.util.module_from_spec(spec)
        yield module_name, module


def load(module: ModuleType) -> None:
    module.__loader__.exec_module(module)


def to_dict(module: ModuleType,
            *,
            utility_fields: Iterable[str] = MODULE_UTILITY_FIELDS
            ) -> Dict[str, Any]:
    result = vars(module)
    for field in utility_fields:
        result.pop(field, None)
    return result
