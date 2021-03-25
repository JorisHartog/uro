#!/usr/bin/env python3

"""uro.py - A simple Uro REPL"""

import argparse
import logging

from uro.generator import Generator
from uro.ir import IRGenerator
from uro.lexer import tokenize
from uro.parser import Parser
from uro.repl import Shell


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="Source file", nargs="?", default=None)
    parser.add_argument("--debug", help="Enable debug logs", action="store_true")
    return parser.parse_args()


def main(debug, filename):
    if debug:
        loglevel = logging.DEBUG
        fmt = "[%(filename)12s:%(lineno)4s - %(funcName)45s() ] %(message)s"
    else:
        loglevel = logging.INFO
        fmt = "%(message)s"
    logging.basicConfig(format=fmt, level=loglevel)

    if filename:
        parser = Parser()
        with open(filename, "r") as f:
            code = f.read()
        tokens = tokenize(code)
        parser.add_tokens(tokens)
        assert parser.parse()
        irg = IRGenerator(parser.ast)
        gen = Generator()
        gen.compile(irg.ir)
        print(gen.asm)
    else:
        repl = Shell()
        repl.run()


if "__main__" == __name__:
    args = parse_args()
    main(args.debug, args.filename)
