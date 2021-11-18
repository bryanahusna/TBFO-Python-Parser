from enum import Enum


class Tokenizer:
    def __init__(self):
        self.tokens = []
        self.lines = []
        self.line = 0
        self.col = 0
        self.current_token = None

    def tokenize(self, filename):
        with open(filename, "r") as f:
            for line in f:
                self.lines.append(line)
        while self.line < len(self.lines):
            line = self.lines[self.line]
            line_length = len(line)
            while self.col < line_length:
                self.push(self.lines[self.line][self.col])
                self.col += 1
            self.line += 1
            self.col = 0
        return self.tokens

    def push(self, char: str):
        char_code = ord(char)
        if (self.has_current_token()):
            type = self.current_token.type
            data = self.current_token.data
            if type == Literal.NAME:
                if char.isalnum() or char == '_':
                    self.current_token.append(char)
                else:
                    name = self.current_token.value
                    if name in keywords.keys():
                        self.current_token = Token(keywords[name], name)
                    self.push_token()
                    self.push(char)
            elif type == Literal.NUMBER:
                if char.isnumeric():
                    self.current_token.append(char)
                    if data["negative"] and not data["has_read_numbers"]:
                        self.current_token.set_data("has_read_numbers", True)
                elif char == "." and not data["past_decimal"]:
                    self.current_token.append(char)
                    self.current_token.set_data("past_decimal", True)
                    if data["negative"] and not data["has_read_numbers"]:
                        self.current_token.set_data("has_read_numbers", True)
                elif char == " " and data["negative"] and not data["has_read_numbers"]:
                    self.current_token.append(char)
                else:
                    self.push_token()
                    self.push(char)
            elif type == Literal.STRING:
                if char_code == 10:
                    raise SyntaxError(
                        f"String literals must be closed between single or \
                            double quotes {self.line}:{self.col}")
                elif char == data["starts_with"]:
                    self.current_token.append(char)
                    self.current_token = Token(
                        Literal.CLOSED_STRING, self.current_token.value)
                    self.current_token.set_data(
                        "starts_with", self.current_token.last_char())
                else:
                    self.current_token.append(char)
            elif type == Literal.COMMENT:
                if char_code == 10:
                    self.push_token()
                    self.push(char)
                else:
                    self.current_token.append(char)
            elif type == Literal.CLOSED_STRING:
                if char == '"' and self.current_token.value == '""':
                    self.current_token.append(char)
                    self.current_token = Token(
                        Literal.STRING_MULTILINE, self.current_token.value)
                    self.current_token.set_data("starts_with", '"')
                    self.current_token.set_data("quotes_trail", 0)
                elif char == "'" and self.current_token.value == "''":
                    self.current_token.append(char)
                    self.current_token = Token(
                        Literal.STRING_MULTILINE, self.current_token.value)
                    self.current_token.set_data("starts_with", "'")
                    self.current_token.set_data("quotes_trail", 0)
                else:
                    self.current_token = Token(
                        Literal.STRING, self.current_token.value)
                    self.push_token()
                    self.push(char)
            elif type == Literal.STRING_MULTILINE:
                if char == "\n":
                    char = "\\n"
                self.current_token.append(char)
                if char == data["starts_with"]:
                    trail = data["quotes_trail"]
                    self.current_token.set_data("quotes_trail", trail + 1)
                    if trail == 2:
                        self.push_token()
                else:
                    self.current_token.set_data("quotes_trail", 0)
            elif type == Literal.NEWLINE:
                self.push_token()
                self.push(char)
            elif type == Literal.WHITESPACE:
                if char_code == 32:
                    self.current_token.append(chr(32))
                else:
                    self.push_token()
                    self.push(char)
            elif type == Literal.CR:
                if char_code == 10:
                    self.current_token = Token(Literal.NEWLINE, "\\r\\n")
                    self.push_token()
                else:
                    self.push_token()
                    self.push(char)
            elif type == Operator.ADDITION:
                if char == "=":
                    self.current_token = Token(
                        Operator.AUGMENTED_ADDITION, "+=")
                else:
                    self.push_token()
                    self.push(char)
            elif type == Operator.SUBTRACTION:
                if char == "=":
                    self.current_token = Token(
                        Operator.AUGMENTED_SUBTRACTION, "-=")
                else:
                    self.push_token()
                    self.push(char)
            elif type == Operator.MULTIPLICATION:
                if char == "=":
                    self.current_token = Token(
                        Operator.AUGMENTED_MULTIPLICATION, "*=")
                else:
                    self.push_token()
                    self.push(char)
            elif type == Operator.DIVISION:
                if char == "=":
                    self.current_token = Token(
                        Operator.AUGMENTED_DIVISION, "/=")
                else:
                    self.push_token()
                    self.push(char)
            elif type == Operator.FLOOR_DIVISION:
                if char == "=":
                    self.current_token = Token(
                        Operator.AUGMENTED_FLOOR_DIVISION, "//=")
                else:
                    self.push_token()
                    self.push(char)
            elif type == Operator.EXPONENTIATION:
                if char == "=":
                    self.current_token = Token(
                        Operator.AUGMENTED_EXPONENTIATION, "**=")
                else:
                    self.push_token()
                    self.push(char)
            elif type == Operator.MODULUS:
                if char_code == 10:
                    raise SyntaxError(
                        f"Modulus operators takes 2 arguments, but only found 1 (at {self.line}:{self.col}).")
                elif char.isnumeric():
                    self.push_token()
                    self.push(char)
                elif char.isalpha():
                    self.push_token()
                    self.push(char)
                elif char_code == 61:
                    self.current_token = Token(
                        Operator.AUGMENTED_MODULUS, "%=")
                    self.push_token()
                else:
                    self.push_token()
                    self.push(char)
            elif type == Operator.EQUAL:
                self.push_token()
                self.push(char)
            elif type == Operator.NOT_EQUAL:
                if data["is_completed"]:
                    self.push_token()
                    self.push(char)
                elif char_code == 61:
                    self.current_token.append(chr(61))
                    self.current_token.delete_data("is_completed")
                    self.push_token()
                else:
                    raise SyntaxError(
                        f"Invalid character at line {self.line}:{self.col}")
            elif type == Operator.GREATER_THAN:
                if char == "=":
                    self.current_token = Token(Operator.GREATER_EQUAL, ">=")
                    self.push_token()
                else:
                    self.push_token()
                    self.push(char)
            elif type == Operator.LESS_THAN:
                if char == "=":
                    self.current_token = Token(Operator.LESS_EQUAL, "<=")
                else:
                    self.push_token()
                    self.push(char)
            elif type == Operator.GREATER_EQUAL:
                self.push_token()
                self.push(char)
            elif type == Operator.LESS_EQUAL:
                self.push_token()
                self.push(char)
            elif type == Operator.ASSIGNMENT:
                if char == "=":
                    self.current_token = Token(Operator.EQUAL, "==")
                else:
                    self.push_token()
                    self.push(char)
            elif type == Operator.BITWISE_AND:
                if char == "=":
                    self.current_token = Token(
                        Operator.AUGMENTED_BITWISE_AND, "&=")
                else:
                    self.push_token()
                    self.push(char)
            elif type == Operator.BITWISE_OR:
                if char == "=":
                    self.current_token = Token(
                        Operator.AUGMENTED_BITWISE_OR, "|=")
                else:
                    self.push_token()
                    self.push(char)
            elif type == Operator.BITWISE_XOR:
                if char == "=":
                    self.current_token = Token(
                        Operator.AUGMENTED_BITWISE_XOR, "^=")
                else:
                    self.push_token()
                    self.push(char)
            elif type == Operator.BITWISE_NOT:
                self.push_token()
                self.push(char)
            elif type == Operator.BITWISE_LEFT_SHIFT:
                if char == "=":
                    self.current_token = Token(
                        Operator.AUGMENTED_BITWISE_LEFT_SHIFT, "<<=")
                else:
                    self.push_token()
                    self.push(char)
            elif type == Operator.BITWISE_RIGHT_SHIFT:
                if char == "=":
                    self.current_token = Token(
                        Operator.AUGMENTED_BITWISE_RIGHT_SHIFT, ">>=")
                else:
                    self.push_token()
                    self.push(char)
            elif type == Operator.AUGMENTED_ADDITION:
                self.push_token()
                self.push(char)
            elif type == Operator.AUGMENTED_SUBTRACTION:
                self.push_token()
                self.push(char)
            elif type == Operator.AUGMENTED_MULTIPLICATION:
                self.push_token()
                self.push(char)
            elif type == Operator.AUGMENTED_DIVISION:
                self.push_token()
                self.push(char)
            elif type == Operator.AUGMENTED_FLOOR_DIVISION:
                self.push_token()
                self.push(char)
            elif type == Operator.AUGMENTED_EXPONENTIATION:
                self.push_token()
                self.push(char)
            elif type == Operator.AUGMENTED_MODULUS:
                self.push_token()
                self.push(char)
            elif type == Operator.AUGMENTED_BITWISE_AND:
                self.push_token()
                self.push(char)
            elif type == Operator.AUGMENTED_BITWISE_OR:
                self.push_token()
                self.push(char)
            elif type == Operator.AUGMENTED_BITWISE_XOR:
                self.push_token()
                self.push(char)
            elif type == Operator.AUGMENTED_BITWISE_LEFT_SHIFT:
                self.push_token()
                self.push(char)
            elif type == Operator.AUGMENTED_BITWISE_RIGHT_SHIFT:
                self.push_token()
                self.push(char)
        else:
            if char_code == 10:
                self.current_token = Token(Literal.NEWLINE, "\\n")
            elif char_code == 13:
                self.current_token = Token(Literal.CR, "\\r")
            elif char_code == 32:
                self.current_token = Token(Literal.WHITESPACE, char)
            elif char_code == 33:
                self.current_token = Token(Operator.NOT_EQUAL, char)
                self.current_token.set_data("is_completed", False)
            elif char_code == 34:
                self.current_token = Token(Literal.STRING, char)
                self.current_token.set_data("starts_with", char)
            elif char_code == 35:
                self.current_token = Token(Literal.COMMENT, char)
            elif char_code == 37:
                self.current_token = Token(Operator.MODULUS, char)
            elif char_code == 38:
                self.current_token = Token(Operator.BITWISE_AND, char)
            elif char_code == 39:
                self.current_token = Token(Literal.STRING, char)
                self.current_token.set_data("starts_with", char)
            elif char_code == 40:
                self.current_token = Token(
                    Punctuation.PARENTHESIS_OPEN, char)
                self.push_token()
            elif char_code == 41:
                self.current_token = Token(
                    Punctuation.PARENTHESIS_CLOSE, char)
                self.push_token()
            elif char_code == 42:
                self.current_token = Token(Operator.MULTIPLICATION, char)
            elif char_code == 43:
                self.current_token = Token(Operator.ADDITION, char)
            elif char_code == 45:
                if (self.has_token() and self.last_not_whitespace_token().type == Literal.NUMBER):
                    self.current_token = Token(
                        Operator.SUBTRACTION, char)
                else:
                    self.current_token = Token(Literal.NUMBER, char)
                    self.current_token.set_data("negative", True)
                    self.current_token.set_data("past_decimal", False)
                    self.current_token.set_data("has_read_numbers", False)
            elif char_code == 46:
                self.current_token = Token(Punctuation.ACCESSOR, char)
                self.push_token()
            elif char_code == 47:
                self.current_token = Token(Operator.DIVISION, char)
            elif char.isnumeric():
                self.current_token = Token(Literal.NUMBER, char_code - 48)
                self.current_token.set_data("negative", False)
                self.current_token.set_data("past_decimal", False)
            elif char_code == 58:
                self.current_token = Token(Punctuation.COLON, char)
                self.push_token()
            elif char_code == 60:
                self.current_token = Token(Operator.LESS_THAN, char)
            elif char_code == 61:
                self.current_token = Token(Operator.ASSIGNMENT, char)
            elif char.isalpha() or char_code == 95:
                self.current_token = Token(Literal.NAME, char)
            elif char_code == 91:
                self.current_token = Token(
                    Punctuation.SQUARE_BRACKET_OPEN, char)
                self.push_token()
            elif char_code == 93:
                self.current_token = Token(
                    Punctuation.SQUARE_BRACKET_OPEN, char)
                self.push_token()
            elif char_code == 94:
                self.current_token = Token(Operator.BITWISE_XOR, char)
            elif char_code == 123:
                self.current_token = Token(Punctuation.BRACKET_OPEN, char)
                self.push_token()
            elif char_code == 124:
                self.current_token = Token(Operator.BITWISE_OR, char)
            elif char_code == 125:
                self.current_token = Token(Punctuation.BRACKET_CLOSE, char)
                self.push_token()
            elif char_code == 126:
                self.current_token = Token(Operator.BITWISE_NOT, char)

    def push_token(self):
        self.tokens.append(self.current_token)
        self.reset_token()

    def next_line(self):
        for line in self.file:
            yield line

    def next(self):
        c = self.current_line[self.col - 1]
        self.col += 1
        return c

    def has_current_token(self):
        return self.current_token != None

    def has_token(self):
        return len(self.tokens) != 0

    def reset_token(self):
        self.current_token = None

    def last_token(self):
        return self.tokens[-1]

    def last_not_whitespace_token(self):
        index = len(self.tokens) - 1
        while index > 0:
            token = self.tokens[index]
            if token.type == Literal.NEWLINE:
                return None
            if token.type != Literal.WHITESPACE:
                return token
            index -= 1
        return None


class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value
        self.data = {}

    def __str__(self):
        return f"Token <type = {self.type}, value = \"{self.value}\">"

    def set_data(self, key, value):
        self.data[key] = value

    def delete_data(self, key):
        del self.data[key]

    def last_char(self):
        return self.value[-1]

    def append(self, value):
        self.value = "".join([self.value, value])


class Literal(Enum):
    NAME = 0
    NUMBER = 1
    STRING = 2
    COMMENT = 3
    STRING_MULTILINE = 4
    NEWLINE = 5
    WHITESPACE = 6
    CR = 7
    CLOSED_STRING = 8


class Punctuation(Enum):
    COLON = 101
    PARENTHESIS_OPEN = 102
    PARENTHESIS_CLOSE = 103
    BRACKET_OPEN = 104
    BRACKET_CLOSE = 105
    SQUARE_BRACKET_OPEN = 106
    SQUARE_BRACKET_CLOSE = 107
    ACCESSOR = 108


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
