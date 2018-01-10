import collections
from typing import (TypingMeta,
                    GenericMeta,
                    Any,
                    Type)

from .base import Annotation


def is_callable(type_: Type) -> bool:
    return issubclass(type_, collections.Callable)


def is_none_annotation(annotation: Annotation) -> bool:
    return annotation.bases == (None,)


def is_typing(object_: Any) -> bool:
    return (isinstance(type(object_), TypingMeta)
            or
            isinstance(object_, GenericMeta))


def is_generic(object_: Any) -> bool:
    return isinstance(object_, GenericMeta) and object_.__extra__ is not None
