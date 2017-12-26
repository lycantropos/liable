import inspect
from itertools import chain
from types import FunctionType
from typing import (Any,
                    Iterator,
                    NamedTuple,
                    Dict)

from . import annotator
from .annotator.detectors import is_generic


class Signature(NamedTuple):
    parameters: Dict[str, annotator.Annotation]
    return_type: annotator.Annotation


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
