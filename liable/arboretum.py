import ast
import inspect
import operator
import os
import pkgutil
from itertools import (chain,
                       repeat,
                       starmap)
from types import ModuleType
from typing import (Union,
                    Callable,
                    Iterable,
                    Iterator)

from . import catalog

ImportType = Union[ast.Import, ast.ImportFrom]


def from_source(source: str,
                *,
                file_name: str = '<unknown>',
                mode: str = 'exec') -> ast.AST:
    return compile(source, file_name, mode, ast.PyCF_ONLY_AST)


def from_module(module: ModuleType) -> ast.AST:
    source = inspect.getsource(module)
    return from_source(source,
                       file_name=module.__file__)


def split_import(statement: ImportType,
                 *,
                 sep: str = catalog.SEPARATOR
                 ) -> Iterator[catalog.ObjectPath]:
    name = operator.attrgetter('name')
    names = list(map(name, statement.names))
    if isinstance(statement, ast.Import):
        # all names are modules names
        objects_names = repeat(None)

        def sup_modules(module_name: str) -> Iterable[str]:
            *result, _ = module_name.split(sep)
            yield from result

        sup_modules = chain.from_iterable(map(sup_modules,
                                              names))
        modules_names = chain(names, sup_modules)
    else:
        if is_import_relative(statement):
            err_msg = ('Import statement should be absolute, '
                       'relative found.')
            raise ValueError(err_msg)

        objects_names = names
        modules_names = repeat(statement.module)
    yield from starmap(catalog.ObjectPath, zip(modules_names, objects_names))


def import_absolutizer(module_path: str
                       ) -> Callable[[ast.ImportFrom], ast.ImportFrom]:
    """Returns operator which makes ``ast.ImportFrom`` statements absolute."""
    module_directory_path = os.path.dirname(module_path)
    module_directory_relative_path = catalog.to_relative(module_directory_path)

    def to_absolute(statement: ImportType) -> ImportType:
        if isinstance(statement, ast.Import):
            return statement
        module_name = to_module_name(statement)
        return ast.ImportFrom(module=module_name,
                              level=0,
                              names=statement.names,
                              lineno=statement.lineno,
                              col_offset=statement.col_offset)

    def to_module_name(statement: ast.ImportFrom) -> str:
        module = statement.module
        if is_import_relative(statement):
            jumps = (os.pardir + os.sep) * (statement.level - 1)
            module_path = os.path.join(module_directory_relative_path,
                                       jumps,
                                       module or '')
            module_path = os.path.normpath(module_path)
            module = catalog.to_import(module_path)
        return module

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
