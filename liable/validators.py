import os
from itertools import filterfalse
from typing import Iterable

from .utils import (join_strings,
                    wrap_with_quotes)


def validate_paths(paths: Iterable[str]) -> None:
    non_existent_paths = list(filterfalse(os.path.exists, paths))

    if not non_existent_paths:
        return

    non_existent_paths_str = join_strings(map(wrap_with_quotes,
                                              non_existent_paths))
    err_msg = ('Next paths not found on file system:\n'
               '{paths}.'
               .format(paths=non_existent_paths_str))
    raise FileNotFoundError(err_msg)
