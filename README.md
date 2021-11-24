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

## Contributors
All thanks goes to these people that contribute to this project.
* [Hafidz Nur Rahman Ghozali](https://github.com/hafidznrg) (13520117)
* [Bryan Amirul Husna](https://github.com/bryanahusna) (13520146)
* [Raden Rifqi Rahman](https://github.com/Radenz) (13520166)