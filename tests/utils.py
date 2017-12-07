from typing import Any

from hypothesis import find
from hypothesis.searchstrategy import SearchStrategy


def example(strategy: SearchStrategy) -> Any:
    return find(specifier=strategy,
                condition=lambda x: True)
