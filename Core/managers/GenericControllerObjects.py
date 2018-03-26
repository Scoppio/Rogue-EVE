import tdl
import logging
from models.EnumStatus import EGameState, EAction
from models.GameObjects import Vector2, Item
from managers import InputPeripherals, ObjectManager

logger = logging.getLogger('Rogue-EVE')


class GameContext(object):
    def __init__(self, object_pool = None, mouse_controller = None, map = None, game_state = None, real_time=False, menu=None):
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
                self.inventory_menu('Press the key next to an item to use it, or any other to cancel.\n')
        return

    def inventory_menu(self, header):
        if self.menu:
            # show a menu with each item of the inventory as an option
            if len(self.player.inventory) == 0:
                options = ['Inventory is empty.']
            else:
                options = [item.name for item in self.player.inventory]

            index = self.menu(header, options, self.inventory_width)
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