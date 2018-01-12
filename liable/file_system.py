import os
from functools import partial
from typing import Iterator

from . import strings

INIT_MODULE_FILE_NAME = '__init__.py'


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
