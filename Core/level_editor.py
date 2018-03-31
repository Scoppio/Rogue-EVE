import yaml
import os
import tdl
import argparse
from models.MapObjects import Tile
from models.GameObjects import GameObject, Vector2

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--loglevel", type=int, default=2,
                    help="increase output verbosity")
parser.add_argument("-s", "--screensize", type=str, default='80x50',
                    help="sets the size of the screen in tiles using the pattern WxH. Ex.: 80x50, 100x75")
args = parser.parse_args()

SCREEN_WIDTH = int(args.screensize.split('x')[0])
SCREEN_HEIGHT = int(args.screensize.split('x')[1])
LIMIT_FPS = 20  # 20 frames-per-second maximum

MAP_WIDTH = SCREEN_WIDTH
MAP_HEIGHT = SCREEN_HEIGHT

color_dark_wall = (0, 0, 100)
color_light_wall = (130, 110, 50)
color_dark_ground = (50, 50, 150)
color_light_ground = (200, 180, 50)

gamedata_dir = os.path.join(os.path.dirname(__file__), "gamedata")
assets_dir= os.path.join(os.path.dirname(__file__), "assets")
font = os.path.join(assets_dir, "arial10x10.png")

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


def make_map():
    global my_map, map_before

    # fill map with "unblocked" tiles
    my_map = [[Tile(False, x, y) for y in range(MAP_HEIGHT)]
              for x in range(MAP_WIDTH)]

    map_before = [[Tile(False, x, y) for y in range(MAP_HEIGHT)]
              for x in range(MAP_WIDTH)]


def render_all():
    # go through all tiles, and set their background color
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            wall = my_map[x][y].block_sight
            if wall:
                con.draw_char(x, y, None, fg=None, bg=color_dark_wall)
            else:
                con.draw_char(x, y, None, fg=None, bg=color_dark_ground)

    # draw all objects in the list
    for obj in objects:
        obj.draw(console=con)

    # blit the contents of "con" to the root console and present it
    root.blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0)


def set_tile_under_mouse():
    global my_map
    global map_before
    print("!!!")

    start = (min(mouse_coord[0], mouse_starting_position[0]), min(mouse_coord[1], mouse_starting_position[1]))
    end = (max(mouse_coord[0], mouse_starting_position[0])+1, max(mouse_coord[1], mouse_starting_position[1])+1)
    if mouse_is_holding_down:

        for x in range(len(my_map)):
            for y in range(len(my_map[0])):
                my_map[x][y] = Tile(map_before[x][y].blocked, x, y)

        for x in range(start[0], end[0]):
            for y in range(start[1], end[1]):
                my_map[x][y].block_sight = not my_map[x][y].block_sight
                my_map[x][y].blocked = my_map[x][y].block_sight
    else:
        for x in range(len(my_map)):
            for y in range(len(my_map[0])):
                map_before[x][y] = Tile(my_map[x][y].blocked, x, y)


def is_blocked(x, y):
    return my_map[x][y].blocked


def player_move_or_attack(dx, dy):
    global fov_recompute, player
    # attack if target found, move otherwise
    fov_recompute = True

    #move by the given amount, if the destination is not blocked
    if not is_blocked(player.coord.X + dx, player.coord.Y + dy):
        player.coord.X += dx
        player.coord.Y += dy


def handle_keys():
    global mouse_coord
    global mouse_is_holding_down
    global mouse_starting_position

    keypress = False

    for event in tdl.event.get():
        if event.type == 'KEYDOWN':
            user_input = event
            keypress = True
        if event.type == 'MOUSEMOTION':
            mouse_coord = event.cell

        elif event.type == 'MOUSEDOWN':
            user_input = event
            if user_input.button == 'LEFT':
                print("click", mouse_coord)
                mouse_is_holding_down = True
                mouse_starting_position = mouse_coord
                return 'mouse_click'

        elif event.type == 'MOUSEUP' and mouse_is_holding_down:
            user_input = event
            if user_input.button == 'LEFT':
                print("clock", mouse_coord)
                mouse_is_holding_down = False
                return 'mouse_click'


    if not keypress:
        return 'didnt-take-turn'

    if user_input.key == 'ENTER' and user_input.alt:
        # Alt+Enter: toggle fullscreen
        tdl.set_fullscreen(not tdl.get_fullscreen())

    elif user_input.key == 'ESCAPE':
        return 'exit'  # exit game

        # movement keys
    if user_input.key == 'UP':
        player_move_or_attack(0, -1)

    elif user_input.key == 'DOWN':
        player_move_or_attack(0, 1)

    elif user_input.key == 'LEFT':
        player_move_or_attack(-1, 0)

    elif user_input.key == 'RIGHT':
        player_move_or_attack(1, 0)
    else:
        return 'didnt-take-turn'


#############################################
# Initialization & Main Loop                #
#############################################

tdl.set_font(font, greyscale=True, altLayout=True)
tdl.setFPS(LIMIT_FPS)
root = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="Roguelike", fullscreen=False)
tdl.setFPS(LIMIT_FPS)
con = tdl.Console(SCREEN_WIDTH, SCREEN_HEIGHT)

player = GameObject(coord=Vector2(SCREEN_WIDTH//2, SCREEN_HEIGHT//2), char='@', color=(255,255,255))

objects = [player]
mouse_coord = (0, 0)

mouse_is_holding_down = False
mouse_starting_position = (0,0)

make_map()

while not tdl.event.is_window_closed():
    # draw all objects in the list

    render_all()

    tdl.flush()

    # erase all objects at their old locations, before they move
    for obj in objects:
        obj.clear(console=con)

    # handle keys and exit game if needed
    player_action = handle_keys()
    if player_action == 'exit':
        break
    if player_action == 'mouse_click' or mouse_is_holding_down:
        set_tile_under_mouse()