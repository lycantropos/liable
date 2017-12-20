import inspect
from itertools import chain
from types import ModuleType
from typing import (Any,
                    Iterator,
                    Dict,
                    Tuple)

from . import modulation
from .utils import to_name

NamespaceType = Dict[str, Any]


def search(object_: Any,
           *,
           namespace: NamespaceType) -> str:
    if object_ in namespace.values():
        object_paths = search_objects(object_,
                                      namespace=namespace)
    else:
        object_paths = chain.from_iterable(
                search_objects(object_,
                               namespace=vars(module),
                               module_name=module_name)
                for module_name, module in namespace_modules(namespace))
    try:
        return next(object_paths)
    except StopIteration as err:
        raise LookupError('Object "{object}" not found in namespace.'
                          .format(object=to_name(object_))) from err


def search_objects(object_: Any,
                   *,
                   namespace: NamespaceType,
                   module_name: str = '') -> str:
    for name, content in namespace.items():
        if content is object_:
            yield modulation.SEPARATOR.join(filter(None, [module_name, name]))


def namespace_modules(namespace: NamespaceType
                      ) -> Iterator[Tuple[str, ModuleType]]:
    for name, content in namespace.items():
        if inspect.ismodule(content):
            yield name, content
