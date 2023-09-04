from typing import List, Tuple
from collections.abc import Sequence
import itertools

ADDITION_SYMBOL = '$or$'
INTERSECTION_SYMBOL = '$and$'


class Operation():

    def __init__(self, op_str: str):
        self.op_str = op_str
        self.op_symbol = None
        self.op_elements = set()
        self.parse_operation(op_str)

    def parse_operation(self, op_str: str):
        # Get the parentheses blocks
        elements_strs = []
        nested_parentheses = 0
        start_pos = 0
        end_pos = -1
        found_flag = False
        for i, char in enumerate(op_str):
            if char == '(':
                found_flag = True
                nested_parentheses += 1
            elif char == ')':
                nested_parentheses -= 1
            if nested_parentheses == 0 and found_flag:
                found_flag = False
                end_pos = i
                elements_strs.append(op_str[start_pos:end_pos + 1])
                start_pos = i + 1
        if len(elements_strs) == 1 and op_str[0] == '(' and op_str[-1] == ')':
            # A single parentheses block was found
            self.parse_operation(op_str[1:-1])
            return
        if start_pos != len(op_str):
            elements_strs.append(op_str[start_pos:])

        # Get the operation symbol and elements
        clean_elements_strs = []
        for element_str in elements_strs:
            open_pos = element_str.find('(')
            if open_pos == -1:
                open_pos = len(element_str)
            elif open_pos == 0:
                clean_elements_strs.append(element_str)
                continue
            # Get the operation symbol
            middle_str = element_str[:open_pos]
            addition_pos = middle_str.find(ADDITION_SYMBOL)
            intersection_pos = middle_str.find(INTERSECTION_SYMBOL)
            if addition_pos == -1:
                new_op_symbol = INTERSECTION_SYMBOL
            elif intersection_pos == -1:
                new_op_symbol = ADDITION_SYMBOL
            else:
                raise Exception(f'Operation symbol combination not supported: {middle_str}')
            if self.op_symbol is None:
                self.op_symbol = new_op_symbol
            elif self.op_symbol != new_op_symbol:
                raise Exception('Operation symbols do not match')
            clean_elements_strs.extend(middle_str.split(self.op_symbol))
            clean_elements_strs.append(element_str[open_pos:])
        # Filter empty strings
        clean_elements_strs = list(filter(None, clean_elements_strs))
        for element_str in clean_elements_strs:
            # If there are operations, the element is an operation
            if element_str.count(ADDITION_SYMBOL) + element_str.count(INTERSECTION_SYMBOL) > 0:
                new_operation_element = Operation(element_str)
                # If the operation symbol is the same, add the elements
                if self.op_symbol == new_operation_element.op_symbol:
                    self.op_elements.update(new_operation_element.op_elements)
                else:
                    self.op_elements.add(new_operation_element)
            # If there are no operations, the element is a string
            else:
                self.op_elements.add(element_str)

    def compare(self, other):
        if self.op_symbol != other.op_symbol:
            return False
        if len(self.op_elements) != len(other.op_elements):
            return False
        found_flag = False
        for element in self.op_elements:
            str_comparison = isinstance(element, str)
            for other_element in other.op_elements:
                # If element is a string
                if str_comparison and isinstance(other_element, str):
                    if element == other_element:
                        found_flag = True
                        break
                # If element is an operation
                elif not str_comparison and isinstance(other_element, Operation):
                    if element.compare(other_element):
                        found_flag = True
                        break
            if not found_flag:
                return False
            found_flag = False
        return True

    def __str__(self):
        sorted_op_elements = sorted(map(str, self.op_elements))
        return '(' + self.op_symbol.join(sorted_op_elements) + ')'


