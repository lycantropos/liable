import inspect
import os
from functools import partial
from itertools import (chain,
                       starmap)
from types import FunctionType
from typing import (Iterable,
                    Type)

from . import (namespaces,
               functions,
               catalog,
               annotator,
               strings)
from .utils import (fix_code,
                    merge_mappings)

TEST_CASE_PARAMETER_TEMPLATE = '{parameter}: {annotation}'
TEST_CASE_DEFINITION_TEMPLATE = 'def test_{function}({parameters}) -> None:\n'
RESULT_NAME = 'result'
FUNCTION_CALL_TEMPLATE = '{result} = {function}({arguments})\n\n'
RETURN_TYPE_CHECK_TEMPLATE = 'isinstance({result}, {return_type})'
NONE_RETURN_TYPE_CHECK_TEMPLATE = '{result} is None'
ASSERTION_TEMPLATE = 'assert {statement}\n'


def from_functions(module_functions: Iterable[FunctionType],
                   *,
                   built_ins: namespaces.NamespaceType,
                   namespace: namespaces.NamespaceType,
                   spaces_count: int) -> str:
    dependants_paths = functions.dependants_paths(module_functions,
                                                  built_ins=built_ins,
                                                  namespace=namespace,
                                                  generic_return_type=False)
    dependants_paths = catalog.modules_objects_paths(dependants_paths)
    imports = chain.from_iterable(starmap(catalog.to_imports,
                                          dependants_paths.values()))
    test_case_factory = partial(from_function,
                                spaces_count=spaces_count,
                                built_ins=built_ins,
                                namespace=namespace)
    tests_cases = map(test_case_factory, module_functions)
    code_blocks = chain(imports, tests_cases)
    return fix_code(''.join(code_blocks))


def from_function(function: FunctionType,
                  *,
                  built_ins: namespaces.NamespaceType,
                  namespace: namespaces.NamespaceType,
                  spaces_count: int) -> str:
    namespace = merge_mappings(built_ins, namespace)

    def to_name(annotation: Type) -> str:
        annotation = annotator.normalize(annotation)
        return annotation.to_string(namespace)

    signature = inspect.signature(function)
    function_parameters = signature.parameters.values()
    test_parameters_str = strings.join(
            TEST_CASE_PARAMETER_TEMPLATE.format(
                    parameter=parameter.name,
                    annotation=to_name(parameter.annotation)
            )
            for parameter in function_parameters)
    function_arguments_str = strings.join(
            functions.ARGUMENTS_TEMPLATES[parameter.kind].format(
                    parameter=parameter.name,
                    argument=parameter.name)
            for parameter in function_parameters)
    return_annotation = signature.return_annotation
    return_annotation_bases = annotator.to_bases(return_annotation)

    def to_statement(annotation_base: Type) -> str:
        if annotation_base is None:
            return NONE_RETURN_TYPE_CHECK_TEMPLATE
        else:
            return RETURN_TYPE_CHECK_TEMPLATE

    statements = sorted(set(map(to_statement, return_annotation_bases)))
    statement = strings.join_with_wrapping(statements,
                                           sep='\nor\n')
    assertion_template = ASSERTION_TEMPLATE.format(statement=statement)

    return_type = None
    defined_return_annotation_bases = list(filter(None,
                                                  return_annotation_bases))
    if defined_return_annotation_bases:
        if len(defined_return_annotation_bases) == 1:
            return_annotation_base, = defined_return_annotation_bases
            return_type = to_name(return_annotation_base)
        else:
            return_types = list(map(to_name,
                                    defined_return_annotation_bases))
            return_types_str = ', '.join(return_types)
            return_type = ('({return_types})'
                           .format(return_types=return_types_str))

    tab = ' ' * spaces_count
    test_case_template = (TEST_CASE_DEFINITION_TEMPLATE
                          + tab + FUNCTION_CALL_TEMPLATE
                          + tab + assertion_template)
    return test_case_template.format(function=function.__name__,
                                     parameters=test_parameters_str,
                                     result=RESULT_NAME,
                                     arguments=function_arguments_str,
                                     return_type=return_type)


def normalize_path(module_path: str) -> str:
    *sub_directories, module_file_name = module_path.split(os.sep)
    return os.path.join(*sub_directories, 'test_' + module_file_name)
