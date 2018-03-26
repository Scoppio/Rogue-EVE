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
                 width: int = 0,
                 height: int = 0,
                 origin: Vector2 = None,
                 target: Vector2 = None,
                 console: object = None,
                 mouse_controller = None
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
        self.mouse_controller = mouse_controller

    def set_mouse_controller(self, mouse_controller):
        self.mouse_controller = mouse_controller

    def set_fov_recompute_to(self, val: bool):
        self.fov_recompute = val

    def reset_fov_recompute(self):
        self.fov_recompute = False

    def fov_must_recompute(self):
        return self.fov_recompute

    def add_bar(self, x, y, total_width, name, value_name, maximum_value_name, obj, bar_color, back_color):

        self.bars.append(
            {'x': x,
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
            text = args['name'] + ': ' + str(value) + '/' + str(maximum)
            x_centered = args['x'] + (args['total_width'] - len(text)) // 2
            self.console.draw_str(x_centered, args['y'], text, fg=Colors.white, bg=None)

        y = self.message_origin_y
        for (line, color) in self.game_msg:
            self.console.draw_str(self.message_origin_x, y, line, bg=None, fg=color)
            y += 1

        if self.mouse_controller:
            self.console.draw_str(1, 0, self.mouse_controller.get_names_under_mouse(), bg=None, fg=Colors.light_gray)

        # blit the contents of "panel" to the root console
        self.root.blit(self.console, self.origin.X, self.origin.Y, self.width, self.height, self.target.X,
                       self.target.Y)

    def render_all_objects(self):
        player = self.object_pool.get_player()

        if self.fov_must_recompute():
            # recompute FOV if needed (the player moved or something)
            self.reset_fov_recompute()
            self.visible_tiles = tdl.map.quickFOV(player.coord.X, player.coord.Y,
                                                  self.map.is_visible_tile,
                                                  fov=self.fov_algorithm,
                                                  radius=player.torch,
                                                  lightWalls=self.fov_light_walls)

            self.map.set_visible_tiles(self.visible_tiles)
            if self.map:
                self.map.draw(self.console)

        if self.object_pool and self.object_pool.get_objects_as_list():
            sorted_objects_list = sorted(self.object_pool.get_objects_as_list(), key=lambda x: x.z_index, reverse=False)

            for obj in sorted_objects_list:
                if (obj.coord.X, obj.coord.Y) in self.visible_tiles:
                    obj.draw(self.console)

            if self.object_pool.get_player():
                player = self.object_pool.get_player()
                player.draw(self.console)

        self.root.blit(self.console, self.origin.X, self.origin.Y, self.width, self.height, self.target.X,
                       self.target.Y)

    def clear_all_objects(self):
        if self.object_pool:
            for obj in self.object_pool.get_objects_as_list():
                obj.clear(self.console)

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
