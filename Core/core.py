import os
import tdl
from tcod import image_load
import logging
import argparse
import textwrap
import shelve
from pathlib import Path
from utils import Colors
from managers import ObjectManager, ObjectPool, Messenger
from managers.GenericControllerObjects import GameContext
from models.GameObjects import Character, Vector2
from models.EnumStatus import EGameState, EAction, MapTypes
from models.MapObjects import MapConstructor, MapObjectsConstructor

# Based on the tutorial from RogueBasin for python3 with tdl
# Adapted to use more objects and be more loosely tied, without many global variables and constants
# http://www.roguebasin.com/index.php?title=Roguelike_Tutorial,_using_python3%2Btdl,_part_7

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--loglevel", type=int, default=0,
                    help="increase output verbosity")
parser.add_argument("-s", "--screensize", type=str, default='80x50',
                    help="sets the size of the screen in tiles using the pattern WxH. Ex.: 80x50, 100x75")
parser.add_argument("--fps", type=int, default=7,
                    help="Defines the fps, and therefore the speed of the game")
parser.add_argument("--realtime", help="run the game in realtime as oposed to turn based",
                    action="store_true")
parser.add_argument("--legacy", help="Prints the tiles as characters",
                    action="store_true")
parser.add_argument("--darkness", help="Does not keep memory of what was already visited",
                    action="store_true")
parser.add_argument("-L", "--level_file", type=str, default='map_data1.yaml',
                    help="Selects a different level file to use")
parser.add_argument("-P", "--player_file", type=str, default='player.yaml',
                    help="Selects a different player file to use")

args = parser.parse_args()
#########################################
# Constants
#########################################

SCREEN_WIDTH = int(args.screensize.split('x')[0])
SCREEN_HEIGHT = int(args.screensize.split('x')[1])
INVENTORY_WIDTH = 50
# sizes and coordinates relevant for the GUI
BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT

MSG_X = BAR_WIDTH + 2
MSG_Y = 1
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1

MAP_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT-PANEL_HEIGHT)
LIMIT_FPS = args.fps
REALTIME = args.realtime
LEGACY_MODE = args.legacy
LOGLEVEL = {0: logging.DEBUG, 1:logging.INFO, 2: logging.WARNING, 3: logging.ERROR, 4: logging.CRITICAL}

# loading gamedata, level objects, player information, etc.
gamedata_dir = os.path.join(os.path.dirname(__file__), "gamedata")
tiles_dir = os.path.join(gamedata_dir, "tiles")
assets_dir = os.path.join(os.path.dirname(__file__), "assets")

LEVEL_DATA = os.path.join(gamedata_dir, args.level_file)
PLAYER_DATA = os.path.join(gamedata_dir, args.player_file)

# instantiating logger
logging.basicConfig(
    filename='debug.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=LOGLEVEL[args.loglevel]
)

log_file = os.path.abspath(os.path.join(str(Path.home()), 'rogue_eve.log'))

logger = logging.getLogger('Rogue-EVE')
logger.setLevel(LOGLEVEL[args.loglevel])
# create file handler which logs even debug messages
fh = logging.FileHandler(log_file)
fh.setLevel(LOGLEVEL[args.loglevel])
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(LOGLEVEL[args.loglevel])
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

root_view = None
game_context = None


def main_menu():
    img = image_load(os.path.join(assets_dir, 'menu_background.png'))
    # show the background image, at twice the regular console resolution

    offset_x = (SCREEN_WIDTH - 80) // 2
    offset_y = (SCREEN_HEIGHT - 50) // 2

    while not tdl.event.is_window_closed():
        img.blit_2x(root_view, offset_x, offset_y)

        # show the game's title, and some credits!
        title = 'ROGUELIKE'
        center = (SCREEN_WIDTH - len(title)) // 2
        root_view.draw_str(center, 2, title, bg=None, fg=Colors.light_yellow)

        title = 'By Scoppio'
        center = (SCREEN_WIDTH - len(title)) // 2
        root_view.draw_str(center, SCREEN_HEIGHT - 2, title, bg=None, fg=Colors.light_yellow)

        # show options and wait for the player's choice
        choice = menu('', ['Play a new game', 'Continue last game', 'Quit'], 24)

        if choice == 0:  # new game
            new_game()
            play_game()
        elif choice == 1:
            load()
            play_game()
        elif choice == 2:  # quit
            break


