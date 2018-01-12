import os
import sys
from functools import partial
from importlib._bootstrap_external import SOURCE_SUFFIXES
from typing import (Iterable,
                    Iterator)

from . import strings

SOURCE_EXTENSION = SOURCE_SUFFIXES[0]
INIT_MODULE_FILE_NAME = '__init__' + SOURCE_EXTENSION


def find_files(path: str,
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
    else:
        yield from filter(os.path.isfile,
                          map(partial(os.path.join, path), os.listdir(path)))


def make_packages(directory: str,
                  *sub_directories: str) -> None:
    test_cases_directory = os.path.join(directory, *sub_directories)
    os.makedirs(test_cases_directory,
                exist_ok=True)
    for package_path in strings.iterative_join(directory, *sub_directories,
                                               sep=os.sep):
        make_init_module(package_path)


def make_init_module(directory: str,
                     file_name: str = INIT_MODULE_FILE_NAME) -> None:
    path = os.path.join(directory, file_name)
    open(path, mode='a').close()


def to_relative(path: str,
                *,
                system_paths: Iterable[str] = sys.path) -> str:
    try:
        root_path = max((system_path
                         for system_path in system_paths
                         if path.startswith(system_path)),
                        key=len)
    except ValueError as err:
        err_msg = ('Invalid module path: "{path}". '
                   'No root path found in `Python` system paths.'
                   .format(path=path))
        raise ModuleNotFoundError(err_msg) from err
    return os.path.normpath(os.path.relpath(path, root_path))
