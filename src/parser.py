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

    def parse(self, filename):
        with open(filename) as f:
            for line in f:
                self.lines.append(line)
        tokenizer = Tokenizer()
        self.tokens = tokenizer.tokenize(filename)
        # for token in self.tokens:
        #     print(token.type.name)

        self.parse_indents()
        self.next_statement()
        while self.statement[-1].type != Literal.ENDMARKER:
            self.parse_simple_statement(self.statement)
            self.next_statement()
        self.parse_simple_statement(self.statement)

        # self.next_statement()
        # while(self.index < len(self.tokens)-1):
        #     # print(len(self.tokens))
        #     # Dimulai dari token ke 0 di statement
        #     # print(self.parse_expression(0))
        #     self.parse_simple_statement(self.statement)
        #     self.next_statement()
        # print(self.parse_expression(0))

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
                raise IndentationError()
            elif expect_indent:
                expect_indent = False

            if token.is_opening_bracket():
                bracket_stack.append(token.type)
            elif token.is_closing_bracket():
                if len(bracket_stack) == 0:
                    raise SyntaxError(
                        "Closing bracket appeared before any opening bracket")
                match bracket_stack[-1]:
                    case Punctuation.PARENTHESIS_OPEN:
                        if token.type != Punctuation.PARENTHESIS_CLOSE:
                            raise SyntaxError("Bracket mismatch")
                    case Punctuation.SQUARE_BRACKET_OPEN:
                        if token.type != Punctuation.SQUARE_BRACKET_CLOSE:
                            raise SyntaxError("Bracket mismatch")
                    case Punctuation.BRACKET_OPEN:
                        if token.type != Punctuation.BRACKET_CLOSE:
                            raise SyntaxError("Bracket mismatch")
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
            raise SyntaxError(
                "Bracket error.")
        if indent_stack != 0:
            raise IndentationError("Indentation error in a single statement.")

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

    def parse_block(self, block):
        indent_stack = 0
        past = False
        while indent_stack != 0 or not past:
            self.next_statement()
            if self.statement[0].type == Indentation.INDENT:
                indent_stack += 1
                past = True
            elif self.statement[0].type == Indentation.DEDENT:
                while self.statement[0].type == Indentation.DEDENT:
                    indent_stack -= 1
                    self.statement = self.statement[1:]
            self.parse_simple_statement(self.statement)

    def parse_simple_statement(self, statement):
        # ENDMARKER only statement
        if len(statement) == 0:
            return

        first_token = statement[0]      # type: Token

        # TODO: Cek setiap token awal yang mungkin sebagai
        # simple_statement

        match first_token.type:
            # Ignore empty statement
            case Literal.NEWLINE:
                pass
            # Single keyword statement
            case Keyword.PASS:
                pass
            case Keyword.BREAK:
                if len(self.loop_stack) > 0:
                    next_token = statement[1]
                    if next_token.type == Literal.NEWLINE:
                        pass
                    elif next_token.type == Literal.WHITESPACE:
                        next_token = statement[2]
                    else:
                        raise SyntaxError("Unexpected token")
                    if next_token.type != Literal.NEWLINE:
                        raise SyntaxError("Unexpected token")
                else:
                    raise SyntaxError(
                        "break keyword must be placed in a loop statement.")
            case Keyword.CONTINUE:
                if len(self.loop_stack) > 0:
                    next_token = statement[1]
                    if next_token.type == Literal.NEWLINE:
                        pass
                    elif next_token.type == Literal.WHITESPACE:
                        next_token = statement[2]
                    else:
                        raise SyntaxError("Unexpected token")
                    if next_token.type != Literal.NEWLINE:
                        raise SyntaxError("Unexpected token")
                else:
                    raise SyntaxError(
                        "continue keyword must be placed in a loop statement.")
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
                    raise SyntaxError()
            # TODO: Add assignment & star_expressions
            # first token here

            # Function definition statement
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
                self.parse_while_stmt(statement)
                self.loop_stack.pop()
            # While statement
            case Keyword.WHILE:
                self.loop_stack.append(Keyword.WHILE)
                self.parse_while_stmt(statement)
                self.loop_stack.pop()
            # Invalid first token
            case _:
                raise SyntaxError()

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

    def parse_expression(self, statement):
        # statement berisi potongan ekspresi yang ingin dicek
        i = 0
        n = len(statement)
        while(i < n and statement[i].type == Literal.WHITESPACE):
            i += 1
        token = statement[i]
        if(token.type == Literal.NEWLINE or token.type == Literal.ENDMARKER):
            raise SyntaxError("Invalid expression")

        bracketstack = []
        numberstack = []
        operatorstack = []
        previoustoken = None
        while(i < n):
            token = statement[i]
            #print(token.type.name)
            if(token.type == Literal.WHITESPACE or token.type == Literal.NEWLINE):
                pass
            elif(len(bracketstack) > 0 and token.type == Literal.ENDMARKER):
                raise SyntaxError("Invalid expression")

            elif(token.type == Literal.NUMBER or token.type == Literal.NAME or token.type == Keyword.TRUE or token.type == Keyword.FALSE or token.type == Keyword.NONE):
                if(len(numberstack) == 0):
                    numberstack.append(token)
                    if(len(operatorstack) > 0 and self.isUnaryOperator(operatorstack[-1])):
                        operatorstack.pop()
                else:
                    if(len(operatorstack) == 0 and len(numberstack) > 0):
                        raise SyntaxError("Invalid expression")
                    else:
                        operator = operatorstack.pop()
                        while(self.isUnaryOperator(operator)):
                            operatorprev = operator
                            operator = operatorstack.pop()
                            if(self.isUnaryOperator(operator) and (operatorprev.type != operator.type)):
                                raise SyntaxError("Invalid expression")

            elif(self.isBinaryOperator(token)):
                if(len(numberstack) == 0):
                    raise SyntaxError("Invalid expression")
                else:
                    operatorstack.append(token)
            elif(self.isUnaryOperator(token)):
                operatorstack.append(token)

            elif(token.type == Punctuation.PARENTHESIS_OPEN):
                bracketstack.append(Punctuation.PARENTHESIS_OPEN)
            elif(token.type == Punctuation.BRACKET_OPEN):
                bracketstack.append(Punctuation.BRACKET_OPEN)
            elif(token.type == Punctuation.SQUARE_BRACKET_OPEN):
                bracketstack.append(Punctuation.SQUARE_BRACKET_OPEN)

            elif(token.type == Punctuation.PARENTHESIS_CLOSE):
                if(len(bracketstack) == 0 or bracketstack[-1] != Punctuation.PARENTHESIS_OPEN):
                    raise SyntaxError("Invalid expression")
                else:
                    bracketstack.pop()
            elif(token.type == Punctuation.BRACKET_CLOSE):
                if(len(bracketstack) == 0 or bracketstack[-1] != Punctuation.BRACKET_OPEN):
                    raise SyntaxError("Invalid expression")
                else:
                    bracketstack.pop()
            elif(token.type == Punctuation.SQUARE_BRACKET_CLOSE):
                if(len(bracketstack) == 0 or bracketstack[-1] != Punctuation.SQUARE_BRACKET_OPEN):
                    raise SyntaxError("Invalid expression")
                else:
                    bracketstack.pop()

            if(token.type != Literal.WHITESPACE and token.type != Literal.NEWLINE):
                previoustoken = token
            i += 1

        if(len(operatorstack) > 0):
            raise SyntaxError("Invalid expression")


    def isUnaryOperator(self, token):
        if(token.type == Keyword.NOT or token.type == Operator.BITWISE_NOT):
            return True
        else:
            return False

    def isBinaryOperator(self, token):
        if(token.type == Keyword.AND or token.type == Keyword.OR):
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

        return False

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
        while token.type != Keyword.IMPORT:
            if token.type not in [Literal.WHITESPACE, Indentation.INDENT,
                                  Indentation.DEDENT]:
                raise SyntaxError()
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
            raise SyntaxError()
        token = statement[1]
        if token.type != Literal.WHITESPACE:
            raise SyntaxError()
        token = statement[2]
        i = 2
        while token.type in [Punctuation.ACCESSOR, Literal.ELLIPSIS]:
            i += 1
            token = statement[i]
            if (token.type != Literal.WHITESPACE):
                raise SyntaxError()
            i += 1
            token = statement[i]
        token = statement[i]
        if token.type != Keyword.IMPORT:
            sub_stmts = self.split(statement[i:], Keyword.IMPORT)
            if len(sub_stmts) != 2:
                raise SyntaxError()
            sub_stmts[0] = self.trim(sub_stmts[0])
            self.parse_dotted_name(sub_stmts[0])
            self.parse_import_from_targets(sub_stmts[1])
        else:
            i += 1
            token = statement[i]
            if token.type != Literal.WHITESPACE:
                raise SyntaxError()
            self.parse_import_from_targets(statement[i + 1:])

    def parse_import_from_targets(self, statement):
        statement = self.trim(statement)
        first_token = statement[0]
        match first_token.type:
            case Operator.MULTIPLICATION:
                token = statement[1]
                if token.type != Literal.NEWLINE:
                    raise SyntaxError()
            case Punctuation.PARENTHESIS_OPEN:
                last_token = statement[-2]
                if last_token.type != Punctuation.PARENTHESIS_CLOSE:
                    raise SyntaxError()
                last = -2
                if statement[last - 1].type == Literal.WHITESPACE:
                    last -= 1
                if statement[last - 1].type == Punctuation.COMMA:
                    last -= 1
                sub_stmt = statement[1:last]
                self.parse_import_from_as_names(sub_stmt)
            case _:
                if statement[-2].type == Punctuation.COMMA:
                    raise SyntaxError()
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
            raise SyntaxError()
        if len(statement) > 1:
            if len(statement) != 5:
                raise SyntaxError()
            if statement[1].type != Literal.WHITESPACE:
                raise SyntaxError()
            if statement[2].type != Keyword.AS:
                raise SyntaxError()
            if statement[3].type != Literal.WHITESPACE:
                raise SyntaxError()
            if statement[4].type != Literal.NAME:
                raise SyntaxError()

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
            raise SyntaxError()
        if len(sub_stmts) == 2:
            [dotted_name, name] = sub_stmts
            name = self.trim(name)
            if len(name) != 1:
                raise SyntaxError()
            name = name[0]
            if name.type != Literal.NAME:
                raise SyntaxError()
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
            i += 1
        res.append(statement[li:])
        return res

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
            raise SyntaxError("Raise Expression not valid")

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
            raise SyntaxError()

        if (len(sub_stmts) > 0):
            left = self.trim(sub_stmts[0])

        if (left[0].type != Literal.NAME):
            raise SyntaxError()

        if (len(left) > 1):
            if (left[1].type != Punctuation.PARENTHESIS_OPEN or left[-1].type != Punctuation.PARENTHESIS_CLOSE):
                raise SyntaxError()
            else:
                params_stmt = left[2:-1]
                self.parse_params(params_stmt)
                # print("finish parse params")

        right = sub_stmts[1]
        self.parse_block(right)
        # print("finish parse function_def")

    def parse_params(self, statement):
        # TODO recheck algorithm

        # pisah pake koma, trus cek =, ke kanan harus ada = semua
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
                raise SyntaxError()

            if (equalSign):
                if (len(new_stmt) != 2):
                    raise SyntaxError
                if (len(new_stmt[-1]) > 0):
                    right = self.trim(new_stmt[-1])
                    self.parse_expression(right)
                else:
                    raise SyntaxError()

        print("finish parse params")

    def parse_class_def(self, statement):
        # Parse grammar class_def
        # NAME ['(' [arguments] ')' ] ':' block

        # Proses :
        # [1] Split di colon, kalau hasilnya != 2 berarti syntax error
        # [2] Cek di sub_stmts[0] ada parenthesis open dan close
        # [3] Kalo ada params, parse_params
        # [4] parse_block

        # TODO : recheck algorithm

        sub_stmts = self.split(statement, Punctuation.COLON)
        if (len(sub_stmts) != 2):
            raise SyntaxError()

        if (len(sub_stmts) > 0):
            left = self.trim(sub_stmts[0])

        if (left[0].type != Literal.NAME):
            raise SyntaxError()

        if (len(left) > 1):
            if (left[1].type != Punctuation.PARENTHESIS_OPEN or left[-1].type != Punctuation.PARENTHESIS_CLOSE):
                raise SyntaxError()
            else:
                arguments_stmt = left[2:-1]
                if (len(arguments_stmt) != 0):
                    self.parse_arguments(arguments_stmt)
                    # print("finish parse arguments")

        right = sub_stmts[1]
        self.parse_block(right)
        # print("finish parse class")

    def parse_arguments(self, statement):
        # args [','] &')'

        # TODO : recheck algorithm
        statements = self.split(statement, Punctuation.COMMA)
        for stmt in statements:
            self.parse_args(stmt)

        # print("finish parse arguments")

    def parse_args(self, statement):
        # ','.(starred_expression | ( assignment_expression | expression !':=') !'=')+ [',' kwargs ]
        # kwargs

        # TODO : bikin algoritma
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
                raise SyntaxError()

            if (equalSign):
                if (len(new_stmt) != 2):
                    raise SyntaxError
                if (len(new_stmt[-1]) > 0):
                    right = self.trim(new_stmt[-1])
                    self.parse_expression(right)
                else:
                    raise SyntaxError()

        # print("finish parse args")

    def parse_with_stmt(self, statement):
        # 'with' '(' ','.with_item+ ','? ')' ':' block
        # 'with' ','.with_item+ ':' block

        # TODO : recheck algorithm

        sub_stmts = self.split(statement, Punctuation.COLON)
        if (len(sub_stmts) != 2):
            raise SyntaxError()

        left = self.trim(sub_stmts[0])

        if (left[1].type != Punctuation.PARENTHESIS_OPEN == left[-1].type != Punctuation.PARENTHESIS_CLOSE):
            raise SyntaxError()
        elif (left[1].type != Punctuation.PARENTHESIS_OPEN):
            left = left[1:-1]

        with_item_stmt = self.split(left, Punctuation.COMMA)
        for with_item in with_item_stmt:
            self.parse_with_item(with_item)

        # parse block
        self.parse_block(sub_stmts[-1])
        # print("finish parse with_stmt")

    def parse_with_item(self, statement):
        # expression 'as' star_target
        # expression

        # TODO : recheck algorithm
        sub_stmt = self.split(statement, Keyword.AS)
        if (len(sub_stmt) == 2):
            # masuk ke cabang pertama
            self.parse_expression(sub_stmt[0])
            self.parse_star_target(sub_stmt[1])
        elif (len(sub_stmt) == 1):
            # masuk ke cabang kedua
            self.parse_expression(statement)
        else:
            raise SyntaxError()

        print("finish parse with item")

    def parse_if_stmt(self, statement):
        token = statement[0]
        if token.type != Keyword.IF:
            raise SyntaxError()
        sub_stmts = self.split(statement[2:], Punctuation.COLON)
        if len(sub_stmts) != 2:
            raise SyntaxError()
        self.parse_named_expression(sub_stmts[0])

        block_first_token = sub_stmts[1][0]
        first_token_index = 0
        if block_first_token.type == Literal.WHITESPACE:
            block_first_token = sub_stmts[1][1]
            first_token_index = 1
        if block_first_token.type == Literal.NEWLINE:
            self.next_block()
            self.parse_block(self.block)
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
            raise SyntaxError()
        sub_stmts = self.split(statement[2:], Punctuation.COLON)
        if len(sub_stmts) != 2:
            raise SyntaxError()
        self.parse_named_expression(sub_stmts[0])

        block_first_token = sub_stmts[1][0]
        first_token_index = 0
        if block_first_token.type == Literal.WHITESPACE:
            block_first_token = sub_stmts[1][1]
            first_token_index = 1
        if block_first_token.type == Literal.NEWLINE:
            self.next_block()
            self.parse_block(self.block)
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
            raise SyntaxError()
        i += 1
        token = statement[i]
        if token.type == Literal.WHITESPACE:
            i += 1
            token = statement[i]
        if token.type != Punctuation.COLON:
            raise SyntaxError()
        i += 1
        if token.type == Literal.WHITESPACE:
            i += 1
            token = statement[i]
        if token.type == Literal.NEWLINE:
            self.next_block()
            self.parse_block(self.block)
        else:
            self.parse_simple_statement(statement[i:])

    def parse_while_stmt(self, statement):
        token = statement[0]
        if token.type != Keyword.WHILE:
            raise SyntaxError()
        sub_stmts = self.split(statement[2:], Punctuation.COLON)
        if len(sub_stmts) != 2:
            raise SyntaxError()
        self.parse_named_expression(sub_stmts[0])

        block_first_token = sub_stmts[1][0]
        first_token_index = 0
        if block_first_token.type == Literal.WHITESPACE:
            block_first_token = sub_stmts[1][1]
            first_token_index = 1
        if block_first_token.type == Literal.NEWLINE:
            self.next_block()
            self.parse_block(self.block)
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
            raise SyntaxError()
        sub_stmts = self.split(statement[2:], Punctuation.COLON)
        if len(sub_stmts) != 2:
            raise SyntaxError()

        left_sub_stmts = self.split(sub_stmts[0], Keyword.IN)
        if len(left_sub_stmts) < 2:
            raise SyntaxError()
        star_targets = left_sub_stmts[0]
        star_targets_tokens = len(star_targets)
        star_expressions = left_sub_stmts[star_targets_tokens:]
        self.parse_star_targets(star_targets)
        self.parse_star_expressions(star_expressions)

        block_first_token = sub_stmts[1][0]
        first_token_index = 0
        if block_first_token.type == Literal.WHITESPACE:
            block_first_token = sub_stmts[1][1]
            first_token_index = 1
        if block_first_token.type == Literal.NEWLINE:
            self.next_block()
            self.parse_block(self.block)
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

    def parse_star_terget(self, statement):
        pass

    def parse_star_targets(self, statement):
        pass

    def parse_star_expressions(self, statement):
        pass

    def parse_empty_stmt(self, statement):
        if len(statement) > 2:
            raise SyntaxError()
        if len(statement) == 2 and statement[0].type != Literal.WHITESPACE:
            raise SyntaxError()

    def parse_named_expression(self, statement):
        statement = self.trim(statement)
        try:
            self.parse_assignment_expression(statement)
        except:
            self.parse_expression(statement)

    def parse_assignment_expression(self, statement):
        pass

    # def parse_expression(self, statement):
    #    pass

    def trim(self, statement):
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


parser = Parser()
parser.parse("test.py")
