import inspect
from functools import partial
from itertools import chain
from typing import Iterable

import pytest

from . import (namespaces,
               catalog,
               strategies)
from .utils import fix_code

TEMPLATE = ('@pytest.fixture(scope=\'function\')\n'
            'def {name}() -> {annotation}:\n'
            '    return strategies.{strategy}.example()\n')


def from_parameters(parameters: Iterable[inspect.Parameter],
                    *,
                    namespace: namespaces.NamespaceType) -> str:
    parameters = list(parameters)
    annotations = (parameter.annotation.origin
                   for parameter in parameters)
    object_path_seeker = partial(namespaces.search_path,
                                 namespace=namespace)
    annotations_paths = map(object_path_seeker, annotations)
    additional_objects_paths = [
        catalog.ObjectPath(module=pytest.__name__,
                           object=None,
                           type=catalog.PathType.absolute),
        catalog.ObjectPath(module='tests',
                           object='strategies',
                           type=catalog.PathType.relative)
    ]
    dependant_objects_paths = chain(additional_objects_paths,
                                    annotations_paths)
    imports = chain.from_iterable(map(catalog.to_imports,
                                      dependant_objects_paths))
    fixtures = [from_parameter(parameter,
                               namespace=namespace)
                for parameter in parameters]
    code_blocks = chain(imports,
                        fixtures)
    return fix_code(''.join(code_blocks))


def from_parameter(parameter: inspect.Parameter,
                   *,
                   namespace: namespaces.NamespaceType) -> str:
    name = parameter.name
    strategy_name = strategies.to_strategy_name(name)
    annotation = parameter.annotation
    return TEMPLATE.format(name=name,
                           annotation=annotation.to_string(namespace),
                           strategy=strategy_name)
