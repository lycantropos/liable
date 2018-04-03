import inspect
from functools import partial
from itertools import (filterfalse,
                       chain)
from typing import (TypingMeta,
                    Any,
                    Union,
                    Type,
                    Iterator)

from liable.types import NamespaceType
from liable.utils import to_name
from . import annotations
from .base import Annotation
from .detectors import (is_typing,
                        is_generic,
                        is_callable,
                        is_none_annotation)

NoneType = type(None)

ANNOTATIONS_REPLACEMENTS = {inspect._empty: Any}


def normalize(type_: Type) -> Annotation:
    return to_annotation(ANNOTATIONS_REPLACEMENTS.get(type_,
                                                      type_))


def to_annotation(object_: Any) -> Annotation:
    if not is_typing(object_):
        return annotations.Raw(object_)

    if object_ is Any:
        return annotations.Any()

    try:
        origin = object_.__origin__
    except AttributeError:
        return annotations.Raw(object)

    if origin is Union:
        object_.__args__ = tuple(map(none_type_to_none,
                                     object_.__args__))
        arguments = object_.__args__
        arguments_annotations = list(map(to_annotation, arguments))
        if None in arguments:
            arguments_annotations = list(filterfalse(is_none_annotation,
                                                     arguments_annotations))
            return annotations.Optional(origin=object_,
                                        arguments=arguments_annotations)
        return annotations.Union(origin=object_,
                                 arguments=arguments_annotations)

    if is_callable(object_):
        signature_annotations = object_.__args__
        if not signature_annotations:
            return annotations.PlainAnnotation(object_)
        *parameters_annotations, return_type_annotation = signature_annotations
        return annotations.Callable(
                origin=object_,
                parameters=list(map(to_annotation, parameters_annotations)),
                return_type=to_annotation(return_type_annotation))
    elif is_generic(object_):
        arguments = object_.__args__
        if not arguments:
            return annotations.PlainGeneric(object_)
        arguments_annotations = list(map(to_annotation, arguments))
        return annotations.Generic(origin=object_,
                                   arguments=arguments_annotations)

    return annotations.PlainAnnotation(object_)


def walk(annotation: Annotation,
         *,
         namespace: NamespaceType) -> Iterator[Union[Type, TypingMeta]]:
    origin = annotation.origin
    if origin in namespace.values():
        yield origin
        return

    if not isinstance(annotation, Annotation):
        err_msg = ('"{cls}" is not an annotation class.'
                   .format(cls=to_name(annotation.__class__)))
        raise TypeError(err_msg)

    if isinstance(annotation, (annotations.Raw,
                               annotations.PlainAnnotation,
                               annotations.Any,
                               annotations.PlainGeneric)):
        yield origin
        yield from annotation.bases
    elif isinstance(annotation, (annotations.Union, annotations.Optional)):
        yield origin.__origin__
        walker = partial(walk, namespace=namespace)
        yield from chain.from_iterable(map(walker, annotation.arguments))
    elif isinstance(annotation, annotations.Generic):
        yield origin.__origin__
        walker = partial(walk, namespace=namespace)
        yield from chain.from_iterable(map(walker, annotation.arguments))
    elif isinstance(annotation, annotations.Callable):
        yield origin.__origin__
        walker = partial(walk, namespace=namespace)
        yield from chain.from_iterable(map(walker, annotation.parameters))
        yield from walker(annotation.return_type)
    else:
        err_msg = ('Do not know how to walk through '
                   '"{cls}" annotation class '
                   'object "{object}".'
                   .format(cls=to_name(annotation.__class__),
                           object=to_name(annotation)))
        raise TypeError(err_msg)


def none_type_to_none(object_: Any) -> Any:
    if object_ is NoneType:
        return None
    return object_
