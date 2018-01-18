import collections
import inspect
import operator
from contextlib import suppress
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
                    Type,
                    Iterable,
                    Iterator,
                    Dict,
                    Tuple,
                    List)

from hypothesis import strategies

from . import (functions,
               annotator,
               namespaces,
               parameters,
               catalog,
               strings)
from .annotator.detectors import is_generic
from .types import NamespaceType
from .utils import (fix_code,
                    merge_mappings,
                    to_name)


def init_module(modules_parameters: Dict[catalog.ModulePath,
                                         List[inspect.Parameter]]) -> str:
    strategies_paths = (
        (catalog.ContentPath(module=catalog.ModulePath(catalog.SEPARATOR
                                                       + str(module_path)),
                             object=to_strategy_name(parameter),
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


def name_to_module_path(full_name: str) -> catalog.ModulePath:
    return (catalog.name_to_module_path(full_name)
            ._replace(type=catalog.PathType.relative))


utilities = {name_to_module_path(strategies.__name__): strategies}


def module_imports(module_parameters: Iterable[inspect.Parameter],
                   *,
                   namespace: NamespaceType) -> Iterator[str]:
    namespace = merge_mappings(namespace, utilities)
    annotations = map(operator.attrgetter('annotation'), module_parameters)
    objects = set(chain.from_iterable(map(dependant_types, annotations)))
    object_path_seeker = partial(namespaces.search_path,
                                 namespace=namespace)
    objects_paths = map(object_path_seeker, objects)
    modules_objects_paths = (catalog.modules_objects_paths(objects_paths)
                             .values())
    yield from chain.from_iterable(starmap(catalog.to_imports,
                                           modules_objects_paths))


def dependant_types(annotation: annotator.Annotation) -> Iterator[Type]:
    bases = annotation.bases
    yield from chain.from_iterable(templates_dependants
                                   .get(base, [strategies.builds, base])
                                   for base in bases)
    initializers_parameters = chain.from_iterable(
            map(parameters.from_type_initializer, bases))
    annotations = map(operator.attrgetter('annotation'),
                      initializers_parameters)
    yield from chain.from_iterable(map(dependant_types,
                                       annotations))
    if isinstance(annotation, annotator.annotations.Generic):
        arguments = annotation.arguments
        yield from chain.from_iterable(map(dependant_types, arguments))


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
    strategy_name = to_strategy_name(parameter)
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


def combine(*objects: Any,
            module_path: catalog.ModulePath
            ) -> Iterable[Tuple[catalog.ContentPath, Any]]:
    for object_ in objects:
        content_path = catalog.ContentPath(module=module_path,
                                           object=object_.__name__,
                                           type=catalog.PathType.absolute)
        yield content_path, object_


with suppress(ImportError):
    from hypothesis.extra import numpy
    import numpy as np

    dtype = functions.Argument(name='dtype',
                               value=object,
                               kind=inspect._POSITIONAL_OR_KEYWORD)
    shape = functions.Argument(name='shape',
                               value=0,
                               kind=inspect._POSITIONAL_OR_KEYWORD)
    templates[np.ndarray] = functions.FunctionCall(numpy.arrays,
                                                   dtype,
                                                   shape)
    numpy_module_path = name_to_module_path(numpy.__name__)
    utilities.update(dict(combine(numpy.arrays,
                                  module_path=numpy_module_path)))

with suppress(ImportError):
    from hypothesis.extra import pandas
    import pandas as pd

    names_or_number = functions.Argument(name='names_or_number',
                                         value=1,
                                         kind=inspect._POSITIONAL_OR_KEYWORD)
    elements = functions.Argument(name='elements',
                                  value=templates[object],
                                  kind=inspect._POSITIONAL_OR_KEYWORD)
    columns = functions.Argument(name='columns',
                                 value=functions.FunctionCall(pandas.columns,
                                                              names_or_number,
                                                              elements))
    templates[pd.Series] = functions.FunctionCall(pandas.series,
                                                  elements)
    templates[pd.DataFrame] = functions.FunctionCall(pandas.data_frames,
                                                     columns)
    pandas_module_path = name_to_module_path(pandas.__name__)
    utilities.update(dict(combine(pandas.columns,
                                  pandas.series,
                                  pandas.data_frames,
                                  module_path=pandas_module_path)))

templates_dependants = {key: list(functions.walk(value))
                        for key, value in templates.items()}


def to_template(annotation: annotator.Annotation
                ) -> functions.FunctionCall:
    try:
        base, = annotation.bases
    except ValueError as err:
        if isinstance(annotation, (annotator.annotations.Union,
                                   annotator.annotations.Optional)):
            return functions.FunctionCall(strategies.one_of,
                                          *map(to_template,
                                               annotation.arguments))
        raise err
    try:
        template = templates[base]
    except KeyError:
        initializer_parameters = parameters.from_type_initializer(base)
        arguments = [
            functions.Argument(name=parameter.name,
                               value=to_template(parameter.annotation),
                               kind=inspect._POSITIONAL_OR_KEYWORD)
            for parameter in initializer_parameters]
        template = functions.FunctionCall(strategies.builds,
                                          functions.Argument(name='target',
                                                             value=base),
                                          *arguments)
    else:
        if isinstance(annotation, annotator.annotations.Generic):
            template = functions.FunctionCall(template.function,
                                              *map(to_template,
                                                   annotation.arguments))
    return template


def to_strategy_name(parameter: inspect.Parameter) -> str:
    annotation = parameter.annotation
    annotation_bases = annotation.bases
    parameter_full_name = parameter.name
    try:
        annotation_base, = annotation_bases
    except ValueError:
        pass
    else:
        if is_generic(annotation.origin):
            parameter_full_name += '_' + to_name(annotation_base).lower()
    return strings.to_plurals(parameter_full_name,
                              target_case=strings.Case.snake)
