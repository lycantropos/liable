import ast
import inspect
import operator
import os
from functools import partial
from itertools import (repeat,
                       starmap,
                       filterfalse)
from types import ModuleType
from typing import (Union,
                    Callable,
                    Iterator,
                    Tuple)

from . import (catalog,
               modules,
               file_system)
from .catalog import ObjectPathType

ImportType = Union[ast.Import, ast.ImportFrom]

ALL_OBJECTS_WILDCARD = '*'

DYNAMIC_MODULES_EXTENSIONS = ('.so', '.dylib', '.dll')


def from_source(source: str,
                *,
                file_name: str = '<unknown>',
                mode: str = 'exec') -> ast.AST:
    return compile(source, file_name, mode, ast.PyCF_ONLY_AST)


def from_module(module: ModuleType) -> ast.AST:
    source = to_source(module)
    return from_source(source,
                       file_name=module.__file__)


def to_source(module: ModuleType,
              *,
              permissible_extensions: Tuple[str] = DYNAMIC_MODULES_EXTENSIONS
              ) -> str:
    module_path = module.__file__
    if os.stat(module_path).st_size == 0:
        return ''
    try:
        return inspect.getsource(module)
    except OSError as err:
        if module_path.endswith(permissible_extensions):
            return ''
        raise err


def to_object_path(statement: ImportType,
                   *,
                   all_objects_wildcard: str = ALL_OBJECTS_WILDCARD
                   ) -> Iterator[ObjectPathType]:
    name = operator.attrgetter('name')
    names = list(map(name, statement.names))
    objects_are_relative = isinstance(statement, ast.ImportFrom)
    if objects_are_relative:
        if is_import_relative(statement):
            err_msg = ('Import statement should be absolute, '
                       'relative found.')
            raise ValueError(err_msg)

        objects_names = names[:]

        module_full_name = statement.module
        module_path = catalog.name_to_module_path(module_full_name)
        module = modules.from_module_path(module_path)

        def is_module(object_name: str) -> bool:
            content = getattr(module, object_name)
            return inspect.ismodule(content)

        if all_objects_wildcard in objects_names:
            objects_names.remove(all_objects_wildcard)
            try:
                imported_objects_names = module.__all__
            except AttributeError:
                imported_objects_names = vars(module).keys()
            objects_names.extend(imported_objects_names)

        modules_paths = repeat(module_path)
        sub_modules_names = filter(is_module, objects_names)
        module_path_factory = partial(catalog.ModulePath,
                                      type=catalog.PathType.relative)
        yield from starmap(module_path_factory,
                           zip(modules_paths, sub_modules_names))

        contents_names = filterfalse(is_module, objects_names)
        content_path_factory = partial(catalog.ContentPath,
                                       type=catalog.PathType.relative)
        yield from starmap(content_path_factory,
                           zip(modules_paths, contents_names))
    else:
        # all names are modules names
        yield from map(catalog.name_to_module_path, names)


def import_absolutizer(path: str
                       ) -> Callable[[ast.ImportFrom], ast.ImportFrom]:
    """Returns operator which makes ``ast.ImportFrom`` statements absolute."""

    def to_absolute(statement: ImportType) -> ImportType:
        if isinstance(statement, ast.Import):
            return statement
        module_full_name = to_module_full_name(statement)
        return ast.ImportFrom(module=module_full_name,
                              level=0,
                              names=statement.names,
                              lineno=statement.lineno,
                              col_offset=statement.col_offset)

    directory_path = os.path.normpath(os.path.dirname(path))
    directory_relative_path = file_system.to_relative(directory_path)

    def to_module_full_name(statement: ast.ImportFrom) -> str:
        result = statement.module
        if is_import_relative(statement):
            jumps = (os.pardir + os.sep) * (statement.level - 1)
            path = os.path.join(directory_relative_path, jumps, result or '')
            path = os.path.normpath(path)
            result = str(catalog.path_to_module_path(path))
        return result

    return to_absolute


def is_import_statement(node: ast.AST) -> bool:
    return isinstance(node, (ast.Import, ast.ImportFrom))


def is_import_relative(statement: ast.ImportFrom) -> bool:
    return statement.level > 0
