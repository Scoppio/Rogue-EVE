
def foo(**kwargs):
    print(kwargs["a"])
    for k, v in kwargs.items():
        print(type(k,), k, type(v), v)

bar = {"a": 0, "b": "alpha", "person": "Kassandra"}

foo(foobar=[1,2,3], **bar)

print("Olá {person}".format(world="world", **bar))
