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
            err_msg = ('Invalid parameter: "{parameter}", '
                       'annotations should agree, '
                       'but found "{previous_annotation}", "{annotation}".'
                       .format(parameter=parameter.name,
                               previous_annotation=previous_annotation.origin,
                               annotation=annotation.origin))
            raise ValueError(err_msg)
        if previous_mro - mro:
            result[name] = parameter
    yield from result.values()


def bases_mro(annotation: annotator.Annotation) -> Set[Type]:
    return set(chain.from_iterable(map(operator.attrgetter('__mro__'),
                                       annotation.bases)))


VARIADIC_PARAMETERS_KINDS = {inspect._VAR_POSITIONAL,
                             inspect._VAR_KEYWORD}


def is_variadic(parameter: inspect.Parameter) -> bool:
    return parameter.kind in VARIADIC_PARAMETERS_KINDS
