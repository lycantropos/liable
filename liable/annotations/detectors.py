import collections
from typing import (TypingMeta,
                    GenericMeta,
                    Any)

from liable.annotations import Annotation


def is_callable(object_: Any) -> bool:
    return isinstance(object_, collections.Callable)


def is_iterable(object_: Any) -> bool:
    return isinstance(object_, collections.Iterable)


def is_mapping(object_: Any) -> bool:
    return isinstance(object_, collections.Mapping)


def is_none_annotation(annotation: Annotation) -> bool:
    return annotation.bases == (None,)


def is_typing(object_: Any) -> bool:
    return (isinstance(type(object_), TypingMeta)
            or
            isinstance(object_, GenericMeta))
