import ast
import astroid
import os
import typing
from typing import List, Dict, Any, Optional, Union
import black
import argparse
import coverage
import asyncio
import importlib
import inspect
from pathlib import Path

class EnhancedTestScenarioGenerator:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.cov = coverage.Coverage()
        self.imports = set()  # Track required imports
        self.module_imports = {}  # Track module-specific imports

    def analyze_repository(self) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Analyze the entire repository and generate test scenarios for each function and method.
        """
        test_scenarios = {}
        
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.repo_path)
                    module_name = relative_path.replace('/', '.').replace('.py', '')
                    
                    try:
                        with open(file_path, "r") as f:
                            tree = astroid.parse(f.read())
                        
                        # Store module path for import generation
                        self.module_imports[module_name] = relative_path
                        test_scenarios[relative_path] = self.analyze_file(tree, module_name)
                    except Exception as e:
                        print(f"Warning: Could not analyze {file_path}: {str(e)}")
        
        return test_scenarios

    def analyze_file(self, tree: astroid.Module, module_name: str) -> Dict[str, List[Dict]]:
        """
        Analyze a single file and generate test scenarios for each function and method.
        """
        file_scenarios = {}
        
        for node in tree.body:
            if isinstance(node, (astroid.FunctionDef, astroid.AsyncFunctionDef)):
                file_scenarios[node.name] = self.generate_test_scenarios(node, is_method=False, module_name=module_name)
            elif isinstance(node, astroid.ClassDef):
                for method in node.mymethods():
                    method_name = f"{node.name}.{method.name}"
                    file_scenarios[method_name] = self.generate_test_scenarios(
                        method, 
                        is_method=True,
                        module_name=module_name,
                        class_name=node.name
                    )
        
        return file_scenarios

    def generate_test_scenarios(self, node: Union[astroid.FunctionDef, astroid.AsyncFunctionDef], 
                              is_method: bool, module_name: str, class_name: str = None) -> List[Dict]:
        """
        Generate test scenarios for a given function or method.
        """
        scenarios = []
        
        # Add basic imports
        self.imports.add('import pytest')
        if isinstance(node, astroid.AsyncFunctionDef):
            self.imports.add('import asyncio')
        
        # Add module import
        module_path = self.module_imports[module_name]
        import_name = module_path.replace('/', '.').replace('.py', '')
        if class_name:
            self.imports.add(f'from {import_name} import {class_name}')
        else:
            self.imports.add(f'from {import_name} import {node.name}')

        # Analyze parameters
        for arg in node.args.args[1:] if is_method else node.args.args:
            arg_name = arg.name
            arg_type = self.infer_type(arg)
            scenarios.append(self.create_parameter_test(
                function_name=node.name,
                arg_name=arg_name,
                arg_type=arg_type,
                is_async=isinstance(node, astroid.AsyncFunctionDef),
                is_method=is_method,
                class_name=class_name
            ))
            
            # Generate edge case tests
            scenarios.extend(self.generate_edge_case_tests(
                function_name=node.name,
                arg_name=arg_name,
                arg_type=arg_type,
                is_async=isinstance(node, astroid.AsyncFunctionDef),
                is_method=is_method,
                class_name=class_name
            ))
        
        # Analyze function body for potential scenarios
        scenarios.extend(self.analyze_function_body(
            node=node,
            is_method=is_method,
            class_name=class_name
        ))
        
        return scenarios

    def create_parameter_test(self, function_name: str, arg_name: str, 
                            arg_type: Optional[type], is_async: bool = False,
                            is_method: bool = False, class_name: str = None) -> Dict:
        """
        Create a parameter test scenario with appropriate test values.
        """
        test_value = self.generate_sample_value(arg_type)
        
        setup_code = ""
        if is_method and class_name:
            setup_code = f"    obj = {class_name}()\n"
            function_call = f"obj.{function_name}"
        else:
            function_call = function_name

        async_prefix = "async " if is_async else ""
        await_prefix = "await " if is_async else ""
        
        test_code = f"""
{async_prefix}def test_{function_name}_with_valid_{arg_name}():
{setup_code}    result = {await_prefix}{function_call}({arg_name}={repr(test_value)})
    assert result is not None
