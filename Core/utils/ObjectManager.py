import tdl
from models.GameObjects import Vector2

class ObjectPool(object):
    class __ObjectPool(object):
        def __init__(self):
            self.object_poll = {}

        def __str__(self):
            return repr(self)

        def append(self, obj):
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
            return True

        # now check for any blocking objects
        for obj in self.object_pool.get_objects_as_list():
            if obj.blocks and obj.coord.X == x and obj.coord.Y == y:
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
