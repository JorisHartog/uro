import atexit
import logging
import os
import readline

from uro.generator import Generator
from uro.ir import IRGenerator
from uro.lexer import tokenize
from uro.parser import Parser, ParseError, UnexpectedEOF


HEADER = r"""__/\\\________/\\\_____________________________________
__\/\\\_______\/\\\____________________________________
___\/\\\_______\/\\\___________________________________
____\/\\\_______\/\\\__/\\/\\\\\\\______/\\\\\_________
_____\/\\\_______\/\\\_\/\\\/////\\\___/\\\///\\\______
______\/\\\_______\/\\\_\/\\\___\///___/\\\__\//\\\____
_______\//\\\______/\\\__\/\\\_________\//\\\__/\\\____
_________\///\\\\\\\\\/___\/\\\__________\///\\\\\/____
____________\/////////_____\///_____________\/////_____
                   U r o b o r o s
Toy programming language with self-hosting as its goal.
                                Written by Joris Hartog
"""

HISTORY_FILENAME = "~/.uro_history"


class Shell:
    def __init__(self):
        self.prompt = ">>>"
        self.continuation_prompt = "..."
        self.parser = Parser()
        self._init_history(HISTORY_FILENAME)

    def _init_history(self, filename):
        history_file = os.path.expanduser(filename)
        try:
            readline.read_history_file(history_file)
        except IOError:
            pass
        readline.set_history_length(1000)
        atexit.register(self._save_history, history_file)

    def _save_history(self, history_file):
        readline.write_history_file(history_file)

    def run(self):
        """Read -> Eval -> Print -> Loop, you know the drill."""
        print(HEADER)
        continuation = False
        try:
            while True:
                prompt = self.continuation_prompt if continuation else self.prompt
                statement = input(f"{prompt} ")
                continuation, result = self.evaluate(statement)
                if result:
                    print(result)
        except EOFError:
            print("Bye!")
            return

    def evaluate(self, statement):
        """Parses and executes/evaluates a given statement."""
        try:
            tokens = tokenize(statement)
            self.parser.add_tokens(tokens)
            success = self.parser.parse()
            assert success  # A ParseError should be raised on a syntax error
            irg = IRGenerator(self.parser.ast)
            gen = Generator()
            gen.compile(irg.ir)
            return False, gen.asm
        except ParseError as e:
            self.parser.reset()
            logging.error(e)
            return False, None
        except UnexpectedEOF:
            return True, None
