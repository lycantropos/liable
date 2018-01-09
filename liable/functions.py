import inspect
from functools import partial
from itertools import (chain,
                       filterfalse)
from types import FunctionType
from typing import (Any,
                    Iterable,
                    Iterator,
                    NamedTuple,
                    Dict)

from . import (annotator,
               namespaces,
               catalog)
from .annotator.detectors import is_generic
from .utils import merge_mappings


class Signature(NamedTuple):
    parameters: Dict[str, annotator.Annotation]
    return_type: annotator.Annotation


def dependants_paths(functions: Iterable[FunctionType],
                     *,
                     built_ins: namespaces.NamespaceType,
                     namespace: namespaces.NamespaceType,
                     generic_return_type: bool
                     ) -> Iterator[catalog.ObjectPath]:
    dependencies_detector = partial(dependencies,
                                    generic_return_type=generic_return_type)
    signatures_dependants = chain.from_iterable(map(dependencies_detector,
                                                    functions))
    object_path_seeker = partial(namespaces.search_path,
                                 namespace=merge_mappings(built_ins,
                                                          namespace))
    result = set(chain(map(object_path_seeker,
                           signatures_dependants)))

    def is_built_in_object_path(object_path: catalog.ObjectPath) -> bool:
        return object_path in built_ins

    yield from filterfalse(is_built_in_object_path, result)


def dependencies(function: FunctionType,
                 *,
                 generic_return_type: bool) -> Iterator[Any]:
    yield function
    function_signature = signature(function)
    parameters = function_signature.parameters
    yield from chain.from_iterable(map(annotator.walk, parameters.values()))
    return_type = function_signature.return_type
    if not generic_return_type and is_generic(return_type.origin):
        yield from return_type.bases
        return
    yield from annotator.walk(return_type)


def signature(function: FunctionType) -> Signature:
    raw_signature = inspect.signature(function)
    parameters = raw_signature.parameters.values()
    parameters = {parameter.name: annotator.normalize(parameter.annotation)
                  for parameter in parameters}
    return_type = annotator.normalize(raw_signature.return_annotation)
    return Signature(parameters=parameters,
                     return_type=return_type)
