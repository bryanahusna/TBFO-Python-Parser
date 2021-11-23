from tokens import *


class Tokenizer:
    def __init__(self):
        # type: () -> Tokenizer
        self.tokens = []
        self.lines = []
        self.line = 0
        self.col = 0
        self.current_token = None

    def tokenize(self, filename):
        # type: (str) -> list[Token]
        with open(filename, "r") as f:
            for line in f:
                self.lines.append(line)
        self.lines[-1] = "".join([self.lines[-1], '\0'])
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
            token_type = self.current_token.type
            data = self.current_token.data
            if char == '\0':
                if token_type == Transition.CLOSED_STRING:
                    self.current_token.type == Literal.STRING
                elif token_type == Transition.DOUBLE_DOT:
                    raise SyntaxError("")
                self.push_token()
                self.push(char)
            elif token_type == Literal.NAME:
                if char.isalnum() or char == '_':
                    self.current_token.append(char)
                else:
                    name = self.current_token.value
                    if name in keywords.keys():
                        self.current_token = Token(keywords[name], name,
                                                   self.current_token.starts_at)
                    self.push_token()
                    self.push(char)
            elif token_type == Literal.NUMBER:
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
                elif char == "j":
                    self.current_token.append(char)
                    self.push_token()
                elif char.isalpha():
                    print(f"An error found at {self.line + 1}:{self.col + 1}")
                    print(f"Syntax Error : Number literals can't be directly \
                        followed by a name.")
                    exit(1)
                else:
                    self.push_token()
                    self.push(char)
            elif token_type == Literal.STRING:
                if data["escape"]:
                    self.current_token.append(char)
                    self.current_token.set_data("escape", False)
                elif char == "\\":
                    self.current_token.append(char)
                    self.current_token.set_data("escape", True)
                elif char_code == 10:
                    print(f"An error found at {self.line + 1}:{self.col + 1}")
                    print(f"Syntax Error : String literals must be closed between single or \
                            double quotes.")
                    exit(1)
                elif char == data["starts_with"]:
                    self.current_token.append(char)
                    self.current_token = Token(
                        Transition.CLOSED_STRING, self.current_token.value,
                        self.current_token.starts_at)
                    self.current_token.set_data(
                        "starts_with", self.current_token.last_char())
                else:
                    self.current_token.append(char)
            elif token_type == Literal.COMMENT:
                if char_code == 10:
                    self.push_token()
                    self.push(char)
                else:
                    self.current_token.append(char)
            elif token_type == Transition.CLOSED_STRING:
                if char == '"' and self.current_token.value == '""':
                    self.current_token.append(char)
                    self.current_token = Token(
                        Literal.STRING_MULTILINE, self.current_token.value,
                        self.current_token.starts_at)
                    self.current_token.set_data("starts_with", '"')
                    self.current_token.set_data("quotes_trail", 0)
                elif char == "'" and self.current_token.value == "''":
                    self.current_token.append(char)
                    self.current_token = Token(
                        Literal.STRING_MULTILINE, self.current_token.value,
                        self.current_token.starts_at)
                    self.current_token.set_data("starts_with", "'")
                    self.current_token.set_data("quotes_trail", 0)
                else:
                    self.current_token = Token(
                        Literal.STRING, self.current_token.value,
                        self.current_token.starts_at)
                    self.push_token()
                    self.push(char)
            elif token_type == Literal.STRING_MULTILINE:
                self.current_token.append(char)
                if char == data["starts_with"]:
                    trail = data["quotes_trail"]
                    self.current_token.set_data("quotes_trail", trail + 1)
                    if trail == 2:
                        self.push_token()
                else:
                    self.current_token.set_data("quotes_trail", 0)
            elif token_type == Literal.NEWLINE:
                self.push_token()
                self.push(char)
            elif token_type == Literal.WHITESPACE:
                if char_code == 32:
                    self.current_token.append(chr(32))
                else:
                    self.push_token()
                    self.push(char)
            elif token_type == Literal.CR:
                if char_code == 10:
                    self.current_token.append(char)
                    self.current_token = Token(
                        Literal.NEWLINE, self.current_token.value, self.current_token.starts_at)
                    self.push_token()
                else:
                    self.push_token()
                    self.push(char)
            elif token_type == Operator.ADDITION:
                if char == "=":
                    self.current_token = Token(
                        Operator.AUGMENTED_ADDITION, "+=", self.current_token.starts_at)
                else:
                    self.push_token()
                    self.push(char)
            elif token_type == Operator.SUBTRACTION:
                if char == "=":
                    self.current_token = Token(
                        Operator.AUGMENTED_SUBTRACTION, "-=", self.current_token.starts_at)
                else:
                    self.push_token()
                    self.push(char)
            elif token_type == Operator.MULTIPLICATION:
                if char == "=":
                    self.current_token = Token(
                        Operator.AUGMENTED_MULTIPLICATION, "*=", self.current_token.starts_at)
                elif char == "*":
                    self.current_token = Token(
                        Operator.EXPONENTIATION, "**", self.current_token.starts_at)
                else:
                    self.push_token()
                    self.push(char)
            elif token_type == Operator.DIVISION:
                if char == "=":
                    self.current_token = Token(
                        Operator.AUGMENTED_DIVISION, "/=", self.current_token.starts_at)
                else:
                    self.push_token()
                    self.push(char)
            elif token_type == Operator.FLOOR_DIVISION:
                if char == "=":
                    self.current_token = Token(
                        Operator.AUGMENTED_FLOOR_DIVISION, "//=", self.current_token.starts_at)
                else:
                    self.push_token()
                    self.push(char)
            elif token_type == Operator.EXPONENTIATION:
                if char == "=":
                    self.current_token = Token(
                        Operator.AUGMENTED_EXPONENTIATION, "**=", self.current_token.starts_at)
                else:
                    self.push_token()
                    self.push(char)
            elif token_type == Operator.MODULUS:
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
                        Operator.AUGMENTED_MODULUS, "%=", self.current_token.starts_at)
                    self.push_token()
                else:
                    self.push_token()
                    self.push(char)
            elif token_type == Operator.EQUAL:
                self.push_token()
                self.push(char)
            elif token_type == Operator.NOT_EQUAL:
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
            elif token_type == Operator.GREATER_THAN:
                if char == "=":
                    self.current_token = Token(
                        Operator.GREATER_EQUAL, ">=", self.current_token.starts_at)
                    self.push_token()
                elif char == ">":
                    self.current_token = Token(
                        Operator.BITWISE_RIGHT_SHIFT, ">>", self.current_token.starts_at)
                else:
                    self.push_token()
                    self.push(char)
            elif token_type == Operator.LESS_THAN:
                if char == "=":
                    self.current_token = Token(
                        Operator.LESS_EQUAL, "<=", self.current_token.starts_at)
                elif char == "<":
                    self.current_token = Token(
                        Operator.BITWISE_RIGHT_SHIFT, "<<", self.current_token.starts_at)
                else:
                    self.push_token()
                    self.push(char)
            elif token_type == Operator.GREATER_EQUAL:
                self.push_token()
                self.push(char)
            elif token_type == Operator.LESS_EQUAL:
                self.push_token()
                self.push(char)
            elif token_type == Operator.ASSIGNMENT:
                if char == "=":
                    self.current_token = Token(Operator.EQUAL, "==",
                                               self.current_token.starts_at)
                else:
                    self.push_token()
                    self.push(char)
            elif token_type == Operator.BITWISE_AND:
                if char == "=":
                    self.current_token = Token(
                        Operator.AUGMENTED_BITWISE_AND, "&=",
                        self.current_token.starts_at)
                else:
                    self.push_token()
                    self.push(char)
            elif token_type == Operator.BITWISE_OR:
                if char == "=":
                    self.current_token = Token(
                        Operator.AUGMENTED_BITWISE_OR, "|=",
                        self.current_token.starts_at)
                else:
                    self.push_token()
                    self.push(char)
            elif token_type == Operator.BITWISE_XOR:
                if char == "=":
                    self.current_token = Token(
                        Operator.AUGMENTED_BITWISE_XOR, "^=",
                        self.current_token.starts_at)
                else:
                    self.push_token()
                    self.push(char)
            elif token_type == Operator.BITWISE_NOT:
                self.push_token()
                self.push(char)
            elif token_type == Operator.BITWISE_LEFT_SHIFT:
                if char == "=":
                    self.current_token = Token(
                        Operator.AUGMENTED_BITWISE_LEFT_SHIFT, "<<=",
                        self.current_token.starts_at)
                else:
                    self.push_token()
                    self.push(char)
            elif token_type == Operator.BITWISE_RIGHT_SHIFT:
                if char == "=":
                    self.current_token = Token(
                        Operator.AUGMENTED_BITWISE_RIGHT_SHIFT, ">>=",
                        self.current_token.starts_at)
                else:
                    self.push_token()
                    self.push(char)
            elif token_type == Operator.AUGMENTED_ADDITION:
                self.push_token()
                self.push(char)
            elif token_type == Operator.AUGMENTED_SUBTRACTION:
                self.push_token()
                self.push(char)
            elif token_type == Operator.AUGMENTED_MULTIPLICATION:
                self.push_token()
                self.push(char)
            elif token_type == Operator.AUGMENTED_DIVISION:
                self.push_token()
                self.push(char)
            elif token_type == Operator.AUGMENTED_FLOOR_DIVISION:
                self.push_token()
                self.push(char)
            elif token_type == Operator.AUGMENTED_EXPONENTIATION:
                self.push_token()
                self.push(char)
            elif token_type == Operator.AUGMENTED_MODULUS:
                self.push_token()
                self.push(char)
            elif token_type == Operator.AUGMENTED_BITWISE_AND:
                self.push_token()
                self.push(char)
            elif token_type == Operator.AUGMENTED_BITWISE_OR:
                self.push_token()
                self.push(char)
            elif token_type == Operator.AUGMENTED_BITWISE_XOR:
                self.push_token()
                self.push(char)
            elif token_type == Operator.AUGMENTED_BITWISE_LEFT_SHIFT:
                self.push_token()
                self.push(char)
            elif token_type == Operator.AUGMENTED_BITWISE_RIGHT_SHIFT:
                self.push_token()
                self.push(char)
            elif token_type == Punctuation.ACCESSOR:
                if char == '.':
                    self.append(char)
                    self.current_token.type = Transition.DOUBLE_DOT
                else:
                    self.push_token()
                    self.push(char)
            elif token_type == Transition.DOUBLE_DOT:
                if char == '.':
                    self.append(char)
                    self.current_token.type = Literal.ELLIPSIS
                else:
                    raise SyntaxError("")
        else:
            if char_code == 0:
                self.current_token = Token(Literal.ENDMARKER,
                                           char, (self.line, self.col))
                self.push_token()
            elif char_code == 10:
                self.current_token = Token(
                    Literal.NEWLINE, char, (self.line, self.col))
            elif char_code == 13:
                self.current_token = Token(Literal.CR, char)
            elif char_code == 32 or char == "\t":
                self.current_token = Token(
                    Literal.WHITESPACE, char, (self.line, self.col))
            elif char_code == 33:
                self.current_token = Token(
                    Operator.NOT_EQUAL, char, (self.line, self.col))
                self.current_token.set_data("is_completed", False)
            elif char_code == 34:
                self.current_token = Token(
                    Literal.STRING, char, (self.line, self.col))
                self.current_token.set_data("starts_with", char)
                self.current_token.set_data("escape", False)
            elif char_code == 35:
                self.current_token = Token(
                    Literal.COMMENT, char, (self.line, self.col))
            elif char_code == 37:
                self.current_token = Token(
                    Operator.MODULUS, char, (self.line, self.col))
            elif char_code == 38:
                self.current_token = Token(
                    Operator.BITWISE_AND, char, (self.line, self.col))
            elif char_code == 39:
                self.current_token = Token(
                    Literal.STRING, char, (self.line, self.col))
                self.current_token.set_data("starts_with", char)
                self.current_token.set_data("escape", False)
            elif char_code == 40:
                self.current_token = Token(
                    Punctuation.PARENTHESIS_OPEN, char, (self.line, self.col))
                self.push_token()
            elif char_code == 41:
                self.current_token = Token(
                    Punctuation.PARENTHESIS_CLOSE, char, (self.line, self.col))
                self.push_token()
            elif char_code == 42:
                self.current_token = Token(
                    Operator.MULTIPLICATION, char, (self.line, self.col))
            elif char_code == 43:
                self.current_token = Token(
                    Operator.ADDITION, char, (self.line, self.col))
            elif char_code == 44:
                self.current_token = Token(
                    Punctuation.COMMA, char, (self.line, self.col)
                )
                self.push_token()
            elif char_code == 45:
                if (self.has_token() and self.last_not_whitespace_token().type == Literal.NUMBER):
                    self.current_token = Token(
                        Operator.SUBTRACTION, char, (self.line, self.col))
                else:
                    self.current_token = Token(
                        Literal.NUMBER, char, (self.line, self.col))
                    self.current_token.set_data("negative", True)
                    self.current_token.set_data("past_decimal", False)
                    self.current_token.set_data("has_read_numbers", False)
            elif char_code == 46:
                self.current_token = Token(
                    Punctuation.ACCESSOR, char, (self.line, self.col))
            elif char_code == 47:
                self.current_token = Token(
                    Operator.DIVISION, char, (self.line, self.col))
            elif char.isnumeric():
                self.current_token = Token(
                    Literal.NUMBER, char, (self.line, self.col))
                self.current_token.set_data("negative", False)
                self.current_token.set_data("past_decimal", False)
            elif char_code == 58:
                self.current_token = Token(
                    Punctuation.COLON, char, (self.line, self.col))
                self.push_token()
            elif char_code == 60:
                self.current_token = Token(
                    Operator.LESS_THAN, char, (self.line, self.col))
            elif char_code == 61:
                self.current_token = Token(
                    Operator.ASSIGNMENT, char, (self.line, self.col))
            elif char_code == 62:
                self.current_token = Token(
                    Operator.GREATER_THAN, char, (self.line, self.col))
            elif char.isalpha() or char_code == 95:
                self.current_token = Token(
                    Literal.NAME, char, (self.line, self.col))
            elif char_code == 91:
                self.current_token = Token(
                    Punctuation.SQUARE_BRACKET_OPEN, char, (self.line, self.col))
                self.push_token()
            elif char_code == 93:
                self.current_token = Token(
                    Punctuation.SQUARE_BRACKET_CLOSE, char, (self.line, self.col))
                self.push_token()
            elif char_code == 94:
                self.current_token = Token(
                    Operator.BITWISE_XOR, char, (self.line, self.col))
            elif char_code == 123:
                self.current_token = Token(
                    Punctuation.BRACKET_OPEN, char, (self.line, self.col))
                self.push_token()
            elif char_code == 124:
                self.current_token = Token(
                    Operator.BITWISE_OR, char, (self.line, self.col))
            elif char_code == 125:
                self.current_token = Token(
                    Punctuation.BRACKET_CLOSE, char, (self.line, self.col))
                self.push_token()
            elif char_code == 126:
                self.current_token = Token(
                    Operator.BITWISE_NOT, char, (self.line, self.col))
            else:
                print(f"Exception : Found unhandled character {char}")

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
    def __init__(self, type, value, start):
        # type: (TokenType, str, tuple[int, int]) -> Token
        self.type = type
        self.value = value
        self.data = {}
        self.starts_at = start

    def __str__(self):
        value = self.value.replace("\n", "\\n")
        value = value.replace("\r", "\\r")
        value = value.replace("\t", "\\t")
        return f"Token <type = {self.type}, value = \"{value}\">"

    def set_data(self, key, value):
        self.data[key] = value

    def delete_data(self, key):
        del self.data[key]

    def last_char(self):
        return self.value[-1]

    def append(self, value):
        self.value = "".join([self.value, value])

    def is_opening_bracket(self):
        return self.type in brackets_opening

    def is_closing_bracket(self):
        return self.type in brackets_closing


# Used for debugging purposes
# tokenizer = Tokenizer()
# for token in tokenizer.tokenize("t.py"):
#     print(token)
