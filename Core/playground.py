import random
from models.MapObjects import Rect

a = Rect(4, 5, 10, 6)

print([i for i in range(a.x1, a.x2)])