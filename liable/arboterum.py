import ast
import operator
import pkgutil
from itertools import chain
from typing import (Union,
                    Iterable,
                    Iterator,
                    Tuple)

from . import modules

ImportType = Union[ast.Import, ast.ImportFrom]


def split_imports(statement: ImportType,
                  *,
                  sep: str = modules.SEPARATOR) -> Iterator[Tuple[str, str]]:
    name = operator.attrgetter('name')
    aliases = statement.names
    objects_names = list(map(name, aliases))
    if isinstance(statement, ast.Import):
        def parse_sup_modules(object_name: str) -> Iterable:
            *result, _ = object_name.split(sep)
            yield from result

        sup_modules = chain.from_iterable(map(parse_sup_modules,
                                              objects_names))
        objects_names = list(chain(objects_names,
                                   sup_modules))
        yield from zip(objects_names, objects_names)
    else:
        package = statement.module

        def module_name(object_name: str) -> str:
            candidate = package + sep + object_name
            if is_module_name(candidate):
                return candidate
            return package

        yield from zip(objects_names, map(module_name, objects_names))


def to_tree(source: str,
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
