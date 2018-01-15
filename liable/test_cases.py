import inspect
import os
from functools import partial
from itertools import (chain,
                       starmap)
from types import FunctionType
from typing import (Iterable,
                    Type)

from . import (functions,
               catalog,
               namespaces,
               strings,
               file_system)
from .types import NamespaceType
from .utils import fix_code

PARAMETER_TEMPLATE = '{parameter}: {annotation}'
DEFINITION_TEMPLATE = 'def test_{function}({parameters}) -> None:\n'
RESULT_NAME = 'result'
FUNCTION_CALL_TEMPLATE = '{result} = {function}({arguments})\n\n'
RETURN_TYPE_CHECK_TEMPLATE = 'isinstance({result}, {return_type})'
NONE_RETURN_TYPE_CHECK_TEMPLATE = '{result} is None'
ASSERTION_TEMPLATE = 'assert {statement}\n'


def from_functions(module_functions: Iterable[FunctionType],
                   *,
                   namespace: NamespaceType,
                   spaces_count: int) -> str:
    module_functions = list(module_functions)
    dependants_paths = functions.dependants_paths(module_functions,
                                                  namespace=namespace)
    dependants_paths = catalog.modules_objects_paths(dependants_paths)
    imports = chain.from_iterable(starmap(catalog.to_imports,
                                          dependants_paths.values()))
    test_case_factory = partial(from_function,
                                spaces_count=spaces_count,
                                namespace=namespace)
    test_cases = map(test_case_factory, module_functions)
    code_blocks = chain(imports, test_cases)
    return fix_code(''.join(code_blocks))


def from_function(function: FunctionType,
                  *,
                  namespace: NamespaceType,
                  spaces_count: int) -> str:
    signature = functions.signature(function)
    parameters = signature.parameters
    parameters_str = strings.join(
        PARAMETER_TEMPLATE.format(
            parameter=parameter.name,
            annotation=parameter.annotation.to_string(namespace))
        for parameter in parameters)
    try:
        parameter, = parameters
    except ValueError:
        arguments_str = strings.join(
            functions.ARGUMENTS_TEMPLATES[parameter.kind].format(
                parameter=parameter.name,
                argument=parameter.name)
            for parameter in parameters)
    else:
        kind = parameter.kind
        if kind == inspect._POSITIONAL_OR_KEYWORD:
            kind = inspect._POSITIONAL_ONLY
        arguments_str = (functions.ARGUMENTS_TEMPLATES[kind]
                         .format(parameter=parameter.name,
                                 argument=parameter.name))
    return_type = signature.return_type
    return_type_bases = return_type.bases

    def to_statement(annotation_base: Type) -> str:
        if annotation_base is None:
            return NONE_RETURN_TYPE_CHECK_TEMPLATE
        else:
            return RETURN_TYPE_CHECK_TEMPLATE

    statements = sorted(set(map(to_statement, return_type_bases)))
    statement = strings.join_with_wrapping(statements,
                                           sep='\nor\n')
    assertion_template = ASSERTION_TEMPLATE.format(statement=statement)

    return_type_str = None
    defined_return_types_bases = list(filter(None, return_type_bases))
    name_seeker = partial(namespaces.search_name,
                          namespace=namespace)
    if defined_return_types_bases:
        if len(defined_return_types_bases) == 1:
            return_type_base, = defined_return_types_bases
            return_type_str = name_seeker(return_type_base)
        else:
            return_types = list(map(name_seeker,
                                    defined_return_types_bases))
            return_types_str = ', '.join(return_types)
            return_type_str = ('({return_types})'
                               .format(return_types=return_types_str))

    tab = ' ' * spaces_count
    template = (DEFINITION_TEMPLATE
                + tab + FUNCTION_CALL_TEMPLATE
                + tab + assertion_template)
    return template.format(function=function.__name__,
                           parameters=parameters_str,
                           result=RESULT_NAME,
                           arguments=arguments_str,
                           return_type=return_type_str)


def normalize_path(module_path: str,
                   *,
                   source_extension: str = file_system.SOURCE_EXTENSION
                   ) -> str:
    module_path = file_system.to_relative(module_path)
    module_full_name = catalog.path_to_module_path(module_path)
    *sup_modules, module_name = str(module_full_name).split(catalog.SEPARATOR)
    module_file_name = 'test_' + module_name + source_extension
    return os.path.join(*sup_modules, module_file_name)
