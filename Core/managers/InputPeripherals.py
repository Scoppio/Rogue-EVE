import logging

logger = logging.getLogger('Rogue-EVE')


class MouseController(object):
    """
    Mouse controller needs the map, get over it
    """
    def __init__(self, map=None, object_pool=None):
        self.mouse_coord = (0, 0)
        self.map = map
        self.object_pool = object_pool

    def set_map(self, map):
        self.map = map

    def set_object_pool(self, object_pool):
        self.object_pool = object_pool

    def get_mouse_coord(self):
        return self.mouse_coord

    def set_mouse_coord(self, new_coord):
        self.mouse_coord = new_coord
        logger.debug("mouse position {}".format(self.mouse_coord))

    def get_names_under_mouse(self):
        # return a string with the names of all objects under the mouse
        (x, y) = self.get_mouse_coord()

        # create a list with the names of all objects at the mouse's coordinates and in FOV
        objects = self.object_pool.get_objects_as_list()
        names = ""
        if self.map and self.object_pool:
            if objects and self.map:
                names = [obj.name for obj in objects
                         if obj.coord.X == x and obj.coord.Y == y  and (x,y) in self.map.get_visible_tiles()]
                names = ', '.join(names)  # join the names, separated by commas
        else:
            logger.warning("map or object pool not initialized!")

        return names.capitalize()
