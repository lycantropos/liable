#!/usr/bin/env python3
import inspect
import operator
import os
from functools import partial
from itertools import (filterfalse,
                       chain)
from typing import (Iterable,
                    Iterator)

import click
from pathspec import (PathSpec,
                      patterns)

LIST_SEPARATOR = ', '


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
                   paths: str) -> None:
    """Searches Python modules in paths."""
    if not paths:
        err_msg = 'No paths specified.'
        raise click.BadParameter(err_msg)

    paths = list(map(os.path.abspath, paths))

    try:
        validate_paths(paths)
    except OSError as err:
        raise click.BadParameter(err) from err

    files_paths = chain.from_iterable(map(partial(find_files,
                                                  recursive=recursive),
                                          paths))
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

    for module_path in modules_paths:
        click.echo(module_path)


def validate_paths(paths: Iterable[str]) -> None:
    non_existent_paths = list(filterfalse(os.path.exists, paths))

    if not non_existent_paths:
        return

    def wrap_with_quotes(string: str) -> str:
        quote_character = '"'
        return quote_character + string + quote_character

    non_existent_paths_str = LIST_SEPARATOR.join(map(wrap_with_quotes,
                                                     non_existent_paths))
    err_msg = ('Next paths not found on file system: {paths}.'
               .format(paths=non_existent_paths_str))
    raise FileNotFoundError(err_msg)


is_python_module = inspect.getmodulename


def find_files(path: str,
               *,
               recursive: bool) -> Iterator[str]:
    if os.path.isdir(path):
        yield from filter(is_python_module,
                          directory_files(path,
                                          recursive=recursive))
    else:
        yield path


def files(path: str,
          *,
          recursive: bool) -> Iterator[str]:
    if os.path.isdir(path):
        yield from directory_files(path,
                                   recursive=recursive)
    else:
        yield path


def directory_files(path: str,
                    *,
                    recursive: bool) -> Iterator[str]:
    if recursive:
        for root, _, files_names in os.walk(path):
            yield from map(partial(os.path.join, root), files_names)
    yield from filter(os.path.isfile,
                      map(partial(os.path.join, path), os.listdir(path)))


if __name__ == '__main__':
    main()
