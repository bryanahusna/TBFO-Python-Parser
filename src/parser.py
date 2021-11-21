from enum import Enum
from os import stat
from tokenizer import Tokenizer, Token
from tokens import *


class Parser:
    def __init__(self):
        self.statements = []
        self.lines = []
        self.tokens = []        # type: list[Token]
        self.indent_stack = []
        self.statement = []

    def parse(self, filename):
        with open(filename) as f:
            for line in f:
                self.lines.append(line)
        tokenizer = Tokenizer()
        self.tokens = tokenizer.tokenize(filename)
        self.parse_indents()

        self.grammar_stack = []
        self.tries = []
        self.try_index_trace = []
        self.required_input = []
        self.index = 0
        token = self.tokens[self.index]
        # TODO : Ganti cara pembacaan jadi tiap satu
        # statement atau block
        while token.type != Literal.ENDMARKER:
            if len(self.grammar_stack) == 0:
                if len(self.required_input) == 0:
                    if token.type in [Keyword.PASS,
                                      Keyword.BREAK, Keyword.CONTINUE]:
                        self.required_input.append(Literal.NEWLINE)
                        token, self.index = self.skip_whitespaces(
                            self.index + 1)
                    elif token.type == Keyword.RAISE:
                        self.tries.append()
                    elif token.type == Keyword.IMPORT:
                        self.tries.append()
                else:
                    next = self.required_input[-1]
                    if token.type != next:
                        raise SyntaxError()
                    else:
                        self.required_input.pop()
                        token, self.index = self.skip_whitespaces(
                            self.index + 1)
            else:
                pass
                # def parse(self, filename):
                #     with open(filename) as f:
                #         for line in f:
                #             self.lines.append(line)
                #     tokenizer = Tokenizer()
                #     self.tokens = tokenizer.tokenize(filename)
                #     self.parse_indents()
                #     self.parse_statements()
                #     # self.check_statements()
                #     self.parse_block(self.statements)

    def skip_whitespaces(self, index):
        token = self.tokens[index]
        while token.type == Literal.WHITESPACE:
            index += 1
            token = self.tokens[index]
        return token, index

    def parse_block(self, block, index=[0]):
        for i in range(len(block)):
            statement = block[i]
            if self.statement_type(statement) == "block":
                self.parse_block(statement)
            else:
                self.parse_simple_statement(statement)

    def parse_simple_statement(self, statement):
        first_token = statement[0]      # type: Token

        # TODO: Cek setiap token awal yang mungkin sebagai
        # simple_statement

        if first_token.type == Literal.NEWLINE:
            pass
        elif first_token.type == Keyword.PASS:
            pass

    def parse_compound_statement(self, statement):
        # TODO: Cek setiap token awal yang mungkin sebagai
        # simple_statement
        pass

    def whitespace_only_until(self, index):
        statement = self.statement
        for i in range(index):
            token = statement[i]
            if token not in [Literal.WHITESPACE, Indentation.INDENT, Indentation.DEDENT]:
                return False
        return True

    def parse_indents(self):
        last_token = None           # type: TokenType | None
        indent_stack = []           # type: list[Indent]
        i = 0
        while i < len(self.tokens):
            token = self.tokens[i]
            if token.type == Literal.ENDMARKER:
                end_marker = self.tokens.pop()
                for j in range(len(indent_stack)):
                    self.tokens.append(Token(
                        Indentation.DEDENT, "",
                        end_marker.starts_at
                    ))
                self.tokens.append(end_marker)
                break
            elif last_token == Literal.NEWLINE:
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
            i += 1

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
        # @deprecated
        # Fungsi ini tidak digunakan lagi
        statements = [[[]]]
        level = 0
        for token in self.tokens:
            if token.type == Literal.NEWLINE:
                statements[level][-1].append(token)
                statements[level].append([])
            elif token.type == Indentation.INDENT:
                statements.append([[]])
                level += 1
                statements[level][-1].append(token)
            elif token.type == Indentation.DEDENT:
                statements[level][-1].append(token)
                block = statements.pop()
                level -= 1
                statements[level].pop()
                statements[level].append(block)
                statements[level].append([])
            else:
                statements[level][-1].append(token)
        self.statements = statements[0]

    def print_statements(self, statements, level=0):
        # @deprecated
        # Fungsi ini tidak digunakan lagi
        for statement in statements:
            if type(statement) == list:
                for token in statement:
                    if type(token) != list and token.type not in [Indentation.INDENT, Indentation.DEDENT,
                                                                  Literal.WHITESPACE, Literal.NEWLINE]:
                        print(f"{'  ' * level}{token.type}")
                self.print_statements(statement, level + 1)

    def check_statements(self, statements):
        # Fungsi ini digunakan untuk debugging
        have_token = False
        have_blocks = False
        for statement in statements:
            if type(statement) == list:
                have_blocks = True
                self.check_statements(statement)
            elif type(statement) in [Indentation, Literal, Operator, Keyword, Punctuation]:
                have_token = True
        if have_token and have_blocks:
            print("detected")

    def statement_type(self, statement):
        # @deprecated
        # Fungsi ini tidak digunakan lagi
        token = statement[0]
        return "block" if type(token) == list else "simple"

    def parse_import_stmt(self, statement):
        # type: (list[Token]) -> None

        # Parse grammar import_stmt
        # Syarat : tipe token pertama dalam statement adalah Keyword.IMPORT

        # Proses :
        # [1] Pisahkan token menjadi
        # Keyword.IMPORT Literal.WHITESPACE sub_stmts Literal.WHITESPACE?
        # [2] trim WHITESPACE dari sub_stmts
        # [3] split sub_stmts menjadi sub_stmt dengan separator Punctuation.COMMA
        # [4] Parse tiap sub_stmt sebagai dotted_as_name

        token = statement[0]
        i = 1
        while token.type == Keyword.IMPORT:
            if token.type not in [Literal.WHITESPACE, Indentation.INDENT,
                                  Indentation.DEDENT]:
                raise SyntaxError()
            token = statement[i]
            i += 1

        stmt_slice = statement[i:]
        sub_stmts = self.split(stmt_slice, Punctuation.COMMA)
        for sub_stmt in sub_stmts:
            self.parse_dotted_as_name(sub_stmt)

    def parse_dotted_as_name(self, statement):
        # type: (list[Token]) -> None

        # Parse grammar dotted_as_name
        # Syarat : grammar berbentuk
        # dotted_name [Literal.WHITESPACE Keyword.AS Literal.WHITESPACE Literal.NAME] Literal.WHITESPACE?
        # dotted_name tidak mengandung WHITESPACE

        # Proses :
        # [1] Jika hanya mengandung 1 token WHITESPACE di akhir, trim dan parse
        # sebagai dotted_name
        # [2] Jika mengandung lebih dari 2 token, cek token opsional [...],
        # kemudian trim dan parse sisa token sebagai dotted_name

        # TODO : Recheck algoritma

        sub_stmts = self.split(statement, Keyword.AS)
        if len(sub_stmts) != 2:
            raise SyntaxError()
        [dotted_name, name] = sub_stmts
        if len(name) != 1:
            raise SyntaxError()
        name = name[0]
        if name.type != Literal.NAME:
            raise SyntaxError()
        self.parse_dotted_name(dotted_name)

    def parse_dotted_name(self, statement):
        # type: (list[Token]) -> None

        # Parse grammar dotted_as_name
        # Syarat : tidak mengandung WHITESPACE, grammar berbentuk
        # NAME [Punctuation.ACCESSOR NAME]+

        # Proses :
        # [1] Cek tipe token saat ini adalah Literal.NAME
        # [2] Jika masih ada token, next
        # [3] Cek tipe token saat ini adalah Punctuation.ACCESSOR,
        #     next & goto [1]

        # TODO : Recheck algoritma

        sub_stmts = self.split(statement, Punctuation.ACCESSOR)
        for stmt in sub_stmts:
            if len(stmt) != 1:
                raise SyntaxError()
            name = stmt[0]
            if name.type != Literal.NAME:
                raise SyntaxError()

    def split(self, statement, separator):
        # type: (list[Token], Token) -> list[list[Token]]

        # Split statement menjadi list Token dengan separator tertentu
        i = 0
        li = 0
        l = len(statement)
        res = []
        while i < l:
            if statement[i].type == separator:
                res.append(statement[li:i])
                li = i + 1
        res.append(statement[li:])
        return res


def next_as(statement, index=0):
    # @deprecated
    # Fungsi ini tidak digunakan lagi
    for i in range(index, len(statement)):
        token = statement[i]
        if token.type == Keyword.AS:
            return i
    return -1


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
# parser.parse("a.py")
