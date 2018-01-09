import builtins
import inspect
import operator
from functools import partial
from itertools import chain
from types import ModuleType
from typing import (Any,
                    Iterable,
                    Iterator,
                    Dict,
                    Tuple)

from . import (catalog,
               modules,
               arboretum)
from .utils import (to_name,
                    merge_mappings)
from .validators import validate_modules

NamespaceType = Dict[catalog.ObjectPath, Any]


def from_module(module: ModuleType) -> NamespaceType:
    return merge_mappings(dependent_objects(module),
                          inner_objects(module))


def built_ins(module: ModuleType = builtins) -> NamespaceType:
    module_map = dict(vars(module))
    module_map['...'] = module_map.pop('Ellipsis')
    return {catalog.ObjectPath(module=None,
                               object=name,
                               type=catalog.PathType.inner): content
            for name, content in module_map.items()}


def dependent_objects(module: ModuleType) -> NamespaceType:
    if modules.is_built_in(module):
        return {}
    objects_paths = list(dependent_objects_paths(module))
    return dict(load_dependent_objects(objects_paths))


def dependent_objects_paths(module: ModuleType
                            ) -> Iterator[catalog.ObjectPath]:
    tree = arboretum.from_module(module)
    imports = filter(arboretum.is_import_statement, tree.body)
    module_path = module.__file__
    relative_import_to_absolute = arboretum.import_absolutizer(module_path)
    imports = map(relative_import_to_absolute, imports)
    yield from chain.from_iterable(map(arboretum.to_object_path, imports))


def load_dependent_objects(objects_paths: Iterable[catalog.ObjectPath]
                           ) -> Iterator[Tuple[catalog.ObjectPath, Any]]:
    dependencies_names = set(map(operator.attrgetter('module'), objects_paths))
    validate_modules(dependencies_names)
    dependencies = dict(zip(dependencies_names,
                            map(modules.from_name, dependencies_names)))
    objects_seeker = partial(modules.search,
                             modules=dependencies)
    yield from zip(objects_paths,
                   map(objects_seeker, objects_paths))


def inner_objects(module: ModuleType) -> NamespaceType:
    module_name = module.__name__
    return {catalog.ObjectPath(module=module_name,
                               object=object_name,
                               type=catalog.PathType.inner): content
            for object_name, content in vars(module).items()
            if modules.is_object_from_module(content,
                                             module=module)}


def search_name(object_: Any,
                *,
                namespace: NamespaceType) -> str:
    path = search_path(object_,
                       namespace=namespace)
    if path.type in catalog.non_absolute_paths:
        return path.object
    return str(path)


def search_path(object_: Any,
                *,
                namespace: NamespaceType) -> catalog.ObjectPath:
    is_relative = is_object_relative(object_,
                                     namespace=namespace)
    if is_relative:
        object_paths = search_relative_objects(object_,
                                               namespace=namespace)
    else:
        object_paths = chain.from_iterable(
                search_absolute_objects(object_,
                                        namespace=from_module(module),
                                        module_name=str(module_path))
                for module_path, module in namespace_modules(namespace))
    try:
        return next(object_paths)
    except StopIteration as err:
        raise LookupError('Object "{object}" not found in namespace.'
                          .format(object=to_name(object_))) from err


def is_object_relative(object_: Any,
                       *,
                       namespace: NamespaceType) -> bool:
    """
    Object called **relative** in namespace
    if it is defined in original module
    or imported using ``import from`` statement.

    Object called **absolute** in namespace
    if it is defined in module
    which imported in original one using ``import`` statement.
    """
    return object_ in namespace.values()


def search_relative_objects(object_: Any,
                            *,
                            namespace: NamespaceType) -> catalog.ObjectPath:
    for path, content in namespace.items():
        if content is object_:
            yield path


def search_absolute_objects(object_: Any,
                            *,
                            namespace: NamespaceType,
                            module_name: str) -> catalog.ObjectPath:
    for path, content in namespace.items():
        if content is object_:
            yield catalog.ObjectPath(module=module_name,
                                     object=path.object,
                                     type=catalog.PathType.absolute)


def namespace_modules(namespace: NamespaceType
                      ) -> Iterator[Tuple[str, ModuleType]]:
    for path, content in namespace.items():
        if inspect.ismodule(content):
            yield path, content
