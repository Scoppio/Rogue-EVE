import tdl
import os
from utils.ObjectManager import ObjectPool, CollisionHandler
from models.GameObjects import Character, Vector2, MapConstructor

#########################################
# Constants
#########################################

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20


def handle_keys(movable_object):
    """
    #realtime

    keypress = False
    for event in tdl.event.get():
        if event.type == 'KEYDOWN':
           user_input = event
           keypress = True
    if not keypress:
        return
    """
    # turn-based
    user_input = tdl.event.key_wait()

    if user_input.key == 'ENTER' and user_input.alt:
        # Alt+Enter: toggle fullscreen
        tdl.set_fullscreen(not tdl.get_fullscreen())

    elif user_input.key == 'ESCAPE':
        return True  # exit game

    # movement keys
    if user_input.key == 'UP':
        movable_object.move(Vector2(0, -1))

    elif user_input.key == 'DOWN':
        movable_object.move(Vector2(0, 1))

    elif user_input.key == 'LEFT':
        movable_object.move(Vector2(-1, 0))

    elif user_input.key == 'RIGHT':
        movable_object.move(Vector2(1, 0))

    return False


class ConsoleBuffer(object):
    def __init__(self, root, object_pool = None, map = None, width: int = 0, height: int =0,
                 origin: Vector2=None, target: Vector2=None):

        self.object_pool = object_pool
        self.map = map
        self.root = root
        self.console = tdl.Console(width, height)
        self.origin = origin
        self.target = target
        self.heigth = height
        self.width = width

    def config_buffer(self, origin: Vector2, width: int, height: int, target: Vector2):
        self.console = tdl.Console(width, height)
        self.origin = origin
        self.target = target
        self.heigth = height
        self.width = width

    def render_all(self):
        if self.map:
            self.map.draw(self.console)

        if self.object_pool:
            for obj in self.object_pool.get_objects_as_list():
                obj.draw(self.console)

        self.root.blit(self.console, self.origin.X, self.origin.Y, self.width, self.heigth, self.target.X, self.target.Y)

    def clar_all_objects(self):
        if self.object_pool:
            for obj in self.object_pool.get_objects_as_list():
                obj.clear(self.console)


def main():
    object_pool = ObjectPool()

    font = os.path.join("assets", "arial10x10.png")

    tdl.set_font(font, greyscale=True, altLayout=True)

    root = tdl.init(width=SCREEN_WIDTH, height=SCREEN_HEIGHT, title="Roguelike", fullscreen=False)

    collision_handler = CollisionHandler()

    player = Character(Vector2(SCREEN_WIDTH//2 , SCREEN_HEIGHT//2), collision_handler=collision_handler)

    npc = Character(Vector2(SCREEN_WIDTH // 2 - 5, SCREEN_HEIGHT // 2), 0, 0, '@', (255, 255, 0))

    object_pool.append(player)
    object_pool.append(npc)

    my_map = MapConstructor(SCREEN_WIDTH, SCREEN_HEIGHT).build_map()
    my_map.draw_with_chars()
    print(my_map)

    collision_handler.set_map(my_map)
    collision_handler.set_object_pool(object_pool)

    renderer = ConsoleBuffer(root, object_pool=object_pool, map=my_map, width=SCREEN_WIDTH, height=SCREEN_HEIGHT,
                                origin=Vector2.zero(), target=Vector2.zero())

    while not tdl.event.is_window_closed():

        renderer.render_all()

        tdl.flush()

        renderer.clar_all_objects()

        exit_game = handle_keys(player)

        if exit_game:
            break

if __name__ == '__main__':
    main()

#http://www.roguebasin.com/index.php?title=Roguelike_Tutorial,_using_python3%2Btdl,_part_2
