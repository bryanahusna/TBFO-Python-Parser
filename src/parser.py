from enum import Enum
from tokenizer import Tokenizer, Token
from tokens import *


class Parser:
    def __init__(self):
        self.statements = []
        self.lines = []
        self.tokens = []        # type: list[Token]
        self.indent_stack = []

    def parse(self, filename):
        with open(filename) as f:
            for line in f:
                self.lines.append(line)
        tokenizer = Tokenizer()
        self.tokens = tokenizer.tokenize(filename)
        self.parse_indents()
        # for token in self.tokens:
        #     print(token)
        # return

        # TODO: parse statements
        # for each statement, check the grammar

    def parse_indents(self):
        last_token = None           # type: TokenType | None
        indent_stack = []           # type: list[Indent]
        for i in range(len(self.tokens)):
            token = self.tokens[i]
            if last_token == Literal.NEWLINE:
                if token.type == Literal.WHITESPACE:
                    if len(indent_stack) == 0:
                        if ' ' in token.value and '\t' in token.value:
                            raise TabError("Inconsistent indentation")
                        if ' ' in token.value:
                            indent_stack.append(
                                Indent(IndentType.WHITESPACE, len(token.value)))
                        else:
                            indent_stack.append(
                                Indent(IndentType.TAB, len(token.value)))
                        token.type = Indentation.INDENT
                    else:
                        if ' ' in token.value and '\t' in token.value:
                            raise TabError("Inconsistent indentation")
                        indent_type = indent_stack[0].type
                        self.check_indent(token, indent_type)
                        indent_length = self.indent_length(indent_stack)
                        current_indent_length = len(token.value)
                        if current_indent_length > indent_length:
                            indent_stack.append(
                                Indent(indent_type,
                                       current_indent_length - indent_length))
                            token.type = Indentation.INDENT
                        elif current_indent_length < indent_length:
                            token.type = Indentation.DEDENT
                            indent_stack.pop()
                            while current_indent_length < self.indent_length(indent_stack) and len(indent_stack) > 0:
                                self.tokens.insert(i + 1, Token(Indentation.DEDENT, '',
                                                                token.starts_at))
                                indent_stack.pop()
                            if current_indent_length != self.indent_length(indent_stack):
                                raise IndentationError(
                                    "Inconsistent indentation")
            last_token = token.type

    def check_indent(self, token, indent_type):
        char_against = ' ' if indent_type == IndentType.TAB else '\t'
        if char_against in token.value:
            raise TabError("Inconsistent indentation")

    def indent_length(self, indents):
        l = 0
        for indent in indents:
            l += indent.value
        return l

    def parse_statements(self):
        pass


class Indent:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __str__(self):
        char = ' ' if self.type == IndentType.WHITESPACE else '\t'
        string = ''
        for i in range(self.value):
            string = "".join([string, char])
        return string


class IndentType(Enum):
    WHITESPACE = 0
    TAB = 1


# parser = Parser()
# parser.parse("t.py")
