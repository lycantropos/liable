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
