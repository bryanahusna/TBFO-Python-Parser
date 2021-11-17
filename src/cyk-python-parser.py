def combineTwoProduction(first, second):
    result = []
    for rule1 in first:
        for rule2 in second:
            result.append(rule1 + " " + rule2)
    return result

def checkProductionList(prodlist, grammar):
    result = []
    for prod in prodlist:
        x = checkProduction(prod, grammar)
        result += x
    return result

def checkProduction(symbol, grammar):
    matchedprod = []
    for key in grammar:
        arr = grammar[key]
        for gramsymbol in arr:
            if(gramsymbol == symbol):
                matchedprod.append(key)
    return matchedprod

def translateCnfLine(x):
    x = x.strip()
    if(x == '&spasi;'):
        return ' '
    elif(x == r'\n'):
        return '\n'
    elif(x == r'\t'):
        return '\t'
    else:
        return x

def cnfToDictGrammar(path):
    grammarFile = open(path)
    grammar = {}
    for line in grammarFile:
        line = line.strip()
        if(len(line) == 0): continue
        if(line[0] == '#'): continue
        line = line.split('-->')
        head = line[0].strip()
        body = line[1]
        body = body.split('|')
        body = list(map(translateCnfLine, body))
        if not head in grammar:
            grammar[head] = body
        else:
            grammar[head] += body
    return grammar

def cyk(path, grammar):
    isvalid = True
    fileChecked = open(path)
    bariske = 0
    for line in fileChecked:
        bariske += 1

        line = line.strip()
        n = len(line)
        if n == 0:
            print(f"Baris {bariske} valid")
            continue
        matrix = [["" for j in range(n)] for i in range(n)]

        for i in range(n):
            matrix[0][i] = checkProduction(line[i], grammar)
        for i in range(1, n):
            for j in range(n - i):
                length = i + 1
                matrix[i][j] = []
                for k in range(i):
                    first = matrix[k][j]
                    second = matrix[length - k - 1 - 1][j + k + 1]
                    if len(first) == 0 or len(second) == 0:
                        continue
                    combined = combineTwoProduction(first, second)
                    x = checkProductionList(combined, grammar)
                    matrix[i][j] += x
                matrix[i][j] = list(set(matrix[i][j]))

        if 'S' in matrix[i][j]:
            print(f"Baris {bariske} valid")
        else:
            print(f"Baris {bariske} tidak valid")

grammar = cnfToDictGrammar("python-cnf-grammar.txt")
cyk('test-var.txt', grammar)