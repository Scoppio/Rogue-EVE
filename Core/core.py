import tdl
import os
from utils.ObjectManager import ObjectPool, CollisionHandler, ConsoleBuffer
from models.GameObjects import Character, Vector2, MapConstructor, Rect
import logging

# Based on the tutorial from RogueBasin for python3 with tdl
# Adapted to use more objects and be more loosely tied, without global variables
# http://www.roguebasin.com/index.php?title=Roguelike_Tutorial,_using_python3%2Btdl,_part_3

#########################################
# Constants
#########################################

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20
REALTIME = True

# instantiating logger
logging.basicConfig(filename='debug.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.DEBUG
                    )

logger = logging.getLogger('Rogue-EVE')
ch = logging.StreamHandler()
logger.addHandler(ch)


def handle_keys(movable_object):

    if REALTIME:

        keypress = False
        for event in tdl.event.get():
            if event.type == 'KEYDOWN':
               user_input = event
               keypress = True
        if not keypress:
            return False, False
    else:
        # turn-based
        user_input = tdl.event.key_wait()

    logger.debug("<User_Input key={} alt={} ctrl={} shift={}>".format(
                  user_input.key, user_input.alt, user_input.control, user_input.shift)
    )

    if user_input.key == 'ENTER' and user_input.alt:
        # Alt+Enter: toggle fullscreen
        tdl.set_fullscreen(not tdl.get_fullscreen())

    elif user_input.key == 'ESCAPE':
        # exit game
        return True, False

    fov_recompute = True
    # movement keys
    if user_input.key == 'UP':
        movable_object.move(Vector2(0, -1))

    elif user_input.key == 'DOWN':
        movable_object.move(Vector2(0, 1))

    elif user_input.key == 'LEFT':
        movable_object.move(Vector2(-1, 0))

    elif user_input.key == 'RIGHT':
        movable_object.move(Vector2(1, 0))

    else:
        fov_recompute = False

    return False, fov_recompute


def main():
    object_pool = ObjectPool()

    font = os.path.join("assets", "arial10x10.png")

    tdl.set_font(font, greyscale=True, altLayout=True)
    tdl.setFPS(LIMIT_FPS)
    root = tdl.init(width=SCREEN_WIDTH, height=SCREEN_HEIGHT, title="Roguelike", fullscreen=False)

    collision_handler = CollisionHandler()

    map_constructor = MapConstructor(SCREEN_WIDTH, SCREEN_HEIGHT)
    map_constructor.add_room(Rect(20, 15, 10, 15)).add_room(Rect(50, 15, 10, 15)).populate_with_random_rooms()
    my_map = map_constructor.build_map()
    my_map.draw_with_chars()

    player = Character(my_map.get_rooms()[0].center(), collision_handler=collision_handler)

    npc = Character(my_map.get_rooms()[1].center(), 0, 0, '@', (255, 255, 0))

    object_pool.add_player(player)
    object_pool.append(npc)

    collision_handler.set_map(my_map)
    collision_handler.set_object_pool(object_pool)

    renderer = ConsoleBuffer(root, object_pool=object_pool, map=my_map, width=SCREEN_WIDTH, height=SCREEN_HEIGHT,
                                origin=Vector2.zero(), target=Vector2.zero())

    while not tdl.event.is_window_closed():

        renderer.render_all()

        tdl.flush()

        renderer.clear_all_objects()

        exit_game, fov_recompute = handle_keys(player)

        renderer.set_fov_recompute_to(fov_recompute)

        if exit_game:
            break

if __name__ == '__main__':
    main()

