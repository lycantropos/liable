import collections
from itertools import chain
from typing import (TypingMeta,
                    Any as AnyType,
                    Union as UnionType,
                    Optional as OptionalType,
                    Type,
                    Tuple,
                    Collection)

from liable import (namespaces,
                    strings)
from .base import Annotation

ELLIPSIS_STRING = '...'


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

        base = origin.__origin__
        base_name = namespaces.search_name(base,
                                           namespace=namespace)
        arguments_names = [argument.to_string(namespace)
                           for argument in self.arguments]
        arguments_name = strings.join(arguments_names,
                                      sep=', ')
        return ('{base}[{arguments}]'
                .format(base=base_name,
                        arguments=arguments_name))

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
        base_name = namespaces.search_name(origin_cls,
                                           namespace=namespace)
        arguments_names = [annotation.to_string(namespace)
                           for annotation in arguments]
        if len(arguments) > 1:
            arguments_names.append(str(None))
        arguments_name = strings.join(arguments_names,
                                      sep=', ')
        return '{base}[{arguments}]'.format(base=base_name,
                                            arguments=arguments_name)

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

        base = origin.__origin__
        base_name = namespaces.search_name(base,
                                           namespace=namespace)
        parameters_names = [parameter.to_string(namespace)
                            for parameter in self.parameters]
        parameters_name = strings.join(parameters_names,
                                       sep=', ')
        return_type_name = self.return_type.to_string(namespace)
        if parameters_name == ELLIPSIS_STRING:
            return ('{origin}[{parameters}, {return_type}]'
                    .format(origin=base_name,
                            parameters=parameters_name,
                            return_type=return_type_name))
        return ('{origin}[[{parameters}], {return_type}]'
                .format(origin=base_name,
                        parameters=parameters_name,
                        return_type=return_type_name))

    @property
    def bases(self) -> Tuple[Type[collections.Callable]]:
        return self.origin.__extra__,


class PlainGeneric(Annotation):
    def __init__(self,
                 origin: TypingMeta):
        super().__init__(origin)

    def to_string(self, namespace: namespaces.NamespaceType) -> str:
        return namespaces.search_name(self.origin,
                                      namespace=namespace)

    @property
    def bases(self) -> Tuple[Type]:
        return self.origin.__extra__,


class Generic(Annotation):
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

        base = origin.__origin__
        base_name = namespaces.search_name(base,
                                           namespace=namespace)
        arguments_names = [argument.to_string(namespace)
                           for argument in self.arguments]
        arguments_name = strings.join(arguments_names,
                                      sep=', ')
        return ('{base}[{elements}]'
                .format(base=base_name,
                        elements=arguments_name))

    @property
    def bases(self) -> Tuple[Type[collections.Iterable]]:
        return self.origin.__extra__,
