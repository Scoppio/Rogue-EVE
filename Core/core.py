import os
import tdl
import logging
import argparse
from pathlib import Path
from utils import Colors
from managers import ObjectManager, ObjectPool, Messenger as ms
from managers.GenericControllerObjects import GameContext
from models.GameObjects import Character, Vector2, Item
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

#sizes and coordinates relevant for the GUI
BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT

MSG_X = BAR_WIDTH + 2
MSG_Y = 1
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1

MAP_SIZE= (SCREEN_WIDTH ,SCREEN_HEIGHT-PANEL_HEIGHT)
LIMIT_FPS = args.fps
REALTIME = args.realtime
LEGACY_MODE = args.legacy
LOGLEVEL = {0: logging.DEBUG, 1:logging.INFO, 2: logging.WARNING, 3: logging.ERROR, 4: logging.CRITICAL}

# loading gamedata, level objects, player information, etc.
gamedata_dir = os.path.join(os.path.dirname(__file__), "gamedata")

LEVEL_DATA = os.path.join(gamedata_dir, args.level_file)
PLAYER_DATA = os.path.join(gamedata_dir, args.player_file)

# instantiating logger
logging.basicConfig(
    filename='debug.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=LOGLEVEL[args.loglevel]
)


log_file = os.path.abspath(os.path.join(str(Path.home()), 'proto_out.log'))

logger = logging.getLogger('Rogue-EVE')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler(log_file)
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

def menu(header, options, width):
    pass

def main():


    # setup to start the TDL and small consoles
    font = os.path.join("assets", "arial10x10.png")
    tdl.set_font(font, greyscale=True, altLayout=True)
    tdl.setFPS(LIMIT_FPS)
    root = tdl.init(width=SCREEN_WIDTH, height=SCREEN_HEIGHT, title="Roguelike", fullscreen=False)

    # Start to setup the object which will handle most of the generally accessed stuff
    game = GameContext()
    game.set_object_pool(ObjectPool.ObjectPool())
    # General tools for management of the game
    game.game_state = ObjectManager.GameState(EGameState.LOADING)

    # A map constructor, that randomly create rooms with (not yet implemented) many different strategies
    # Legacy mode makes the map be drawn using chars instead of colored blocks
    game.set_map(
        MapConstructor(
            MAP_SIZE[0],
            MAP_SIZE[1]
        ).make_random_map(
            strategy="random",
            maximum_number_of_tries=15,
            legacy_mode=LEGACY_MODE
        )
    )

    # Now start the setup of the object managers
    # ObjectPool keeps track of all the objects on the scene
    # Starting up the collision handler, which manages all the objects collision events
    # Adding the object pool and the map to the collision handler so they interact

    # Before we start the map objects constructor we load the level data that is being hold on a file
    # With all the information necessary to build the monsters from the template
    # Map objects constructor is a special factory that randomly populates the map with object templates
    # and does deal with weighted distributions, It makes everything in place, by reference

    MapObjectsConstructor(game_instance=game).load_object_templates(LEVEL_DATA).populate_map()
    inventory = []
    # Creation of the player
    player = Character.load(yaml_file=PLAYER_DATA, coord=game.map.get_rooms()[0].center(),
                       collision_handler=game.collision_handler, inventory=inventory, game_state=game.game_state)
    game.player = player
    game.object_pool.add_player(player)

    viewport = ObjectManager.ConsoleBuffer(
        root,
        object_pool=game.object_pool,
        map=game.map,
        width=MAP_SIZE[0],
        height=MAP_SIZE[1],
        origin=Vector2.zero(),
        target=Vector2.zero(),
        mouse_controller=game.mouse_controller
    )

    lower_gui_renderer = ObjectManager.ConsoleBuffer(
        root,
        origin=Vector2(0, SCREEN_HEIGHT-PANEL_HEIGHT),
        target=Vector2(0, 0),
        width=SCREEN_WIDTH,
        height=PANEL_HEIGHT,
        mouse_controller=game.mouse_controller
    )

    lower_gui_renderer.add_message_console(MSG_WIDTH, MSG_HEIGHT, MSG_X, MSG_Y)

    lower_gui_renderer.add_bar(
        1, 1, BAR_WIDTH, 'HP', 'hp',
        'max_hp', player.fighter,
        Colors.light_red, Colors.darker_red
    )

    # a warm welcoming message!
    ms.send_message('Welcome stranger! Prepare to perish in the Tombs of the Ancient Kings.', Colors.red)

    game.game_state.set_state(EGameState.PLAYING)

    while not tdl.event.is_window_closed():

        viewport.render_all_objects()
        lower_gui_renderer.render_gui()

        tdl.flush()

        viewport.clear_all_objects()

        game.handle_keys()

        viewport.set_fov_recompute_to(game.fov_recompute)

        if game.player_action == EAction.EXIT:
            break

        game.run_ai_turn()


if __name__ == '__main__':
    main()
