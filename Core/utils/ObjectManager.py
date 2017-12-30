import tdl
from models.GameObjects import Vector2
import logging

logger = logging.getLogger('Rogue-EVE')


class ObjectPool(object):
    class __ObjectPool(object):
        def __init__(self):
            self.id_counter = 0
            self.object_poll = {}
            self.player = None

        def __str__(self):
            return repr(self)

        def identify_object(self):
            ret = self.id_counter
            self.id_counter += 1
            return ret

        def get_player(self):
            return self.player

        def add_player(self, player):
            """Add the player"""
            player._id = self.identify_object()
            self.player = player
            self.append(player)

        def remove_player(self):
            self.delete_by_id(self.player._id)
            self.player = None

        def append(self, obj):
            """For non-player objects"""
            if obj._id is None:
                obj._id = self.identify_object()

            if obj._id not in self.object_poll.keys():
                self.object_poll[obj._id] = obj

        def get_objects_as_list(self):
            return self.object_poll.values()

        def get_objects_as_dict(self):
            return self.object_poll

        def __delitem__(self, key):
            del self.object_poll[key]

        def __delete__(self, key):
            self.object_poll = {}

        def delete_object(self, obj):
            key_to_delete = None
            for key, val in self.object_poll.items():
                if val == obj:
                    key_to_delete = key
                    break;

            del self.object_poll[key_to_delete]

        def delete_by_id(self, key):
            if key in self.object_poll.keys():
                del self.object_poll[key]
            else:
                print("Key not present in the object pool")
                # raise KeyError

        def find_by_id(self, key):
            if key in self.object_poll.keys():
                return self.object_poll[key]
            else:
                print("Key not present in the object pool")
                # raise KeyError

    instance = None

    def __init__(self):
        if not ObjectPool.instance:
            ObjectPool.instance = ObjectPool.__ObjectPool()
        #else:
        #    ObjectPool.instance.val = arg

    def __getattr__(self, name):
        return getattr(self.instance, name)


class CollisionHandler(object):
    def __init__(self, map=None, object_pool=None):
        self.map = map
        self.object_pool = object_pool

    def set_map(self, map):
        self.map = map

    def set_object_pool(self, object_pool):
        self.object_pool = object_pool

    def is_blocked(self, x, y):
        if self.map.get_map()[x][y].blocked:
            logger.debug("<CollisionHandler collided_with={} coord={} >".format(self.map.get_map()[x][y], Vector2(x,y)))
            return True

        # now check for any blocking objects
        for obj in self.object_pool.get_objects_as_list():
            if obj.blocks and obj.coord.X == x and obj.coord.Y == y:
                logger.debug("<CollisionHandler collided_with={} >".format(obj, obj.coord))
                return True

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
        self.fov_recompute = True
        self.fov_algorithm = 'SHADOW' # 'DIAMOND', 'BASIC'
        self.fov_light_walls = True
        self.visible_tiles = None

    def config_buffer(self, origin: Vector2, width: int, height: int, target: Vector2):
        self.console = tdl.Console(width, height)
        self.origin = origin
        self.target = target
        self.heigth = height
        self.width = width

    def set_fov_recompute_to(self, val: bool):
        self.fov_recompute = val

    def reset_fov_recompute(self):
        self.fov_recompute = False

    def fov_must_recompute(self):
        return self.fov_recompute

    def render_all(self):
        if self.fov_must_recompute():
            # recompute FOV if needed (the player moved or something)
            self.reset_fov_recompute()
            player = self.object_pool.get_player()
            self.visible_tiles = tdl.map.quickFOV(player.coord.X, player.coord.Y,
                                             self.map.is_visible_tile,
                                             fov=self.fov_algorithm,
                                             radius=player.torch,
                                             lightWalls=self.fov_light_walls)

            self.map.set_visible_tiles(self.visible_tiles)
            if self.map:
                self.map.draw(self.console)

        if self.object_pool:
            for obj in self.object_pool.get_objects_as_list():
                if (obj.coord.X, obj.coord.Y) in self.visible_tiles:
                    obj.draw(self.console)

        self.root.blit(self.console, self.origin.X, self.origin.Y, self.width, self.heigth, self.target.X, self.target.Y)

    def clear_all_objects(self):
        if self.object_pool:
            for obj in self.object_pool.get_objects_as_list():
                obj.clear(self.console)
