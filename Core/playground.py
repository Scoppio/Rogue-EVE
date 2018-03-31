import yaml
import os

gamedata_dir = os.path.join(os.path.dirname(__file__), "gamedata")

map_template = os.path.join(gamedata_dir, "map_tile_templates.yaml")

with open(map_template) as stream:
    level_template = yaml.safe_load(stream)

print(level_template)

def make_tile (map):
    rows = map.split()
    height = len(rows)
    width = len(rows[0])
    door_map = []
    new_map = [[(True, x, y)
      for y in range(height)]
      for x in range(width)]

    for y, row in enumerate(rows):
        for x, char in enumerate(row):
            if char == "#":
                new_map[x][y] = (True, x, y)
            if char == ".":
                new_map[x][y] = (False, x, y)
            if char == "D":
                new_map[x][y] = (True, x, y)
                door_map = (x,y)

make_tile(level_template["room_tiles"]["map"])
