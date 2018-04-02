import logging

logger = logging.getLogger('Rogue-EVE')


class ObjectPool(object):

    def __init__(self):
        self.id_counter = 0
        self.object_poll = {}
        self.player = None

    def __str__(self):
        return repr(self)

    def _identify_object(self):
        """Returns the actual value of the id_counter and increments it for posterior use"""
        ret = self.id_counter
        self.id_counter += 1
        return ret

    def get_player(self):
        return self.player

    def add_player(self, player):
        """Add the player"""
        if not player.get_id():
            player._id = self._identify_object()
        self.player = player
        self.append(player)

    def remove_player(self):
        self.delete_by_id(self.player.get_id())
        self.player = None

    def append(self, obj):
        """For non-player objects
        If the _id of the object is already present in the object_pool,
        the new object will overwrite the old one with the same _id"""

        if obj._id is None:
            obj._id = self._identify_object()

        if obj._id not in self.object_poll.keys():
            self.object_poll[obj._id] = obj
            obj.object_pool = self

    def get_objects_as_list(self):
        """Get objects as a list instead of a dictionary"""
        return self.object_poll.values()

    def clear_object_pool(self, keep_player: bool=True):
        """Clears the object pool, used if necessary to reload the monstrs and itens on level or a new level,
        if the player is not set to be kept it will be deleted from the object pool, needing to recreate it"""
        self.object_poll = {}
        if keep_player:
            self.append(self.player)
        else:
            self.player = None

    def get_objects_as_dict(self):
        """Gets the object pool as a dictionary"""
        return self.object_poll

    def __delitem__(self, key):
        del self.object_poll[key]

    def __delete__(self):
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
            logger.error("Key not present in the object pool")
            # raise KeyError

    def find_by_id(self, key):
        if key in self.object_poll.keys():
            return self.object_poll[key]
        else:
            logger.warning("Key {key} not present in the object pool".format(key=key))
            # raise KeyError

    def find_by_tag(self, tag):
        return [obj for obj in self.get_objects_as_list() if tag in obj.tags]


object_pool = ObjectPool()