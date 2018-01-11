import inspect
import operator
from collections import defaultdict
from itertools import chain
from types import FunctionType
from typing import (Any,
                    Iterable,
                    Iterator,
                    Type,
                    Dict,
                    Set,
                    List)

from liable import namespaces
from liable.utils import merge_mappings

from . import (annotator,
               functions)


def combine(parameters: Iterable[inspect.Parameter],
            *,
            built_ins: namespaces.NamespaceType,
            namespace: namespaces.NamespaceType
            ) -> Dict[str, List[inspect.Parameter]]:
    result = defaultdict(list)
    for parameter in parameters:
        annotation = parameter.annotation
        cls = annotation.bases[-1]
        path = namespaces.search_path(cls,
                                      namespace=merge_mappings(built_ins,
                                                               namespace))
        if path in built_ins:
            module = 'utils'
        else:
            module = path.module
        result[module].append(parameter)
    return result


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
        mro = bases_mro(annotation)
        previous_annotation = previous_parameter.annotation
        previous_mro = bases_mro(previous_annotation)
        if (mro & previous_mro == {object} and
                not (previous_annotation.origin is annotation.origin is Any)):
            err_msg = ('Invalid parameters: annotations should agree, '
                       'but found "{previous_annotation}", "{annotation}".'
                       .format(previous_annotation=previous_annotation.origin,
                               annotation=annotation.origin))
            raise ValueError(err_msg)
        if previous_mro - mro:
            result[name] = parameter
    yield from result.values()


def bases_mro(annotation: annotator.Annotation) -> Set[Type]:
    return set(chain.from_iterable(map(operator.attrgetter('__mro__'),
                                       annotation.bases)))