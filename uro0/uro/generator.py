import logging

from uro.ir import *


"""This module contains code to generate x84-64 assembly code.

So, we've got an AST which is begging to be converted into something more machine
code-y. The sensible thing to do is to use LLVM, but we've been re-inventing the wheel
with the parsing process, so why take the easy route here?

The AST is first converted into an intermediate representation (IR), which is a list of
`(op, args)` tuples. The IR has no knowledge of any register; it keeps pointers in the
stack and objects in heap memory. This also means that every value is an object, even
integers and booleans are represented as pointers on the stack to objects in heap.

Function calling conventions within the program are:

    * All parameters are pushed to the stack, last parameter is pushed first
    * The return value is stored in rax

However, the stack must be cleaned up after a function call, so:

    * The rsp register must be incremented by 8 times the number of parameters
    * The rax value must be pushed to the stack

These steps are performed in IR_CALL_FUNCTION.
"""


ARCHITECTURE_X86_64_LINUX = "X86_64_LINUX"


class Context:
    def __init__(self, name=None, parent=None):
        self.name = name
        self._variables = {}
        self._parent = parent
        self._position = 0

    @property
    def variables(self):
        """Returns a shallow merge of this scope's variables and the parent's."""
        if self._parent:
            return self.parent.variables | self._variables
        else:
            return self._variables

    @property
    def child(self):
        """Returns a child-context.

        This is a property as any context "parent" could only have a single child at any
        time.
        """
        return Context(parent=self)

    def add_variable(self, name):
        """Adds a variable."""
        self._variables[name] = self._position

    def move_stack_pointer(self):
        """Move the stack pointer over."""
        self._position -= 8

    def get_position(self, name):
        """Returns the position of a given variable."""
        position = self._variables.get(name)
        if not position:
            raise ValueError(f"Unknown variable: {name}")
        return position


class Generator:
    """Turns IR into assemby code for a given CPU architecture."""

    def _factory(architecture=ARCHITECTURE_X86_64_LINUX, *args, **kwargs):
        if architecture == ARCHITECTURE_X86_64_LINUX:
            return GeneratorX86_64Linux(*args, **kwargs)
        raise NotImplementedError(f"Unknown CPU architecture: {architecture}")

    def __new__(cls, *args, **kwargs):
        return cls._factory(*args, **kwargs)


class _Generator:
    def compile(self, ir):
        """Compile an IR to ASM."""
        methods = {
            IR_MAKE_NUMBER: self.make_number,
            IR_EXTERN: self.extern,
            IR_SET_NAME: self.set_name,
            IR_CALL_FUNCTION: self.call_function,
            IR_MAKE_STRING: self.make_string,
            IR_PUSH_REFERENCE: self.push_reference,
        }
        for instr, args in ir:
            if instr != IR_NOP:
                methods[instr](*args)

    def _next_label(self, prefix):
        """Generates a new label for a given prefix."""
        number = self._labels.get(prefix, 1)
        label = f"{prefix}_{number:06d}"
        self._labels[prefix] = number + 1
        return label

    def extern(self, name, param_len):
        """Creates a function object of an external C function."""
        raise NotImplementedError("Please create a concrete implementation")

    def set_name(self, name):
        """Sets a given name to the current top-of-stack."""
        raise NotImplementedError("Please create a concrete implementation")

    def make_string(self, value):
        """Creates a string object and pushes a pointer to it to the stack."""
        raise NotImplementedError("Please create a concrete implementation")

    def make_number(self, value):
        """Creates an integer object and pushes it to the stack."""
        raise NotImplementedError("Please create a concrete implementation")

    def make_boolean(self, value):
        """Creates a boolean object and pushes a pointer to it to the stack."""
        raise NotImplementedError("Please create a concrete implementation")

    def make_dictionary(self, value):
        """Creates a dictionary object and pushes a pointer to it to the stack.

        A dictionary is a linked list of key-value-next structs. The end of the list is
        marked by an empty key-value-next.
        """
        raise NotImplementedError("Please create a concrete implementation")

    def search_dictionary(self, value):
        """Searches a dictionary for a given key and pushes the value."""
        raise NotImplementedError("Please create a concrete implementation")

    def expand_dictionary(self, value):
        """Adds a key-value pair to an existing dictionary."""
        raise NotImplementedError("Please create a concrete implementation")

    def make_function(self, value):
        """Defines a function and pushes a pointer to it to the stack."""
        raise NotImplementedError("Please create a concrete implementation")

    def call_function(self, value):
        """Sets up parameters and calls a function."""
        raise NotImplementedError("Please create a concrete implementation")

    def free_object(self, value):
        """Frees up the memory taken by the object which is referenced."""
        raise NotImplementedError("Please create a concrete implementation")

    def push_reference(self, name):
        """Pushes a given pointer to the stack."""
        raise NotImplementedError("Please create a concrete implementation")


