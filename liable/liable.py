#!/usr/bin/env python3
import collections
import operator
import os
from functools import partial
from itertools import (filterfalse,
                       chain)
from typing import (Any,
                    Optional,
                    Iterable,
                    Iterator,
                    Dict,
                    Tuple,
                    List)

import click
from pathspec import (PathSpec,
                      patterns)

from liable import (modules,
                    namespaces,
                    file_system,
                    catalog,
                    parameters,
                    strategies,
                    fixtures,
                    test_cases)
from liable.types import NamespaceType
from liable.utils import (is_python_module,
                          merge_mappings)
from liable.validators import (validate_paths,
                               validate_modules_paths)

__version__ = '0.0.3'


@click.group()
def main() -> None:
    return


@main.command(name='modules')
@click.option('--recursive', '-r',
              is_flag=True,
              help='Recursively walks through given directory.')
@click.option('--ignore-patterns-path', '-i',
              help='Path to file with patterns of paths names to ignore '
                   '(based on ".gitignore" syntax, '
                   'more at https://git-scm.com/docs/gitignore).')
@click.argument('paths',
                nargs=-1)
def search_modules(recursive: bool,
                   ignore_patterns_path: str,
                   paths: List[str]) -> None:
    """Searches Python modules in paths."""
    if not paths:
        err_msg = 'No paths specified.'
        raise click.BadParameter(err_msg)

    paths = list(map(os.path.abspath, paths))

    try:
        validate_paths(paths)
    except OSError as err:
        raise click.BadParameter(err) from err

    files_paths_seeker = partial(file_system.find_files,
                                 recursive=recursive)
    files_paths = chain.from_iterable(map(files_paths_seeker, paths))
    modules_paths = filter(is_python_module, files_paths)

    if ignore_patterns_path:
        with open(ignore_patterns_path) as ignore_patterns_file:
            path_spec = PathSpec.from_lines(patterns.GitWildMatchPattern,
                                            ignore_patterns_file)
        modules_paths = list(modules_paths)
        ignored_paths = list(path_spec.match_files(modules_paths))
        modules_paths = filterfalse(partial(operator.contains,
                                            ignored_paths),
                                    modules_paths)
    click.echo(' '.join(modules_paths))


utilities = {
    catalog.ModulePath(collections.__name__): collections,
    catalog.ContentPath(module=catalog.ModulePath(Any.__module__),
                        object='Any',
                        type=catalog.PathType.relative): Any,
    catalog.ContentPath(module=catalog.ModulePath(Optional.__module__),
                        object='Optional',
                        type=catalog.PathType.relative): Optional,
    catalog.ContentPath(module=catalog.ModulePath(Tuple.__module__),
                        object='Tuple',
                        type=catalog.PathType.relative): Tuple,
    catalog.ContentPath(module=catalog.ModulePath(Dict.__module__),
                        object='Dict',
                        type=catalog.PathType.relative): Dict,
}


@main.command(name='utilities')
@click.option('--target-directory', '-t',
              type=click.Path(exists=True),
              required=True,
              help='Target directory.')
@click.option('--spaces-count', '-s',
              type=click.IntRange(1),
              default=4,
              help='Number of spaces used for indentation.')
@click.option('--strategies-module-name',
              default='strategies',
              help='Strategies module name.')
@click.option('--fixtures-module-name',
              default='fixtures',
              help='Fixtures module name.')
@click.option('--tests-module-name',
              default='tests',
              help='Tests module name.')
@click.option('--overwrite',
              is_flag=True,
              help='Overwrites source file '
                   'if it\'s already exists.')
@click.argument('modules_paths',
                nargs=-1)
