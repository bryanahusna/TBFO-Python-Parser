for i in range(10):
    print(i)


def func4(a, b, c):
    x = c
    x -= b
    y = x
    y += x
    y = y // 2
    y += b
    if y > a:
        y -= 1
        return 2 * func4(a, b, y)
    elif y < a:
        x = 0
        return 2 * func4(a, y + 1, c) + 1
    else:
        return 0


x = func4(7, 0, 1)
