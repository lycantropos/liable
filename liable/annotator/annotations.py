import collections
from itertools import chain
from typing import (TypingMeta,
                    Any as AnyType,
                    Union as UnionType,
                    Optional as OptionalType,
                    Type,
                    Tuple,
                    Collection)

from liable import namespaces
from .base import Annotation


class Raw(Annotation):
    def __init__(self,
                 origin: Type):
        super().__init__(origin)

    def to_string(self, namespace: namespaces.NamespaceType) -> str:
        return namespaces.search_name(self.origin,
                                      namespace=namespace)

    @property
    def bases(self) -> Tuple[Type]:
        return self.origin,


class PlainAnnotation(Annotation):
    def __init__(self,
                 origin: TypingMeta):
        super().__init__(origin)

    def to_string(self, namespace: namespaces.NamespaceType) -> str:
        return namespaces.search_name(self.origin,
                                      namespace=namespace)

    @property
    def bases(self) -> Tuple[Type]:
        return self.origin.__origin__,


class Any(Annotation):
    def __init__(self):
        super().__init__(AnyType)

    def to_string(self, namespace: namespaces.NamespaceType) -> str:
        return namespaces.search_name(self.origin,
                                      namespace=namespace)

    @property
    def bases(self) -> Tuple[object]:
        return object,


class Union(Annotation):
    def __init__(self,
                 origin: TypingMeta,
                 arguments: Collection[Annotation]):
        super().__init__(origin)
        self.arguments = arguments

    def to_string(self, namespace: namespaces.NamespaceType) -> str:
        origin = self.origin

        if namespaces.is_object_relative(origin,
                                         namespace=namespace):
            return namespaces.search_name(origin,
                                          namespace=namespace)

        result = str(origin)

        base = origin.__origin__
        base_name = namespaces.search_name(base,
                                           namespace=namespace)
        result = result.replace(str(base),
                                base_name)
        for annotation in self.arguments:
            result = replace_sub_annotation(result,
                                            sub_annotation=annotation,
                                            namespace=namespace)
        return result

    @property
    def bases(self) -> Tuple[Type, ...]:
        return tuple(chain.from_iterable(annotation.bases
                                         for annotation in self.arguments))


class Optional(Annotation):
    def __init__(self,
                 origin: TypingMeta,
                 arguments: Collection[Annotation]):
        super().__init__(origin)
        self.arguments = arguments

    def to_string(self, namespace: namespaces.NamespaceType) -> str:
        origin = self.origin

        if namespaces.is_object_relative(origin,
                                         namespace=namespace):
            return namespaces.search_name(origin,
                                          namespace=namespace)

        arguments = self.arguments
        # since "Flat is better than nested."
        #   Union[...types..., None]
        # looks better than
        #   Optional[Union[...types...]]
        origin_cls = OptionalType if len(arguments) == 1 else UnionType
        origin_name = namespaces.search_name(origin_cls,
                                             namespace=namespace)
        arguments_strings = [annotation.to_string(namespace)
                             for annotation in arguments]
        if len(arguments) > 1:
            arguments_strings.append(str(None))
        arguments_str = ', '.join(arguments_strings)
        return '{origin}[{arguments}]'.format(origin=origin_name,
                                              arguments=arguments_str)

    @property
    def bases(self) -> Tuple[Type, ...]:
        result = tuple(chain.from_iterable(annotation.bases
                                           for annotation in self.arguments))
        return result + (None,)


class Callable(Annotation):
    def __init__(self,
                 origin: TypingMeta,
                 parameters: Collection[Annotation],
                 return_type: Annotation):
        super().__init__(origin)
        self.parameters = parameters
        self.return_type = return_type

    def to_string(self, namespace: namespaces.NamespaceType) -> str:
        origin = self.origin

        if namespaces.is_object_relative(origin,
                                         namespace=namespace):
            return namespaces.search_name(origin,
                                          namespace=namespace)

        result = str(origin)
        base = origin.__origin__
        base_name = namespaces.search_name(base,
                                           namespace=namespace)
        result = result.replace(str(base),
                                base_name)
        for annotation in self.parameters:
            result = replace_sub_annotation(result,
                                            sub_annotation=annotation,
                                            namespace=namespace)
        result = replace_sub_annotation(result,
                                        sub_annotation=self.return_type,
                                        namespace=namespace)
        return result

    @property
    def bases(self) -> Tuple[Type[collections.Callable]]:
        return self.origin.__extra__,


class Iterable(Annotation):
    def __init__(self,
                 origin: TypingMeta,
                 elements: Collection[Annotation]):
        super().__init__(origin)
        self.elements = elements

    def to_string(self, namespace: namespaces.NamespaceType) -> str:
        origin = self.origin

        if namespaces.is_object_relative(origin,
                                         namespace=namespace):
            return namespaces.search_name(origin,
                                          namespace=namespace)

        result = str(origin)
        base = origin.__origin__
        base_name = namespaces.search_name(base,
                                           namespace=namespace)
        result = result.replace(str(base),
                                base_name)
        for annotation in self.elements:
            result = replace_sub_annotation(result,
                                            sub_annotation=annotation,
                                            namespace=namespace)
        return result

    @property
    def bases(self) -> Tuple[Type[collections.Iterable]]:
        return self.origin.__extra__,


class Mapping(Annotation):
    def __init__(self,
                 origin: TypingMeta,
                 keys: Annotation,
                 values: Annotation):
        super().__init__(origin)
        self.keys = keys
        self.values = values

    def to_string(self, namespace: namespaces.NamespaceType) -> str:
        origin = self.origin

        if namespaces.is_object_relative(origin,
                                         namespace=namespace):
            return namespaces.search_name(origin,
                                          namespace=namespace)

        result = str(origin)
        base = origin.__origin__
        base_name = namespaces.search_name(base,
                                           namespace=namespace)
        result = result.replace(str(base),
                                base_name)
        result = replace_sub_annotation(result,
                                        sub_annotation=self.keys,
                                        namespace=namespace)
        result = replace_sub_annotation(result,
                                        sub_annotation=self.values,
                                        namespace=namespace)
        return result

    @property
    def bases(self) -> Tuple[Type[collections.Mapping]]:
        return self.origin.__extra__,


def replace_sub_annotation(annotation_name: str,
                           *,
                           sub_annotation: Annotation,
                           namespace: namespaces.NamespaceType) -> str:
    sub_annotation_name = sub_annotation.to_string(namespace)
    return annotation_name.replace(str(sub_annotation.origin),
                                   sub_annotation_name)
