import inspect
from itertools import (filterfalse,
                       chain)
from typing import (TypingMeta,
                    Any,
                    Union,
                    Type,
                    Iterator)

from liable.utils import to_name
from . import annotations
from .base import Annotation
from .detectors import (is_typing,
                        is_generic,
                        is_callable,
                        is_none_annotation)

NoneType = type(None)

ANNOTATIONS_REPLACEMENTS = {inspect._empty: Any}


def normalize(annotation: Type) -> Annotation:
    return to_annotation(ANNOTATIONS_REPLACEMENTS.get(annotation,
                                                      annotation))


def to_annotation(annotation: Any) -> Annotation:
    if not is_typing(annotation):
        return annotations.Raw(annotation)

    if annotation is Any:
        return annotations.Any()

    try:
        origin = annotation.__origin__
    except AttributeError:
        return annotations.Raw(object)

    if origin is Union:
        annotation.__args__ = tuple(map(none_type_to_none,
                                        annotation.__args__))
        arguments = annotation.__args__
        arguments_annotations = list(map(to_annotation, arguments))
        if None in arguments:
            arguments_annotations = list(filterfalse(is_none_annotation,
                                                     arguments_annotations))
            return annotations.Optional(origin=annotation,
                                        arguments=arguments_annotations)
        return annotations.Union(origin=annotation,
                                 arguments=arguments_annotations)

    if is_callable(annotation):
        signature_annotations = annotation.__args__
        if not signature_annotations:
            return annotations.PlainAnnotation(annotation)
        *parameters_annotations, return_type_annotation = signature_annotations
        return annotations.Callable(
                origin=annotation,
                parameters=list(map(to_annotation, parameters_annotations)),
                return_type=to_annotation(return_type_annotation))
    elif is_generic(annotation):
        arguments = annotation.__args__
        if not arguments:
            return annotations.PlainGeneric(annotation)
        return annotations.Generic(origin=annotation,
                                   arguments=arguments)

    return annotations.PlainAnnotation(annotation)


def walk(annotation: Annotation) -> Iterator[Union[Type, TypingMeta]]:
    if not isinstance(annotation, Annotation):
        err_msg = ('"{cls}" is not an annotation class.'
                   .format(cls=to_name(annotation.__class__)))
        raise TypeError(err_msg)

    if isinstance(annotation, (annotations.Raw,
                               annotations.PlainAnnotation,
                               annotations.Any,
                               annotations.PlainGeneric)):
        yield annotation.origin
        yield from annotation.bases
    elif isinstance(annotation, (annotations.Union, annotations.Optional)):
        yield annotation.origin.__origin__
        yield from chain.from_iterable(map(walk, annotation.arguments))
    elif isinstance(annotation, annotations.Generic):
        yield annotation.origin.__origin__
        yield from chain.from_iterable(map(walk, annotation.arguments))
    elif isinstance(annotation, annotations.Callable):
        yield annotation.origin.__origin__
        yield from chain.from_iterable(map(walk, annotation.parameters))
        yield from walk(annotation.return_type)
    else:
        err_msg = ('Do not know how to walk through '
                   '"{cls}" annotation class '
                   'object "{object}".'
                   .format(cls=to_name(annotation.__class__),
                           object=to_name(annotation)))
        raise TypeError(err_msg)


def none_type_to_none(object_: Any) -> Type:
    if object_ is NoneType:
        return None
    return object_
