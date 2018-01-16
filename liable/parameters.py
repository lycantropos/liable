import inspect
import operator
from collections import defaultdict
from itertools import (chain,
                       filterfalse,
                       product,
                       repeat,
                       starmap)
from types import FunctionType
from typing import (Optional,
                    Type,
                    Iterable,
                    Iterator,
                    Dict,
                    List)

from . import (annotator,
               functions,
               catalog,
               namespaces)
from .types import NamespaceType

COMMONS_MODULE_PATH = catalog.ModulePath('utils')


def to_top(module_path: catalog.ModulePath) -> catalog.ModulePath:
    try:
        sup_module = module_path.module
    except AttributeError:
        return module_path
    else:
        return to_top(sup_module)


def combine(parameters: Iterable[inspect.Parameter],
            *,
            namespace: NamespaceType,
            commons_module_path: str = COMMONS_MODULE_PATH
            ) -> Dict[catalog.ModulePath, List[inspect.Parameter]]:
    result = defaultdict(list)
    for parameter in parameters:
        annotation = parameter.annotation
        try:
            cls, = annotation.bases
        except ValueError:
            module_path = commons_module_path
        else:
            path = namespaces.search_path(cls,
                                          namespace=namespace)
            if catalog.is_built_in(path):
                module_path = commons_module_path
            else:
                module_path = path.module
        result[to_top(module_path)].append(parameter)
    return result


def from_type_initializer(type_: Type) -> Iterator[inspect.Parameter]:
    initializer_signature = functions.signature(type_.__init__)
    # ignoring `self`
    initializer_parameters = initializer_signature.parameters[1:]
    yield from filterfalse(is_variadic, initializer_parameters)


def from_functions(module_functions: Iterable[FunctionType]
                   ) -> Iterator[inspect.Parameter]:
    signatures = list(map(functions.signature, module_functions))
    parameters = chain.from_iterable(map(operator.attrgetter('parameters'),
                                         signatures))
    result = {}
    for parameter in parameters:
        name = parameter.name
        annotation = parameter.annotation
        try:
            previous_parameter = result[name]
        except KeyError:
            result[name] = parameter
            continue
        previous_annotation = previous_parameter.annotation
        if not are_annotations_consistent(annotation, previous_annotation):
            err_msg = ('Invalid parameter: "{parameter}", '
                       'different annotations should agree, '
                       'but found "{previous_annotation}", "{annotation}".'
                       .format(parameter=name,
                               previous_annotation=previous_annotation.origin,
                               annotation=annotation.origin))
            raise ValueError(err_msg)
        if is_annotation_more_specific(annotation, previous_annotation):
            result[name] = parameter
    yield from result.values()


def is_annotation_more_specific(annotation: annotator.Annotation,
                                other_annotation: annotator.Annotation
                                ) -> bool:
    sub_types = set(bases_mro(annotation))
    sub_types -= {object}
    other_sub_types = set(bases_mro(other_annotation))
    other_sub_types -= {object}
    for type_ in sub_types:
        sibling = next(find_siblings(type_,
                                     other_types=other_sub_types))
        other_annotation_is_more_specific = issubclass(sibling, type_)
        if other_annotation_is_more_specific:
            return False
    return True


def are_annotations_consistent(annotation: annotator.Annotation,
                               previous_annotation: annotator.Annotation
                               ) -> bool:
    sub_types = set(bases_mro(annotation))
    sub_types -= {object}
    other_sub_types = set(bases_mro(previous_annotation))
    other_sub_types -= {object}
    return (are_type_systems_related(sub_types, other_sub_types) or
            are_type_systems_related(other_sub_types, sub_types))


def are_type_systems_related(types: Iterable[Type],
                             other_types: Iterable[Type]) -> bool:
    other_types = list(other_types)
    return all(has_sibling(type_,
                           other_types=other_types)
               for type_ in types)


def has_sibling(type_: Type,
                *,
                other_types: Iterable[Type]) -> bool:
    siblings = find_siblings(type_,
                             other_types=other_types)
    sibling = next(siblings, None)
    return sibling is not None


def find_siblings(type_: Type,
                  *,
                  other_types: Iterable[Type]) -> Iterator[Type]:
    other_types = list(other_types)
    types_pairs = product(repeat(type_,
                                 times=len(other_types)),
                          other_types)
    sup_classes = starmap(to_sup_class, types_pairs)
    yield from filter(None, sup_classes)


def to_sup_class(type_: Type, other_type: Type) -> Optional[Type]:
    if issubclass(type_, other_type):
        return other_type
    elif issubclass(other_type, type_):
        return type_
    else:
        return None


def bases_mro(annotation: annotator.Annotation) -> Iterator[Type]:
    yield from chain.from_iterable(map(operator.attrgetter('__mro__'),
                                       annotation.bases))


VARIADIC_PARAMETERS_KINDS = {inspect._VAR_POSITIONAL,
                             inspect._VAR_KEYWORD}


def is_variadic(parameter: inspect.Parameter) -> bool:
    return parameter.kind in VARIADIC_PARAMETERS_KINDS