def menu(header, options, width):
    if len(options) > 26:
        raise ValueError('Cannot have a menu with more than 26 options.')
    # calculate total height for the header (after textwrap) and one line per option
    header_wrapped = []
    for header_line in header.splitlines():
        header_wrapped.extend(textwrap.wrap(header_line, width))
    header_height = len(header_wrapped)
    height = len(options) + header_height
    # create an off-screen console that represents the menu's window
    window = tdl.Console(width, height)

    # print the header, with wrapped text
    window.draw_rect(0, 0, width, height, None, fg=Colors.white, bg=None)
    for i, line in enumerate(header_wrapped):
        window.draw_str(0, 0 + i, header_wrapped[i])

    y = header_height
    letter_index = ord('1')
    for option_text in options:
        text = '(' + chr(letter_index) + ') ' + option_text
        window.draw_str(0, y, text, bg=None)
        y += 1
        letter_index += 1

    #blit the contents of "window" to the root console
    x = SCREEN_WIDTH//2 - width//2
    y = SCREEN_HEIGHT//2 - height//2
    root_view.blit(window, x, y, width, height, 0, 0)
    # present the root console to the player and wait for a key-press
    tdl.flush()
    key = tdl.event.key_wait()
    key_char = key.char
    if key_char == '':
        key_char = ' '  # placeholder

    if key.key == 'ENTER' and key.alt:  # (special case) Alt+Enter: toggle fullscreen
        tdl.set_fullscreen(not tdl.get_fullscreen())

    #convert the ASCII code to an index; if it corresponds to an option, return it
    index = ord(key_char) - ord('1')
    if index >= 0 and index < len(options):
        return index
    return None


def next_level():
    global game_context
    # advance to the next level
    Messenger.send_message('You take a moment to rest, and recover your strength.', Colors.light_violet)
    player = game_context.player
    player.fighter.heal_percent(0.5)  # heal the player by 50%

    game_context.object_pool.clear_object_pool(keep_player=True)
    game_context.set_map(
        make_map()
    )

    MapObjectsConstructor(
        game_instance=game_context
    ).load_object_templates(
        LEVEL_DATA
    ).populate_map()

    player.coord = game_context.map.get_rooms()[0].center()

    Messenger.send_message('After a rare moment of peace, you descend deeper into the heart of the dungeon...', Colors.red)

    viewport = ObjectManager.ConsoleBuffer(
        root_view,
        object_pool=game_context.object_pool,
        map=game_context.map,
        width=MAP_SIZE[0],
        height=MAP_SIZE[1],
        origin=Vector2.zero(),
        target=Vector2.zero(),
        mouse_controller=game_context.mouse_controller
    )

    lower_gui_renderer = ObjectManager.ConsoleBuffer(
        root_view,
        origin=Vector2(0, SCREEN_HEIGHT - PANEL_HEIGHT),
        target=Vector2(0, 0),
        width=SCREEN_WIDTH,
        height=PANEL_HEIGHT,
        mouse_controller=game_context.mouse_controller
    )

    lower_gui_renderer.add_message_console(MSG_WIDTH, MSG_HEIGHT, MSG_X, MSG_Y)

    lower_gui_renderer.add_bar(
        1, 1, BAR_WIDTH, 'HP', 'hp', 'max_hp', player.fighter, Colors.light_red, Colors.darker_red
    )

    game_context.camera = viewport
    game_context.lower_gui_renderer = lower_gui_renderer


def new_game():
    global game_context

    # Start to setup the object which will handle most of the generally accessed stuff
    # GameContext will keep setup of the object managers
    # ObjectPool keeps track of all the objects on the scene
    # Starting up the collision handler, which manages all the objects collision events
    # Adding the object pool and the map to the collision handler so they interact
    game_context = GameContext(next_level=next_level, game_state=ObjectManager.GameState(EGameState.LOADING), real_time=REALTIME, menu=menu)

    game_context.set_object_pool(ObjectPool.ObjectPool())

    # A map constructor, that randomly create rooms with (not yet implemented) many different strategies
    # Legacy mode makes the map be drawn using chars instead of colored blocks
    game_context.set_map(
        make_map()
    )

    # Before we start the map objects constructor we load the level data that is being hold on a file
    # With all the information necessary to build the monsters from the template
    # Map objects constructor is a special factory that randomly populates the map with object templates
    # and does deal with weighted distributions, It makes everything in place, by reference

    MapObjectsConstructor(
        game_instance=game_context
    ).load_object_templates(
        LEVEL_DATA
    ).populate_map()

    # Creation of the player
    player = Character.load(
        yaml_file=PLAYER_DATA,
        coord=game_context.map.get_rooms()[0].center(),
        collision_handler=game_context.collision_handler,
        inventory=list(),
        game_state=game_context.game_state
    )

    game_context.set_player(player, inventory_width=INVENTORY_WIDTH)

    viewport = ObjectManager.ConsoleBuffer(
        root_view,
        object_pool=game_context.object_pool,
        map=game_context.map,
        width=MAP_SIZE[0],
        height=MAP_SIZE[1],
        origin=Vector2.zero(),
        target=Vector2.zero(),
        mouse_controller=game_context.mouse_controller
    )

    lower_gui_renderer = ObjectManager.ConsoleBuffer(
        root_view,
        origin=Vector2(0, SCREEN_HEIGHT - PANEL_HEIGHT),
        target=Vector2(0, 0),
        width=SCREEN_WIDTH,
        height=PANEL_HEIGHT,
        mouse_controller=game_context.mouse_controller
    )

    lower_gui_renderer.add_message_console(MSG_WIDTH, MSG_HEIGHT, MSG_X, MSG_Y)

    lower_gui_renderer.add_bar(
        1, 1, BAR_WIDTH, 'HP', 'hp', 'max_hp', player.fighter, Colors.light_red, Colors.darker_red
    )

    # a warm welcoming message!
    Messenger.send_message('Welcome stranger! Prepare to perish in the Tombs of the Ancient Kings.', Colors.red)

    game_context.game_state.set_state(EGameState.PLAYING)
    game_context.camera = viewport
    game_context.lower_gui_renderer = lower_gui_renderer

    return game_context


