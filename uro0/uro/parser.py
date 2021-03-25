import logging

from uro.ast import *
from uro.tokens import *

"""This module contains a recursive descent parser with the following rules:

program → statements
statements → statement SEMICOLON statements
statements → ε
statement → expression
statement → KEYWORD<return> return_cont
statement → import
statement → for
statement → free
for → KEYWORD<for> identity KEYWORD<in> identity block
free → KEYWORD<free> LBRACKET identity RBRACKET
import → KEYWORD<import> STRING
return_cont → expression
return_cont → ε
keys → key keys
keys → ε
key → LSTRAIGHTBRACKET expression RSTRAIGHTBRACKET
expression → STRING comparison_cont
expression → NUMBER comparison_cont
expression → LBRACKET expression RBRACKET comparison_cont
expression → function comparison_cont
expression → dictionary comparison_cont
expression → boolean comparison_cont
expression → identity assignment_or_identity_or_function_call comparison_cont
expression → extern
extern → KEYWORD<extern> LBRACKET STRING COMMA NUMBER RBRACKET
comparison_cont → EQUAL expression comparison_cont
comparison_cont → GREATERTHAN expression comparison_cont
comparison_cont → LESSTHAN expression comparison_cont
comparison_cont → ε
boolean → KEYWORD<True>
boolean → KEYWORD<False>
identity → IDENTIFIER keys
dictionary → LCURLYBRACKET key_values RCURLYBRACKET
key_values → key_value later_key_values
key_values → ε
later_key_values → COMMA key_values
later_key_values → ε
key_value → expression TOKEN_COLON expression
function → KEYWORD<fn> LBRACKET args RBRACKET block
block → LCURLYBRACKET statements RCURLYBRACKET
assignment_or_identity_or_function_call → assignment_cont
assignment_or_identity_or_function_call → identity_or_function_call
assignment_cont → ASSIGN expression
identity_or_function_call → function_call_cont
identity_or_function_call → identity_cont
identity_cont → ε
function_call_cont → LBRACKET args RBRACKET
args → arg later_args
args → ε
later_args → COMMA args
later_args → ε
arg → expression
"""


class ParseError(Exception):
    def __init__(self, token):
        if token == TOKEN_EOF:
            raise UnexpectedEOF()
        msg = f"Syntax error at line {token.line}: '{token.value}'"
        super().__init__(msg)


class UnexpectedEOF(Exception):
    pass


