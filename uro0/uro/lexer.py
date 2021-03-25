import logging
import re

from uro.tokens import *


class LexerError(Exception):
    pass


def tokenize(code):
    """Tokenize code."""

    def _find_token(s):
        for rule, token_type in PATTERNS:
            match = re.match(rule, s)
            if match:
                token_value = match.group(0)
                if token_value in KEYWORDS:
                    return TOKEN_KEYWORD, token_value
                else:
                    return token_type, token_value
        return TOKEN_UNKNOWN, s

    tokens = []

    for line_number, line in enumerate(code.split("\n")):
        while line:
            token_type, token_value = _find_token(line)
            if token_type not in {TOKEN_WHITESPACE, TOKEN_COMMENT}:
                token = Token(token_type, token_value, line_number + 1)
                logging.debug("Found token: %s", token)
                tokens.append(token)
            line = line[len(token_value) :]

    return tokens
