TOKEN_WHITESPACE = "token_whitespace"
TOKEN_COMMENT = "token_comment"
TOKEN_KEYWORD = "token_keyword"
TOKEN_NUMBER = "token_number"
TOKEN_STRING = "token_string"
TOKEN_IDENTIFIER = "token_identifier"
TOKEN_LBRACKET = "token_lbracket"
TOKEN_RBRACKET = "token_rbracket"
TOKEN_LCURLYBRACKET = "token_lcurlybracket"
TOKEN_RCURLYBRACKET = "token_rcurlybracket"
TOKEN_LSTRAIGHTBRACKET = "token_lstraightbracket"
TOKEN_RSTRAIGHTBRACKET = "token_rstraightbracket"
TOKEN_PERIOD = "token_period"
TOKEN_COMMA = "token_comma"
TOKEN_EQUAL = "token_equal"
TOKEN_GREATERTHAN = "token_greaterthan"
TOKEN_LESSTHAN = "token_lessthan"
TOKEN_ASSIGN = "token_assign"
TOKEN_COLON = "token_colon"
TOKEN_SEMICOLON = "token_semicolon"
TOKEN_MINUS = "token_minus"
TOKEN_PLUS = "token_plus"
TOKEN_ASTERISK = "token_asterisk"
TOKEN_UNKNOWN = "token_unknown"
TOKEN_EMPTY = "ε"
TOKEN_EOF = "$"

PATTERNS = [
    (r"\s+", TOKEN_WHITESPACE),
    (r"\d+", TOKEN_NUMBER),
    (r"#.*$", TOKEN_COMMENT),
    (r"'.*?'", TOKEN_STRING),
    (r'".*?"', TOKEN_STRING),
    (r"[a-zA-Z_][a-zA-Z_0-9]*", TOKEN_IDENTIFIER),
    (r"\(", TOKEN_LBRACKET),
    (r"\)", TOKEN_RBRACKET),
    (r"{", TOKEN_LCURLYBRACKET),
    (r"}", TOKEN_RCURLYBRACKET),
    (r"\[", TOKEN_LSTRAIGHTBRACKET),
    (r"\]", TOKEN_RSTRAIGHTBRACKET),
    (r"\.", TOKEN_PERIOD),
    (r"\,", TOKEN_COMMA),
    (r"==", TOKEN_EQUAL),
    (r">", TOKEN_GREATERTHAN),
    (r"<", TOKEN_LESSTHAN),
    (r"=", TOKEN_ASSIGN),
    (r":", TOKEN_COLON),
    (r";", TOKEN_SEMICOLON),
    (r"-", TOKEN_MINUS),
    (r"\+", TOKEN_PLUS),
    (r"\*", TOKEN_ASTERISK),
]

KEYWORDS = [
    "fn",
    "for",
    "import",
    "in",
    "return",
    "True",
    "False",
    "extern",
    "free",
]


class Token:
    def __init__(self, token_type, value, line):
        self.type = token_type
        self.value = value
        self.line = line

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"<{self.type}('{self.value}') @ line {self.line}>"

    def __eq__(self, other):
        return self.type == other

    def __hash__(self):
        return hash(self.type)
