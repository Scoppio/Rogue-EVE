from models.GameObjects import Vector2

a = Vector2(0, 1)
x, y = a

b = (2,3)
c = Vector2(*b)

print(c)