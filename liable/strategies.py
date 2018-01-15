import collections
import inspect
import operator
from datetime import (time,
                      timedelta,
                      date,
                      datetime)
from decimal import Decimal
from fractions import Fraction
from functools import partial
from itertools import (chain,
                       starmap)
from typing import (Any,
                    Iterable,
                    Iterator,
                    Dict,
                    List)

from hypothesis import strategies

from . import (functions,
               annotator,
               namespaces,
               parameters,
               catalog,
               strings)
from .types import NamespaceType
from .utils import (fix_code,
                    merge_mappings)


def init_module(modules_parameters: Dict[catalog.ModulePath,
                                         List[inspect.Parameter]]) -> str:
    strategies_paths = (
        (catalog.ContentPath(module=catalog.ModulePath(catalog.SEPARATOR
                                                       + str(module_path)),
                             object=to_strategy_name(parameter.name),
                             type=catalog.PathType.relative)
         for parameter in module_parameters)
        for module_path, module_parameters in modules_parameters.items()
    )
    imports = chain.from_iterable(starmap(catalog.to_imports,
                                          strategies_paths))
    source = ''.join(imports)
    return fix_code(source)


def from_parameters(module_parameters: Iterable[inspect.Parameter],
                    *,
                    namespace: NamespaceType) -> str:
    module_parameters = list(module_parameters)
    code_blocks = chain(module_imports(module_parameters,
                                       namespace=namespace),
                        module_strategies_definitions(module_parameters,
                                                      namespace=namespace))
    return fix_code(''.join(code_blocks))


utilities = {
    catalog.ModulePath(module=catalog.ModulePath(strategies.__package__),
                       object='strategies',
                       type=catalog.PathType.relative): strategies}


def module_imports(module_parameters: Iterable[inspect.Parameter],
                   *,
                   namespace: NamespaceType) -> Iterator[str]:
    namespace = merge_mappings(namespace, utilities)
    annotations = map(operator.attrgetter('annotation'), module_parameters)
    objects = set(dependant_objects(annotations))
    object_path_seeker = partial(namespaces.search_path,
                                 namespace=namespace)
    objects_paths = map(object_path_seeker, objects)
    modules_objects_paths = (catalog.modules_objects_paths(objects_paths)
                             .values())
    yield from chain.from_iterable(starmap(catalog.to_imports,
                                           modules_objects_paths))


def dependant_objects(annotations: Iterable[annotator.Annotation]
                      ) -> Iterator[Any]:
    for annotation in annotations:
        yield from chain.from_iterable(templates_dependants
                                       .get(base,
                                            [strategies.builds, base])
                                       for base in annotation.bases)
        if isinstance(annotation, annotator.annotations.Generic):
            yield from dependant_objects(annotation.arguments)


def module_strategies_definitions(
        module_parameters: Iterable[inspect.Parameter],
        *,
        namespace: NamespaceType) -> Iterator[str]:
    namespace = merge_mappings(namespace, utilities)
    strategy_definition_factory = partial(strategy_definition,
                                          namespace=namespace)
    yield from map(strategy_definition_factory, module_parameters)


def strategy_definition(parameter: inspect.Parameter,
                        *,
                        namespace: NamespaceType) -> str:
    strategy_name = to_strategy_name(parameter.name)
    template = to_template(parameter.annotation)
    value = template.to_string(namespace)
    return strategy_name + ' = ' + value + '\n'


templates = {
    type: functions.FunctionCall(
            strategies.builds,
            functions.Argument(name='target',
                               value=type),
            functions.FunctionCall(strategies.from_regex,
                                   functions.Argument(name='regex',
                                                      value='\A[_a-zA-Z]+\Z')),
            functions.FunctionCall(strategies.tuples),
            functions.FunctionCall(strategies.builds,
                                   functions.Argument(name='target',
                                                      value=dict))),
    object: functions.FunctionCall(strategies.none),
    int: functions.FunctionCall(strategies.integers),
    bool: functions.FunctionCall(strategies.booleans),
    str: functions.FunctionCall(strategies.text),
    float: functions.FunctionCall(strategies.floats),
    Decimal: functions.FunctionCall(strategies.decimals),
    Fraction: functions.FunctionCall(strategies.fractions),
    None: functions.FunctionCall(strategies.none),
    collections.Hashable: functions.FunctionCall(strategies.integers),
    collections.Iterator: functions.FunctionCall(strategies.iterables),
    collections.Iterable: functions.FunctionCall(strategies.iterables),
    collections.Mapping: functions.FunctionCall(strategies.dictionaries),
    collections.Container: functions.FunctionCall(strategies.lists),
    collections.Sequence: functions.FunctionCall(strategies.lists),
    collections.Collection: functions.FunctionCall(strategies.lists),
    collections.MutableSet: functions.FunctionCall(strategies.lists),
    dict: functions.FunctionCall(strategies.dictionaries),
    tuple: functions.FunctionCall(strategies.tuples),
    frozenset: functions.FunctionCall(strategies.frozensets),
    set: functions.FunctionCall(strategies.sets),
    list: functions.FunctionCall(strategies.lists),
    timedelta: functions.FunctionCall(strategies.timedeltas),
    time: functions.FunctionCall(strategies.times),
    date: functions.FunctionCall(strategies.dates),
    datetime: functions.FunctionCall(strategies.datetimes),
}

templates_dependants = {key: list(functions.walk(value))
                        for key, value in templates.items()}


def to_template(annotation: annotator.Annotation
                ) -> functions.FunctionCall:
    try:
        cls, = annotation.bases
    except ValueError as err:
        if isinstance(annotation, (annotator.annotations.Union,
                                   annotator.annotations.Optional)):
            return functions.FunctionCall(strategies.one_of,
                                          *map(to_template,
                                               annotation.arguments))
        raise err
    try:
        template = templates[cls]
    except KeyError:
        initializer_signature = functions.signature(cls.__init__)
        # ignoring `self`
        initializer_parameters = initializer_signature.parameters[1:]
        arguments = [
            functions.Argument(name=parameter.name,
                               value=to_template(parameter.annotation),
                               kind=inspect._POSITIONAL_OR_KEYWORD)
            for parameter in initializer_parameters
            if not parameters.is_variadic(parameter)]
        template = functions.FunctionCall(strategies.builds,
                                          functions.Argument(name='target',
                                                             value=cls),
                                          *arguments)
    else:
        if isinstance(annotation, annotator.annotations.Generic):
            template = functions.FunctionCall(template.function,
                                              *map(to_template,
                                                   annotation.arguments))
    return template


to_strategy_name = strings.to_plurals
