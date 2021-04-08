# Uroboros (`uro`)

Uro is a compiled, loosely-typed, branchless toy programming language which is designed
to easily implement a self-hosted compiler.

The bare-minimum features will be implemented in the language itself, while extra tools
needed to easily create a self-hosted compiler (e.g. a regex parser) are created in the
standard library.


## Quirks

* There are only strings, integers, booleans, dictionaries and functions
* Classes and objects are dictionaries
  * Methods are just key-value pairs where the value is a function
* If-statements are dictionaries
  * `{True: do_true, False: do_false}[1+1==2]()`
  * This means that uro is a branchless programming language
* There are no lists
  * A list could be implemented as a dictionary with integer keys
  * A linked list can be implemented as a set of objects (dictionaries)
* Any feature beyond the bare minimum needed for the compiler will be written in uro
* The stage-1 compiler (uro0) will compile to x86-64 assembly, uro might use LLVM-IR.


## Roadmap

The development of this language will be in stages:

| Reached | Version | Name | Description                               | Language |
|---------|---------|------|-------------------------------------------|----------|
| ⌛      | 0.1.0   | uro0 | A compiler for the bare-minimum language. | Python   |
| 🛑      | < 1.0.0 | std  | A standard library.                       | Uro0     |
| 🛑      | 1.0.0   | uro  | The self-hosted interpreter.              | Uro0     |
| 🛑      | > 1.0.0 | uro  | New language features.                    | Uro      |

| Icon | Meaning        |
|------|----------------|
| 🛑   | Hasn't started |
| ⌛   | In progress    |
| ✅   | Done           |


## Example syntax

```uro
from std import new, printf, if

# The standard library could contain functions like `new`, which act as OOP helpers:
#
#  > ## copy - creates a deep copy of a dictionary
#  > copy = fn (obj) {
#  >     new_obj = {};
#  >
#  >     # `for` gives keys of a dictionary or characters from a string
#  >     for key in obj {
#  >         new_obj[key] = obj[key];
#  >     };
#  >
#  >     return new_obj;
#  > };
#  >
#  > ## new - Initializes an object
#  > new = fn (class, kwargs) {
#  >     obj = copy(class);
#  >     obj['_init'](obj, kwargs);
#  >     return obj;
#  > };
#  >
#  > ## if - Executes a function if a condition is True
#  > if = fn (cond, func) {
#  >     return { True: func }[cond]();
#  > };
#

## Person - A Person does this and that
# :params:
#   name - The name of the person
Person = {
    '_init': fn (self, kwargs) {
        self['name'] = kwargs['name'];
        self['species'] = 'Human';
    },
    'greet': fn (self) {
        printf("Hi, fellow {a}! I'm {b}!\n", {a: self['species'], b: self['name']});
    },
};


bob = new(Person, 'Bob');

if (bob['species'] == 'Human', fn () {
    bob['greet'](bob);  # => 'Hi, fellow Human! I'm Bob!\n'
});

# Inline ASM is also possible
open = fn(filename, flags, mode) {
    asm("pop rdx");   # int mode
    asm("pop rsi");   # int flags
    asm("pop rdi");   # const char *filename
    asm("mov rax,2"); # sys_open
    asm("syscall");   # rax contains file descriptor
};
```
