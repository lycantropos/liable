import os
from functools import partial
from typing import Iterator


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
    for package_path in iterative_join(directory, *sub_directories):
        make_init_module(package_path)


def make_init_module(directory: str) -> None:
    path = os.path.join(directory, '__init__.py')
    open(path, mode='a').close()


def iterative_join(directory: str,
                   *sub_directories: str) -> Iterator[str]:
    package_path = directory
    yield package_path
    for sub_dir in sub_directories:
        package_path = os.path.join(package_path, sub_dir)
        yield package_path
