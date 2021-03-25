NODE_STATEMENT = "node_statement"
NODE_ASSIGNMENT = "node_assignment"
NODE_IDENTITY = "node_identity"
NODE_KEY = "node_key"
NODE_STRING_LITERAL = "node_string_literal"
NODE_NUMBER_LITERAL = "node_number_literal"
NODE_FUNCTION_CALL = "node_function_call"
NODE_FUNCTION = "node_function"
NODE_ARG = "node_arg"
NODE_BLOCK = "node_block"
NODE_RETURN = "node_return"
NODE_DICTIONARY = "node_dictionary"
NODE_KEY_VALUE = "node_key_value"
NODE_IMPORT = "node_import"
NODE_FOR = "node_for"
NODE_BOOLEAN = "node_boolean"
NODE_COMPARISON = "node_comparison"
NODE_EXTERN = "node_extern"
NODE_FREE = "node_free"


class Node:
    def __init__(self, node_type, content):
        self.type = node_type
        self.content = content

    def __str__(self):
        return f"{self.type}({self.content})"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.type == other