def generate_utilities(target_directory: Optional[str],
                       spaces_count: int,
                       strategies_module_name: str,
                       fixtures_module_name: str,
                       tests_module_name: str,
                       overwrite: bool,
                       modules_paths: List[str]) -> None:
    """Generates strategies & fixtures skeletons."""
    if not modules_paths:
        err_msg = 'No paths specified.'
        raise click.BadParameter(err_msg)

    modules_paths = list(map(os.path.abspath, modules_paths))

    try:
        validate_paths(modules_paths)
        validate_modules_paths(modules_paths)
    except OSError as err:
        raise click.BadParameter(err) from err

    modules_namespaces = list(modules_paths_to_namespaces(modules_paths))
    modules_functions = chain.from_iterable(map(namespaces.inner_functions,
                                                modules_namespaces))
    modules_namespace = merge_mappings(*modules_namespaces)
    modules_parameters = parameters.from_functions(modules_functions)
    built_ins = namespaces.built_ins()
    modules_namespace = merge_mappings(built_ins, modules_namespace)
    modules_parameters = parameters.combine(modules_parameters,
                                            namespace=modules_namespace)
    strategies_directory = os.path.join(target_directory,
                                        strategies_module_name)
    fixtures_directory = os.path.join(target_directory, fixtures_module_name)
    file_system.make_packages(strategies_directory)
    file_system.make_packages(fixtures_directory)
    fixtures_factory = partial(fixtures.from_parameters,
                               spaces_count=spaces_count,
                               tests_module_name=tests_module_name,
                               strategies_module_name=strategies_module_name)
    for module_path, module_parameters in modules_parameters.items():
        module_full_name = str(module_path)
        write_source(strategies.from_parameters(module_parameters,
                                                namespace=modules_namespace),
                     top_directory=strategies_directory,
                     module_full_name=module_full_name,
                     overwrite=overwrite)
        write_source(fixtures_factory(module_parameters,
                                      namespace=modules_namespace),
                     top_directory=fixtures_directory,
                     module_full_name=module_full_name,
                     overwrite=overwrite)
    init_module_path = os.path.join(strategies_directory,
                                    file_system.INIT_MODULE_FILE_NAME)
    # TODO: merge related or duplicated imports
    with open(init_module_path, mode='a') as init_module_file:
        init_module_file.write(strategies.init_module(modules_parameters))


@main.command(name='tests')
@click.option('--target-directory', '-t',
              type=click.Path(exists=True),
              required=True,
              help='Target directory.')
@click.option('--spaces-count', '-s',
              type=click.IntRange(1),
              default=4,
              help='Number of spaces used for indentation.')
@click.option('--overwrite',
              is_flag=True,
              help='Overwrites source file '
                   'if it\'s already exists.')
@click.argument('modules_paths',
                nargs=-1)
def generate_tests(target_directory: Optional[str],
                   spaces_count: int,
                   overwrite: bool,
                   modules_paths: List[str]) -> None:
    """Generates test cases skeletons."""
    if not modules_paths:
        err_msg = 'No paths specified.'
        raise click.BadParameter(err_msg)

    modules_paths = list(map(os.path.abspath, modules_paths))

    try:
        validate_paths(modules_paths)
        validate_modules_paths(modules_paths)
    except OSError as err:
        raise click.BadParameter(err) from err

    built_ins = namespaces.built_ins()
    test_cases_generator = partial(test_cases.from_functions,
                                   spaces_count=spaces_count)
    for path, namespace in zip(modules_paths,
                               modules_paths_to_namespaces(modules_paths)):
        module_functions = list(namespaces.inner_functions(namespace))
        if not module_functions:
            continue
        namespace = merge_mappings(built_ins, namespace)
        try:
            source = test_cases_generator(module_functions,
                                          namespace=namespace)
        except ImportError as err:
            raise click.BadParameter(err) from err
        else:
            path = test_cases.normalize_path(path)
            module_full_name = str(catalog.path_to_module_path(path))
            write_source(source,
                         top_directory=target_directory,
                         module_full_name=module_full_name,
                         overwrite=overwrite)


def modules_paths_to_namespaces(modules_paths: Iterable[str]
                                ) -> Iterator[NamespaceType]:
    add_utilities = partial(merge_mappings, utilities)
    modules_namespaces = map(namespaces.from_module,
                             map(modules.from_path, modules_paths))
    yield from map(add_utilities, modules_namespaces)


def write_source(source: str,
                 *,
                 top_directory: str,
                 module_full_name: str,
                 source_extension: str = file_system.SOURCE_EXTENSION,
                 overwrite: bool) -> None:
    *sub_directories, module_name = module_full_name.split(catalog.SEPARATOR)
    file_system.make_packages(top_directory, *sub_directories)
    module_directory = os.path.join(top_directory,
                                    *sub_directories)
    os.makedirs(module_directory,
                exist_ok=True)
    module_path = os.path.join(module_directory,
                               module_name + source_extension)
    mode = 'w' if overwrite else 'a'
    with open(module_path,
              mode=mode) as module_file:
        module_file.write(source)


if __name__ == '__main__':
    main()
