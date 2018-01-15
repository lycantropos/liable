import inspect
import operator
from functools import partial
from itertools import (chain,
                       filterfalse)
from types import FunctionType
from typing import (Any,
                    Iterable,
                    Iterator,
                    NamedTuple,
                    Dict,
                    Tuple,
                    List)

from liable import (annotator,
                    namespaces,
                    catalog,
                    strings)
from liable.catalog import ObjectPathType
from liable.types import NamespaceType

from .detectors import (supports_to_string,
                        is_literal)

ARGUMENTS_TEMPLATES = {
    inspect._POSITIONAL_ONLY: '{argument}',
    inspect._POSITIONAL_OR_KEYWORD: '{parameter}={argument}',
    inspect._VAR_POSITIONAL: '*{argument}',
    inspect._KEYWORD_ONLY: '{parameter}={argument}',
    inspect._VAR_KEYWORD: '**{argument}'}


class Signature(NamedTuple):
    parameters: List[inspect.Parameter]
    return_type: annotator.Annotation


class Argument:
    def __init__(self,
                 *,
                 name: str,
                 value: Any,
                 kind: inspect._ParameterKind = inspect._POSITIONAL_ONLY):
        self.name = name
        self.value = value
        self.kind = kind

    def to_string(self, namespace: NamespaceType) -> str:
        value = self.value
        if supports_to_string(value):
            value_name = value.to_string(namespace)
        elif is_literal(value):
            if isinstance(value, str):
                value_name = '\'' + value + '\''
            else:
                value_name = str(value)
        else:
            value_name = namespaces.search_name(value,
                                                namespace=namespace)
        return (ARGUMENTS_TEMPLATES[self.kind]
                .format(parameter=self.name,
                        argument=value_name))


class FunctionCall:
    def __init__(self,
                 function: FunctionType,
                 *arguments: Argument):
        self.function = function
        self.arguments = arguments

    def to_string(self, namespace: NamespaceType) -> str:
        function_name = namespaces.search_name(self.function,
                                               namespace=namespace)
        arguments_str = strings.join(parameter.to_string(namespace)
                                     for parameter in self.arguments)
        return ('{name}({arguments})'
                .format(name=function_name,
                        arguments=arguments_str))


def walk(function_call: FunctionCall) -> Iterator[Any]:
    yield function_call.function

    def is_function_call(object_: Any) -> bool:
        return isinstance(object_, FunctionCall)

    sub_calls = filter(is_function_call, function_call.arguments)
    yield from chain.from_iterable(map(walk, sub_calls))

    plain_arguments = filterfalse(is_function_call, function_call.arguments)
    yield from plain_arguments


def dependants_paths(functions: Iterable[FunctionType],
                     *,
                     namespace: NamespaceType
                     ) -> Iterator[ObjectPathType]:
    dependencies_detector = partial(dependencies,
                                    namespace=namespace)
    signatures_dependants = chain.from_iterable(map(dependencies_detector,
                                                    functions))
    object_path_seeker = partial(namespaces.search_path,
                                 namespace=namespace)
    result = set(chain(map(object_path_seeker,
                           signatures_dependants)))
    yield from filterfalse(catalog.is_built_in, result)


def dependencies(function: FunctionType,
                 *,
                 namespace: NamespaceType) -> Iterator[Any]:
    yield function
    function_signature = signature(function)
    parameters = function_signature.parameters
    annotations = map(operator.attrgetter('annotation'), parameters)
    annotation_walker = partial(annotator.walk,
                                namespace=namespace)
    yield from chain.from_iterable(map(annotation_walker, annotations))
    return_type = function_signature.return_type
    yield from return_type.bases


def signature(function: FunctionType) -> Signature:
    raw_signature = inspect.signature(function)
    parameters = raw_signature.parameters.values()
    parameters = list(map(normalize_annotation, parameters))
    return_type = annotator.normalize(raw_signature.return_annotation)
    return Signature(parameters=parameters,
                     return_type=return_type)


def normalize_annotation(parameter: inspect.Parameter) -> inspect.Parameter:
    parameter = normalize_parameter(parameter)
    annotation = annotator.normalize(parameter.annotation)
    return parameter.replace(annotation=annotation)


def normalize_parameter(parameter: inspect.Parameter) -> inspect.Parameter:
    if parameter.kind == inspect._VAR_POSITIONAL:
        return parameter.replace(annotation=Tuple[parameter.annotation])
    elif parameter.kind == inspect._VAR_KEYWORD:
        return parameter.replace(annotation=Dict[str, parameter.annotation])
    return parameter
