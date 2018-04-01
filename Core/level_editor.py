import yaml
import os
import tdl
import random
import argparse
from models.MapObjects import Tile
from models.GameObjects import GameObject, Vector2
from models.EnumStatus import Cardinals
from utils import Colors
from slugify import slugify

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--screensize", type=str, default='20x20',
                    help="sets the size of the screen in tiles using the pattern WxH. Ex.: 20x20")
parser.add_argument("-l", "--load", type=str, help="Load from file")


def load(absolute_file_path):
    with open(absolute_file_path) as stream:
        level_template = yaml.safe_load(stream)

    w, h = load_tile_template(level_template["room_tiles"][0]["map"])
    return w, h, level_template["room_tiles"][0]["name"]


def get_cardinal(x, y):
    if x == 0:
        return Cardinals.WEST
    if x == SCREEN_WIDTH - 1:
        return Cardinals.EAST
    if y == 0:
        return Cardinals.NORTH
    if y == SCREEN_HEIGHT - 1:
        return Cardinals.SOUTH
    raise ReferenceError('The attachment is not posed on a border!')


def load_tile_template (stringified_template):
    global my_map, map_before, objects
    rows = stringified_template
    height = len(rows)
    width = len(rows[0])

    my_map = [[Tile(False, x, y)
      for y in range(height)]
      for x in range(width)]

    for y, row in enumerate(rows):
        for x, char in enumerate(row):
            if char is "#":
                print("painting tile", x, y)
                my_map[x][y] = Tile(True, x, y)
                print(my_map[x][y])
            elif char is ".":
                my_map[x][y] = Tile(False, x, y)
            else:
                obj = GameObject(coord=Vector2(x, y), char=char, color=(255, 255, 255))
                objects.append(obj)

    map_before = [[Tile(my_map[x][y].blocked, x, y)
      for y in range(height)]
      for x in range(width)]

    return width, height


def make_map():
    global my_map, map_before
    # fill map with "unblocked" tiles
    my_map = [[Tile(False, x, y) for y in range(SCREEN_HEIGHT)]
              for x in range(SCREEN_WIDTH)]

    map_before = [[Tile(False, x, y) for y in range(SCREEN_HEIGHT)]
              for x in range(SCREEN_WIDTH)]


def render_all():
    global file_name

    panel.clear(fg=Colors.white, bg=Colors.black)

    if panel_menu == 'save':
        panel.draw_str(1, 0, file_name, fg=Colors.white, bg=None)
        panel.draw_str(1, 1, "n = new", fg=Colors.white, bg=Colors.dark_cyan if editor_option == 'n' else None)
        panel.draw_str(1, 2, "s = save", fg=Colors.white, bg=Colors.dark_chartreuse if editor_option == 's' else None)
        panel.draw_str(1, 3, "q = exit", fg=Colors.white, bg=Colors.dark_gray if editor_option == 'q' else None)

    else:
        panel.draw_str(1, 0, "w = wall/floor", fg=Colors.white, bg=Colors.dark_crimson if editor_option == 'w' else None)
        panel.draw_str(1, 1, "a = attachment", fg=Colors.white, bg=Colors.dark_cyan if editor_option == 'a' else None)
        panel.draw_str(1, 2, "d = door", fg=Colors.white, bg=Colors.dark_chartreuse if editor_option == 'd' else None)
        panel.draw_str(1, 3, "x = monster", fg=Colors.white, bg=Colors.dark_gray if editor_option == 'x' else None)
        panel.draw_str(1, 4, "i = item", fg=Colors.white, bg=Colors.dark_yellow if editor_option == 'i' else None)

    root.blit(panel, 0, PANEL_Y, TOTAL_SCREEN_WIDTH, PANEL_HEIGHT, 0, 0)
    # go through all tiles, and set their background color
    for y in range(SCREEN_HEIGHT):
        for x in range(SCREEN_WIDTH):
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

    start = (min(mouse_coord[0], mouse_starting_position[0]), min(mouse_coord[1], mouse_starting_position[1]))
    end = (max(mouse_coord[0], mouse_starting_position[0])+1, max(mouse_coord[1], mouse_starting_position[1])+1)

    if mouse_left_down:
        if editor_option == 'w':
            for x in range(len(my_map)):
                for y in range(len(my_map[0])):
                    my_map[x][y] = Tile(map_before[x][y].blocked, x, y)

            for x in range(start[0], end[0]):
                for y in range(start[1], end[1]):
                    try:
                        my_map[x][y].block_sight = not my_map[x][y].block_sight
                        my_map[x][y].blocked = my_map[x][y].block_sight
                    except IndexError:
                        pass

    else:
        for x in range(len(my_map)):
            for y in range(len(my_map[0])):
                map_before[x][y] = Tile(my_map[x][y].blocked, x, y)

        if editor_option == 'a':
            coord = Vector2(*mouse_coord)
            position = None
            for n, obj in enumerate(objects):
                if obj.coord == coord:
                    position = n
                    break
            if position is not None and position >= 0:
                del objects[position]
            else:
                try:
                    get_cardinal(*coord)
                    obj = GameObject(coord=coord, char='A', color=(255, 255, 255))
                    objects.append(obj)
                except Exception as e:
                    print("You must place the attachment in the borders of the tile template")


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
    global mouse_coord, mouse_starting_position, mouse_left_down, mouse_right_down
    global editor_option, panel_menu

    user_input = None
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
                mouse_left_down = True
                mouse_starting_position = mouse_coord
                return 'mouse_click'

            if user_input.button == 'RIGHT':
                mouse_right_down = True
                mouse_starting_position = mouse_coord
                return 'mouse_click'

        elif event.type == 'MOUSEUP' and mouse_left_down:
            user_input = event
            if user_input.button == 'LEFT':
                mouse_left_down = False
                return 'mouse_click'

    if not keypress:
        return 'didnt-take-turn'

    if user_input.key == 'ESCAPE':
        if panel_menu == 'save':
            panel_menu = 'editor'
        else:
            panel_menu = 'save'
        return panel_menu

    if user_input.text in ['w', 'a', 'd', 'x', 'i', 's', 'n', 'l', 'q']:
        editor_option = user_input.text
    else:
        editor_option = None

    return 'didnt-take-turn'


