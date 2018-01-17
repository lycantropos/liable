import inspect
from functools import partial
from itertools import (chain,
                       filterfalse,
                       starmap)
from typing import Iterable

import pytest

from . import (annotator,
               namespaces,
               catalog,
               strategies)
from .types import NamespaceType
from .utils import (fix_code,
                    to_name)

DEFINITION_TEMPLATE = ('@{pytest}.{fixture}(scope=\'function\')\n'
                       .format(pytest=to_name(pytest),
                               fixture=to_name(pytest.fixture))
                       + 'def {name}() -> {annotation}:\n')
RETURN_TEMPLATE = 'return {strategies}.{strategy}.example()\n'


def from_parameters(parameters: Iterable[inspect.Parameter],
                    *,
                    namespace: NamespaceType,
                    spaces_count: int,
                    tests_module_name: str,
                    strategies_module_name: str) -> str:
    annotations = chain.from_iterable(annotator.walk(parameter.annotation,
                                                     namespace=namespace)
                                      for parameter in parameters)
    object_path_seeker = partial(namespaces.search_path,
                                 namespace=namespace)
    annotations_paths = map(object_path_seeker, annotations)
    additional_objects_paths = [
        catalog.ModulePath(to_name(pytest)),
        catalog.ModulePath(module=catalog.ModulePath(tests_module_name),
                           object=strategies_module_name,
                           type=catalog.PathType.relative)
    ]
    dependant_objects_paths = chain(additional_objects_paths,
                                    annotations_paths)
    dependant_objects_paths = filterfalse(catalog.is_built_in,
                                          dependant_objects_paths)
    modules_dependant_objects_paths = (
        catalog.modules_objects_paths(dependant_objects_paths).values())
    imports = chain.from_iterable(starmap(catalog.to_imports,
                                          modules_dependant_objects_paths))
    fixture_factory = partial(from_parameter,
                              strategies_module_name=strategies_module_name,
                              spaces_count=spaces_count,
                              namespace=namespace)
    fixtures = map(fixture_factory, parameters)
    code_blocks = chain(imports,
                        fixtures)
    return fix_code(''.join(code_blocks))


def from_parameter(parameter: inspect.Parameter,
                   *,
                   namespace: NamespaceType,
                   strategies_module_name: str,
                   spaces_count: int) -> str:
    strategy_name = strategies.to_strategy_name(parameter)
    annotation = parameter.annotation
    tab = ' ' * spaces_count
    return (DEFINITION_TEMPLATE.format(name=parameter.name,
                                       annotation=annotation.to_string(
                                               namespace))
            + tab + RETURN_TEMPLATE.format(strategies=strategies_module_name,
                                           strategy=strategy_name))