class Parser:
    def __init__(self):
        self._tokens = []
        self.ast = []

    def add_tokens(self, tokens):
        """Add a list of tokens to the buffer."""
        self._tokens.extend(tokens)

    def reset(self):
        """Empty the token buffer."""
        self._tokens = []

    @property
    def line_range(self):
        """Returns the first and last line numbers."""
        if self._tokens:
            return self._tokens[0].line, self._tokens[-1].line
        return 0, 0

    def parse(self):
        """Parse the buffered tokens and return True if parsed successfully.

        Note that the boolean which is returned only exists to verify the parser itself;
        the parser should always raise a ParseError when a syntax error is detected."""
        tokens = self._tokens + [Token(TOKEN_EOF, TOKEN_EOF, self.line_range[1])]
        ast = Parser.parse_program(tokens)
        if tokens.pop() == TOKEN_EOF:
            self.ast = ast
            self.reset()
            return True
        return False

    @classmethod
    def parse_program(cls, tokens):
        """Parses a 'program' symbol and returns an AST.

        program → statements
        * first: IDENTIFIER, STRING, NUMBER, LBRACKET, LCURLYBRACKET, KEYWORD<return>,
                 KEYWORD<import>, KEYWORD<fn>, KEYWORD<True>, KEYWORD<False>,
                 KEYWORD<extern>, KEYWORD<free>
        """
        logging.debug("%s", tokens[0])
        if tokens[0] in {
            TOKEN_IDENTIFIER,
            TOKEN_STRING,
            TOKEN_NUMBER,
            TOKEN_LBRACKET,
            TOKEN_LCURLYBRACKET,
        } or (
            tokens[0] == TOKEN_KEYWORD
            and tokens[0].value
            in {"return", "import", "fn", "for", "True", "False", "extern", "free"}
        ):
            return cls.parse_statements(tokens)
        raise ParseError(tokens[0])

    @classmethod
    def parse_statements(cls, tokens):
        """Parses a 'statements' symbol and returns an AST.

        statements → statement SEMICOLON statements
        * first: STRING, NUMBER, LBRACKET, IDENTIFIER, KEYWORD<fn> LCURLYBRACKET
                 KEYWORD<return>, KEYWORD<import>, KEYWORD<True>, KEYWORD<False>,
                 KEYWORD<extern>, KEYWORD<free>
        statements → ε
        * follow: $ RCURLYBRACKET
        """
        logging.debug("%s", tokens[0])
        if tokens[0] in {
            TOKEN_IDENTIFIER,
            TOKEN_STRING,
            TOKEN_NUMBER,
            TOKEN_LBRACKET,
            TOKEN_LCURLYBRACKET,
        } or (
            tokens[0] == TOKEN_KEYWORD
            and tokens[0].value
            in {"return", "import", "fn", "for", "True", "False", "extern", "free"}
        ):
            statement = cls.parse_statement(tokens)
            semicolon = tokens.pop(0)
            if semicolon != TOKEN_SEMICOLON:
                raise ParseError(semicolon)
            statements = cls.parse_statements(tokens)
            return [Node(NODE_STATEMENT, statement)] + statements
        elif tokens[0] in {TOKEN_EOF, TOKEN_RCURLYBRACKET}:
            return []
        raise ParseError(tokens[0])

    @classmethod
    def parse_statement(cls, tokens):
        """Parses a 'statement' symbol and returns an AST.

        statement → expression
        * first: STRING, NUMBER, LBRACKET, IDENTIFIER, KEYWORD<fn>, LCURLYBRACKET,
                 KEYWORD<True>, KEYWORD<False>
        statement → for
        * first: KEYWORD<for>
        statement → KEYWORD<return> return_cont
        statement → import
        * first: KEYWORD<import>
        statement → extern
        * first: KEYWORD<extern>
        statement → free
        * first: KEYWORD<free>
        """
        logging.debug("%s", tokens[0])
        if tokens[0] in {
            TOKEN_STRING,
            TOKEN_NUMBER,
            TOKEN_LBRACKET,
            TOKEN_IDENTIFIER,
            TOKEN_LCURLYBRACKET,
        } or (
            tokens[0] == TOKEN_KEYWORD and tokens[0].value in {"fn", "True", "False"}
        ):
            return cls.parse_expression(tokens)
        elif tokens[0] == TOKEN_KEYWORD and tokens[0].value == "for":
            return cls.parse_for(tokens)
        elif tokens[0] == TOKEN_KEYWORD and tokens[0].value == "return":
            keyword = tokens.pop(0)
            return cls.parse_return_cont(tokens)
        elif tokens[0] == TOKEN_KEYWORD and tokens[0].value == "import":
            return cls.parse_import(tokens)
        elif tokens[0] == TOKEN_KEYWORD and tokens[0].value == "free":
            return cls.parse_free(tokens)
        raise ParseError(tokens[0])

    @classmethod
    def parse_extern(cls, tokens):
        """Parses an 'extern' node and returns an AST.

        extern → KEYWORD<extern> LBRACKET STRING COMMA  RBRACKET
        """
        logging.debug("%s", tokens[0])
        if tokens[0] == TOKEN_KEYWORD and tokens[0].value == "extern":
            extern = tokens.pop(0)
            lbracket = tokens.pop(0)
            if lbracket != TOKEN_LBRACKET:
                raise ParseError(lbracket)
            string = tokens.pop(0)
            if string != TOKEN_STRING:
                raise ParseError(string)
            comma = tokens.pop(0)
            if comma != TOKEN_COMMA:
                raise ParseError(string)
            number = tokens.pop(0)
            if number != TOKEN_NUMBER:
                raise ParseError(number)
            rbracket = tokens.pop(0)
            if rbracket != TOKEN_RBRACKET:
                raise ParseError(rbracket)
            return Node(NODE_EXTERN, (string, number))
        raise ParseError(tokens[0])

    @classmethod
    def parse_free(cls, tokens):
        """Parses a 'free' node and returns an AST.

        free → KEYWORD<free> LBRACKET identity RBRACKET
        """
        logging.debug("%s", tokens[0])
        if tokens[0] == TOKEN_KEYWORD and tokens[0].value == "free":
            free = tokens.pop(0)
            lbracket = tokens.pop(0)
            if lbracket != TOKEN_LBRACKET:
                raise ParseError(lbracket)
            identity = cls.parse_identity(tokens)
            rbracket = tokens.pop(0)
            if rbracket != TOKEN_RBRACKET:
                raise ParseError(rbracket)
            return Node(NODE_FREE, identity)
        raise ParseError(tokens[0])

    @classmethod
    def parse_import(cls, tokens):
        """Parses an 'import' node and returns an AST.

        return → KEYWORD<import> STRING
        """
        logging.debug("%s", tokens[0])
        if tokens[0] == TOKEN_KEYWORD and tokens[0].value == "import":
            keyword = tokens.pop(0)
            module = tokens.pop(0)
            if module != TOKEN_STRING:
                raise ParseError(module)
            return Node(NODE_IMPORT, module)
        raise ParseError(tokens[0])

    @classmethod
    def parse_for(cls, tokens):
        """Parses a 'for' node and returns an AST.

        for → KEYWORD<for> identity KEYWORD<in> identity block
        """
        logging.debug("%s", tokens[0])
        if tokens[0] == TOKEN_KEYWORD and tokens[0].value == "for":
            keyword_for = tokens.pop(0)
            obj = cls.parse_identity(tokens)
            keyword_in = tokens.pop(0)
            if keyword_in != TOKEN_KEYWORD or keyword_in.value != "in":
                raise ParseError(keyword_in)
            iterable = cls.parse_identity(tokens)
            block = cls.parse_block(tokens)
            return Node(NODE_FOR, [obj, iterable, block])
        raise ParseError(tokens[0])

    @classmethod
    def parse_return_cont(cls, tokens):
        """Parses a 'return_cont' node and returns an AST.

        return → expression
        * first: STRING, NUMBER, LBRACKET, IDENTIFIER, LCURLYBRACKET, KEYWORD<fn>,
                 KEYWORD<True>, KEYWORD<False>
        return → ε
        * follow: SEMICOLON
        """
        logging.debug("%s", tokens[0])
        if tokens[0] in {
            TOKEN_STRING,
            TOKEN_NUMBER,
            TOKEN_LBRACKET,
            TOKEN_IDENTIFIER,
            TOKEN_LCURLYBRACKET,
        } or (
            tokens[0] == TOKEN_KEYWORD and tokens[0].value in {"fn", "True", "False"}
        ):
            expression = cls.parse_expression(tokens)
            return Node(NODE_RETURN, expression)
        elif tokens[0] == TOKEN_SEMICOLON:
            return Node(NODE_RETURN, [])
        raise ParseError(tokens[0])

    @classmethod
    def parse_assignment_or_identity_or_function_call(cls, tokens):
        """Parses an 'assignment'/'identity'/'function_call' node and returns an AST.

        assignment_or_identity_or_function_call → assignment_cont
        * first: ASSIGN
        assignment_or_identity_or_function_call → identity_or_function_call
        * first: LBRACKET
        * follow: RBRACKET, RSTRAIGHTBRACKET, COMMA, SEMICOLON, COLON, RCURLYBRACKET,
                  EQUAL, GREATERTHAN, LESSTHAN
        """
        logging.debug("%s", tokens[0])
        if tokens[0] == TOKEN_ASSIGN:
            return cls.parse_assignment_cont(tokens)
        elif tokens[0] in {
            TOKEN_LBRACKET,
            TOKEN_RBRACKET,
            TOKEN_RSTRAIGHTBRACKET,
            TOKEN_COMMA,
            TOKEN_SEMICOLON,
            TOKEN_COLON,
            TOKEN_RCURLYBRACKET,
            TOKEN_EQUAL,
            TOKEN_GREATERTHAN,
            TOKEN_LESSTHAN,
        }:
            return cls.parse_identity_or_function_call(tokens)
        raise ParseError(tokens[0])

    @classmethod
    def parse_assignment_cont(cls, tokens):
        """Parses an 'assignment_cont' node and returns an AST.

        assignment_cont → ASSIGN expression
        * first: ASSIGN
        """
        logging.debug("%s", tokens[0])
        if tokens[0] == TOKEN_ASSIGN:
            assign = tokens.pop(0)
            expression = cls.parse_expression(tokens)
            return Node(NODE_ASSIGNMENT, [expression])
        raise ParseError(tokens[0])

    @classmethod
    def parse_identity(cls, tokens):
        """Parses an 'identity' symbol and returns an AST.

        identity → IDENTIFIER keys
        * first: IDENTIFIER
        """
        logging.debug("%s", tokens[0])
        if tokens[0] == TOKEN_IDENTIFIER:
            identifier = tokens.pop(0)
            keys = cls.parse_keys(tokens)
            return Node(NODE_IDENTITY, [identifier, keys])
        raise ParseError(tokens[0])

    @classmethod
    def parse_keys(cls, tokens):
        """Parses a 'keys' symbol and returns an AST.

        keys → key keys
        * first: LSTRAIGHTBRACKET
        keys → ε
        * follow: SEMICOLON, ASSIGN, RBRACKET, RSTRAIGHTBRACKET, LBRACKET, COMMA, COLON,
                  LCURLYBRACKET, RCURLYBRACKET, KEYWORD<in>, EQUAL, GREATERTHAN,
                  LESSTHAN
        """
        logging.debug("%s", tokens[0])
        if tokens[0] == TOKEN_LSTRAIGHTBRACKET:
            key = cls.parse_key(tokens)
            keys = cls.parse_keys(tokens)
            return [Node(NODE_KEY, key)] + keys
        elif (
            tokens[0]
            in {
                TOKEN_SEMICOLON,
                TOKEN_ASSIGN,
                TOKEN_RBRACKET,
                TOKEN_RSTRAIGHTBRACKET,
                TOKEN_LBRACKET,
                TOKEN_COMMA,
                TOKEN_COLON,
                TOKEN_LCURLYBRACKET,
                TOKEN_RCURLYBRACKET,
                TOKEN_EQUAL,
                TOKEN_GREATERTHAN,
                TOKEN_LESSTHAN,
            }
            or (tokens[0] == TOKEN_KEYWORD and tokens[0].value == "in")
        ):
            return []
        raise ParseError(tokens[0])

    @classmethod
    def parse_key(cls, tokens):
        """Parses a 'key' symbol and returns an AST.

        key → LSTRAIGHTBRACKET expression RSTRAIGHTBRACKET
        """
        logging.debug("%s", tokens[0])
        if tokens[0] == TOKEN_LSTRAIGHTBRACKET:
            lstraightbracket = tokens.pop(0)
            expression = cls.parse_expression(tokens)
            rstraightbracket = tokens.pop(0)
            assert rstraightbracket == TOKEN_RSTRAIGHTBRACKET
            return expression
        raise ParseError(tokens[0])

    @classmethod
    def parse_expression(cls, tokens):
        """Parses an 'expression' node and returns an AST.

        expression → STRING comparison_cont
        expression → NUMBER comparison_cont
        expression → LBRACKET expression RBRACKET comparison_cont
        expression → identity assignment_or_identity_or_function_call comparison_cont
        * first: IDENTIFIER
        expression → function comparison_cont
        * first: KEYWORD<fn>
        expression → dictionary comparison_cont
        * first: LCURLYBRACKET
        expression → boolean comparison_cont
        * first: KEYWORD<True>, KEYWORD<False>
        expression → extern
        * first: KEYWORD<extern>
        """
        logging.debug("%s", tokens[0])
        if tokens[0] == TOKEN_STRING:
            node = Node(NODE_STRING_LITERAL, tokens.pop(0))
            comparison = cls.parse_comparison_cont(tokens)
            if comparison:
                return Node(NODE_COMPARISON, [node] + comparison.content)
            else:
                return node
        elif tokens[0] == TOKEN_NUMBER:
            node = Node(NODE_NUMBER_LITERAL, tokens.pop(0))
            comparison = cls.parse_comparison_cont(tokens)
            if comparison:
                return Node(NODE_COMPARISON, [node] + comparison.content)
            else:
                return node
        elif tokens[0] == TOKEN_IDENTIFIER:
            identity = cls.parse_identity(tokens)
            _node = cls.parse_assignment_or_identity_or_function_call(tokens)
            node_type = _node.type
            content = [identity.content] + _node.content
            node = Node(node_type, content)
            comparison = cls.parse_comparison_cont(tokens)
            if comparison:
                return Node(NODE_COMPARISON, [node] + comparison.content)
            else:
                return node
        elif tokens[0] == TOKEN_LBRACKET:
            lbracket = tokens.pop(0)
            expression = cls.parse_expression(tokens)
            rbracket = tokens.pop(0)
            if rbracket != TOKEN_RBRACKET:
                raise ParseError(rbracket)
            comparison = cls.parse_comparison_cont(tokens)
            if comparison:
                return Node(NODE_COMPARISON, [expression] + comparison.content)
            else:
                return expression
        elif tokens[0] == TOKEN_KEYWORD and tokens[0].value == "fn":
            node = cls.parse_function(tokens)
            comparison = cls.parse_comparison_cont(tokens)
            if comparison:
                return Node(NODE_COMPARISON, [node] + comparison.content)
            else:
                return node
        elif tokens[0] == TOKEN_LCURLYBRACKET:
            node = cls.parse_dictionary(tokens)
            comparison = cls.parse_comparison_cont(tokens)
            if comparison:
                return Node(NODE_COMPARISON, [node] + comparison.content)
            else:
                return node
        elif tokens[0] == TOKEN_KEYWORD and tokens[0].value in {"True", "False"}:
            node = cls.parse_boolean(tokens)
            comparison = cls.parse_comparison_cont(tokens)
            if comparison:
                return Node(NODE_COMPARISON, [node] + comparison.content)
            else:
                return node
        elif tokens[0] == TOKEN_KEYWORD and tokens[0].value == "extern":
            return cls.parse_extern(tokens)
        raise ParseError(tokens[0])

    @classmethod
    def parse_identity_or_function_call(cls, tokens):
        """Parses an 'identity' or 'function_call' symbol and returns an AST.

        identity_or_function_call → function_call_cont
        * first: LBRACKET
        identity_or_function_call → identity_cont
        * follow: ASSIGN, RBRACKET, RSTRAIGHTBRACKET, COMMA, SEMICOLON, COLON,
                  RCURLYBRACKET, EQUAL, GREATERTHAN, LESSTHAN
        """
        logging.debug("%s", tokens[0])
        if tokens[0] == TOKEN_LBRACKET:
            return cls.parse_function_call_cont(tokens)
        elif tokens[0] in {
            TOKEN_ASSIGN,
            TOKEN_RBRACKET,
            TOKEN_RSTRAIGHTBRACKET,
            TOKEN_COMMA,
            TOKEN_SEMICOLON,
            TOKEN_COLON,
            TOKEN_RCURLYBRACKET,
            TOKEN_EQUAL,
            TOKEN_GREATERTHAN,
            TOKEN_LESSTHAN,
        }:
            return cls.parse_identity_cont(tokens)
        raise ParseError(tokens[0])

    @classmethod
    def parse_identity_cont(cls, tokens):
        """Parses an 'identity_cont' symbol and returns an AST.

        identity_cont → ε
        * follow: ASSIGN, RBRACKET, RSTRAIGHTBRACKET, COMMA, SEMICOLON, COLON,
                  RCURLYBRACKET, EQUAL, GREATERTHAN, LESSTHAN
        """
        logging.debug("%s", tokens[0])
        if tokens[0] in {
            TOKEN_ASSIGN,
            TOKEN_RBRACKET,
            TOKEN_RSTRAIGHTBRACKET,
            TOKEN_COMMA,
            TOKEN_SEMICOLON,
            TOKEN_COLON,
            TOKEN_RCURLYBRACKET,
            TOKEN_EQUAL,
            TOKEN_GREATERTHAN,
            TOKEN_LESSTHAN,
        }:
            return Node(NODE_IDENTITY, [])
        raise ParseError(tokens[0])

    @classmethod
    def parse_function_call_cont(cls, tokens):
        """Parses an 'function_call_cont' symbol and returns an AST.

        function_call_cont → LBRACKET args RBRACKET
        """
        logging.debug("%s", tokens[0])
        if tokens[0] == TOKEN_LBRACKET:
            lbracket = tokens.pop(0)
            args = cls.parse_args(tokens)
            rbracket = tokens.pop(0)
            if rbracket != TOKEN_RBRACKET:
                raise ParseError(rbracket)
            return Node(NODE_FUNCTION_CALL, [args])
        raise ParseError(tokens[0])

    @classmethod
    def parse_args(cls, tokens):
        """Parses an 'args' node and returns an AST.

        args → arg later_args
        * first: STRING, NUMBER, LBRACKET, IDENTIFIER, LCURLYBRACKET, KEYWORD<fn>,
                 KEYWORD<True>, KEYWORD<False>
        args → ε
        * follow: RBRACKET
        """
        logging.debug("%s", tokens[0])
        if tokens[0] in {
            TOKEN_STRING,
            TOKEN_NUMBER,
            TOKEN_LBRACKET,
            TOKEN_IDENTIFIER,
            TOKEN_LCURLYBRACKET,
        } or (
            tokens[0] == TOKEN_KEYWORD and tokens[0].value in {"fn", "True", "False"}
        ):
            arg = cls.parse_arg(tokens)
            later_args = cls.parse_later_args(tokens)
            return [arg] + later_args
        if tokens[0] == TOKEN_RBRACKET:
            return []
        raise ParseError(tokens[0])

    @classmethod
    def parse_later_args(cls, tokens):
        """Parses an 'later_args' node and returns an AST.

        later_args → ε
        * follow: RBRACKET
        later_args → COMMA args
        """
        logging.debug("%s", tokens[0])
        if tokens[0] == TOKEN_COMMA:
            comma = tokens.pop(0)
            args = cls.parse_args(tokens)
            return args
        elif tokens[0] == TOKEN_RBRACKET:
            return []
        raise ParseError(tokens[0])

    @classmethod
    def parse_arg(cls, tokens):
        """Parses an 'arg' node and returns an AST.

        later_args → expression
        * first: STRING, NUMBER, LBRACKET, IDENTIFIER, LCURLYBRACKET, KEYWORD<fn>,
                 KEYWORD<True>, KEYWORD<False>
        """
        logging.debug("%s", tokens[0])
        if tokens[0] in {
            TOKEN_STRING,
            TOKEN_NUMBER,
            TOKEN_LBRACKET,
            TOKEN_IDENTIFIER,
            TOKEN_LCURLYBRACKET,
        } or (
            tokens[0] == TOKEN_KEYWORD and tokens[0].value in {"fn", "True", "False"}
        ):
            arg = cls.parse_expression(tokens)
            return Node(NODE_ARG, arg)
        raise ParseError(tokens[0])

    @classmethod
    def parse_function(cls, tokens):
        """Parses a 'function' node and returns an AST.

        function → KEYWORD<fn> LBRACKET args RBRACKET block
        """
        logging.debug("%s", tokens[0])
        if tokens[0] == TOKEN_KEYWORD and tokens[0].value == "fn":
            keyword = tokens.pop(0)
            lbracket = tokens.pop(0)
            if lbracket != TOKEN_LBRACKET:
                raise ParseError(lbracket)
            args = cls.parse_args(tokens)
            rbracket = tokens.pop(0)
            if rbracket != TOKEN_RBRACKET:
                raise ParseError(rbracket)
            block = cls.parse_block(tokens)
            return Node(NODE_FUNCTION, [args, block])
        raise ParseError(tokens[0])

    @classmethod
    def parse_block(cls, tokens):
        """Parses a 'block' node and returns an AST.

        block → LCURLYBRACKET statements RCURLYBRACKET
        """
        logging.debug("%s", tokens[0])
        if tokens[0] == TOKEN_LCURLYBRACKET:
            lcurlybraket = tokens.pop(0)
            statements = cls.parse_statements(tokens)
            rcurlybracket = tokens.pop(0)
            if rcurlybracket != TOKEN_RCURLYBRACKET:
                raise ParseError(rcurlybracket)
            return Node(NODE_BLOCK, statements)
        raise ParseError(tokens[0])

    @classmethod
    def parse_dictionary(cls, tokens):
        """Parses a 'dictionary' node and returns an AST.

        dictionary → LCURLYBRACKET key_values RCURLYBRACKET
        """
        logging.debug("%s", tokens[0])
        if tokens[0] == TOKEN_LCURLYBRACKET:
            lcurlybraket = tokens.pop(0)
            key_values = cls.parse_key_values(tokens)
            rcurlybracket = tokens.pop(0)
            if rcurlybracket != TOKEN_RCURLYBRACKET:
                raise ParseError(rcurlybracket)
            return Node(NODE_DICTIONARY, key_values)
        raise ParseError(tokens[0])

    @classmethod
    def parse_key_values(cls, tokens):
        """Parses a 'key_values' node and returns an AST.

        key_values → key_value later_key_values
        * first: STRING NUMBER LBRACKET IDENTIFIER KEYWORD<fn> LCURLYBRACKET
        key_values → ε
        * follow: RCURLYBRACKET
        """
        logging.debug("%s", tokens[0])
        if tokens[0] in {
            TOKEN_STRING,
            TOKEN_NUMBER,
            TOKEN_LBRACKET,
            TOKEN_IDENTIFIER,
            TOKEN_LCURLYBRACKET,
        } or (
            tokens[0] == TOKEN_KEYWORD and tokens[0].value in {"fn", "True", "False"}
        ):
            key_value = cls.parse_key_value(tokens)
            later_key_values = cls.parse_later_key_values(tokens)
            return [key_value] + later_key_values
        elif tokens[0] == TOKEN_RCURLYBRACKET:
            return []
        raise ParseError(tokens[0])

    @classmethod
    def parse_later_key_values(cls, tokens):
        """Parses a 'later_key_values' node and returns an AST.

        later_key_values → COMMA key_values
        key_values → ε
        * follow: RCURLYBRACKET
        """
        logging.debug("%s", tokens[0])
        if tokens[0] == TOKEN_COMMA:
            comma = tokens.pop(0)
            key_values = cls.parse_key_values(tokens)
            return key_values
        elif tokens[0] == TOKEN_RCURLYBRACKET:
            return []
        raise ParseError(tokens[0])

    @classmethod
    def parse_key_value(cls, tokens):
        """Parses a 'key_value' node and returns an AST.

        key_value → expression TOKEN_COLON expression
        * first: STRING, NUMBER, LBRACKET, IDENTIFIER, KEYWORD<fn>, LCURLYBRACKET,
                 KEYWORD<True>, KEYWORD<False>
        """
        logging.debug("%s", tokens[0])
        if tokens[0] in {
            TOKEN_STRING,
            TOKEN_NUMBER,
            TOKEN_LBRACKET,
            TOKEN_IDENTIFIER,
            TOKEN_LCURLYBRACKET,
        } or (
            tokens[0] == TOKEN_KEYWORD and tokens[0].value in {"fn", "True", "False"}
        ):
            key = cls.parse_expression(tokens)
            colon = tokens.pop(0)
            if colon != TOKEN_COLON:
                raise ParseError(colon)
            value = cls.parse_expression(tokens)
            return Node(NODE_KEY_VALUE, [key, value])
        raise ParseError(tokens[0])

    @classmethod
    def parse_boolean(cls, tokens):
        """Parses a 'boolean' node and returns an AST.

        boolean → KEYWORD<True>
        boolean → KEYWORD<False>
        """
        logging.debug("%s", tokens[0])
        if tokens[0] == TOKEN_KEYWORD and tokens[0].value in {"True", "False"}:
            boolean = tokens.pop(0)
            return Node(NODE_BOOLEAN, boolean)
        raise ParseError(tokens[0])

    @classmethod
    def parse_comparison_cont(cls, tokens):
        """Parses a 'comparison_cont' node and returns an AST.

        comparison_cont → EQUAL expression
        comparison_cont → GREATERTHAN expression
        comparison_cont → LESSTHAN expression
        comparison_cont → ε
        * follow: ASSIGN, RBRACKET, RSTRAIGHTBRACKET, COMMA, SEMICOLON, COLON,
                  RCURLYBRACKET
        """
        logging.debug("%s", tokens[0])
        if tokens[0] == TOKEN_EQUAL:
            equal = tokens.pop(0)
            expression = cls.parse_expression(tokens)
            return Node(NODE_COMPARISON, [equal, expression])
        elif tokens[0] == TOKEN_GREATERTHAN:
            gt = tokens.pop(0)
            expression = cls.parse_expression(tokens)
            return Node(NODE_COMPARISON, [gt, expression])
        elif tokens[0] == TOKEN_LESSTHAN:
            lt = tokens.pop(0)
            expression = cls.parse_expression(tokens)
            return Node(NODE_COMPARISON, [lt, expression])
        elif tokens[0] in {
            TOKEN_ASSIGN,
            TOKEN_RBRACKET,
            TOKEN_RSTRAIGHTBRACKET,
            TOKEN_COMMA,
            TOKEN_SEMICOLON,
            TOKEN_COLON,
            TOKEN_RCURLYBRACKET,
        }:
            return []
        raise ParseError(tokens[0])
