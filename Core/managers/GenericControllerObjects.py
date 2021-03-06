import tdl
import logging
from models.EnumStatus import EGameState, EAction, EMessage
from models.GameObjects import Item, Equipment
from models.GenericObjects import Vector2
from managers import InputPeripherals, ObjectManager, Messenger
from utils import Colors

logger = logging.getLogger('Rogue-EVE')


class GameContext(object):
    def __init__(self, next_level, object_pool = None, mouse_controller = None, map = None, game_state=None,
                 real_time=False, menu=None, camera=None, lower_gui_renderer=None):
        self.object_pool = object_pool
        self.mouse_controller = mouse_controller
        self.map = map
        self.player = None
        self.game_state = game_state
        self.fov_recompute = False
        self.collision_handler = None
        self.player_action = None
        self.real_time = real_time
        self.menu = menu
        self.camera = camera
        self.lower_gui_renderer = lower_gui_renderer
        self.next_level = next_level
        self.extras = {}
        self.setup_broadcast_message()
        if self.collision_handler and self.object_pool:
            self._set_collision_handler()
            self._set_mouse_controller()

    def setup_broadcast_message(self):
        Messenger.broadcast_handler = self

    def broadcast_message(self, tag, body):
        if tag == "game-controller":
            if EMessage.LEVEL_UP in body.keys():
                self._player_level_up(body[EMessage.LEVEL_UP])
                self._monsters_level_up()
                Messenger.send_message(
                    "You hear a thundering roar echoing! The monsters also became stronger!",
                    color=Colors.crimson
                )
            elif EMessage.MONSTERS_LEVEL_UP in body.keys():
                self._monsters_level_up()

        for obj in self.object_pool.find_by_tag(tag):
            obj.receive_message(tag, body)

    def _player_level_up(self, player):
        choice = None
        while choice is None:  # keep asking until a choice is made
            choice = self.menu('Level up! Choose a stat to raise:\n',
                          ['Constitution (+20 HP, from ' + str(player.fighter.max_hp) + ')',
                           'Strength (+1 attack, from ' + str(player.fighter.power) + ')',
                           'Agility (+1 defense, from ' + str(player.fighter.defense) + ')'], 40)
        if choice == 0:
            player.fighter.base_max_hp += 20
            player.fighter.hp += 20
        elif choice == 1:
            player.fighter.base_power += 1
        elif choice == 2:
            player.fighter.base_defense += 1
        player.fighter.heal_percent(1)

    def _monsters_level_up(self):
        for monster in self.object_pool.find_by_tag("monster"):
            if monster.fighter:
                monster.level = self.player.fighter.level
                monster.fighter.automatic_level_up()

    def add_extra(self, key, value):
        self.extras[key] = value

    def get_extra(self, key, default=None):
        if key in self.extras.keys():
            return self.extras[key]
        else:
            logger.error("Key {} is not present in extras".format(key))
        return default

    def set_object_pool(self, object_pool):
        self.object_pool = object_pool
        if self.map:
            self.object_pool.map = self.map
            self._set_collision_handler()
            self._set_mouse_controller()

    def set_map(self, map):
        self.map = map
        if self.object_pool:
            self._set_collision_handler()
            self._set_mouse_controller()
            self.object_pool.map=self.map

    def set_player(self, player, inventory_width=8):
        self.player = player
        self.player.context = self
        self.object_pool.add_player(self.player)
        self.inventory_width = inventory_width

    def _set_mouse_controller(self):
        self.mouse_controller = InputPeripherals.MouseController(map=self.map, object_pool=self.object_pool)
        self.mouse_controller.camera = self.camera
        logger.info("Mouse is set up")

    def _set_collision_handler(self):
        if self.collision_handler:
            self.collision_handler.set_map(self.map)
        else:
            self.collision_handler = ObjectManager.CollisionHandler(map=self.map, object_pool=self.object_pool)

    def message_box(self, message, width=40):
        self.menu(message, [], width)

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

            return

        if self.game_state.state == EGameState.PLAYING:
            self.fov_recompute = False
            # movement keys
            if user_input.key == "UP" or user_input.key == "KP8":
                self.fov_recompute = self.player.move_or_attack(Vector2(0, -1))
                self.player_action = EAction.MOVE_UP
            elif user_input.key == "DOWN" or user_input.key == "KP2":
                self.fov_recompute = self.player.move_or_attack(Vector2(0, 1))
                self.player_action = EAction.MOVE_DOWN
            elif user_input.key == "LEFT" or user_input.key == "KP4":
                self.fov_recompute = self.player.move_or_attack(Vector2(-1, 0))
                self.player_action = EAction.MOVE_LEFT
            elif user_input.key == "RIGHT" or user_input.key == "KP6":
                self.fov_recompute = self.player.move_or_attack(Vector2(1, 0))
                self.player_action = EAction.MOVE_RIGHT
            elif user_input.key == "HOME" or user_input.key == "KP7":
                self.fov_recompute = self.player.move_or_attack(Vector2(-1, -1))
                self.player_action = EAction.MOVE_DIAGONAL_UL
            elif user_input.key == "PAGEUP" or user_input.key == "KP9":
                self.fov_recompute = self.player.move_or_attack(Vector2(1, -1))
                self.player_action = EAction.MOVE_DIAGONAL_UR
            elif user_input.key == "END" or user_input.key == "KP1":
                self.fov_recompute = self.player.move_or_attack(Vector2(-1, 1))
                self.player_action = EAction.MOVE_DIAGONAL_DL
            elif user_input.key == "PAGEDOWN" or user_input.key == "KP3":
                self.fov_recompute = self.player.move_or_attack(Vector2(1, 1))
                self.player_action = EAction.MOVE_DIAGONAL_DR
            elif user_input.key == "KP5":
                self.player_action = EAction.WAITING
                # do nothing ie wait for the monster to come to you

            elif user_input.text == 'g':
                # pick up an item
                for obj in [item for item in self.object_pool.get_objects_as_list()
                            if (type(item) == Item or type(item) == Equipment)
                               and item.coord == self.player.coord]:
                    obj.pick_up(self.player)
                    self.object_pool.delete_by_id(obj._id)
                    break

            elif user_input.text == '<' or user_input.text == '/' :
                # pick up an item
                for obj in [stair for stair in self.object_pool.find_by_tag("stairs")
                            if stair.coord == self.player.coord]:
                    self.extras["dungeon_level"] += 1
                    self.next_level()
                    self.fov_recompute = True
                    break

            elif user_input.text == 'i':
                # show the inventory
                chosen_item = self.inventory_menu('Press the key next to an item to use it, or any other to cancel.\n')
                if chosen_item is not None:
                    chosen_item.use()

            elif user_input.text == 'd':
                # show the inventory; if an item is selected, drop it
                chosen_item = self.inventory_menu('Press the key next to an item to' +
                                             'drop it, or any other to cancel.\n')
                if chosen_item is not None:
                    chosen_item.drop()

            elif user_input.text == 'c':
                # show character information
                self.message_box(
                    'Character Information\n\nLevel: ' + str(self.player.fighter.level) + '\nExperience: ' + str(self.player.fighter.xp) +
                    '\nExperience to level up: ' + str(self.player.fighter.level_up_xp) + '\n\nMaximum HP: ' + str(self.player.fighter.max_hp) +
                    '\nAttack: ' + str(self.player.fighter.power) + '\nDefense: ' + str(self.player.fighter.defense))

    def inventory_menu(self, header):
        if self.menu:
            # show a menu with each item of the inventory as an option
            if len(self.player.inventory) == 0:
                options = ['Inventory is empty.']
            else:
                options = [item.get_name() for item in self.player.inventory]

            index = self.menu(header, options, self.inventory_width)

            # if an item was chosen, return it
            if index is None or len(self.player.get_inventory()) == 0:
                return None
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

            coord = Vector2(*self.mouse_controller.mouse_coord) + self.camera.camera_coord

            if (clicked and self.map.is_visible_tile(coord.X, coord.Y)
                    and (max_range is None or Vector2.distance(coord, self.player.coord) <= max_range)):
                self.mouse_controller.set_mouse_coord(coord)
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

    def targeting(self, **kwargs):
        target_mode, target_tag, range, visible_only, radius = None, None, None, True, 0
        for k, v in kwargs.items():
            if k == "target_mode":
                target_mode = v
            if k == "target_tag":
                target_tag = v
            if k == "range":
                range = v
            if k == "visible_only":
                visible_only = v
            if k == "radius":
                radius = v

        if target_mode == "ranged":
            return [self.target_object(range, target_tag)]

        elif target_mode == "self":
            return [self.player]

        elif target_mode == "closest":
            return [self.closest_object(range, target_tag)]

        elif target_mode == "area":
            x, y = self.target_tile(range)
            coord = Vector2(x, y)
            if not x and not y:
                return []

        else:
            logger.error("target_mode unknown {}".format(target_mode))
            return []

        ret = []
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

    def set_camera(self, camera):
        self.camera = camera
        if self.mouse_controller:
            self.mouse_controller.camera = self.camera