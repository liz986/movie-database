def f1(x):
    def f2(y):
        return(x+y)
    return f2
p = f1(5)
t = p(6)
print(t)