"""
        return {
            "type": "parameter_test",
            "name": f"test_{function_name}_with_valid_{arg_name}",
            "description": f"Test {function_name} with valid {arg_name}",
            "input": {arg_name: test_value},
            "test_code": black.format_str(test_code, mode=black.FileMode())
        }

    def generate_sample_value(self, arg_type: Optional[type]) -> Any:
        """
        Generate a sample value for a given type.
        """
        if arg_type == str:
            return "sample_string"
        elif arg_type == int:
            return 42
        elif arg_type == float:
            return 3.14
        elif arg_type == bool:
            return True
        elif arg_type == list:
            return [1, 2, 3]
        elif arg_type == dict:
            return {"key": "value"}
        elif arg_type == set:
            return {1, 2, 3}
        elif arg_type == tuple:
            return (1, 2, 3)
        return None

    def generate_edge_case_tests(self, function_name: str, arg_name: str, 
                               arg_type: Optional[type], is_async: bool = False,
                               is_method: bool = False, class_name: str = None) -> List[Dict]:
        """
        Generate edge case tests for different parameter types.
        """
        edge_cases = []
        setup_code = ""
        if is_method and class_name:
            setup_code = f"    obj = {class_name}()\n"
            function_call = f"obj.{function_name}"
        else:
            function_call = function_name

        async_prefix = "async " if is_async else ""
        await_prefix = "await " if is_async else ""

        # Define edge cases for different types
        type_edge_cases = {
            str: [
                ("empty", ""),
                ("very_long", "a" * 1000),
                ("special_chars", "!@#$%^&*()"),
                ("numeric", "12345"),
                ("whitespace", "   "),
            ],
            int: [
                ("zero", 0),
                ("negative", -1),
                ("large", 1000000),
                ("min_int", -2147483648),
                ("max_int", 2147483647),
            ],
            float: [
                ("zero", 0.0),
                ("negative", -1.0),
                ("very_small", 1e-10),
                ("very_large", 1e10),
                ("infinity", float('inf')),
            ],
            list: [
                ("empty", []),
                ("single", [1]),
                ("large", list(range(100))),
                ("nested", [[1, 2], [3, 4]]),
            ],
            dict: [
                ("empty", {}),
                ("single", {"key": "value"}),
                ("nested", {"outer": {"inner": "value"}}),
            ],
            set: [
                ("empty", set()),
                ("single", {1}),
                ("multiple", {1, 2, 3}),
            ],
            bool: [
                ("true", True),
                ("false", False),
            ],
        }

        if arg_type in type_edge_cases:
            for case_name, value in type_edge_cases[arg_type]:
                test_code = f"""
{async_prefix}def test_{function_name}_with_{case_name}_{arg_name}():
{setup_code}    result = {await_prefix}{function_call}({arg_name}={repr(value)})
    assert result is not None
"""
                edge_cases.append({
                    "type": "edge_case",
                    "name": f"test_{function_name}_with_{case_name}_{arg_name}",
                    "description": f"Test {function_name} with {case_name} {arg_name}",
                    "input": {arg_name: value},
                    "test_code": black.format_str(test_code, mode=black.FileMode())
                })

        return edge_cases

    def analyze_function_body(self, node: Union[astroid.FunctionDef, astroid.AsyncFunctionDef],
                            is_method: bool = False, class_name: str = None) -> List[Dict]:
        """
        Analyze the function body for potential test scenarios.
        """
        scenarios = []
        setup_code = ""
        if is_method and class_name:
            setup_code = f"    obj = {class_name}()\n"
            function_call = f"obj.{node.name}"
        else:
            function_call = node.name

        for child in node.body:
            if isinstance(child, astroid.If):
                scenarios.append(self.analyze_conditional(
                    node.name, child, setup_code, function_call,
                    is_async=isinstance(node, astroid.AsyncFunctionDef)
                ))
            elif isinstance(child, astroid.TryExcept):
                scenarios.append(self.analyze_exception_handling(
                    node.name, child, setup_code, function_call,
                    is_async=isinstance(node, astroid.AsyncFunctionDef)
                ))

        return scenarios

    def analyze_conditional(self, function_name: str, node: astroid.If, 
                          setup_code: str, function_call: str, is_async: bool = False) -> Dict:
        """
        Analyze conditional statements and create test scenarios.
        """
        condition = node.test.as_string()
        async_prefix = "async " if is_async else ""
        
        test_code = f"""
{async_prefix}def test_{function_name}_condition_{condition.replace('.', '_').replace(' ', '_')}():
{setup_code}    # Test the condition: {condition}
    try:
        {function_call}()
    except Exception as e:
        pytest.fail(f"Unexpected error: {{e}}")
"""
        return {
            "type": "conditional_test",
            "name": f"test_{function_name}_condition_{condition}",
            "description": f"Test conditional branch: {condition}",
            "test_code": black.format_str(test_code, mode=black.FileMode())
        }

    def analyze_exception_handling(self, function_name: str, node: astroid.TryExcept,
                                 setup_code: str, function_call: str, is_async: bool = False) -> Dict:
        """
        Analyze exception handling blocks and create test scenarios.
        """
        exceptions = [handler.type.as_string() for handler in node.handlers if handler.type]
        exception_list = ", ".join(exceptions)
        async_prefix = "async " if is_async else ""
        
        test_code = f"""
{async_prefix}def test_{function_name}_exceptions():
{setup_code}    with pytest.raises(({exception_list})):
        {function_call}()
"""
        return {
            "type": "exception_test",
            "name": f"test_{function_name}_exceptions",
            "description": f"Test exception handling for: {exception_list}",
            "test_code": black.format_str(test_code, mode=black.FileMode())
        }

def main():
    parser = argparse.ArgumentParser(description="Generate test scenarios for a Python repository")
    parser.add_argument("repo_path", help="Path to the repository")
    parser.add_argument("--output", help="Output file for generated tests", default="generated_tests.py")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    generator = EnhancedTestScenarioGenerator(args.repo_path)
    test_scenarios = generator.analyze_repository()

    with open(args.output, "w") as f:
        # Write imports
        for import_statement in sorted(generator.imports):
            f.write(f"{import_statement}\n")
        f.write("\n\n")

        # Write test scenarios
        for file, scenarios in test_scenarios.items():
            f.write(f"# Tests for {file}\n")
            for func, tests in scenarios.items():
                for test in tests:
                    if args.verbose:
                        f.write(f"# {test['description']}\n")
                    f.write(test["test_code"])
                    f.write("\n")

if __name__ == "__main__":
    main()
