import ast
import operator
import os
import pkgutil
from itertools import chain
from typing import (Union,
                    Callable,
                    Iterable,
                    Iterator,
                    Tuple)

from . import catalog

ImportType = Union[ast.Import, ast.ImportFrom]


def split_imports(statement: ImportType,
                  *,
                  sep: str = catalog.SEPARATOR) -> Iterator[Tuple[str, str]]:
    name = operator.attrgetter('name')
    aliases = statement.names
    objects_names = list(map(name, aliases))
    if isinstance(statement, ast.Import):
        def parse_sup_modules(object_name: str) -> Iterable:
            *result, _ = object_name.split(sep)
            yield from result

        sup_modules = chain.from_iterable(map(parse_sup_modules,
                                              objects_names))
        objects_names = list(chain(objects_names, sup_modules))
        yield from zip(objects_names, objects_names)
    else:
        if is_import_relative(statement):
            err_msg = ('Import statement should be absolute, '
                       'relative found.')
            raise ValueError(err_msg)

        package_name = statement.module

        def module_name(object_name: str) -> str:
            candidate = package_name + sep + object_name
            if is_module_name(candidate):
                return candidate
            return package_name

        yield from zip(objects_names, map(module_name, objects_names))


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


def from_source(source: str,
                *,
                file_name: str = '<unknown>',
                mode: str = 'exec') -> ast.AST:
    return compile(source, file_name, mode, ast.PyCF_ONLY_AST)


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
