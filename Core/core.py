import os
import tdl
import logging
import argparse
from utils import Colors
from managers import ObjectManager, ObjectPool, Messenger as ms, InputPeripherals
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

logger = logging.getLogger('Rogue-EVE')
ch = logging.StreamHandler()
logger.addHandler(ch)


def handle_keys(movable_object, mouse_controller, object_pool):

    action = EAction.DIDNT_TAKE_TURN
    fov_recompute = False
    user_input = None
    keypress = False

    for event in tdl.event.get():
        if event.type == 'KEYDOWN':
            user_input = event
            keypress = True

        if event.type == 'MOUSEMOTION':
            mouse_controller.set_mouse_coord(event.cell)

    if not keypress:
        return action, fov_recompute

    logger.debug("User_Input [key={} alt={} ctrl={} shift={}]".format(
        user_input.key, user_input.alt, user_input.control, user_input.shift))

    if user_input.key == 'ENTER' and user_input.alt:
        # Alt+Enter: toggle fullscreen
        tdl.set_fullscreen(not tdl.get_fullscreen())

    elif user_input.key == 'ESCAPE':
        action = EAction.EXIT
        # exit game
        return action, fov_recompute

    if movable_object.game_state.state == EGameState.PLAYING:
        fov_recompute = False

        # movement keys
        if user_input.key == 'UP':
            fov_recompute = movable_object.move_or_attack(Vector2(0, -1))
            action = EAction.MOVE_UP
        elif user_input.key == 'DOWN':
            fov_recompute = movable_object.move_or_attack(Vector2(0, 1))
            action = EAction.MOVE_DOWN
        elif user_input.key == 'LEFT':
            fov_recompute = movable_object.move_or_attack(Vector2(-1, 0))
            action = EAction.MOVE_LEFT
        elif user_input.key == 'RIGHT':
            fov_recompute = movable_object.move_or_attack(Vector2(1, 0))
            action = EAction.MOVE_RIGHT

        elif user_input.text == 'g':
            # pick up an item
            for obj in [item for item in object_pool.get_objects_as_list()
                        if type(item) == Item
                           and item.coord == movable_object.coord]:
                obj.pick_up(movable_object)
                object_pool.delete_by_id(obj._id)
                break

    return action, fov_recompute


def run_ai_turn(game_state, player_action, object_pool):
    monster_action = True

    if REALTIME:
        if player_action != EAction.DIDNT_TAKE_TURN:
            monster_action = True
    else:
        if player_action == EAction.DIDNT_TAKE_TURN:
            monster_action = False

    if game_state.get_state() == EGameState.PLAYING and monster_action:
        for obj in object_pool.find_by_tag('monster'):
            if obj.ai:
                obj.ai.take_turn()


def main():
    object_pool = ObjectPool.ObjectPool()
    # General tools for management of the game
    game_state = ObjectManager.GameState(EGameState.LOADING)

    # setup to start the TDL and small consoles
    font = os.path.join("assets", "arial10x10.png")
    tdl.set_font(font, greyscale=True, altLayout=True)
    tdl.setFPS(LIMIT_FPS)
    root = tdl.init(width=SCREEN_WIDTH, height=SCREEN_HEIGHT, title="Roguelike", fullscreen=False)

    # A map constructor, that randomly create rooms with (not yet implemented) many different strategies
    # Legacy mode makes the map be drawn using chars instead of colored blocks
    my_map = MapConstructor(
        MAP_SIZE[0],
        MAP_SIZE[1]
    ).make_random_map(
        strategy="random",
        maximum_number_of_tries=15,
        legacy_mode=LEGACY_MODE
    )

    # Now start the setup of the object managers
    # ObjectPool keeps track of all the objects on the scene
    # Starting up the collision handler, which manages all the objects collision events
    # Adding the object pool and the map to the collision handler so they interact
    collision_handler = ObjectManager.CollisionHandler(map=my_map, object_pool=object_pool)

    # Add the map to the mouse so it understand what is visible and what is not
    mouse_controller = InputPeripherals.MouseController(map=my_map, object_pool=object_pool)

    # Before we start the map objects constructor we load the level data that is being hold on a file
    # With all the information necessary to build the monsters from the template
    # Map objects constructor is a special factory that randomly populates the map with object templates
    # and does deal with weighted distributions, It makes everything in place, by reference
    MapObjectsConstructor(my_map, object_pool, collision_handler).load_object_templates(LEVEL_DATA).populate_map()
    inventory = []
    # Creation of the player
    player = Character.load(yaml_file=PLAYER_DATA, coord=my_map.get_rooms()[0].center(),
                       collision_handler=collision_handler, inventory=inventory, game_state=game_state)

    object_pool.add_player(player)

    viewport = ObjectManager.ConsoleBuffer(
        root,
        object_pool=object_pool,
        map=my_map,
        width=MAP_SIZE[0],
        height=MAP_SIZE[1],
        origin=Vector2.zero(),
        target=Vector2.zero(),
        mouse_controller=mouse_controller
    )

    lower_gui_renderer = ObjectManager.ConsoleBuffer(
        root,
        origin=Vector2(0, SCREEN_HEIGHT-PANEL_HEIGHT),
        target=Vector2(0, 0),
        width=SCREEN_WIDTH,
        height=PANEL_HEIGHT,
        mouse_controller=mouse_controller
    )

    lower_gui_renderer.add_message_console(MSG_WIDTH, MSG_HEIGHT, MSG_X, MSG_Y)

    lower_gui_renderer.add_bar(
        1, 1, BAR_WIDTH, 'HP', 'hp',
        'max_hp', player.fighter,
        Colors.light_red, Colors.darker_red
    )

    # a warm welcoming message!
    ms.send_message('Welcome stranger! Prepare to perish in the Tombs of the Ancient Kings.', Colors.red)

    game_state.set_state(EGameState.PLAYING)

    while not tdl.event.is_window_closed():

        viewport.render_all_objects()
        lower_gui_renderer.render_gui()

        tdl.flush()

        viewport.clear_all_objects()

        player_action, fov_recompute = handle_keys(player, mouse_controller, object_pool)

        viewport.set_fov_recompute_to(fov_recompute)

        if player_action == EAction.EXIT:
            break

        run_ai_turn(game_state, player_action, object_pool)


if __name__ == '__main__':
    main()
