import tdl
import logging
from models.EnumStatus import EGameState, EAction
from models.GameObjects import Vector2, Item
from managers import InputPeripherals, ObjectManager

logger = logging.getLogger('Rogue-EVE')


class GameContext(object):
    def __init__(self, object_pool = None, mouse_controller = None, map = None, game_state = None, real_time=False, menu=None, camera=None):
        self.object_pool = object_pool
        self.mouse_controller = mouse_controller
        self.map = map
        self.player = None
        self.game_state = game_state
        self.fov_recompute = False
        self.collision_handler = None
        self.mouse_controller = None
        self.player_action = None
        self.real_time = real_time
        self.menu = menu
        self.camera = camera

        if self.collision_handler and self.object_pool:
            self._set_collision_handler()
            self._set_mouse_controller()

    def set_object_pool(self, object_pool):
        self.object_pool = object_pool
        if self.map:
            self._set_collision_handler()
            self._set_mouse_controller()

    def set_map(self, map):
        self.map = map
        if self.object_pool:
            self._set_collision_handler()
            self._set_mouse_controller()

    def set_player(self, player, inventory_width=40):
        self.player = player
        self.player.context = self
        self.object_pool.add_player(self.player)
        self.inventory_width = inventory_width

    def _set_mouse_controller(self):
        self.mouse_controller = InputPeripherals.MouseController(map=self.map, object_pool=self.object_pool)

    def _set_collision_handler(self):
        self.collision_handler = ObjectManager.CollisionHandler(map=self.map, object_pool=self.object_pool)

    def handle_keys(self):
        self.player_action = EAction.DIDNT_TAKE_TURN
        self.fov_recompute = False
        user_input = None
        keypress = False

        for event in tdl.event.get():
            if event.type == 'KEYDOWN':
                user_input = event
                keypress = True

            if event.type == 'MOUSEMOTION':
                self.mouse_controller.set_mouse_coord(event.cell)

        if not keypress:
            return

        logger.debug("User_Input [key={} alt={} ctrl={} shift={}]".format(
            user_input.key, user_input.alt, user_input.control, user_input.shift))

        if user_input.key == 'ENTER' and user_input.alt:
            # Alt+Enter: toggle fullscreen
            tdl.set_fullscreen(not tdl.get_fullscreen())

        elif user_input.key == 'ESCAPE':
            self.player_action = EAction.EXIT
            # exit game
            return

        if self.game_state.state == EGameState.PLAYING:
            self.fov_recompute = False

            # movement keys
            if user_input.key == 'UP':
                self.fov_recompute = self.player.move_or_attack(Vector2(0, -1))
                self.player_action = EAction.MOVE_UP
            elif user_input.key == 'DOWN':
                self.fov_recompute = self.player.move_or_attack(Vector2(0, 1))
                self.player_action = EAction.MOVE_DOWN
            elif user_input.key == 'LEFT':
                self.fov_recompute = self.player.move_or_attack(Vector2(-1, 0))
                self.player_action = EAction.MOVE_LEFT
            elif user_input.key == 'RIGHT':
                self.fov_recompute = self.player.move_or_attack(Vector2(1, 0))
                self.player_action = EAction.MOVE_RIGHT
            elif user_input.text == 'g':
                # pick up an item
                for obj in [item for item in self.object_pool.get_objects_as_list()
                            if type(item) == Item
                               and item.coord == self.player.coord]:
                    obj.pick_up(self.player)
                    self.object_pool.delete_by_id(obj._id)
                    break

            elif user_input.text == 'i':
                # show the inventory
                chosen_item = self.inventory_menu('Press the key next to an item to use it, or any other to cancel.\n')
                if chosen_item is not None:
                    chosen_item.use()

    def inventory_menu(self, header):
        if self.menu:
            # show a menu with each item of the inventory as an option
            if len(self.player.inventory) == 0:
                options = ['Inventory is empty.']
            else:
                options = [item.name for item in self.player.inventory]

            index = self.menu(header, options, self.inventory_width)

            # if an item was chosen, return it
            if index is None or len(self.player.get_inventory()) == 0: return None
            return self.player.get_inventory()[index]
        else:
            logger.error("menu function is not being referenced inside the game context")

    def run_ai_turn(self):
        monster_action = True

        if self.real_time:
            if self.player_action != EAction.DIDNT_TAKE_TURN:
                monster_action = True
        else:
            if self.player_action == EAction.DIDNT_TAKE_TURN:
                monster_action = False

        if self.game_state.get_state() == EGameState.PLAYING and monster_action:
            for obj in self.object_pool.find_by_tag('monster'):
                if obj.ai:
                    obj.ai.take_turn()

    def closest_object(self, max_range, tag_of_interest):
        # find closest enemy, up to a maximum range, and in the player's FOV
        closest_enemy = None
        closest_dist = max_range + 1  # start with (slightly more than) maximum range

        for monster in self.object_pool.find_by_tag(tag_of_interest):
            if self.map.is_visible_tile(monster.coord.X, monster.coord.Y):
                # calculate distance between this object and the player
                dist = Vector2.distance(monster.coord, self.player.coord)
                if dist < closest_dist:  # it's closer, so remember it
                    closest_enemy = monster
                    closest_dist = dist
        return closest_enemy

    def target_tile(self, max_range=None):
        # return the position of a tile left-clicked in player's FOV (optionally in
        # a range), or (None,None) if right-clicked.
        while True:
            tdl.flush()
            clicked = False
            for event in tdl.event.get():
                if event.type == 'MOUSEMOTION':
                    self.mouse_controller.mouse_coord = event.cell
                if event.type == 'MOUSEDOWN' and event.button == 'LEFT':
                    clicked = True
                elif ((event.type == 'MOUSEDOWN' and event.button == 'RIGHT') or
                      (event.type == 'KEYDOWN' and event.key == 'ESCAPE')):
                    return (None, None)

            self.camera.render_all_objects()

            coord = Vector2(*self.mouse_controller.mouse_coord)

            if (clicked and self.map.is_visible_tile(coord.X, coord.Y)
                    and (max_range is None or Vector2.distance(coord, self.player.coord) <= max_range)):
                return self.mouse_controller.mouse_coord

    def target_object(self, max_range=None, target_tag=None):
        # returns a clicked monster inside FOV up to a range, or None if right-clicked
        while True:
            (x, y) = self.target_tile(max_range)
            if x is None:  # player cancelled
                return None

            mouse_coord = Vector2(x,y)
            # return the first clicked monster, otherwise continue looping
            if target_tag:
                for obj in self.object_pool.find_by_tag(target_tag):
                    if obj.coord == mouse_coord and obj != self.player:
                        return obj
            else:
                for obj in self.object_pool.get_objects_as_list():
                    if obj.coord == mouse_coord and obj != self.player:
                        return obj

    def targeting(self, target_mode=None, target_tag=None, max_range=None, radius=0, visible_only=True):

        if target_mode == "single":
            return list(self.target_object(max_range, target_tag))

        elif target_mode == "self":
            return list(self.player)

        elif target_mode == "closest":
            return list(self.closest_object(max_range, target_tag))

        elif target_mode == "area":
            x, y = self.target_tile(max_range)
            coord = Vector2(x, y)

        else:
            logger.error("target_mode unknown {}".format(target_mode))
            return []

        ret = list()
        if target_tag:
            for obj in self.object_pool.find_by_tag(target_tag):
                if not visible_only or self.map.is_visible_tile(obj.coord.X, obj.coord.Y):
                    if Vector2.distance(obj.coord, coord) <= radius:
                        ret.append(obj)
        else:
            for obj in self.object_pool.get_objects_as_list():
                if not visible_only or self.map.is_visible_tile(obj.coord.X, obj.coord.Y):
                    if Vector2.distance(obj.coord, coord) <= radius:
                        ret.append(obj)
        return ret