def make_map(starting_room="room-02.yaml", max_rooms=3):
    return MapConstructor(
        MAP_SIZE[0],
        MAP_SIZE[1],
        max_number_of_rooms=max_rooms
    ).add_starting_tile_template(
        os.path.join(tiles_dir, starting_room)
    ).add_tile_template_folder(
        tiles_dir
    ).make_random_map(
        strategy=MapTypes.CONSTRUCTIVE1,
        maximum_number_of_tries=150,
        legacy_mode=LEGACY_MODE
    )


def play_game():
    while not tdl.event.is_window_closed():

        game_context.camera.render_all_objects()
        game_context.lower_gui_renderer.render_gui()

        tdl.flush()

        game_context.camera.clear_all_objects()

        game_context.handle_keys()

        game_context.camera.set_fov_recompute(game_context.fov_recompute)

        if game_context.player_action == EAction.EXIT:
            save()
            break

        game_context.run_ai_turn()


def save():
    with shelve.open('savegame', 'n') as savefile:
        savefile['game_context'] = game_context
        savefile['player-id'] = game_context.player.get_id()
        savefile['object_pool'] = game_context.object_pool.get_objects_as_dict()
        savefile['map'] = game_context.map
        savefile['game_msgs'] = game_context.lower_gui_renderer.game_msg
        savefile['game_state'] = game_context.game_state
        savefile['ais'] = {k: monster.ai
                                for k, monster in game_context.object_pool.get_objects_as_dict().items()
                                if type(monster) == Character
                            }
        savefile['fighters'] = {k: monster.fighter
                                for k, monster in game_context.object_pool.get_objects_as_dict().items()
                                if type(monster) == Character
                            }
        savefile.close()


def load():
    global game_context
    with shelve.open('savegame', 'r') as savefile:
        map = savefile['map']
        objects = savefile['object_pool']
        player_id = savefile['player-id']
        game_msgs = savefile['game_msgs']
        game_state = savefile['game_state']
        ais = savefile['ais']
        fighters = savefile['fighters']

    game_context = GameContext(next_level=next_level, game_state=ObjectManager.GameState(game_state), real_time=REALTIME, menu=menu)
    game_context.set_object_pool(ObjectPool.ObjectPool())
    game_context.set_map(map)

    for k, v in objects.items():
        v.collision_handler = game_context.collision_handler
        if k in fighters.keys():
            v.fighter = fighters[k]
            if v.fighter:
                v.fighter.owner = v
        if k in ais.keys():
            v.ai = ais[k]
            if v.ai:
                v.ai.owner = v
                v.ai.visible_tiles_ref = map.visible_tiles
        if k == player_id:
            v.game_state = game_context.game_state
            game_context.set_player(v, inventory_width=INVENTORY_WIDTH)
        else:
            game_context.object_pool.append(v)

    inventory = game_context.player.get_inventory()
    for i in inventory:
        i.context = game_context

    viewport = ObjectManager.ConsoleBuffer(
        root_view,
        object_pool=game_context.object_pool,
        map=game_context.map,
        width=MAP_SIZE[0],
        height=MAP_SIZE[1],
        origin=Vector2.zero(),
        target=Vector2.zero(),
        mouse_controller=game_context.mouse_controller
    )

    lower_gui_renderer = ObjectManager.ConsoleBuffer(
        root_view,
        origin=Vector2(0, SCREEN_HEIGHT - PANEL_HEIGHT),
        target=Vector2(0, 0),
        width=SCREEN_WIDTH,
        height=PANEL_HEIGHT,
        mouse_controller=game_context.mouse_controller
    )

    lower_gui_renderer.add_message_console(MSG_WIDTH, MSG_HEIGHT, MSG_X, MSG_Y)
    lower_gui_renderer.game_msg = game_msgs

    lower_gui_renderer.add_bar(
        1, 1, BAR_WIDTH, 'HP', 'hp', 'max_hp', game_context.player.fighter, Colors.light_red, Colors.darker_red
    )

    game_context.game_state.set_state(EGameState.PLAYING)
    game_context.camera = viewport
    game_context.lower_gui_renderer = lower_gui_renderer


def main():
    global root_view
    # setup to start the TDL and small consoles
    font = os.path.join(assets_dir, "arial10x10.png")
    tdl.set_font(font, greyscale=True, altLayout=True)
    tdl.setFPS(LIMIT_FPS)
    root_view = tdl.init(width=SCREEN_WIDTH, height=SCREEN_HEIGHT, title="Roguelike", fullscreen=False)

    main_menu()


if __name__ == '__main__':
    main()
