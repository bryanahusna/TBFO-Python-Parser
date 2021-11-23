from enum import Enum


class Literal(Enum):
    NAME = 0
    NUMBER = 1
    STRING = 2
    COMMENT = 3
    STRING_MULTILINE = 4
    NEWLINE = 5
    WHITESPACE = 6
    CR = 7
    ELLIPSIS = 9
    ENDMARKER = 10


class Punctuation(Enum):
    COLON = 101
    PARENTHESIS_OPEN = 102
    PARENTHESIS_CLOSE = 103
    BRACKET_OPEN = 104
    BRACKET_CLOSE = 105
    SQUARE_BRACKET_OPEN = 106
    SQUARE_BRACKET_CLOSE = 107
    ACCESSOR = 108
    COMMA = 109


class Keyword(Enum):
    DEF = 200
    CLASS = 201
    FALSE = 202
    TRUE = 203
    IS = 204
    RETURN = 205
    NONE = 206
    CONTINUE = 207
    FOR = 208
    FROM = 209
    WHILE = 210
    WITH = 211
    AS = 212
    IF = 213
    ELIF = 214
    ELSE = 215
    IMPORT = 216
    PASS = 217
    BREAK = 218
    IN = 219
    RAISE = 220
    AND = 221
    OR = 222
    NOT = 223


class Operator(Enum):
    ADDITION = 401
    SUBTRACTION = 402
    MULTIPLICATION = 403
    DIVISION = 404
    FLOOR_DIVISION = 405
    EXPONENTIATION = 406
    MODULUS = 407
    EQUAL = 408
    NOT_EQUAL = 409
    GREATER_THAN = 410
    LESS_THAN = 411
    GREATER_EQUAL = 412
    LESS_EQUAL = 413
    ASSIGNMENT = 414
    BITWISE_AND = 415
    BITWISE_OR = 416
    BITWISE_XOR = 417
    BITWISE_NOT = 418
    BITWISE_LEFT_SHIFT = 419
    BITWISE_RIGHT_SHIFT = 420
    AUGMENTED_ADDITION = 421
    AUGMENTED_SUBTRACTION = 422
    AUGMENTED_MULTIPLICATION = 423
    AUGMENTED_DIVISION = 424
    AUGMENTED_FLOOR_DIVISION = 425
    AUGMENTED_EXPONENTIATION = 426
    AUGMENTED_MODULUS = 427
    AUGMENTED_BITWISE_AND = 428
    AUGMENTED_BITWISE_OR = 429
    AUGMENTED_BITWISE_XOR = 430
    AUGMENTED_BITWISE_LEFT_SHIFT = 431
    AUGMENTED_BITWISE_RIGHT_SHIFT = 432


class Transition(Enum):
    DOUBLE_DOT = 900
    CLOSED_STRING = 901


class Indentation(Enum):
    INDENT = 300
    DEDENT = 301


TokenType = Literal | Punctuation | Keyword | Operator | Indentation

keywords = {
    "def": Keyword.DEF,
    "class": Keyword.CLASS,
    "False": Keyword.FALSE,
    "True": Keyword.TRUE,
    "is": Keyword.IS,
    "return": Keyword.RETURN,
    "None": Keyword.NONE,
    "continue": Keyword.CONTINUE,
    "for": Keyword.FOR,
    "from": Keyword.FROM,
    "while": Keyword.WHILE,
    "with": Keyword.WITH,
    "as": Keyword.AS,
    "if": Keyword.IF,
    "elif": Keyword.ELIF,
    "else": Keyword.ELSE,
    "import": Keyword.IMPORT,
    "pass": Keyword.PASS,
    "break": Keyword.BREAK,
    "in": Keyword.IN,
    "raise": Keyword.RAISE,
    "and": Keyword.AND,
    "or": Keyword.OR,
    "not": Keyword.NOT
}

brackets_opening = [
    Punctuation.PARENTHESIS_OPEN,
    Punctuation.BRACKET_OPEN,
    Punctuation.SQUARE_BRACKET_OPEN
]

brackets_closing = [
    Punctuation.PARENTHESIS_CLOSE,
    Punctuation.BRACKET_CLOSE,
    Punctuation.SQUARE_BRACKET_CLOSE
]
