# TBFO-Python-Parser
TBFO Python Parser

## Requirements
This program requires python 3.10.

## Setup
This program is standalone and ready to use, thus requires no setup.

## Usage
To lint a python script file, run
```
py src/linter.py [filepath]
```

## Limitations
There are some keywords, operators, and statements that are not handled by the linter.
Such keywords are (but not limited to) `async`, `await`, `global`, `nonlocal`, `lambda`, `del`, `assert`, `yield`, `try`,
`except`, and `finally`.
This linter is also not handling some of the relatively new python operators such as the matrix
multiplication operator `@`. Some of the relatively new statements that is available in python
are also not handled (e.g. the `match` statement).

## Acknowledgements
--- credit job masing2 & matkul disini

## Known Issues
--- ntar isi kalo ada isu yg ga bisa di resolve