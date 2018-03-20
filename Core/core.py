import os
import tdl
import logging
import argparse
from utils import Colors
from utils.Messenger import send_message
from utils.ObjectManager import CollisionHandler, ConsoleBuffer, GameState
from utils.ObjectPool import object_pool
from utils.MouseController import mouse_controller
from models.GameObjects import Character, Vector2, Fighter, BasicMonsterAI, DeathMethods
from models.MapObjects import MapConstructor, MapObjectsConstructor

# Based on the tutorial from RogueBasin for python3 with tdl
# Adapted to use more objects and be more loosely tied, without many global variables and constants
# http://www.roguebasin.com/index.php?title=Roguelike_Tutorial,_using_python3%2Btdl,_part_7

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--loglevel", type=int, default=2,
                    help="increase output verbosity")
parser.add_argument("-s", "--screensize", type=str, default='80x50',
                    help="sets the size of the screen in tiles using the pattern WxH. Ex.: 80x50, 100x75")
parser.add_argument("--fps", type=int, default=20,
                    help="Defines the fps, and therefore the speed of the game")
parser.add_argument("--realtime", help="run the game in realtime as oposed to turn based",
                    action="store_true")
parser.add_argument("--legacy", help="Prints the tiles as characters",
                    action="store_true")

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

# instantiating logger
logging.basicConfig(filename='debug.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=LOGLEVEL[args.loglevel]
                    )

logger = logging.getLogger('Rogue-EVE')
ch = logging.StreamHandler()
logger.addHandler(ch)


def handle_keys(movable_object):
    action = 'didnt-take-turn'
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
        action = 'exit'
        # exit game
        return action, fov_recompute

    if movable_object.game_state.state == 'playing':
        fov_recompute = False

        # movement keys
        if user_input.key == 'UP':
            fov_recompute = movable_object.move_or_attack(Vector2(0, -1))
            action = 'move-up'
        elif user_input.key == 'DOWN':
            fov_recompute = movable_object.move_or_attack(Vector2(0, 1))
            action = 'move-down'
        elif user_input.key == 'LEFT':
            fov_recompute = movable_object.move_or_attack(Vector2(-1, 0))
            action = 'move-left'
        elif user_input.key == 'RIGHT':
            fov_recompute = movable_object.move_or_attack(Vector2(1, 0))
            action = 'move-right'

    return action, fov_recompute


def main():

    # General tools for management of the game
    games_tate = GameState('loading')

    # setup to start the TDL and small consoles
    font = os.path.join("assets", "arial10x10.png")
    tdl.set_font(font, greyscale=True, altLayout=True)
    tdl.setFPS(LIMIT_FPS)
    root = tdl.init(width=SCREEN_WIDTH, height=SCREEN_HEIGHT, title="Roguelike", fullscreen=False)

    # Now start the setup of the object managers

    # ObjectPool keeps track of all the objects on the scene
    # Starting up the collision handler, which manages all the objects collision events
    collision_handler = CollisionHandler()

    # A map constructor, that randomly create rooms with (not yet implemented) many different strategies
    # Legacy mode makes the map be drawn using chars instead of colored blocks
    my_map = MapConstructor(MAP_SIZE[0],MAP_SIZE[1]).make_random_map(
        strategy="random",
        maximum_number_of_tries=15,
        legacy_mode=LEGACY_MODE
    )

    # Adding the object pool and the map to the collision handler so they interact
    collision_handler.set_map(my_map)
    collision_handler.set_object_pool(object_pool)

    # Add the map to the mouse so it understand what is visible and what is not
    mouse_controller.set_map(my_map)
    # Map objects constructor is a special factory that randomly populates the map with object templates
    # and does deal with weighted distributions, It makes everything in place, by reference
    MapObjectsConstructor(
        my_map,
        object_pool,
        collision_handler
    ).add_object_template(
        Character,
        {
            'char': 'o',
            'color': Colors.dark_fuchsia,
            'name': 'orc',
            'ai': BasicMonsterAI(interest_tag='player'),
            'fighter': Fighter(hp=10, defense=0, power=3, death_function=DeathMethods.monster_death),
            'tags': ['monster', 'orc', 'small']
        },
        3.0
    ).add_object_template(
        Character,
        {
            'char': 'T',
            'color': Colors.dark_crimson,
            'name': 'Troll',
            'ai': BasicMonsterAI(interest_tag='player'),
            'fighter': Fighter(hp=16, defense=1, power=4, death_function=DeathMethods.monster_death),
            'tags': ['monster', 'troll', 'big']
        },
        1.0
    ).populate_map()

    # Creation of the player
    fighter_component = Fighter(hp=30, defense=2, power=5, death_function=DeathMethods.player_death)

    player = Character(my_map.get_rooms()[0].center(),
                       collision_handler=collision_handler,
                       color=Colors.white,
                       name='Player',
                       fighter=fighter_component,
                       tags=['player'],
                       game_state=games_tate)

    object_pool.add_player(player)

    map_renderer = ConsoleBuffer(root,
                                 object_pool=object_pool,
                                 map=my_map,
                                 width=MAP_SIZE[0],
                                 height=MAP_SIZE[1],
                                 origin=Vector2.zero(),
                                 target=Vector2.zero()
                                 )

    lower_gui_renderer = ConsoleBuffer(root,
                                       origin=Vector2(0, SCREEN_HEIGHT-PANEL_HEIGHT),
                                       target=Vector2(0, 0),
                                       width=SCREEN_WIDTH,
                                       height=PANEL_HEIGHT)

    lower_gui_renderer.add_message_console(MSG_WIDTH, MSG_HEIGHT, MSG_X, MSG_Y)

    lower_gui_renderer.add_bar(1, 1, BAR_WIDTH, 'HP', 'hp', 'max_hp', player.fighter,
                               Colors.light_red, Colors.darker_red
                               )

    # a warm welcoming message!
    send_message('Welcome stranger! Prepare to perish in the Tombs of the Ancient Kings.', Colors.red)

    games_tate.state = 'playing'

    while not tdl.event.is_window_closed():

        map_renderer.render_all_objects()
        lower_gui_renderer.render_gui()

        tdl.flush()

        map_renderer.clear_all_objects()

        player_action, fov_recompute = handle_keys(player)

        map_renderer.set_fov_recompute_to(fov_recompute)

        if player_action == 'exit':
            break

        if games_tate.state == 'playing' and player_action != 'didnt-take-turn':
            for obj in object_pool.find_by_tag('monster'):
                if obj.ai:
                    obj.ai.take_turn()


if __name__ == '__main__':
    main()
