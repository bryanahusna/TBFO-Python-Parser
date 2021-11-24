from sys import exit
from enum import Enum
from tokenizer import Tokenizer, Token
from tokens import *


class Parser:
    def __init__(self):
        self.statements = []
        self.lines = []
        self.tokens = []        # type: list[Token]
        self.indent_stack = []  # type: list[Indent]
        self.statement = []     # type: list[Token]
        self.index = 0
        self.loop_stack = []    # type: list[TokenType]
        self.func_stack = []
        self.try_stack = 0
        self.block_stack = 0

    def parse(self, filename):
        with open(filename, encoding="utf-8") as f:
            for line in f:
                self.lines.append(line)
        tokenizer = Tokenizer()
        self.tokens = tokenizer.tokenize(filename)

        self.parse_indents()

        self.next_statement()
        while self.statement[-1].type != Literal.ENDMARKER:
            self.parse_simple_statement(self.statement)
            self.next_statement()
        self.statement[-1].type = Literal.NEWLINE
        self.parse_simple_statement(self.statement)

    def next_statement(self):
        # type: () -> None
        # Baca statement berikutnya sebagai list token
        bracket_stack = []
        expect_indent = False
        indent_stack = 0
        expect_dedent = 0
        self.statement = []
        last_token = None
        token = self.tokens[self.index]
        end_with_dedent = False
        while token.type not in [Literal.NEWLINE, Literal.ENDMARKER] or len(bracket_stack) != 0 or expect_dedent != 0:
            if expect_indent and type(token.type) != Indentation:
                self.throw(token.starts_at,
                           "Indentation Error : Expected indentation.")
            elif expect_indent:
                expect_indent = False

            if token.is_opening_bracket():
                bracket_stack.append(token.type)
            elif token.is_closing_bracket():
                if len(bracket_stack) == 0:
                    self.throw(token.starts_at,
                               "Bracket Error : Closing bracket appeared before any opening bracket.")
                match bracket_stack[-1]:
                    case Punctuation.PARENTHESIS_OPEN:
                        if token.type != Punctuation.PARENTHESIS_CLOSE:
                            self.throw(token.starts_at,
                                       "Bracket Error : Bracket mismatch.")
                    case Punctuation.SQUARE_BRACKET_OPEN:
                        if token.type != Punctuation.SQUARE_BRACKET_CLOSE:
                            self.throw(token.starts_at,
                                       "Bracket Error : Bracket mismatch.")
                    case Punctuation.BRACKET_OPEN:
                        if token.type != Punctuation.BRACKET_CLOSE:
                            self.throw(token.starts_at,
                                       "Bracket Error : Bracket mismatch.")
                bracket_stack.pop()
            elif token.type == Indentation.INDENT:
                indent_stack += 1
            elif token.type == Indentation.DEDENT:
                indent_stack -= 1
                expect_dedent -= 1
                if last_token.type == Literal.NEWLINE and expect_dedent == 0:
                    end_with_dedent = True
                    self.index += 1
                    break

            if token.type == Literal.NEWLINE and len(bracket_stack) > indent_stack:
                expect_indent = True
                expect_dedent += 1

            self.statement.append(token)
            self.index += 1
            last_token = token
            token = self.tokens[self.index]

        if not end_with_dedent:
            self.statement.append(token)
            self.index += 1

        if len(bracket_stack) != 0:
            self.throw(token.starts_at,
                       "Bracket Error : All brackets are not fully closed.")
        if indent_stack != 0:
            self.throw(token.starts_at,
                       "Indentation Error : Found indentation in a simple statement.")
        self.condense_statement()

    def condense_statement(self):
        i = 0
        while i < len(self.statement):
            token = self.statement[i]
            if token.type == Literal.NEWLINE:
                if i != len(self.statement) - 1 and type(self.statement[i + 1].type) == Indentation:
                    self.statement.pop(i)
                    self.statement.pop(i)
            i += 1

    def next_block(self):
        # type: () -> None
        # Baca block berikutnya sebagai list token
        indent_stack = 0
        past = False
        self.block = []
        self.block_stack += 1
        token = self.tokens[self.index]
        while indent_stack != 0 or not past:
            # Ignore comment
            if token.type != Literal.COMMENT:
                if token.type == Indentation.INDENT:
                    indent_stack += 1
                    past = True
                elif token.type == Indentation.DEDENT:
                    indent_stack -= 1
                self.block.append(token)
                self.index += 1
                token = self.tokens[self.index]

    def has_block_next(self):
        return self.tokens[self.index].type == Indentation.INDENT

    def skip_whitespaces(self, index):
        token = self.tokens[index]
        while token.type == Literal.WHITESPACE:
            index += 1
            token = self.tokens[index]
        return token, index

    def parse_block(self):
        j = self.index - 1
        self.index = j - len(self.block) + 2
        self.next_statement()
        while self.index < j:
            self.statement = self.trim(self.statement)
            self.parse_simple_statement(self.statement)
            if self.index >= j:
                break
            self.next_statement()
        self.index = j + 1
        while self.tokens[self.index].type == Indentation.DEDENT:
            if self.block_stack > 0:
                self.block_stack -= 1
            else:
                self.throw(self.tokens[self.index].starts_at,
                           "Indentation Error : Unexpected end of block.")
            self.index += 1

    def parse_simple_statement(self, statement):
        # ENDMARKER only statement
        if len(statement) == 0 or len(statement) == 1 and statement[0].type == Literal.ENDMARKER:
            return

        first_token = statement[0]      # type: Token

        match first_token.type:
            # Ignore empty statement
            case Literal.NEWLINE:
                pass
            # Single keyword statement
            case Keyword.PASS:
                next_token = statement[1]
                if next_token.type == Literal.NEWLINE:
                    pass
                elif next_token.type == Literal.WHITESPACE:
                    next_token = statement[2]
                else:
                    self.throw(first_token.starts_at,
                               "Syntax Error : Unexpected token after pass keyword.")
                if next_token.type != Literal.NEWLINE:
                    self.throw(first_token.starts_at,
                               "Syntax Error : Unexpected token after pass keyword.")
            case Keyword.BREAK:
                if len(self.loop_stack) > 0:
                    next_token = statement[1]
                    if next_token.type == Literal.NEWLINE:
                        pass
                    elif next_token.type == Literal.WHITESPACE:
                        next_token = statement[2]
                    else:
                        self.throw(first_token.starts_at,
                                   "Syntax Error : Unexpected token after break keyword.")
                    if next_token.type != Literal.NEWLINE:
                        self.throw(first_token.starts_at,
                                   "Syntax Error : Unexpected token after break keyword.")
                else:
                    self.throw(first_token.starts_at,
                               "Syntax Error : break keyword must be place inside a loop.")
            case Keyword.CONTINUE:
                if len(self.loop_stack) > 0:
                    next_token = statement[1]
                    if next_token.type == Literal.NEWLINE:
                        pass
                    elif next_token.type == Literal.WHITESPACE:
                        next_token = statement[2]
                    else:
                        self.throw(first_token.starts_at,
                                   "Syntax Error : Unexpected token after continue keyword.")
                    if next_token.type != Literal.NEWLINE:
                        self.throw(first_token.starts_at,
                                   "Syntax Error : Unexpected token after continue keyword.")
                else:
                    self.throw(first_token.starts_at,
                               "Syntax Error : continue keyword must be place inside a loop.")
            # Import statement
            case Keyword.IMPORT:
                self.parse_import_stmt(statement)
            # Import from statement
            case Keyword.FROM:
                self.parse_import_from_stmt(statement)
            # Raise statement
            case Keyword.RAISE:
                self.parse_raise_stmt(statement)
            # Return statement
            case Keyword.RETURN:
                if (len(self.func_stack) == 0):
                    self.throw(first_token.starts_at,
                               "Syntax Error : return keyword must be place inside a function.")
            case Keyword.DEF:
                self.func_stack.append(Keyword.DEF)
                statement = statement[1:]
                self.parse_function_def(statement)
                self.func_stack.pop()
            # If statement
            case Keyword.IF:
                self.parse_if_stmt(statement)
            # Class definition statementt
            case Keyword.CLASS:
                statement = statement[1:]
                self.parse_class_def(statement)
            # With statement
            case Keyword.WITH:
                statement = statement[1:]
                self.parse_with_stmt(statement)
            # For statement
            case Keyword.FOR:
                self.loop_stack.append(Keyword.FOR)
                self.parse_for_stmt(statement)
                self.loop_stack.pop()
            # While statement
            case Keyword.WHILE:
                self.loop_stack.append(Keyword.WHILE)
                self.parse_while_stmt(statement)
                self.loop_stack.pop()
            # Invalid first token
            case _:
                try:
                    self.try_stack += 1
                    self.parse_assignment(statement)
                    self.try_stack -= 1
                except:
                    self.try_stack -= 1
                    self.parse_expression(statement)

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
                self.tokens.append(Token(
                    Literal.NEWLINE, "",
                    end_marker.starts_at
                ))
                for j in range(len(indent_stack)):
                    self.tokens.append(Token(
                        Indentation.DEDENT, "",
                        end_marker.starts_at
                    ))
                self.tokens.append(end_marker)
                break
            elif token.type == Literal.STRING_MULTILINE:
                j = i
                if last_token not in [Indentation.INDENT, Indentation.DEDENT, Literal.NEWLINE, Literal.WHITESPACE]:
                    self.throw(token.starts_at,
                               "Syntax Error : Statements must be separated with a line break.")
                i += 1
                next_token = self.tokens[i]
                if next_token.type == Literal.WHITESPACE:
                    self.tokens.pop(i)
                if next_token.type == Literal.ENDMARKER:
                    self.tokens.pop(i - 1)
                elif next_token.type == Literal.NEWLINE:
                    self.tokens.pop(j)
                else:
                    self.throw(token.starts_at,
                               "Syntax Error : Statements must be separated with a line break.")
            elif token.type == Literal.COMMENT:
                j = i
                i += 1
                next_token = self.tokens[i]
                if next_token.type == Literal.WHITESPACE:
                    self.tokens.pop(i)
                if next_token.type in [Literal.ENDMARKER, Literal.NEWLINE]:
                    self.tokens.pop(j)
                    i -= 1
                    token = self.tokens[i]
                else:
                    self.throw(token.starts_at,
                               "Syntax Error : Statements must be separated with line break.")
            elif last_token == Literal.NEWLINE:
                if token.type == Literal.WHITESPACE:
                    if len(indent_stack) == 0:
                        if ' ' in token.value and '\t' in token.value:
                            self.throw(token.starts_at,
                                       "Tab Error : Inconsistent indentation using tab and spaces.")
                        if ' ' in token.value:
                            indent_stack.append(
                                Indent(IndentType.WHITESPACE, len(token.value)))
                        else:
                            indent_stack.append(
                                Indent(IndentType.TAB, len(token.value)))
                        token.type = Indentation.INDENT
                    else:
                        if ' ' in token.value and '\t' in token.value:
                            self.throw(token.starts_at,
                                       "Tab Error : Inconsistent indentation using tab and spaces.")
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
                                self.throw(token.starts_at,
                                           "Indentation Error : Inconsistent indentation.")
                else:
                    indent_length = self.indent_length(indent_stack)
                    current_indent_length = 0
                    if current_indent_length < indent_length:
                        self.tokens.insert(i, Token(Indentation.DEDENT, '',
                                                    token.starts_at))
                        indent_stack.pop()
                        while current_indent_length < self.indent_length(indent_stack) and len(indent_stack) > 0:
                            self.tokens.insert(i, Token(Indentation.DEDENT, '',
                                                        token.starts_at))
                            indent_stack.pop()
                        if current_indent_length != self.indent_length(indent_stack):
                            self.throw(token.starts_at,
                                       "Indentation Error : Inconsistent indentation.")
            last_token = token.type
            i += 1

    def check_indent(self, token, indent_type):
        char_against = ' ' if indent_type == IndentType.TAB else '\t'
        if char_against in token.value:
            self.throw(token.starts_at,
                       "Indentation Error : Inconsistent indentation using tab and spaces.")

    def indent_length(self, indents):
        l = 0
        for indent in indents:
            l += indent.value
        return l

    def parse_assignment(self, statement):
        try:
            self.try_stack += 1
            self.parse_assignment_simple(statement)
            self.try_stack -= 1
        except:
            self.try_stack -= 1
            try:
                self.try_stack += 1
                self.parse_assignment_multiple_targets(statement)
                self.try_stack -= 1
            except:
                self.try_stack -= 1
                self.parse_assignment_augmented(statement)

    def parse_assignment_simple(self, statement):
        subexpr = self.split_one_level(statement, Operator.ASSIGNMENT)
        if(len(subexpr) != 2):
            self.throw(self.tokens[self.index],
                       "Syntax Error : Invalid target")

        self.parse_star_target_single(subexpr[0])   # Bagian kiri harus target
        # Bagian kanan harus ekspresi
        self.parse_expression(subexpr[1])

    def parse_assignment_multiple_targets(self, statement):
        subexpr = self.split_one_level(statement, Operator.ASSIGNMENT)
        i = 0
        n = len(subexpr)
        while(i < n-1):
            # Cek tiap variabel target (a = b = c = ekspr, a b dan c harus target)
            self.parse_star_target_single(subexpr[i])
            i += 1
        if(n > 0):
            # Pecahan terakhir harus ekspresi
            self.parse_expression(subexpr[n-1])
        else:
            self.throw(self.tokens[self.index],
                       "Syntax Error : Invalid target")

    def parse_assignment_augmented(self, statement):
        i = 0
        n = len(statement)
        while(i < n):
            # Mencari operator augassign
            if(self.isAugassignOperator(statement[i])):
                break
            else:
                i += 1
        if(i == n):
            self.throw(self.tokens[self.index],
                       "Syntax Error : Invalid target")
        # Bagian kiri harus single target
        self.parse_star_target_single(statement[:i])
        # Bagian kanan harus ekspresi
        self.parse_expression(statement[i+1:])

    def isAugassignOperator(self, token):
        if(token.type == Operator.AUGMENTED_ADDITION or token.type == Operator.AUGMENTED_SUBTRACTION or token.type == Operator.MULTIPLICATION or
           token.type == Operator.AUGMENTED_DIVISION or token.type == Operator.AUGMENTED_MODULUS or token.type == Operator.AUGMENTED_BITWISE_AND or
           token.type == Operator.AUGMENTED_BITWISE_OR or token.type == Operator.AUGMENTED_BITWISE_XOR or token.type == Operator.AUGMENTED_BITWISE_LEFT_SHIFT or
           token.type == Operator.AUGMENTED_BITWISE_RIGHT_SHIFT or token.type == Operator.AUGMENTED_EXPONENTIATION or token.type == Operator.AUGMENTED_FLOOR_DIVISION):
            return True
        else:
            return False

    def parse_star_target_single(self, statement):

        if len(statement) == 0:
            self.throw(self.tokens[self.index],
                       "Syntax Error : Empty target")

        if statement[0].type == Operator.MULTIPLICATION:
            if len(statement) == 1:
                self.throw(self.tokens[self.index],
                           "Syntax Error : Invalid target")
            self.parse_target_with_star_atom(statement[1:])
        else:
            self.parse_target_with_star_atom(statement)

    def parse_target_with_star_atom(self, statement):
        # Mengembalikan apakah star target valid, serta indeks token terakhir di statement
        i = 0
        statement = self.trim(statement)
        if len(statement) == 0:
            self.throw(self.tokens[self.index],
                       "Syntax Error : Empty target.")

        if statement[0].type == Operator.MULTIPLICATION:
            if len(statement) == 1:
                self.throw(statement[0].starts_at,
                           "Syntax Error : Invalid target.")
            statement = statement[1:]

        last_token = statement[-1]
        if last_token.type in [Punctuation.BRACKET_OPEN,
                               Punctuation.PARENTHESIS_OPEN,
                               Punctuation.SQUARE_BRACKET_OPEN]:
            self.throw(last_token.starts_at,
                       "Syntax Error : Invalid target.")

        if last_token.type == Literal.NAME:
            i = - 2
            if len(statement) == 1:
                return
            last_token = statement[-2]
            if last_token.type == Literal.WHITESPACE:
                i -= 1
                last_token = statement[i]
                if len(statement) == 2:
                    return

            if last_token.type == Punctuation.ACCESSOR:
                sub_stmt = statement[:i]
                self.parse_t_primary(sub_stmt)
            else:
                self.throw(last_token.starts_at,
                           "Syntax Error : Invalid target.")

            last_token = statement[-2]

        elif last_token.type == Punctuation.SQUARE_BRACKET_CLOSE:
            sub_stmt = []
            sub_stmt.append(last_token.type)
            bracket_stack = [last_token]
            i = len(statement) - 2
            while i >= 0 and bracket_stack != 0:
                token = statement[i]
                sub_stmt.append(token)
                if token.type in [Punctuation.SQUARE_BRACKET_CLOSE, Punctuation.BRACKET_CLOSE,
                                  Punctuation.PARENTHESIS_CLOSE]:
                    bracket_stack.append(token.type)
                if token.type == Punctuation.SQUARE_BRACKET_OPEN:
                    if len(bracket_stack) == 0 or bracket_stack[-1] != Punctuation.SQUARE_BRACKET_CLOSE:
                        self.throw(token.starts_at,
                                   "Bracket Error : Bracket mismatch.")
                if token.type == Punctuation.BRACKET_OPEN:
                    if len(bracket_stack) == 0 or bracket_stack[-1] != Punctuation.BRACKET_CLOSE:
                        self.throw(token.starts_at,
                                   "Bracket Error : Bracket mismatch.")
                if token.type == Punctuation.PARENTHESIS_OPEN:
                    if len(bracket_stack) == 0 or bracket_stack[-1] != Punctuation.PARENTHESIS_CLOSE:
                        self.throw(token.starts_at,
                                   "Bracket Error : Bracket mismatch.")
                i -= 1

            sub_stmt.reverse()

            if len(bracket_stack) != 0:
                self.throw(sub_stmt[-1].starts_at,
                           "Bracket Error : Bracket mismatch.")
            elif i == 0:
                self.throw(sub_stmt[0].starts_at,
                           "Syntax Error : Invalid target.")
            elif len(sub_stmt) == 2:
                self.throw(sub_stmt[0].starts_at,
                           "Index Error : Invalid index.")

            slices = sub_stmt[1:-1]
            t_primary = statement[:len(statement) - len(sub_stmt)]
            self.parse_slices(slices)
            self.parse_t_primary(t_primary)

        else:
            self.parse_star_atom(statement)

    def parse_t_primary(self, statement):
        i = 0
        statement = self.trim(statement)
        if len(statement) == 0:
            self.throw(self.tokens[self.index],
                       "Syntax Error : Empty target.")

        if statement[0].type == Operator.MULTIPLICATION:
            if len(statement) == 1:
                self.throw(statement[0].starts_at,
                           "Syntax Error : Invalid target.")
            statement = statement[1:]

        last_token = statement[-1]
        if last_token.type in [Punctuation.BRACKET_OPEN,
                               Punctuation.PARENTHESIS_OPEN,
                               Punctuation.SQUARE_BRACKET_OPEN]:
            self.throw(last_token.starts_at,
                       "Syntax Error : Invalid target.")

        if last_token.type == Literal.NAME:
            i = - 2
            if len(statement) == 1:
                return
            last_token = statement[-2]
            if last_token.type == Literal.WHITESPACE:
                i -= 1
                last_token = statement[i]
                if len(statement) == 2:
                    return

            if last_token.type == Punctuation.ACCESSOR:
                sub_stmt = statement[:i]
                self.parse_t_primary(sub_stmt)
            else:
                self.throw(last_token.starts_at,
                           "Syntax Error : Invalid target.")

            last_token = statement[-2]

        elif last_token.type == Punctuation.SQUARE_BRACKET_CLOSE:
            sub_stmt = []
            sub_stmt.append(last_token.type)
            bracket_stack = [last_token]
            i = len(statement) - 2
            while i >= 0 and bracket_stack != 0:
                token = statement[i]
                sub_stmt.append(token)
                if token.type in [Punctuation.SQUARE_BRACKET_CLOSE, Punctuation.BRACKET_CLOSE,
                                  Punctuation.PARENTHESIS_CLOSE]:
                    bracket_stack.append(token.type)
                if token.type == Punctuation.SQUARE_BRACKET_OPEN:
                    if len(bracket_stack) == 0 or bracket_stack[-1] != Punctuation.SQUARE_BRACKET_CLOSE:
                        self.throw(token.starts_at,
                                   "Bracket Error : Bracket mismatch.")
                if token.type == Punctuation.BRACKET_OPEN:
                    if len(bracket_stack) == 0 or bracket_stack[-1] != Punctuation.BRACKET_CLOSE:
                        self.throw(token.starts_at,
                                   "Bracket Error : Bracket mismatch.")
                if token.type == Punctuation.PARENTHESIS_OPEN:
                    if len(bracket_stack) == 0 or bracket_stack[-1] != Punctuation.PARENTHESIS_CLOSE:
                        self.throw(token.starts_at,
                                   "Bracket Error : Bracket mismatch.")
                i -= 1

            sub_stmt.reverse()

            if len(bracket_stack) != 0:
                self.throw(sub_stmt[-1].starts_at,
                           "Bracket Error : Bracket mismatch.")
            elif i == 0:
                self.throw(sub_stmt[0].starts_at,
                           "Syntax Error : Invalid target.")
            elif len(sub_stmt) == 2:
                self.throw(sub_stmt[0].starts_at,
                           "Index Error : Invalid index.")

            slices = sub_stmt[1:-1]
            t_primary = statement[:len(statement) - len(sub_stmt)]
            self.parse_slices(slices)
            self.parse_t_primary(t_primary)

        elif last_token.type == Punctuation.PARENTHESIS_CLOSE:
            sub_stmt = []
            sub_stmt.append(last_token.type)
            bracket_stack = [last_token]
            i = len(statement) - 2
            while i >= 0 and bracket_stack != 0:
                token = statement[i]
                sub_stmt.append(token)
                if token.type in [Punctuation.SQUARE_BRACKET_CLOSE, Punctuation.BRACKET_CLOSE,
                                  Punctuation.PARENTHESIS_CLOSE]:
                    bracket_stack.append(token.type)
                if token.type == Punctuation.SQUARE_BRACKET_OPEN:
                    if len(bracket_stack) == 0 or bracket_stack[-1] != Punctuation.SQUARE_BRACKET_CLOSE:
                        self.throw(token.starts_at,
                                   "Bracket Error : Bracket mismatch.")
                if token.type == Punctuation.BRACKET_OPEN:
                    if len(bracket_stack) == 0 or bracket_stack[-1] != Punctuation.BRACKET_CLOSE:
                        self.throw(token.starts_at,
                                   "Bracket Error : Bracket mismatch.")
                if token.type == Punctuation.PARENTHESIS_OPEN:
                    if len(bracket_stack) == 0 or bracket_stack[-1] != Punctuation.PARENTHESIS_CLOSE:
                        self.throw(token.starts_at,
                                   "Bracket Error : Bracket mismatch.")
                i -= 1

            sub_stmt.reverse()

            if len(bracket_stack) != 0:
                self.throw(sub_stmt[-1].starts_at,
                           "Bracket Error : Bracket mismatch.")
            elif i == 0:
                self.throw(sub_stmt[0].starts_at,
                           "Syntax Error : Invalid target.")
            elif len(sub_stmt) == 2:
                self.throw(sub_stmt[0].starts_at,
                           "Index Error : Invalid index.")

            arguments = sub_stmt[1:-1]
            t_primary = statement[:len(statement) - len(sub_stmt)]
            self.parse_arguments(arguments)
            self.parse_t_primary(t_primary)

        else:
            self.parse_atom(statement)

    def parse_star_atom(self, statement):
        statement = self.trim(statement)
        if len(statement) < 2:
            if len(statement) != 0:
                self.throw(statement[0].starts_at,
                           "Syntax Error : Invalid target.")
            else:
                self.throw(self.tokens[self.index].starts_at,
                           "Syntax Error : Invalid target.")
        first_token = statement[0]
        if first_token.type not in [Punctuation.PARENTHESIS_OPEN, Punctuation.SQUARE_BRACKET_OPEN]:
            self.throw(first_token.starts_at,
                       "Syntax Error : Unexpected token.")
        last_token = statement[-1]
        if first_token.type == Punctuation.PARENTHESIS_OPEN and last_token != Punctuation.PARENTHESIS_CLOSE:
            self.throw(last_token.starts_at,
                       "Bracket Error : Parenthesis mismatch.")
        if first_token.type == Punctuation.SQUARE_BRACKET_OPEN and last_token != Punctuation.SQUARE_BRACKET_CLOSE:
            self.throw(last_token.starts_at,
                       "Bracket Error : Brakcet mismatch.")
        sub_stmt = statement[1:-1]
        if len(sub_stmt) == 0:
            return
        else:
            if sub_stmt[-1].type == Punctuation.COMMA:
                sub_stmt = sub_stmt[:-1]
            if first_token.type == Punctuation.PARENTHESIS_OPEN:
                self.parse_star_target_multiple(sub_stmt)
            else:
                try:
                    self.try_stack += 1
                    self.parse_target_with_star_atom(sub_stmt)
                    self.try_stack -= 1
                except:
                    self.try_stack -= 1
                    self.parse_star_target_multiple(sub_stmt)

    def parse_star_target_multiple(self, statement):
        # Mengembalikan apakah star target valid, serta indeks token terakhir di statement
        statement = self.trim(statement)
        if len(statement) == 0:
            self.throw(self.tokens[self.index],
                       "Syntax Error : Empty target")
        targets = self.split_args(statement)
        for target in targets:
            self.parse_star_target_single(target)

    def parse_star_expression(self, statement):
        # return True jika ekspresi valid, false jika tidak
        i = 0
        n = len(statement)
        while(i < n and statement[i].type == Literal.WHITESPACE):
            i += 1
        if(i == n):
            return (False, statement[i-1])
        token = statement[i]
        if(token.type == Literal.NEWLINE or token.type == Literal.ENDMARKER):
            return (False, token)

        subexprs = self.split_one_level(statement[i:], Punctuation.COMMA)
        for j in range(len(subexprs)):
            i = 0
            n = len(subexprs[j])
            if(n == 0 and j != len(subexprs)-1):
                return (False, token)
            bracketstack = []
            numberstack = []
            operatorstack = []
            previoustoken = None
            while(i < n):
                token = subexprs[j][i]
                if(token.type == Literal.WHITESPACE or token.type == Literal.NEWLINE or token.type == Literal.COMMENT):
                    pass
                elif(len(bracketstack) > 0 and token.type == Literal.ENDMARKER):
                    return (False, token)

                elif(token.type == Literal.NUMBER or token.type == Literal.NAME or token.type == Literal.STRING or token.type == Literal.STRING_MULTILINE or
                     token.type == Keyword.TRUE or token.type == Keyword.FALSE or token.type == Keyword.NONE):
                    if(len(numberstack) == 0):
                        numberstack.append(token)
                        if(len(operatorstack) > 0 and self.isUnaryOperator(operatorstack[-1])):
                            operatorstack.pop()
                    else:
                        if(len(operatorstack) == 0 and len(numberstack) > 0):
                            return (False, token)
                        else:
                            operator = operatorstack.pop()
                            while(len(operatorstack) > 0 and self.isUnaryOperator(operator)):
                                operatorprev = operator
                                operator = operatorstack.pop()
                                if(self.isUnaryOperator(operator) and self.isUnaryOperator(operatorprev) and (operatorprev.type != operator.type)):
                                    return (False, token)

                elif(previoustoken != None and token.type == Punctuation.ACCESSOR and self.isAtom(previoustoken)):
                    i += 1
                    token = subexprs[j][i]
                    while(i < n and (token.type == Literal.WHITESPACE or token.type == Literal.NEWLINE)):
                        token = subexprs[j][i]
                        i += 1
                    if(i == n or token.type != Literal.NAME):
                        return (False, token)
                    numberstack.pop()
                    if(len(numberstack) == 0):
                        numberstack.append(token)
                        if(len(operatorstack) > 0 and self.isUnaryOperator(operatorstack[-1])):
                            operatorstack.pop()
                    else:
                        if(len(operatorstack) == 0 and len(numberstack) > 0):
                            return (False, token)
                        else:
                            operator = operatorstack.pop()
                            while(len(operatorstack) > 0 and self.isUnaryOperator(operator)):
                                operatorprev = operator
                                operator = operatorstack.pop()
                                if(self.isUnaryOperator(operator) and self.isUnaryOperator(operatorprev) and (operatorprev.type != operator.type)):
                                    return (False, token)

                elif(token.type == Punctuation.PARENTHESIS_OPEN):
                    if(previoustoken == None or (self.isBinaryOperator(previoustoken) or self.isUnaryOperator(previoustoken))):
                        bracketstack.append(Punctuation.PARENTHESIS_OPEN)
                    elif(self.isAtom(previoustoken)):   # Call to function
                        argstoken = []
                        parenthesisopencnt = 1
                        token = subexprs[j][i]
                        i += 1
                        while(parenthesisopencnt > 0 and i < n):
                            token = subexprs[j][i]
                            argstoken.append(token)
                            if(token.type == Punctuation.PARENTHESIS_OPEN):
                                parenthesisopencnt += 1
                            elif(token.type == Punctuation.PARENTHESIS_CLOSE):
                                parenthesisopencnt -= 1
                            i += 1
                        argstoken.pop()
                        self.parse_arguments(argstoken)
                        previoustoken = token
                        continue
                    else:
                        return (False, token)
                elif(token.type == Punctuation.BRACKET_OPEN):
                    argstoken = []
                    bracketopencnt = 1
                    token = subexprs[j][i]
                    i += 1
                    while(bracketopencnt > 0 and i < n):
                        token = subexprs[j][i]
                        argstoken.append(token)
                        if(token.type == Punctuation.BRACKET_OPEN):
                            bracketopencnt += 1
                        elif(token.type == Punctuation.BRACKET_CLOSE):
                            bracketopencnt -= 1
                        i += 1
                    argstoken.pop()
                    if(self.isStatementWhitespace(argstoken)):
                        pass
                    else:
                        validity = self.parse_star_expression(argstoken)
                        if(not validity[0]):
                            kwds = self.split_one_level(
                                argstoken, Punctuation.COMMA)
                            for k in range(len(kwds)):
                                # Jika kosong, tidak valid
                                if(self.isStatementWhitespace(kwds[k]) and k != (len(kwds)-1)):
                                    return (False, token)
                                # Jika kosong tapi di akhir (ada koma di akhir), valid
                                elif(self.isStatementWhitespace(kwds[k]) and k == (len(kwds)-1)):
                                    pass
                                else:
                                    temp = self.split_one_level(
                                        kwds[k], Punctuation.COLON)
                                    if(len(temp) == 1 or len(temp) > 2):
                                        return (False, token)
                                    else:
                                        validity1 = self.parse_star_expression(
                                            temp[0])
                                        validity2 = self.parse_star_expression(
                                            temp[1])
                                        if(not validity1[0] or not validity2[0]):
                                            return (False, token)
                    previoustoken = token
                    if(len(numberstack) == 0):
                        numberstack.append(token)
                        if(len(operatorstack) > 0 and self.isUnaryOperator(operatorstack[-1])):
                            operatorstack.pop()
                    else:
                        if(len(operatorstack) == 0 and len(numberstack) > 0):
                            return (False, token)
                        else:
                            operator = operatorstack.pop()
                            while(len(operatorstack) > 0 and self.isUnaryOperator(operator)):
                                operatorprev = operator
                                operator = operatorstack.pop()
                                if(self.isUnaryOperator(operator) and self.isUnaryOperator(operatorprev) and (operatorprev.type != operator.type)):
                                    return (False, token)
                    continue

                elif(token.type == Punctuation.SQUARE_BRACKET_OPEN):
                    argstoken = []
                    bracketopencnt = 1
                    token = subexprs[j][i]
                    i += 1
                    while(bracketopencnt > 0 and i < n):
                        token = subexprs[j][i]
                        argstoken.append(token)
                        if(token.type == Punctuation.SQUARE_BRACKET_OPEN):
                            bracketopencnt += 1
                        elif(token.type == Punctuation.SQUARE_BRACKET_CLOSE):
                            bracketopencnt -= 1
                        i += 1
                    argstoken.pop()
                    if(self.isStatementWhitespace(argstoken)):
                        pass
                    elif(previoustoken == None or not(self.isAtom(previoustoken))):
                        validity = self.parse_star_expression(argstoken)
                        if(not validity[0]):
                            return (False, token)
                    elif(self.isAtom(previoustoken)):
                        validity = self.parse_star_expression(argstoken)
                        if(not validity[0]):
                            self.parse_slices(argstoken)
                    previoustoken = token
                    if(len(numberstack) == 0):
                        numberstack.append(token)
                        if(len(operatorstack) > 0 and self.isUnaryOperator(operatorstack[-1])):
                            operatorstack.pop()
                    else:
                        if(len(operatorstack) == 0 and len(numberstack) > 0):
                            return (False, token)
                        else:
                            operator = operatorstack.pop()
                            while(len(operatorstack) > 0 and self.isUnaryOperator(operator)):
                                operatorprev = operator
                                operator = operatorstack.pop()
                                if(self.isUnaryOperator(operator) and self.isUnaryOperator(operatorprev) and (operatorprev.type != operator.type)):
                                    return (False, token)
                    continue

                elif(token.type == Punctuation.PARENTHESIS_CLOSE):
                    if(len(bracketstack) == 0 or bracketstack[-1] != Punctuation.PARENTHESIS_OPEN):
                        return (False, token)
                    else:
                        bracketstack.pop()
                elif(token.type == Punctuation.BRACKET_CLOSE):
                    if(len(bracketstack) == 0 or bracketstack[-1] != Punctuation.BRACKET_OPEN):
                        return (False, token)
                    else:
                        bracketstack.pop()
                elif(token.type == Punctuation.SQUARE_BRACKET_CLOSE):
                    if(len(bracketstack) == 0 or bracketstack[-1] != Punctuation.SQUARE_BRACKET_OPEN):
                        return (False, token)
                    else:
                        bracketstack.pop()
                elif(token.type == Keyword.IN and previoustoken != None and previoustoken.type == Keyword.NOT):
                    if(len(numberstack) == 0):
                        return (False, token)
                elif(self.isBinaryOperator(token)):
                    if(len(numberstack) == 0):
                        return (False, token)
                    else:
                        operatorstack.append(token)
                elif(self.isUnaryOperator(token)):
                    operatorstack.append(token)
                else:
                    return (False, token)

                if(token.type != Literal.WHITESPACE and token.type != Literal.NEWLINE):
                    previoustoken = token
                i += 1

            if(len(operatorstack) > 0):
                return (False, token)
        return (True, token)

    def parse_expression(self, statement):
        # statement berisi potongan ekspresi yang ingin dicek
        (isvalid, lasttoken) = self.parse_star_expression(statement)
        if(not isvalid):
            self.throw(lasttoken.starts_at,
                       "Syntax Error : Invalid expression.")

    def parse_slices(self, statement):
        subexprs = self.split_one_level(statement, Punctuation.COLON)
        if(len(subexprs) == 1):
            isempty = True
            for i in range(len(subexprs[0])):
                if(subexprs[0][i].type != Literal.WHITESPACE and subexprs[0][i].type != Literal.WHITESPACE):
                    isempty = False
                    return
            if(isempty):
                self.throw(statement[0].starts_at,
                           "Syntax Error : Invalid expression.")
            else:
                self.parse_expression(subexprs[0])
        elif(len(subexprs) > 3):
            self.throw(statement[0].starts_at,
                       "Syntax Error : Invalid expression.")
        else:
            for i in range(len(subexprs)):
                if(self.isStatementWhitespace(subexprs[i])):
                    continue
                self.parse_expression(subexprs[i])

    def isStatementWhitespace(self, statement):
        for i in range(len(statement)):
            if(statement[i].type != Literal.WHITESPACE and statement[i].type != Literal.NEWLINE):
                return False
        return True

    def isAtom(self, token):
        if(token.type == Literal.NUMBER or token.type == Literal.NAME or token.type == Literal.STRING or token.type == Literal.STRING_MULTILINE or
           token.type == Keyword.TRUE or token.type == Keyword.FALSE or token.type == Keyword.NONE):
            return True
        else:
            return False

    def isUnaryOperator(self, token):
        if(token.type == Keyword.NOT or token.type == Operator.BITWISE_NOT):
            return True
        else:
            return False

    def isBinaryOperator(self, token):
        if(token.type == Keyword.AND or token.type == Keyword.OR or token.type == Keyword.IN or token.type == Keyword.IS):
            return True

        if(token.type == Operator.EQUAL or token.type == Operator.NOT_EQUAL or token.type == Operator.LESS_EQUAL or
           token.type == Operator.LESS_THAN or token.type == Operator.GREATER_EQUAL or token.type == Operator.GREATER_THAN):
            return True

        if(token.type == Operator.BITWISE_OR or token.type == Operator.BITWISE_XOR or token.type == Operator.BITWISE_LEFT_SHIFT or
           token.type == Operator.BITWISE_RIGHT_SHIFT):
            return True

        if(token.type == Operator.ADDITION or token.type == Operator.SUBTRACTION or token.type == Operator.MULTIPLICATION or
           token.type == Operator.DIVISION or token.type == Operator.FLOOR_DIVISION or token.type == Operator.MODULUS or token.type == Operator.EXPONENTIATION):
            return True

        if token.type in [Keyword.IN, Keyword.IS]:
            return True

        return False

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
        while token.type != Keyword.IMPORT:
            if token.type not in [Literal.WHITESPACE, Indentation.INDENT,
                                  Indentation.DEDENT]:
                self.throw(token.starts_at,
                           "Syntax Error : Unexpected token.")
            token = statement[i]
            i += 1

        stmt_slice = statement[i:]
        self.parse_dotted_as_names(stmt_slice)

    def parse_dotted_as_names(self, statement):
        statement = self.trim(statement[:-1])
        sub_stmts = self.split(statement, Punctuation.COMMA)
        for sub_stmt in sub_stmts:
            self.parse_dotted_as_name(sub_stmt)

    def parse_import_from_stmt(self, statement):
        token = statement[0]
        if token.type != Keyword.FROM:
            self.throw(token.starts_at,
                       "Syntax Error : Unexpected token.")
        token = statement[1]
        if token.type != Literal.WHITESPACE:
            self.throw(token.starts_at,
                       "Syntax Error : Unexpected token.")
        token = statement[2]
        i = 2
        while token.type in [Punctuation.ACCESSOR, Literal.ELLIPSIS]:
            i += 1
            token = statement[i]
            if (token.type != Literal.WHITESPACE):
                self.throw(token.starts_at,
                           "Syntax Error : Ellipsis must be separated with whitespaces.")
            i += 1
            token = statement[i]
        token = statement[i]
        if token.type != Keyword.IMPORT:
            sub_stmts = self.split(statement[i:], Keyword.IMPORT)
            if len(sub_stmts) != 2:
                self.throw(token.starts_at,
                           "Syntax Error : Too many import keyword in a single statement.")
            sub_stmts[0] = self.trim(sub_stmts[0])
            self.parse_dotted_name(sub_stmts[0])
            self.parse_import_from_targets(sub_stmts[1])
        else:
            i += 1
            token = statement[i]
            if token.type != Literal.WHITESPACE:
                self.throw(token.starts_at,
                           "Syntax Error : Unexpected token.")
            self.parse_import_from_targets(statement[i + 1:])

    def parse_import_from_targets(self, statement):
        statement = self.trim(statement)
        first_token = statement[0]
        match first_token.type:
            case Operator.MULTIPLICATION:
                token = statement[1]
                if token.type != Literal.NEWLINE:
                    self.throw(token.starts_at,
                               "Syntax Error : Unexpected token. Expected a line break.")
            case Punctuation.PARENTHESIS_OPEN:
                last_token = statement[-2]
                if last_token.type != Punctuation.PARENTHESIS_CLOSE:
                    self.throw(first_token.starts_at,
                               "Bracket Error : Parenthesis mismatch.")
                last = -2
                if statement[last - 1].type == Literal.WHITESPACE:
                    last -= 1
                if statement[last - 1].type == Punctuation.COMMA:
                    last -= 1
                sub_stmt = statement[1:last]
                self.parse_import_from_as_names(sub_stmt)
            case _:
                if statement[-2].type == Punctuation.COMMA:
                    self.throw(statement[-2].starts_at,
                               "Syntax Error : Import statement can't end with a comma.")
                self.parse_import_from_as_names(statement[:-1])

    def parse_import_from_as_names(self, statement):
        statement = self.trim(statement)
        sub_stmts = self.split(statement, Punctuation.COMMA)
        for sub_stmt in sub_stmts:
            self.parse_import_from_as_name(sub_stmt)

    def parse_import_from_as_name(self, statement):
        statement = self.trim(statement)
        first_token = statement[0]
        if first_token.type != Literal.NAME:
            self.throw(first_token.starts_at,
                       "Syntax Error : Invalid name.")
        if len(statement) > 1:
            if len(statement) != 5:
                self.throw(first_token.starts_at,
                           "Syntax Error : Illegal name.")
            if statement[1].type != Literal.WHITESPACE:
                self.throw(statement[1].starts_at,
                           "Syntax Error : Import name must be separated with whitespaces.")
            if statement[2].type != Keyword.AS:
                self.throw(statement[2].starts_at,
                           "Syntax Error : Unexpected token. Expected as keyword.")
            if statement[3].type != Literal.WHITESPACE:
                self.throw(statement[3].starts_at,
                           "Syntax Error : Import name must be separated with whitespaces.")
            if statement[4].type != Literal.NAME:
                self.throw(first_token.starts_at,
                           "Syntax Error : Illegal name.")

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

        sub_stmts = self.split(statement, Keyword.AS)
        if len(sub_stmts) > 2:
            self.throw(sub_stmts[0].starts_at,
                       "Syntax Error : Too many as keywords.")
        if len(sub_stmts) == 2:
            [dotted_name, name] = sub_stmts
            name = self.trim(name)
            if len(name) != 1:
                self.throw(name[0].starts_at,
                           "Syntax Error : Illegal name.")
            name = name[0]
            if name.type != Literal.NAME:
                self.throw(name[0].starts_at,
                           "Syntax Error : Illegal name.")
            self.parse_dotted_name(dotted_name)
        else:
            self.parse_dotted_name(statement)

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

        statement = self.trim(statement)
        sub_stmts = self.split(statement, Punctuation.ACCESSOR)
        for stmt in sub_stmts:
            if len(stmt) != 1:
                self.throw(name[0].starts_at,
                           "Syntax Error : Illegal name.")
            name = stmt[0]
            if name.type != Literal.NAME:
                self.throw(name[0].starts_at,
                           "Syntax Error : Illegal name.")

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
            i += 1
        res.append(statement[li:])
        return res

    def split_one_level(self, statement, separator):
        # Bracket dianggap sudah valid karena sudah dicek di awal di next statement
        # Sepatarator tidak bisa keluarga bracket
        i = 0
        li = 0
        l = len(statement)
        res = []
        bracketstackcnt = 0
        while i < l:
            if statement[i].type == Punctuation.PARENTHESIS_OPEN or statement[i].type == Punctuation.BRACKET_OPEN or statement[i].type == Punctuation.SQUARE_BRACKET_OPEN:
                bracketstackcnt += 1
            elif statement[i].type == Punctuation.PARENTHESIS_CLOSE or statement[i].type == Punctuation.BRACKET_CLOSE or statement[i].type == Punctuation.SQUARE_BRACKET_CLOSE:
                bracketstackcnt -= 1
            elif statement[i].type == separator and bracketstackcnt == 0:
                res.append(statement[li:i])
                li = i + 1
            i += 1
        res.append(statement[li:])
        return res

    def split_args(self, arguments):
        l = len(arguments)
        i = 0
        arg_index = 0
        args = [[]]
        bracket_stack = []
        while i < l:
            token = arguments[i]
            if token.type in [Punctuation.BRACKET_OPEN,
                              Punctuation.PARENTHESIS_OPEN,
                              Punctuation.SQUARE_BRACKET_OPEN]:
                bracket_stack.append(token.type)
                args[arg_index].append(token)
            match token.type:
                case Punctuation.BRACKET_CLOSE:
                    if len(bracket_stack) == 0:
                        self.throw(token.starts_at,
                                   "Bracket Error : Closing bracket appeared before any opening bracket.")
                    if bracket_stack[-1] != Punctuation.BRACKET_OPEN:
                        self.throw(token.starts_at,
                                   "Bracket Error : Bracket mismatch.")
                    bracket_stack.pop()
                    args[arg_index].append(token)
                case Punctuation.PARENTHESIS_CLOSE:
                    if len(bracket_stack) == 0:
                        self.throw(token.starts_at,
                                   "Bracket Error : Closing bracket appeared before any opening bracket.")
                    if bracket_stack[-1] != Punctuation.PARENTHESIS_OPEN:
                        self.throw(token.starts_at,
                                   "Bracket Error : Bracket mismatch.")
                    bracket_stack.pop()
                    args[arg_index].append(token)
                case Punctuation.SQUARE_BRACKET_CLOSE:
                    if len(bracket_stack) == 0:
                        self.throw(token.starts_at,
                                   "Bracket Error : Closing bracket appeared before any opening bracket.")
                    if bracket_stack[-1] != Punctuation.SQUARE_BRACKET_OPEN:
                        self.throw(token.starts_at,
                                   "Bracket Error : Bracket mismatch.")
                    bracket_stack.pop()
                    args[arg_index].append(token)
                case Punctuation.COMMA:
                    if len(bracket_stack) == 0:
                        args.append([])
                        arg_index += 1
                case _:
                    args[arg_index].append(token)
            i += 1
        if len(bracket_stack) != 0:
            self.throw(arguments[-1].starts_at,
                       "Bracket Error : All brackets are not fully closed.")
        return args

    def split_accessor(self, arguments):
        l = len(arguments)
        i = 0
        arg_index = 0
        args = [[]]
        bracket_stack = []
        while i < l:
            token = arguments[i]
            if token.type in [Punctuation.BRACKET_OPEN,
                              Punctuation.PARENTHESIS_OPEN,
                              Punctuation.SQUARE_BRACKET_OPEN]:
                bracket_stack.append(token.type)
                args[arg_index].append(token)
            match token.type:
                case Punctuation.BRACKET_CLOSE:
                    if len(bracket_stack) == 0:
                        self.throw(token.starts_at,
                                   "Bracket Error : Closing bracket appeared before any opening bracket.")
                    if bracket_stack[-1] != Punctuation.BRACKET_OPEN:
                        self.throw(token.starts_at,
                                   "Bracket Error : Bracket mismatch.")
                    bracket_stack.pop()
                    args[arg_index].append(token)
                case Punctuation.PARENTHESIS_CLOSE:
                    if len(bracket_stack) == 0:
                        self.throw(token.starts_at,
                                   "Bracket Error : Closing bracket appeared before any opening bracket.")
                    if bracket_stack[-1] != Punctuation.PARENTHESIS_OPEN:
                        self.throw(token.starts_at,
                                   "Bracket Error : Bracket mismatch.")
                    bracket_stack.pop()
                    args[arg_index].append(token)
                case Punctuation.SQUARE_BRACKET_CLOSE:
                    if len(bracket_stack) == 0:
                        self.throw(token.starts_at,
                                   "Bracket Error : Closing bracket appeared before any opening bracket.")
                    if bracket_stack[-1] != Punctuation.SQUARE_BRACKET_OPEN:
                        self.throw(token.starts_at,
                                   "Bracket Error : Bracket mismatch.")
                    bracket_stack.pop()
                    args[arg_index].append(token)
                case Punctuation.ACCESSOR:
                    if len(bracket_stack) == 0:
                        args.append([])
                        arg_index += 1
                case _:
                    args[arg_index].append(token)
            i += 1
        if len(bracket_stack) != 0:
            self.throw(arguments[-1].starts_at,
                       "Bracket Error : All brackets are not fully closed.")
        return args

    def parse_raise_stmt(self, statement):
        statement = statement[1:]
        i = 0
        while(statement[i].type == Literal.WHITESPACE):
            i += 1
        if(statement[i].type == Literal.NEWLINE):   # Empty raise
            return

        statement = statement[i:]
        splitted = self.split(statement, Keyword.FROM)
        if(len(splitted) > 2):      # Jika ada lebih dari 1 from, tidak valid
            self.throw(splitted[0][0].starts_at,
                       "Syntax Error : Too many from keywords.")

        isvalid = True
        self.parse_expression(splitted[0])
        if(len(splitted) == 2):
            self.parse_expression(splitted[1])

    def parse_function_def(self, statement):
        # Parse grammar function def
        # 'def' NAME '(' [params] ')' ':' block

        # Proses :
        # [1] Split di colon, kalau hasilnya != 2 berarti syntax error
        # [2] Skip whitespace di awal dan di akhir
        # [3] Cek di sub_stmts[0] ada NAME sama parenthesis open dan close
        # [4] Kalo ada params, parse_params
        # [5] parse_block

        # TODO : recheck algorithm

        sub_stmts = self.split(statement, Punctuation.COLON)
        if (len(sub_stmts) != 2):
            self.throw(sub_stmts[0][0].starts_at,
                       "Syntax Error : Too many colons.")

        if (len(sub_stmts) > 0):
            left = self.trim(sub_stmts[0])

        if (left[0].type != Literal.NAME):
            self.throw(sub_stmts[0][0].starts_at,
                       "Syntax Error : Illegal name.")

        if (len(left) > 1):
            if (left[1].type != Punctuation.PARENTHESIS_OPEN or left[-1].type != Punctuation.PARENTHESIS_CLOSE):
                self.throw(sub_stmts[0][0].starts_at,
                           "Bracket Error : Parenthesis mismatch.")
            elif (left[1].type == Punctuation.PARENTHESIS_OPEN):
                params_stmt = left[2:-1]
                self.parse_params(params_stmt)

        right = sub_stmts[1]
        self.next_block()
        self.parse_block()

    def parse_params(self, statement):
        sub_stmt = self.split(statement, Punctuation.COMMA)
        equalSign = False
        for stmt in sub_stmt:
            new_stmt = self.split(stmt, Operator.ASSIGNMENT)
            if (len(new_stmt) > 1):
                equalSign = True

            left = new_stmt[0]
            if (len(left) > 0):
                left = self.trim(left)

            if (len(left) > 1 or (len(left) == 1 and left[0].type != Literal.NAME)):
                self.throw(left[0].starts_at,
                           "Syntax Error : Invalid parameter.")

            if (equalSign):
                if (len(new_stmt) != 2):
                    self.throw(new_stmt[0][0].starts_at,
                               "Syntax Error : Invalid parameter.")
                if (len(new_stmt[-1]) > 0):
                    right = self.trim(new_stmt[-1])
                    self.parse_expression(right)
                else:
                    self.throw(new_stmt[0][0].starts_at,
                               "Syntax Error : Invalid parameter.")

    def parse_class_def(self, statement):
        # Parse grammar class_def
        # NAME ['(' [arguments] ')' ] ':' block

        # Proses :
        # [1] Split di colon, kalau hasilnya != 2 berarti syntax error
        # [2] Cek di sub_stmts[0] ada parenthesis open dan close
        # [3] Kalo ada params, parse_params
        # [4] parse_block

        sub_stmts = self.split(statement, Punctuation.COLON)
        if (len(sub_stmts) != 2):
            self.throw(sub_stmts[0][0].starts_at,
                       "Syntax Error : Too many colons.")

        if (len(sub_stmts) > 0):
            left = self.trim(sub_stmts[0])

        if (left[0].type != Literal.NAME):
            self.throw(left[0].starts_at,
                       "Syntax Error : Illegal name.")

        if (len(left) > 1):
            if (left[1].type != Punctuation.PARENTHESIS_OPEN or left[-1].type != Punctuation.PARENTHESIS_CLOSE):
                self.throw(left[0].starts_at,
                           "Bracket Error : Parenthesis mismatch.")
            elif (left[1].type == Punctuation.PARENTHESIS_OPEN):
                arguments_stmt = left[2:-1]
                if (len(arguments_stmt) != 0):
                    self.parse_arguments(arguments_stmt)

        right = sub_stmts[1]
        self.next_block()
        self.parse_block()

    def parse_arguments(self, statement):
        # args [','] &')'

        new_stmt = self.trim(statement)
        if len(new_stmt) == 0:
            return
        if (new_stmt[-1].type == Punctuation.COMMA):
            if (len(new_stmt) > 1):
                self.parse_args(new_stmt[:-1])
            else:
                self.throw(new_stmt[0].starts_at,
                           "Syntax Error : Invalid arguments.")

        # print("finish parse arguments")

    def parse_args(self, statement):
        # ','.(starred_expression | ( assignment_expression | expression !':=') !'=')+ [',' kwargs ]
        # kwargs

        sub_stmt = self.split_args(statement)
        equalSign = False
        for stmt in sub_stmt:
            new_stmt = self.split(stmt, Operator.ASSIGNMENT)
            if (len(new_stmt) > 1):
                equalSign = True

            left = new_stmt[0]
            if (len(left) > 0):
                left = self.trim(left)

            if (len(left) > 1 or (len(left) == 1 and left[0].type != Literal.NAME)):
                self.throw(left[0].starts_at,
                           "Syntax Error : Invalid argument(s).")

            if (equalSign):
                if (len(new_stmt) != 2):
                    self.throw(new_stmt[0][0].starts_at,
                               "Syntax Error : Invalid argument(s).")
                if (len(new_stmt[-1]) > 0):
                    right = self.trim(new_stmt[-1])
                    self.parse_expression(right)
                else:
                    self.throw(new_stmt[0][0].starts_at,
                               "Syntax Error : Invalid argument(s).")

        # print("finish parse args")

    def parse_with_stmt(self, statement):
        # 'with' '(' ','.with_item+ ','? ')' ':' block
        # 'with' ','.with_item+ ':' block

        sub_stmts = self.split(statement, Punctuation.COLON)
        if (len(sub_stmts) != 2):
            self.throw(sub_stmts[0][0].starts_at,
                       "Syntax Error : Too many colon.")

        left = self.trim(sub_stmts[0])

        if (left[1].type != Punctuation.PARENTHESIS_OPEN == left[-1].type != Punctuation.PARENTHESIS_CLOSE):
            self.throw(left[0].starts_at,
                       "Bracket Error : Parenthesis mismatch.")
        elif (left[1].type != Punctuation.PARENTHESIS_OPEN):
            left = left[1:-1]

        with_item_stmt = self.split(left, Punctuation.COMMA)
        for with_item in with_item_stmt:
            self.parse_with_item(with_item)

        # parse block
        self.next_block()
        self.parse_block()

    def parse_with_item(self, statement):
        # expression 'as' star_target
        # expression

        sub_stmt = self.split(statement, Keyword.AS)
        if (len(sub_stmt) == 2):
            # masuk ke cabang pertama
            self.parse_expression(sub_stmt[0])
            self.parse_star_target_single(sub_stmt[1])
        elif (len(sub_stmt) == 1):
            # masuk ke cabang kedua
            self.parse_expression(statement)
        else:
            self.throw(sub_stmt[0][0].starts_at,
                       "Syntax Error : Invalid statement.")

    def parse_if_stmt(self, statement):
        token = statement[0]
        if token.type != Keyword.IF:
            self.throw(token.starts_at,
                       "Syntax Error : Unexpected token. Expected if keyword.")
        sub_stmts = self.split(statement[1:], Punctuation.COLON)
        if len(sub_stmts) != 2:
            self.throw(token.starts_at,
                       "Syntax Error : Too many colons.")
        self.parse_named_expression(sub_stmts[0])

        block_first_token = sub_stmts[1][0]
        first_token_index = 0
        if block_first_token.type == Literal.WHITESPACE:
            block_first_token = sub_stmts[1][1]
            first_token_index = 1
        if block_first_token.type == Literal.NEWLINE:
            self.next_block()
            self.parse_block()
        else:
            self.parse_simple_statement(sub_stmts[1][first_token_index:])
        cindex = self.index
        self.next_statement()
        statement = self.trim_left(self.statement)
        first_token = statement[0]
        if first_token.type == Keyword.ELIF:
            self.parse_elif_stmt(statement)
        elif first_token.type == Keyword.ELSE:
            self.parse_else_stmt(statement)
        else:
            self.index = cindex

    def parse_elif_stmt(self, statement):
        token = statement[0]
        if token.type != Keyword.ELIF:
            self.throw(token.starts_at,
                       "Syntax Error : Unexpected token. Expected elif keyword.")
        sub_stmts = self.split(statement[1:], Punctuation.COLON)
        if len(sub_stmts) != 2:
            self.throw(token.starts_at,
                       "Syntax Error : Too many colons.")
        self.parse_named_expression(sub_stmts[0])

        block_first_token = sub_stmts[1][0]
        first_token_index = 0
        if block_first_token.type == Literal.WHITESPACE:
            block_first_token = sub_stmts[1][1]
            first_token_index = 1
        if block_first_token.type == Literal.NEWLINE:
            self.next_block()
            self.parse_block()
        else:
            self.parse_simple_statement(sub_stmts[1][first_token_index:])
        cindex = self.index
        self.next_statement()
        statement = self.trim_left(self.statement)
        first_token = statement[0]
        if first_token.type == Keyword.ELIF:
            self.parse_elif_stmt(statement)
        elif first_token.type == Keyword.ELSE:
            self.parse_else_stmt(statement)
        else:
            self.index = cindex

    def parse_else_stmt(self, statement):
        i = 0
        token = statement[i]
        if token.type != Keyword.ELSE:
            self.throw(token.starts_at,
                       "Syntax Error : Unexpected token. Expected else keyword.")
        i += 1
        token = statement[i]
        if token.type == Literal.WHITESPACE:
            i += 1
            token = statement[i]
        if token.type != Punctuation.COLON:
            self.throw(token.starts_at,
                       "Syntax Error : Unexpected token. Expected a colon.")
        i += 1
        token = statement[i]
        if token.type == Literal.WHITESPACE:
            i += 1
            token = statement[i]
        if token.type == Literal.NEWLINE:
            self.next_block()
            self.parse_block()
        else:
            self.parse_simple_statement(statement[i:])

    def parse_while_stmt(self, statement):
        token = statement[0]
        if token.type != Keyword.WHILE:
            self.throw(token.starts_at,
                       "Syntax Error : Unexpected token. Expected while keyword.")
        sub_stmts = self.split(statement[1:], Punctuation.COLON)
        if len(sub_stmts) != 2:
            self.throw(token.starts_at,
                       "Syntax Error : Too many colons.")
        self.parse_named_expression(sub_stmts[0])

        block_first_token = sub_stmts[1][0]
        first_token_index = 0
        if block_first_token.type == Literal.WHITESPACE:
            block_first_token = sub_stmts[1][1]
            first_token_index = 1
        if block_first_token.type == Literal.NEWLINE:
            self.next_block()
            self.parse_block()
        else:
            self.parse_simple_statement(sub_stmts[1][first_token_index:])

        cindex = self.index
        self.next_statement()
        statement = self.trim_left(self.statement)
        first_token = statement[0]
        if first_token.type == Keyword.ELSE:
            self.parse_else_stmt(statement)
        else:
            self.index = cindex

    def parse_for_stmt(self, statement):
        token = statement[0]
        if token.type != Keyword.FOR:
            self.throw(token.starts_at,
                       "Syntax Error : Unexpected token. Expected for keyword.")
        sub_stmts = self.split(statement[1:], Punctuation.COLON)
        if len(sub_stmts) != 2:
            self.throw(token.starts_at,
                       "Syntax Error : Too many colons.")

        left_sub_stmts = self.split(sub_stmts[0], Keyword.IN)
        if len(left_sub_stmts) < 2:
            self.throw(token.starts_at,
                       "Syntax Error : Invalid for loop statement.")
        star_targets = left_sub_stmts[0]
        star_expressions = left_sub_stmts[1]
        i = 2
        while i < len(left_sub_stmts):
            star_expressions.extend(left_sub_stmts[i])
        self.parse_star_target_multiple(star_targets)
        self.parse_star_expression(star_expressions)

        block_first_token = sub_stmts[1][0]
        first_token_index = 0
        if block_first_token.type == Literal.WHITESPACE:
            block_first_token = sub_stmts[1][1]
            first_token_index = 1
        if block_first_token.type == Literal.NEWLINE:
            self.next_block()
            self.parse_block()
        else:
            self.parse_simple_statement(sub_stmts[1][first_token_index:])

        cindex = self.index
        self.next_statement()
        statement = self.trim_left(self.statement)
        first_token = statement[0]
        if first_token.type == Keyword.ELSE:
            self.parse_else_stmt(statement)
        else:
            self.index = cindex

    def parse_empty_stmt(self, statement):
        if len(statement) > 2:
            raise SyntaxError()
        if len(statement) == 2 and statement[0].type != Literal.WHITESPACE:
            raise SyntaxError()

    def parse_named_expression(self, statement):
        statement = self.trim(statement)
        try:
            self.try_stack += 1
            self.parse_assignment(statement)
            self.try_stack -= 1
        except:
            self.try_stack -= 1
            self.parse_expression(statement)

    def trim(self, statement):
        if(len(statement) == 0):
            return []
        start = 0
        end = len(statement)
        if statement[start].type == Literal.WHITESPACE:
            start = 1
        if statement[end - 1].type == Literal.WHITESPACE:
            end -= 1
        return statement[start:end]

    def trim_left(self, statement):
        token = statement[0]
        i = 0
        while token.type == Literal.WHITESPACE and i < len(statement):
            i += 1
            token = statement[i]
        return statement[i:]

    def throw(self, at, message):
        if self.try_stack == 0:
            i = 0
            l = len(self.tokens)
            while self.tokens[i].starts_at[0] != at[0]:
                i += 1
            while i < l and self.tokens[i].starts_at[0] == at[0] and self.tokens[i].type != Literal.ENDMARKER:
                print(self.tokens[i].value, end="")
                i += 1
            if self.tokens[i - 1].value != '\n':
                print()
            print(f"{' ' * at[1]}^^^")
            print(f"An error found at {at[0] + 1}:{at[1] + 1}")
            print(message)
        exit(1)


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