def save_panel_options():
    global objects, panel_menu, editor_option
    if editor_option == 'n':
        objects = []
        make_map()
        editor_option = None
        panel_menu = 'editor'

    if editor_option == 's':
        save()
        editor_option = None

    if editor_option == 'q':
        exit()


def save():
    global file_name

    def letter(tile):
        return "#" if tile.blocked else "."

    map_stringified = []

    for row in my_map:
        map_stringified.append([letter(n) for n in row])

    map_stringified = [list(i) for i in zip(*map_stringified)]

    for obj in objects:
        map_stringified[obj.coord.Y][obj.coord.X] = obj.char

    _map_temp = []
    for n, line in enumerate(map_stringified):
        _map_temp.append(''.join(line))

    tdl_input()

    data = {"room_tiles": [{"name": file_name, "map": _map_temp}]}

    file_name = slugify(file_name)
    if ".yaml" not in file_name:
        file_name += ".yaml"

    absolute_file_path = os.path.join(gamedata_dir, file_name)

    with open(absolute_file_path, 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)
        print("Save done!")


def tdl_input():
    global file_name
    string_finished = False

    while not string_finished:
        render_all()
        tdl.flush()

        user_input = tdl.event.key_wait()
        if user_input.key == 'ENTER':
            string_finished = True

        elif user_input.key == 'BACKSPACE':
            if len(file_name):
                file_name = file_name [:-1]

        elif user_input.text:
            file_name += user_input.text


def size_of_tile():
    global tile_height_width, SCREEN_HEIGHT, SCREEN_WIDTH
    render_all()
    tdl.flush()
    tile_height_width = ""
    string_finished = False
    while not string_finished:
        user_input = tdl.event.key_wait()
        if user_input.key == 'ENTER':
            try:
                h, w = int(tile_height_width.split()[0]), int(tile_height_width.split()[1])
                string_finished = True
            except Exception as e:
                tile_height_width = ""
                string_finished = False
        elif user_input.text:
            tile_height_width += user_input.text

        render_all()
        tdl.flush()

    SCREEN_HEIGHT = h
    SCREEN_WIDTH = w


#############################################
# Initialization & Main Loop                #
#############################################

file_name = "new file"

objects = []
mouse_coord = (0, 0)

mouse_right_down = False
mouse_left_down = False
mouse_starting_position = (0, 0)
editor_option = None
panel_menu = 'editor'

args = parser.parse_args()

if args.load:
    SCREEN_WIDTH, SCREEN_HEIGHT, file_name = load(args.load)
else:
    SCREEN_WIDTH = int(args.screensize.split('x')[0])
    SCREEN_HEIGHT = int(args.screensize.split('x')[1])


LIMIT_FPS = 20  # 20 frames-per-second maximum

color_dark_wall = (0, 0, 100)
color_light_wall = (130, 110, 50)
color_dark_ground = (50, 50, 150)
color_light_ground = (200, 180, 50)

gamedata_dir = os.path.join(os.path.dirname(__file__), "gamedata")
assets_dir= os.path.join(os.path.dirname(__file__), "assets")
font = os.path.join(assets_dir, "arial10x10.png")

tdl.set_font(font, greyscale=True, altLayout=True)
tdl.setFPS(LIMIT_FPS)

PANEL_HEIGHT = 5

TOTAL_SCREEN_WIDTH = max(20, SCREEN_WIDTH)
TOTAL_SCREEN_HEIGHT = max(25, SCREEN_HEIGHT+PANEL_HEIGHT)
PANEL_Y = TOTAL_SCREEN_HEIGHT-PANEL_HEIGHT

root = tdl.init(TOTAL_SCREEN_WIDTH, TOTAL_SCREEN_HEIGHT, title="Roguelike", fullscreen=False)
con = tdl.Console(SCREEN_WIDTH, SCREEN_HEIGHT)
panel = tdl.Console(TOTAL_SCREEN_WIDTH, PANEL_HEIGHT)

# player = GameObject(coord=Vector2(SCREEN_WIDTH//2, SCREEN_HEIGHT//2), char='@', color=(255,255,255))

if not args.load:
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

    if panel_menu == 'save':
        save_panel_options()

    if player_action == 'mouse_click' or mouse_left_down:
        set_tile_under_mouse()