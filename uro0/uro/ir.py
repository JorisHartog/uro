import logging

from uro.ast import *


IR_SET_NAME = "ir_set_name"
IR_PUSH_REFERENCE = "ir_push_reference"
IR_MAKE_STRING = "ir_make_string"
IR_MAKE_NUMBER = "ir_make_number"
IR_MAKE_BOOLEAN = "ir_make_boolean"
IR_MAKE_FUNCTION = "ir_make_function"
IR_CALL_FUNCTION = "ir_call_function"
IR_EXTERN = "ir_extern"
IR_NOP = "ir_nop"


def _remove_quotes(s):
    assert s[0] in "'\"" and s[-1] in "'\""
    return s[1:-1]


class IRGenerator:
    """Turns an AST into an intermediate representation (IR).

    The IR is formatted as a list of `(op, args)` tuples.
    """

    def __init__(self, ast):
        self.ast = ast

    @property
    def ir(self):
        """Returns the IR."""
        ir = self._generate_program(self.ast)
        logging.debug(ir)
        return ir

    def _generate_program(self, root):
        logging.debug("%s", root)
        ir = []
        for node in root:
            statement_ir = self._generate_statement(node)
            ir.extend(statement_ir)
        return ir

    def _generate_statement(self, node):
        logging.debug("%s", node)
        statement = node.content
        if statement == NODE_ASSIGNMENT:
            return self._generate_assignment(statement)
        elif statement == NODE_FUNCTION_CALL:
            return self._generate_function_call(statement)
        else:
            return self._generate_expression(statement)

    def _generate_assignment(self, node):
        logging.debug("%s", node)
        identity_node, expression_node = node.content
        identity_token, keys_tokens = identity_node

        ir_expression = self._generate_expression(expression_node)
        if keys_tokens:
            raise NotImplementedError
        else:
            ir_identity = (IR_SET_NAME, (identity_token.value,))
            return ir_expression + [ir_identity]

    def _generate_expression(self, node):
        logging.debug("%s", node)
        if node == NODE_IDENTITY:
            return self._generate_identity(node)
        elif node == NODE_STRING_LITERAL:
            return self._generate_string_literal(node)
        elif node == NODE_NUMBER_LITERAL:
            return self._generate_number_literal(node)
        elif node == NODE_BOOLEAN:
            return self._generate_boolean(node)
        elif node == NODE_FUNCTION:
            return self._generate_function(node)
        elif node == NODE_FUNCTION_CALL:
            return self._generate_function_call(node)
        elif node == NODE_EXTERN:
            return self._generate_extern(node)
        raise NotImplementedError

    def _generate_identity(self, node):
        logging.debug("%s", node)
        identity_token, keys_tokens = node.content[0]
        if keys_tokens:
            raise NotImplementedError
        else:
            ir_identity = (IR_PUSH_REFERENCE, identity_token.value)
            return [ir_identity]

    def _generate_string_literal(self, node):
        logging.debug("%s", node)
        string = _remove_quotes(node.content.value)
        ir_string = (IR_MAKE_STRING, (string,))
        return [ir_string]

    def _generate_number_literal(self, node):
        logging.debug("%s", node)
        number = int(node.content.value)
        ir_number = (IR_MAKE_NUMBER, (number,))
        return [ir_number]

    def _generate_boolean(self, node):
        logging.debug("%s", node)
        boolean = node.content.value == "True"
        ir_boolean = (IR_MAKE_BOOLEAN, (boolean,))
        return [ir_boolean]

    def _generate_function(self, node):
        logging.debug("%s", node)
        args_node, block_node = node.content
        assert all(arg.content == NODE_IDENTITY for arg in args_node)
        args = [name.value for arg in args_node for name, _ in arg.content.content]
        block = self._generate_program(block_node.content)
        ir_function = (IR_MAKE_FUNCTION, (args, block))
        return [ir_function]

    def _generate_extern(self, node):
        logging.debug("%s", node)
        name_token, arg_len_token = node.content
        name = _remove_quotes(name_token.value)
        arg_len = int(arg_len_token.value)
        ir_extern = (IR_EXTERN, (name, arg_len))
        return [ir_extern]

    def _generate_function_call(self, node):
        logging.debug("%s", node)
        identifier_node, args_node = node.content
        name = identifier_node[0].value
        args = [ir for a in args_node for ir in self._generate_expression(a.content)]
        ir_function_call = (IR_CALL_FUNCTION, (name, args))
        return [ir_function_call]
