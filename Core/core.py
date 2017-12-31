import tdl
import os
from utils.ObjectManager import ObjectPool, CollisionHandler, ConsoleBuffer, GameState
from models.GameObjects import Character, Vector2, MapConstructor, Fighter, MapObjectsConstructor, BasicMonsterAI, DeathMethods
import logging
from utils import Colors
import argparse

# Based on the tutorial from RogueBasin for python3 with tdl
# Adapted to use more objects and be more loosely tied, without global variables
# http://www.roguebasin.com/index.php?title=Roguelike_Tutorial,_using_python3%2Btdl,_part_6

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
LIMIT_FPS = args.fps
REALTIME = args.realtime
LEGACY_MODE = args.legacy
LOGLEVEL = {0: logging.DEBUG, 1:logging.INFO, 2: logging.WARNING, 3: logging.ERROR, 4: logging.CRITICAL}

# instantiating logger
logging.basicConfig(filename='debug.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=LOGLEVEL[args.loglevel]
                    )

logger = logging.getLogger('Rogue-EVE')
ch = logging.StreamHandler()
logger.addHandler(ch)


def handle_keys(movable_object):

    action = 'nop'
    fov_recompute = False
    user_input = None

    if REALTIME:

        keypress = False
        for event in tdl.event.get():
            if event.type == 'KEYDOWN':
               user_input = event
               keypress = True
        if not keypress:
            return action, fov_recompute
    else:
        # turn-based
        action = 'didnt-take-turn'
        user_input = tdl.event.key_wait()

    logger.debug("User_Input [key={} alt={} ctrl={} shift={}]".format(
                  user_input.key, user_input.alt, user_input.control, user_input.shift)
    )

    if user_input.key == 'ENTER' and user_input.alt:
        # Alt+Enter: toggle fullscreen
        tdl.set_fullscreen(not tdl.get_fullscreen())

    elif user_input.key == 'ESCAPE':
        action = 'exit'
        # exit game
        return action, fov_recompute

    print(movable_object.game_state, movable_object.game_state == 'playing')

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

    games_tate = GameState('loading')

    # General tools for management of the game

    # setup to start the TDL and small consoles
    font = os.path.join("assets", "arial10x10.png")
    tdl.set_font(font, greyscale=True, altLayout=True)
    tdl.setFPS(LIMIT_FPS)
    root = tdl.init(width=SCREEN_WIDTH, height=SCREEN_HEIGHT, title="Roguelike", fullscreen=False)

    # Now start the setup of the object managers

    # ObjectPool keeps track of all the objects on the scene
    object_pool = ObjectPool()
    # Starting up the collision handler, which manages all the objects collision events
    collision_handler = CollisionHandler()
    # A map constructor, that randomly create rooms with (not yet implemented) many different strategies
    map_constructor = MapConstructor(SCREEN_WIDTH, SCREEN_HEIGHT)
    map_constructor.populate_with_random_rooms()
    my_map = map_constructor.build_map()
    if LEGACY_MODE:
        # Legacy mode makes the map be drawn using chars instead of colored blocks
        my_map.set_legacy_mode()

    # Adding the object pool and the map to the collision handler so they interact
    collision_handler.set_map(my_map)
    collision_handler.set_object_pool(object_pool)

    # Map objects constructor is a special factory that randomly populates the map with object templates
    # and does deal with weighted distributions, It makes everything in place, by reference
    MapObjectsConstructor(my_map, object_pool, collision_handler).add_object_template(
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

    renderer = ConsoleBuffer(root, object_pool=object_pool, map=my_map,
                             width=SCREEN_WIDTH, height=SCREEN_HEIGHT,
                             origin=Vector2.zero(), target=Vector2.zero())

    games_tate.state = 'playing'

    while not tdl.event.is_window_closed():

        renderer.render_all()

        tdl.flush()

        renderer.clear_all_objects()

        player_action, fov_recompute = handle_keys(player)

        renderer.set_fov_recompute_to(fov_recompute)

        if player_action == 'exit':
            break

        if games_tate.state == 'playing' and player_action != 'didnt-take-turn':
            for obj in object_pool.find_by_tag('monster'):
                if obj.ai:
                    obj.ai.take_turn()


if __name__ == '__main__':
    main()
