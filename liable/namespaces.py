import builtins
import inspect
from functools import partial
from itertools import chain
from types import (FunctionType,
                   ModuleType)
from typing import (Any,
                    Iterable,
                    Iterator,
                    Tuple)

from . import (catalog,
               modules,
               arboretum)
from .catalog import ObjectPathType
from .types import NamespaceType
from .utils import (to_name,
                    merge_mappings)


def from_module(module: ModuleType) -> NamespaceType:
    return merge_mappings(dependent_objects(module),
                          inner_objects(module))


def built_ins(module: ModuleType = builtins) -> NamespaceType:
    raw_namespace = dict(vars(module))
    raw_namespace['...'] = raw_namespace.pop('Ellipsis')
    assert not any(inspect.ismodule(content)
                   for content in raw_namespace.values())
    return {catalog.guess_type(content)(module=catalog.BUILT_INS_MODULE_PATH,
                                        object=name,
                                        type=catalog.PathType.inner): content
            for name, content in raw_namespace.items()}


def dependent_objects(module: ModuleType) -> NamespaceType:
    if modules.is_built_in(module):
        return {}
    objects_paths = dependent_objects_paths(module)
    return dict(load_dependent_objects(objects_paths))


def dependent_objects_paths(module: ModuleType) -> Iterator[ObjectPathType]:
    tree = arboretum.from_module(module)
    imports = filter(arboretum.is_import_statement, tree.body)
    module_path = module.__file__
    relative_import_to_absolute = arboretum.import_absolutizer(module_path)
    imports = map(relative_import_to_absolute, imports)
    yield from chain.from_iterable(map(arboretum.to_object_path, imports))


def load_dependent_objects(objects_paths: Iterable[ObjectPathType]
                           ) -> Iterator[Tuple[ObjectPathType, Any]]:
    objects_paths = list(objects_paths)
    dependencies_paths = map(catalog.to_module_path, objects_paths)
    dependencies_paths = set(dependencies_paths)
    dependencies = dict(zip(dependencies_paths,
                            map(modules.from_module_path, dependencies_paths)))
    objects_seeker = partial(modules.search,
                             modules=dependencies)
    yield from zip(objects_paths,
                   map(objects_seeker, objects_paths))


def inner_objects(module: ModuleType) -> NamespaceType:
    module_full_name = module.__name__
    module_path = catalog.name_to_module_path(module_full_name)

    return {catalog.guess_type(content)(module=module_path,
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
    if path.type != catalog.PathType.absolute:
        return path.object
    module_path = path.module
    if module_path.type == catalog.PathType.relative:
        return module_path.object + catalog.SEPARATOR + path.object
    return str(path)


def search_path(object_: Any,
                *,
                namespace: NamespaceType) -> ObjectPathType:
    object_paths = search_paths(object_,
                                namespace=namespace)
    try:
        return next(object_paths)
    except StopIteration as err:
        raise LookupError('Object "{object}" not found in namespace.'
                          .format(object=to_name(object_))) from err


def search_paths(object_: Any,
                 *,
                 namespace: NamespaceType) -> Iterator[ObjectPathType]:
    is_relative = is_object_relative(object_,
                                     namespace=namespace)
    if is_relative:
        yield from search_relative_objects(object_,
                                           namespace=namespace)
    else:
        yield from search_absolute_paths(object_,
                                         namespace=namespace)


def search_absolute_paths(object_: Any,
                          *,
                          namespace: NamespaceType) -> Iterator[Any]:
    sub_modules_by_paths = dict(namespace_modules(namespace))
    sub_namespaces = list(map(from_module, sub_modules_by_paths.values()))
    yield from chain.from_iterable(
            search_absolute_objects(object_,
                                    namespace=namespace,
                                    module_path=module_path)
            for module_path, namespace in zip(sub_modules_by_paths.keys(),
                                              sub_namespaces))
    yield from chain.from_iterable(search_absolute_paths(object_,
                                                         namespace=namespace)
                                   for namespace in sub_namespaces)


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
                            namespace: NamespaceType) -> ObjectPathType:
    for path, content in namespace.items():
        if content is object_:
            yield path


def search_absolute_objects(object_: Any,
                            *,
                            namespace: NamespaceType,
                            module_path: catalog.ModulePath
                            ) -> ObjectPathType:
    for path, content in namespace.items():
        if content is object_:
            yield catalog.guess_type(content)(module=module_path,
                                              object=path.object,
                                              type=catalog.PathType.absolute)


def namespace_modules(namespace: NamespaceType
                      ) -> Iterator[Tuple[catalog.ModulePath, ModuleType]]:
    for path, content in namespace.items():
        if inspect.ismodule(content):
            err_msg = ('Module\'s path in namespace '
                       'should be instance of "{type}".'
                       .format(type=catalog.ModulePath.__qualname__))
            assert isinstance(path, catalog.ModulePath), err_msg
            yield path, content


def functions_by_path_type(namespace: NamespaceType,
                           *,
                           path_type: catalog.PathType
                           ) -> Iterator[FunctionType]:
    objects_by_path_type = (content
                            for path, content in namespace.items()
                            if path.type == path_type)
    yield from filter(inspect.isfunction, objects_by_path_type)


inner_functions = partial(functions_by_path_type,
                          path_type=catalog.PathType.inner)
