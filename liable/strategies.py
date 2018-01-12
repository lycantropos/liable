import collections
import inspect
import operator
from functools import partial
from itertools import (chain,
                       starmap)
from typing import (Iterable,
                    Iterator,
                    Dict,
                    List)

from hypothesis import strategies

from . import (functions,
               annotator,
               namespaces,
               catalog,
               strings)
from .types import NamespaceType
from .utils import (fix_code,
                    merge_mappings)


def init_module(modules_parameters: Dict[str, List[inspect.Parameter]]) -> str:
    strategies_paths = (
        (catalog.ObjectPath(module=catalog.SEPARATOR + module,
                            object=to_strategy_name(parameter.name),
                            type=catalog.PathType.relative)
         for parameter in parameters)
        for module, parameters in modules_parameters.items()
    )
    imports = chain.from_iterable(starmap(catalog.to_imports,
                                          strategies_paths))
    source = ''.join(imports)
    return fix_code(source)


def from_parameters(parameters: Iterable[inspect.Parameter],
                    *,
                    namespace: NamespaceType) -> str:
    parameters = list(parameters)
    code_blocks = chain(module_imports(parameters,
                                       namespace=namespace),
                        module_strategies_definitions(parameters,
                                                      namespace=namespace))
    return fix_code(''.join(code_blocks))


hypothesis_strategies_path = catalog.ObjectPath(
        module=strategies.__package__,
        object='strategies',
        type=catalog.PathType.relative)

utilities = {hypothesis_strategies_path: strategies}


def module_imports(parameters: Iterable[inspect.Parameter],
                   *,
                   namespace: NamespaceType) -> Iterator[str]:
    namespace = merge_mappings(namespace, utilities)
    annotations = map(operator.attrgetter('annotation'), parameters)
    bases = [annotation.bases[-1] for annotation in annotations]
    object_path_seeker = partial(namespaces.search_path,
                                 namespace=namespace)
    bases_paths = chain([hypothesis_strategies_path],
                        map(object_path_seeker, bases))
    modules_bases_paths = catalog.modules_objects_paths(bases_paths).values()

    def is_valid_object_path(object_path: catalog.ObjectPath) -> bool:
        return object_path.module is not None

    valid_objects_paths_filter = partial(filter, is_valid_object_path)
    modules_bases_paths = map(valid_objects_paths_filter, modules_bases_paths)
    modules_bases_paths = filter(None, map(list, modules_bases_paths))
    yield from chain.from_iterable(starmap(catalog.to_imports,
                                           modules_bases_paths))


def module_strategies_definitions(parameters: Iterable[inspect.Parameter],
                                  *,
                                  namespace: NamespaceType
                                  ) -> Iterator[str]:
    namespace = merge_mappings(namespace, utilities)
    strategy_definition_factory = partial(strategy_definition,
                                          namespace=namespace)
    yield from map(strategy_definition_factory, parameters)


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
    None: functions.FunctionCall(strategies.none),
    collections.Iterator: functions.FunctionCall(strategies.iterables),
    collections.Iterable: functions.FunctionCall(strategies.iterables),
    dict: functions.FunctionCall(strategies.dictionaries),
    tuple: functions.FunctionCall(strategies.tuples),
    set: functions.FunctionCall(strategies.sets),
    list: functions.FunctionCall(strategies.lists),
}


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
        signature = functions.signature(cls.__init__)
        parameters = signature.parameters[1:]  # ignoring `self`
        arguments = [
            functions.Argument(name=parameter.name,
                               value=to_template(parameter.annotation),
                               kind=parameter.kind)
            for parameter in parameters]
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