def split_operation(operation: str) -> Tuple[str, str, str]:
    # Split the operation by the operation symbol
    # For example: (A+B)+C -> ['(A+B)', 'C']
    # Remove the first and last parenthesis
    operation = operation[1:-1]
    # First check if the operation has the operation symbol before any parenthesis
    addition_pos = operation.find(ADDITION_SYMBOL)
    intersection_pos = operation.find(INTERSECTION_SYMBOL)
    if addition_pos == -1 and intersection_pos == -1:
        raise Exception('Operation symbol not found')
    elif addition_pos == -1:
        operation_pos = intersection_pos
        operation_symbol = INTERSECTION_SYMBOL
    elif intersection_pos == -1:
        operation_pos = addition_pos
        operation_symbol = ADDITION_SYMBOL
    else:
        operation_pos = addition_pos if addition_pos < intersection_pos else intersection_pos
        operation_symbol = ADDITION_SYMBOL if addition_pos < intersection_pos else INTERSECTION_SYMBOL
    first_parenthesis_pos = operation.find('(')
    if first_parenthesis_pos == -1 or operation_pos < first_parenthesis_pos:
        return (operation[:operation_pos], operation_symbol, operation[operation_pos + len(operation_symbol):])
    # Iterate over the string and count the number of parentheses
    nested_parentheses = 0
    found_flag = False
    for idx, char in enumerate(operation):
        if char == '(':
            nested_parentheses += 1
            found_flag = True
        elif char == ')':
            nested_parentheses -= 1
        if nested_parentheses == 0 and found_flag:
            addition_pos = operation.find(ADDITION_SYMBOL, idx)
            intersection_pos = operation.find(INTERSECTION_SYMBOL, idx)
            if addition_pos == -1 and intersection_pos == -1:
                raise Exception('Operation symbol not found')
            elif addition_pos == -1:
                operation_pos = intersection_pos
                operation_symbol = INTERSECTION_SYMBOL
            elif intersection_pos == -1:
                operation_pos = addition_pos
                operation_symbol = ADDITION_SYMBOL
            else:
                operation_pos = addition_pos if addition_pos < intersection_pos else intersection_pos
                operation_symbol = ADDITION_SYMBOL if addition_pos < intersection_pos else INTERSECTION_SYMBOL
            return (operation[:operation_pos], operation_symbol, operation[operation_pos + len(operation_symbol):])
    raise Exception('Operation symbol not found')


def generate_combinations(elements: List[str], max_combinations: int) -> List[str]:
    # Permutations of the elements
    combinations = min(max_combinations, len(elements)) if max_combinations > 0 else len(elements)
    permutations = itertools.permutations(elements, combinations)
    # Generate all possible groups
    all_groups = []
    for permutation in permutations:
        all_groups.extend(_generate_groups(permutation))
    # Add all possible operations from the groups
    operation_list = []
    for group in all_groups:
        group_operations = _generate_operations(group)
        if len(operation_list) > 0:
            group_operations = group_operations[1:-1]  # Remove the first and last all equal operations
        for group_operation in group_operations:
            op_instance = Operation(group_operation)
            # Check if the operation is already in the list
            found_flag = False
            for existing_op in operation_list:
                if op_instance.compare(existing_op):
                    found_flag = True
                    break
            if not found_flag:
                operation_list.append(op_instance)
    operations_str_list = [op.op_str for op in operation_list]
    # Generate the smaller operations based on the parenthesis from the bigger operations
    all_operations = set()
    for operation_str in operations_str_list:
        inner_operations = _get_inner_operations(operation_str)
        all_operations.update(inner_operations)
    # Sort by the number of operations and then alphabetically
    all_operations = sorted(all_operations, key=lambda x: (x.count(ADDITION_SYMBOL) + x.count(INTERSECTION_SYMBOL), x))
    return all_operations


def _get_inner_operations(operation: str) -> List[str]:
    # Get the inner operations of the operations based on the parenthesis
    # For example: (a+(b*(c+d))) -> (c+d), (b*(c+d)), (a+(b*(c+d)))
    inner_operations = []
    starting_pos = []
    for i, char in enumerate(operation):
        if char == '(':
            starting_pos.append(i)
        elif char == ')':
            start_pos = starting_pos.pop()
            inner_operations.append(operation[start_pos:i + 1])
    return inner_operations


def _generate_operations(group: str) -> List[str]:
    # Each ")(" is an operation
    operations_counts = group.count(')(')
    operations_symbols = itertools.product([ADDITION_SYMBOL, INTERSECTION_SYMBOL], repeat=operations_counts)
    operations = []
    for operation_symbols in operations_symbols:
        op_str = group
        for operation_symbol in operation_symbols:
            op_str = op_str.replace(')(', operation_symbol, 1)
        operations.append(op_str[1:-1])  # Remove the first and last parenthesis
    return operations


def _generate_groups(elements: Sequence[str]) -> List[str]:
    if len(elements) == 1:
        return [f'({elements[0]})']

    groups = []
    for i in range(1, len(elements)):
        left_groups = _generate_groups(elements[:i])
        right_groups = _generate_groups(elements[i:])
        for left in left_groups:
            for right in right_groups:
                groups.append(f"({left}{right})")
    return groups
