import ast
import inspect
import operator
import os
import pkgutil
from functools import partial
from itertools import (chain,
                       repeat,
                       starmap)
from types import ModuleType
from typing import (Union,
                    Callable,
                    Iterable,
                    Iterator,
                    Tuple)

from liable import strings

from . import (catalog,
               modules)

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
                   sep: str = catalog.SEPARATOR,
                   all_objects_wildcard: str = ALL_OBJECTS_WILDCARD
                   ) -> Iterator[catalog.ObjectPath]:
    name = operator.attrgetter('name')
    names = list(map(name, statement.names))
    objects_are_relative = isinstance(statement, ast.ImportFrom)

    if objects_are_relative:
        if is_import_relative(statement):
            err_msg = ('Import statement should be absolute, '
                       'relative found.')
            raise ValueError(err_msg)

        objects_names = names

        module_name = statement.module

        if all_objects_wildcard in objects_names:
            module = modules.from_name(module_name)
            objects_names.remove(all_objects_wildcard)
            objects_names.extend(module.__all__)

        modules_names = repeat(module_name)
    else:
        # all names are modules names
        objects_names = repeat(None)

        def sup_modules(module_name: str) -> Iterable[str]:
            *result, _ = module_name.split(sep)
            yield from strings.iterative_join(*result,
                                              sep=sep)

        sup_modules = chain.from_iterable(map(sup_modules,
                                              names))
        modules_names = chain(names, sup_modules)

    path_type = (catalog.PathType.relative
                 if objects_are_relative
                 else catalog.PathType.absolute)
    object_path_factory = partial(catalog.ObjectPath,
                                  type=path_type)
    yield from starmap(object_path_factory, zip(modules_names, objects_names))


def import_absolutizer(module_path: str
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

    module_directory_path = os.path.dirname(module_path)
    module_directory_relative_path = catalog.to_relative(module_directory_path)

    def to_module_full_name(statement: ast.ImportFrom) -> str:
        result = statement.module
        if is_import_relative(statement):
            jumps = (os.pardir + os.sep) * (statement.level - 1)
            module_path = os.path.join(module_directory_relative_path,
                                       jumps,
                                       result or '')
            module_path = os.path.normpath(module_path)
            result = catalog.to_module_full_name(module_path)
        return result

    return to_absolute


def is_module_name(name: str) -> bool:
    try:
        loader = pkgutil.get_loader(name)
    except ImportError:
        return False
    else:
        return loader is not None


def is_import_statement(node: ast.AST) -> bool:
    return isinstance(node, (ast.Import, ast.ImportFrom))


def is_import_relative(statement: ast.ImportFrom) -> bool:
    return statement.level > 0
