from managers.ObjectPool import object_pool
import logging

logger = logging.getLogger('Rogue-EVE')


class MouseController(object):
    """
    Mouse controller needs the map, get over it
    """
    def __init__(self):
        self.mouse_coord = (0, 0)
        self.map = None

    def set_map(self, map):
        self.map = map

    def get_mouse_coord(self):
        return self.mouse_coord

    def set_mouse_coord(self, new_coord):
        self.mouse_coord = new_coord
        logger.debug("mouse position", self.mouse_coord)

    def get_names_under_mouse(self):
        # return a string with the names of all objects under the mouse
        (x, y) = self.get_mouse_coord()

        # create a list with the names of all objects at the mouse's coordinates and in FOV
        objects = object_pool.get_objects_as_list()
        names = ""
        if objects and self.map:
            names = [obj.name for obj in objects
                     if obj.coord.X == x and obj.coord.Y == y  and (x,y) in self.map.get_visible_tiles()]
            names = ', '.join(names)  # join the names, separated by commas
        return names.capitalize()


mouse_controller = MouseController()
