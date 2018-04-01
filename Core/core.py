import os
import tdl
import logging
import argparse
import textwrap
from pathlib import Path
from utils import Colors
from managers import ObjectManager, ObjectPool, Messenger
from managers.GenericControllerObjects import GameContext
from models.GameObjects import Character, Vector2
from models.EnumStatus import EGameState, EAction
from models.MapObjects import MapConstructor, MapObjectsConstructor

# Based on the tutorial from RogueBasin for python3 with tdl
# Adapted to use more objects and be more loosely tied, without many global variables and constants
# http://www.roguebasin.com/index.php?title=Roguelike_Tutorial,_using_python3%2Btdl,_part_7

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--loglevel", type=int, default=2,
                    help="increase output verbosity")
parser.add_argument("-s", "--screensize", type=str, default='80x50',
                    help="sets the size of the screen in tiles using the pattern WxH. Ex.: 80x50, 100x75")
parser.add_argument("--fps", type=int, default=7,
                    help="Defines the fps, and therefore the speed of the game")
parser.add_argument("--realtime", help="run the game in realtime as oposed to turn based",
                    action="store_true")
parser.add_argument("--legacy", help="Prints the tiles as characters",
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
    letter_index = ord('a')
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

    #convert the ASCII code to an index; if it corresponds to an option, return it
    index = ord(key_char) - ord('a')
    if index >= 0 and index < len(options):
        return index
    return None


def main():
    global root_view
    # setup to start the TDL and small consoles
    font = os.path.join(assets_dir, "arial10x10.png")
    tdl.set_font(font, greyscale=True, altLayout=True)
    tdl.setFPS(LIMIT_FPS)
    root_view = tdl.init(width=SCREEN_WIDTH, height=SCREEN_HEIGHT, title="Roguelike", fullscreen=False)

    # Start to setup the object which will handle most of the generally accessed stuff
    # GameContext will keep setup of the object managers
    # ObjectPool keeps track of all the objects on the scene
    # Starting up the collision handler, which manages all the objects collision events
    # Adding the object pool and the map to the collision handler so they interact
    game_context = GameContext(game_state=ObjectManager.GameState(EGameState.LOADING), real_time=REALTIME, menu=menu)

    game_context.set_object_pool(ObjectPool.object_pool)

    # A map constructor, that randomly create rooms with (not yet implemented) many different strategies
    # Legacy mode makes the map be drawn using chars instead of colored blocks
    game_context.set_map(
        MapConstructor(
            MAP_SIZE[0],
            MAP_SIZE[1]
        ).make_random_map(
            strategy="random",
            maximum_number_of_tries=15,
            legacy_mode=LEGACY_MODE
        )
    )

    # Before we start the map objects constructor we load the level data that is being hold on a file
    # With all the information necessary to build the monsters from the template
    # Map objects constructor is a special factory that randomly populates the map with object templates
    # and does deal with weighted distributions, It makes everything in place, by reference

    MapObjectsConstructor(game_instance=game_context).load_object_templates(LEVEL_DATA).populate_map()

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
        origin=Vector2(0, SCREEN_HEIGHT-PANEL_HEIGHT),
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
    while not tdl.event.is_window_closed():

        viewport.render_all_objects()
        lower_gui_renderer.render_gui()

        tdl.flush()

        viewport.clear_all_objects()

        game_context.handle_keys()

        viewport.set_fov_recompute(game_context.fov_recompute)

        if game_context.player_action == EAction.EXIT:
            break

        game_context.run_ai_turn()


if __name__ == '__main__':
    main()
