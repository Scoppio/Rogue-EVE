import os
from utils import Colors
colors = [color for color in dir(Colors) if "__" not in color]

print(
    colors
)