import builtins
import enum
import inspect
import operator
import os
from collections import defaultdict
from itertools import filterfalse
from typing import (Any,
                    Union,
                    Optional,
                    Type,
                    Iterable,
                    Iterator,
                    NamedTuple,
                    Dict,
                    Set)

from . import (file_system,
               strings)

SEPARATOR = '.'


class PathType(enum.Enum):
    inner = 'inner'
    absolute = 'absolute'
    relative = 'relative'


IMPORTS_TEMPLATES = {PathType.absolute: 'import {module}\n',
                     PathType.relative: 'from {module} import {objects}\n'}


class ModulePath(NamedTuple):
    module: Union[str, 'ModulePath']
    object: Optional[str] = None
    type: PathType = PathType.absolute

    def __str__(self):
        module_full_name = str(self.module)
        if self.object is None:
            return module_full_name
        else:
            return module_full_name + SEPARATOR + self.object


class ContentPath(NamedTuple):
    module: ModulePath
    object: str
    type: PathType

    def __str__(self):
        module_full_name = str(self.module)
        if is_built_in(self):
            return self.object
        else:
            return module_full_name + SEPARATOR + self.object


BUILT_INS_MODULE_PATH = ModulePath(builtins.__name__)

ObjectPathType = Union[ModulePath, ContentPath]


def is_absolute(object_path: ObjectPathType) -> bool:
    return object_path.type == PathType.absolute


def is_built_in(object_path: ObjectPathType) -> bool:
    return object_path.module == BUILT_INS_MODULE_PATH


def path_to_module_path(path: str) -> ModulePath:
    package_name, file_name = os.path.split(path)
    module_name = to_module_name(file_name)
    if not package_name:
        return ModulePath(module_name)
    if module_name is None:
        return path_to_module_path(package_name)
    return ModulePath(module=path_to_module_path(package_name),
                      object=module_name,
                      type=PathType.absolute)


def name_to_module_path(full_name: str) -> ModulePath:
    try:
        package_name, full_name = full_name.rsplit(SEPARATOR, 1)
    except ValueError:
        return ModulePath(full_name)
    else:
        return ModulePath(module=name_to_module_path(package_name),
                          object=full_name,
                          type=PathType.absolute)


def to_module_name(file_name: str) -> Optional[str]:
    module_name = inspect.getmodulename(file_name)
    if module_name is None:
        return file_name
    if module_name == file_system.INIT_MODULE_NAME:
        return None
    return module_name


def to_imports(*module_objects_paths: ObjectPathType) -> Iterator[str]:
    modules_paths = set(map(operator.attrgetter('module'),
                            module_objects_paths))
    try:
        module_path, = modules_paths
    except ValueError as err:
        if modules_paths:
            modules_names_str = strings.join('"' + name + '"'
                                             for name in modules_paths)
            err_msg = ('Found modules paths for different modules: '
                       '{modules}.'
                       .format(modules=modules_names_str))
        else:
            err_msg = 'No modules paths found.'
        raise ValueError(err_msg) from err

    if is_built_in(module_objects_paths[0]):
        return

    non_absolute_paths = list(filterfalse(is_absolute, module_objects_paths))
    if non_absolute_paths:
        objects_names = sorted(map(operator.attrgetter('object'),
                                   non_absolute_paths))
        objects_names_str = strings.join_with_wrapping(objects_names)
        yield (IMPORTS_TEMPLATES[PathType.relative]
               .format(module=module_path,
                       objects=objects_names_str))
    absolute_path = next(filter(is_absolute, module_objects_paths), None)
    if absolute_path is not None:
        yield (IMPORTS_TEMPLATES[PathType.absolute]
               .format(module=module_path))


def modules_objects_paths(objects_paths: Iterable[ObjectPathType]
                          ) -> Dict[str, Set[ObjectPathType]]:
    result = defaultdict(list)
    for object_path in objects_paths:
        module_path = to_module_path(object_path)
        if module_path.type == PathType.relative:
            result[module_path.module].append(module_path)
        else:
            result[module_path].append(object_path)
    return dict(zip(result.keys(), map(set, result.values())))


def to_module_path(object_path: ObjectPathType) -> ModulePath:
    if isinstance(object_path, ModulePath):
        return object_path
    return object_path.module


def guess_type(object_: Any) -> Type[ObjectPathType]:
    if inspect.ismodule(object_):
        return ModulePath
    return ContentPath
