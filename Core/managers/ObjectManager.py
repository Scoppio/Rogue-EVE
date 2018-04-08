import tdl
from utils import Colors
import logging
import textwrap
from models.EnumStatus import EGameState
from models.GameObjects import Vector2
from managers import Messenger

logger = logging.getLogger('Rogue-EVE')


class GameState(object):
    def __init__(self, state: EGameState):
        self.state = state

    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state

    def __cmp__(self, other: EGameState):
        return self.state == other


class CollisionHandler(object):
    def __init__(self, map=None, object_pool=None):
        self.map = map
        self.object_pool = object_pool

    def set_map(self, map):
        self.map = map

    def set_object_pool(self, object_pool):
        self.object_pool = object_pool

    def get_visible_tiles(self):
        return self.map.get_map().visible_tiles

    def is_blocked(self, x, y):
        if self.map.get_map()[x][y].blocked:
            logger.debug(
                "CollisionHandler [collided_with={} position={}]".format(self.map.get_map()[x][y], Vector2(x, y)))
            return True

        # now check for any blocking objects
        for obj in self.object_pool.get_objects_as_list():
            if obj.blocks and obj.coord == Vector2(x, y):
                logger.debug("CollisionHandler [collided_with={} position={}]".format(obj.name, obj.coord))
                return True

        return False

    def collides_with(self, this, x, y):
        for obj in self.object_pool.get_objects_as_list():
            if obj.blocks and obj.coord.X == x and obj.coord.Y == y and this._id != obj._id:
                logger.debug("CollisionHandler [collided_with={} position={}]".format(obj.name, obj.coord))
                return obj