class GeneratorX86_64Linux(_Generator):
    def __init__(self):
        self._global = "main"
        self._extern = []
        self._functions = {
            self._global: [("", "mov", "rbp, rsp")],
            "exit": [
                ("", "mov", "rax, 60"),
                ("", "mov", "rdi, [rsp+8]"),
                ("", "syscall", ""),
            ],
        }
        self._data = {}
        self._labels = {}
        self._context = Context(self._global)

    @property
    def asm(self):
        """Format the assembly code."""

        def _format_line(left, middle, right):
            return f"{left:10s} {middle:10s} {right:10s}\n"

        self._functions[self._global].append(("", "push", "0"))
        self._functions[self._global].append(("", "call", "exit"))

        asm = "; Generated by uro0 compiler - written by Joris Hartog\n"
        asm += _format_line("", "global", self._global)

        for module in self._extern:
            asm += _format_line("", "extern", module)

        asm += _format_line("", "section", ".text")

        for name, function in self._functions.items():
            asm += _format_line(f"{name}:", "", "")
            for line in function:
                asm += _format_line(*line)

        asm += _format_line("", "section", ".data")
        for name, data in self._data.items():
            asm += _format_line(f"{name}: ", "", "")
            asm += _format_line(*data)

        return asm

    def extern(self, name, param_len):
        """Creates a function object of an external C function."""
        if param_len > 4:
            raise NotImplementedError
        if name in self._extern:
            # Already implemented this function
            return None

        label = self._next_label("f")
        self._extern.append(name)
        self._functions[self._context.name].append(("", "mov", f"rax, {label}"))
        self._functions[self._context.name].append(("", "push", "rax"))

        self._functions[label] = [("", "push", "rbp")]
        if param_len > 0:
            self._functions[label].append(("", "push", "rdi"))
        if param_len > 1:
            self._functions[label].append(("", "push", "rsi"))
        if param_len > 2:
            self._functions[label].append(("", "push", "rdx"))
        if param_len > 3:
            self._functions[label].append(("", "push", "rcx"))

        self._functions[label].append(("", "mov", "rbp, rsp"))

        if param_len > 0:
            self._functions[label].append(("", "mov", f"rdi, [rbp+{16+8*param_len}]"))
        if param_len > 1:
            self._functions[label].append(("", "mov", f"rsi, [rbp+{24+8*param_len}]"))
        if param_len > 2:
            self._functions[label].append(("", "mov", f"rdx, [rbp+{32+8*param_len}]"))
        if param_len > 3:
            self._functions[label].append(("", "mov", f"rcx, [rbp+{40+8*param_len}]"))

        self._functions[label].append(("", "call", name))
        self._functions[label].append(("", "mov", "rsp, rbp"))
        if param_len > 3:
            self._functions[label].append(("", "pop", "rcx"))
        if param_len > 2:
            self._functions[label].append(("", "pop", "rdx"))
        if param_len > 1:
            self._functions[label].append(("", "pop", "rsi"))
        if param_len > 0:
            self._functions[label].append(("", "pop", "rdi"))

        self._functions[label].append(("", "pop", "rbp"))
        self._functions[label].append(("", "ret", ""))

        self._context.move_stack_pointer()

    def set_name(self, name):
        """Sets a given name to the current top-of-stack."""
        self._context.add_variable(name)

    def call_function(self, name, args):
        """Sets up parameters and calls a function."""
        self.compile(args)
        position = self._context.get_position(name)
        arg_len = len(args)
        assert position <= 0
        self._functions[self._context.name].append(("", "call", f"[rbp-{-position}]"))
        self._functions[self._context.name].append(("", "add", f"rsp, {8*arg_len}"))
        self._functions[self._context.name].append(("", "push", "rax"))

    def make_string(self, value):
        """Creates a string object and pushes a pointer to it to the stack."""
        string_length = len(value) + 1

        self.extern("malloc", 1)
        self.set_name("malloc")
        self.make_number(string_length)
        self.call_function("malloc", [(IR_NOP, ())])

        string_label = self._next_label("s")
        start_label = self._next_label("l")
        end_label = self._next_label("e")

        self._data[string_label] = ("", "db", f'"{value}", 0')

        self._functions[self._context.name].append(("", "mov", f"rdi, {string_label}"))
        self._functions[self._context.name].append(("", "mov", f"rcx, {string_length}"))
        self._functions[self._context.name].append(("", "xor", "rbx, rbx"))
        self._functions[self._context.name].append(
            (f"{start_label}:", "mov", "bl, byte [rdi]")
        )
        self._functions[self._context.name].append(("", "mov", "byte [rax], bl"))
        self._functions[self._context.name].append(("", "inc", "rax"))
        self._functions[self._context.name].append(("", "inc", "rdi"))
        self._functions[self._context.name].append(("", "dec", "rcx"))
        self._functions[self._context.name].append(("", "cmp", "rcx, byte 0"))
        self._functions[self._context.name].append(("", "je", end_label))
        self._functions[self._context.name].append(("", "jmp", start_label))
        self._functions[self._context.name].append((f"{end_label}:", "", ""))
        self._context.move_stack_pointer()

    def make_number(self, value):
        """Creates an integer object and pushes it to the stack."""
        self._functions[self._context.name].append(("", "push", str(value)))
        self._context.move_stack_pointer()

    def push_reference(self, name):
        """Pushes a given pointer to the stack."""
        position = self._context.get_position(name)
        assert position <= 0
        self._functions[self._context.name].append(
            ("", "mov", f"rax, [rbp-{-position}]")
        )
        self._functions[self._context.name].append(("", "push", "rax"))
        self._context.move_stack_pointer()
