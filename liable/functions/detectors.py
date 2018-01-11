import inspect
from typing import (Any,
                    Type,
                    Tuple)


def supports_to_string(object_: Any) -> bool:
    to_string = getattr(object_, 'to_string', None)
    return inspect.ismethod(to_string)


def is_literal(object_: Any,
               *,
               basic_types: Tuple[Type] = (int, bool, float, str)) -> bool:
    return isinstance(object_, basic_types)