class ConsoleBuffer(object):
    def __init__(self,
                 root,
                 object_pool=None,
                 map=None,
                 width: int=0,
                 height: int=0,
                 origin: Vector2=None,
                 target: Vector2=None,
                 console: object=None,
                 mouse_controller=None,
                 map_width=None,
                 map_height=None,
                 camera_width=None,
                 camera_height=None,
                 ):
        self.object_pool = object_pool
        self.map = map
        self.root = root

        if console:
            self.console = console
        else:
            self.console = tdl.Console(width, height)

        self.origin = origin
        self.target = target
        self.height = height
        self.width = width
        self.fov_recompute = True
        self.fov_algorithm = 'SHADOW'
        self.fov_light_walls = True
        self.visible_tiles = None
        self.bars = []
        self.game_msg = None
        self.message_height = None
        self.message_width = None
        self.message_origin_x = None
        self.message_origin_y = None
        self.map_width = map_width
        self.map_height = map_height
        self.camera_height = camera_height
        self.camera_width = camera_width
        self.camera_coord = Vector2(0,0)
        self.mouse_controller = mouse_controller
        self.extras = []

    def set_mouse_controller(self, mouse_controller):
        self.mouse_controller = mouse_controller

    def set_fov_recompute(self, val: bool):
        self.fov_recompute = val

    def reset_fov_recompute(self):
        self.fov_recompute = False

    def fov_must_recompute(self):
        return self.fov_recompute

    def add_extra(self, x, y, name, obj, char_color, back_color):
        """
         To add an extra you need to simply apply this template to the extra, filling the blanks
        :param x:
        :param y:
        :param total_width:
        :param name:
        :param value_name:
        :param obj:
        :param char_color:
        :param back_color:
        :return:
        """
        self.extras.append(
            {
                'x': x,
                'y': y,
                'name': name,
                'obj': obj,
                'char_color': char_color,
                'back_color': back_color
            }
        )

    def add_bar(self, x, y, total_width, name, value_name, maximum_value_name, obj, bar_color, back_color):
        """
        To add a bar you need to simply apply this template to the bar, filling the blanks

        :param x: position relative in x to the console origin
        :param y: position relative in y to the console origin
        :param total_width: total width in chars of the bar
        :param name: name of this bar to be printed
        :param value_name: string name of the variable in the object you are passing
        :param maximum_value_name: string name of the variable that holds the maximum value of the variable of interest
        :param obj: object which holds the values of interest to be shown
        :param bar_color: color of the filling of the bar
        :param back_color: color of the background of the bar
        :return:
        """
        self.bars.append(
            {
                'x': x,
                 'y': y,
                 'value_name': value_name,
                 'maximum_value_name': maximum_value_name,
                 'total_width': total_width,
                 'name': name,
                 'obj': obj,
                 'bar_color': bar_color,
                 'back_color': back_color
             }
        )

    def render_gui(self):

        # prepare to render the GUI panel
        self.console.clear(fg=Colors.white, bg=Colors.black)

        for args in self.bars:
            # render a bar (HP, experience, etc). first calculate the width of the bar
            obj = args['obj']
            value = obj.__getattribute__(args['value_name'])
            maximum = obj.__getattribute__(args['maximum_value_name'])
            bar_width = int(float(value) / maximum * args['total_width'])

            # render the background first
            self.console.draw_rect(args['x'], args['y'], args['total_width'], 1, None, bg=args['back_color'])

            # now render the bar on top
            if bar_width > 0:
                self.console.draw_rect(args['x'], args['y'], bar_width, 1, None, bg=args['bar_color'])

            # finally, some centered text with the values
            text = "{}: {}/{}".format(args['name'], int(value), int(maximum))
            x_centered = args['x'] + (args['total_width'] - len(text)) // 2
            self.console.draw_str(x_centered, args['y'], text, fg=Colors.white, bg=None)

        for args in self.extras:
            # render a bar (HP, experience, etc). first calculate the width of the bar
            value = args['obj']

            text = "{}: {}".format(args['name'], value)
            self.console.draw_str(args['x'], args['y'], text, fg=args["char_color"], bg=args['back_color'])

        y = self.message_origin_y
        for (line, color) in self.game_msg:
            self.console.draw_str(self.message_origin_x, y, line, bg=None, fg=color)
            y += 1

        if self.mouse_controller:
            self.console.draw_str(1, 0, self.mouse_controller.get_names_under_mouse(self.camera_coord), bg=None, fg=Colors.light_gray)

        # blit the contents of "panel" to the root console
        self.root.blit(self.console, self.origin.X, self.origin.Y, self.width, self.height, self.target.X,
                       self.target.Y)

    def set_camera(self, camera_width, camera_height, map_width, map_height):
        self.map_width = map_width
        self.map_height = map_height
        self.camera_height = camera_height
        self.camera_width = camera_width

    def move_camera(self, target_coord):

        # new camera coordinates (top-left corner of the screen relative to the map)
        x = target_coord.X - self.camera_width // 2  # coordinates so that the target is at the center of the screen
        y = target_coord.Y - self.camera_height // 2

        # make sure the camera doesn't see outside the map
        x = 0 if x < 0 else y
        y = 0 if y < 0 else y

        if x >= self.map_width - self.camera_width - 1:
            x = self.map_width - self.camera_width - 1
        if y >= self.map_height - self.camera_height - 1:
            y = self.map_height - self.camera_height - 1

        if Vector2(x, y) != self.camera_coord:
            self.fov_recompute = True

        self.camera_coord = Vector2(x, y)

    def render_all_objects(self):
        player = self.object_pool.get_player()
        debug = True
        self.move_camera(player.coord)

        if debug:
            self.console.draw_str(0, 0, "{}/{}".format(self.camera_coord, player.coord))

        if self.fov_must_recompute():
            # recompute FOV if needed (the player moved or something)
            self.console.clear(fg=Colors.white, bg=Colors.black)

            self.reset_fov_recompute()
            self.visible_tiles = tdl.map.quickFOV(
                player.coord.X,
                player.coord.Y,
                self.map.is_visible_tile,
                fov=self.fov_algorithm,
                radius=player.torch,
                lightWalls=self.fov_light_walls
            )

            self.map.set_visible_tiles(self.visible_tiles)
            if self.map:
                self.map.draw(self.console, self)

        if self.object_pool and self.object_pool.get_objects_as_list():
            sorted_objects_list = sorted(self.object_pool.get_objects_as_list(), key=lambda x: x.z_index, reverse=False)

            for obj in sorted_objects_list:
                if (obj.coord.X, obj.coord.Y) in self.visible_tiles:
                    obj.draw(self.console, self.camera_offset)

            if self.object_pool.get_player():
                player = self.object_pool.get_player()
                player.draw(self.console, self.camera_offset)

        self.root.blit(self.console, self.origin.X, self.origin.Y, self.width, self.height, self.target.X,
                       self.target.Y)

    def camera_offset(self, obj_coord):
        # convert coordinates on the map to coordinates on the screen
        coord = obj_coord - self.camera_coord

        if 0 < coord.X < self.camera_width or 0 < coord.Y < self.camera_width:
            return coord

        return None

    def clear_all_objects(self):
        if self.object_pool:
            for obj in self.object_pool.get_objects_as_list():
                obj.clear(self.console, self.camera_offset)

    def add_message_console(self, message_width, message_height, message_origin_x, message_origin_y):
        Messenger.message_handler = self
        self.game_msg = []
        self.message_width = message_width
        self.message_height = message_height
        self.message_origin_x = message_origin_x
        self.message_origin_y = message_origin_y

    def send_message(self, new_msg, color=Colors.white):
        # split the message if necessary, among multiple lines
        new_msg_lines = textwrap.wrap(new_msg, self.message_width)

        for line in new_msg_lines:
            # if the buffer is full, remove the first line to make room for the new one
            if len(self.game_msg) == self.message_height:
                self.game_msg = self.game_msg[1:]

            # add the new line as a tuple, with the text and the color
            self.game_msg.append((line, color))
