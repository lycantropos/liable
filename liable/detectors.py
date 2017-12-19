from .utils import parse_module_name


def is_python_module(path: str) -> bool:
    return parse_module_name(path) is not None
