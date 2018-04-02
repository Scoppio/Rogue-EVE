import numbers
import math
import logging
import copy
import yaml
from utils import PathFinding
from random import randint
from utils import Colors
from models.EnumStatus import EGameState
from managers.Messenger import send_message

logger = logging.getLogger('Rogue-EVE')


class Vector2(object):
    def __init__(self, X=0.0, Y=0.0):
        self.X = X
        self.Y = Y

    def __add__(self, other):
        if isinstance(other, Vector2):
            new_vec = Vector2()
            new_vec.X = self.X + other.X
            new_vec.Y = self.Y + other.Y
            return new_vec
        else:
            raise TypeError("other must be of type Vector2")

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, Vector2):
            new_vec = Vector2()
            new_vec.X = self.X - other.X
            new_vec.Y = self.Y - other.Y
            return new_vec
        else:
            raise TypeError("other must be of type Vector2")

    def __rsub__(self, other):
        return self.__sub__(other)

    def __mul__(self, value):
        if isinstance(value, numbers.Number):
            new_vec = self.copy()
            new_vec.X = new_vec.X * value
            new_vec.Y = new_vec.Y * value
            return new_vec
        else:
            raise TypeError("value must be a number.")

    def __rmul__(self, value):
        return self.__mul__(value)

    def __truediv__(self, value):
        if isinstance(value, numbers.Number):
            if value:
                new_vec = self.copy()
                new_vec.X /= value
                new_vec.Y /= value
                return new_vec
            else:
                raise ZeroDivisionError("Cannot divide by zero.")
        else:
            raise TypeError("value must be a number.")

    def __floordiv__(self, value):
        if isinstance(value, numbers.Number):
            if value:
                new_vec = self.copy()
                new_vec.X = new_vec.X // value
                new_vec.Y = new_vec.Y // value
                return new_vec
            else:
                raise ZeroDivisionError("Cannot divide by zero.")
        else:
            raise TypeError("value must be a number.")

    def __rtruediv__(self, value):
        return self.__truediv__(value)

    def __rfloordiv__(self, value):
        return self.__floordiv__(value)

    def __abs__(self):
        return Vector2(abs(self.X), abs(self.Y))

    def __eq__(self, other):
        """Check to see if two Vector2 objects are equal"""
        if isinstance(other, Vector2):
            if self.X == other.X and self.Y == other.Y:
                return True
        else:
            raise TypeError("other must be of type Vector2")

        return False

    def __neg__(self):
        return Vector2(-self.X, -self.Y)

    def __getitem__(self, index):
        if index > 1:
            raise IndexError("Index must be less than 2")

        if index == 0:
            return self.X
        else:
            return self.Y

    def __setitem__(self, index, value):
        if index > 1:
            raise IndexError("Index must be less than 2")

        if index == 0:
            self.X = value
        else:
            self.Y = value

    def __str__(self):
        return "(X=" + str(self.X) + " Y=" + str(self.Y)+")"

    def __len__(self):
        return 2

    def as_tuple(self):
        return (self.X, self.Y)

    # Define our properties
    @staticmethod
    def zero():
        """Returns a Vector2 with all attributes set to 0"""
        return Vector2(0, 0)

    @staticmethod
    def one():
        """Returns a Vector2 with all attribures set to 1"""
        return Vector2(1, 1)

    def copy(self):
        """Create a copy of this Vector"""
        new_vec = Vector2()
        new_vec.X = self.X
        new_vec.Y = self.Y
        return new_vec

    def length(self):
        """Gets the length of this Vector"""
        return math.sqrt((self.X * self.X) + (self.Y * self.Y))

    def normalize(self):
        """Gets the normalized Vector"""
        length = self.length()
        if length > 0:
            return Vector2(int(self.X / length), int(self.Y / length))
        else:
            logger.error("Length 0, cannot normalize.")
            return Vector2.zero()

    def as_tuple(self):
        return (self.X, self.Y)

    def normalize_copy(self):
        """Create a copy of this Vector, normalize it, and return it."""
        vec = self.copy()
        vec.normalize()
        return vec

    @staticmethod
    def distance(vec1, vec2):
        """Calculate the distance between two Vectors"""
        if isinstance(vec1, Vector2) \
                and isinstance(vec2, Vector2):
            dist_vec = vec2 - vec1
            return dist_vec.length()
        else:
            raise TypeError("vec1 and vec2 must be Vector2's")

    @staticmethod
    def dot(vec1, vec2):
        """Calculate the dot product between two Vectors"""
        if isinstance(vec1, Vector2) \
                and isinstance(vec2, Vector2):
            return (vec1.X * vec2.X) + (vec1.Y * vec2.Y)
        else:
            raise TypeError("vec1 and vec2 must be Vector2's")

    @staticmethod
    def angle(vec1, vec2):
        """Calculate the angle between two Vector2's"""
        dotp = Vector2.dot(vec1, vec2)
        mag1 = vec1.length()
        mag2 = vec2.length()
        result = dotp / (mag1 * mag2)
        return math.acos(result)

    @staticmethod
    def lerp(vec1, vec2, time):
        """Lerp between vec1 to vec2 based on time. Time is clamped between 0 and 1."""
        if isinstance(vec1, Vector2) \
                and isinstance(vec2, Vector2):
            # Clamp the time value into the 0-1 range.
            if time < 0:
                time = 0
            elif time > 1:
                time = 1

            x_lerp = vec1[0] + time * (vec2[0] - vec1[0])
            y_lerp = vec1[1] + time * (vec2[1] - vec1[1])
            return Vector2(x_lerp, y_lerp)
        else:
            raise TypeError("Objects must be of type Vector2")

    @staticmethod
    def from_polar(degrees, magnitude):
        """Convert polar coordinates to Carteasian Coordinates"""
        vec = Vector2()
        vec.X = math.cos(math.radians(degrees)) * magnitude

        # Negate because y in screen coordinates points down, oppisite from what is
        # expected in traditional mathematics.
        vec.Y = -math.sin(math.radians(degrees)) * magnitude
        return vec

    @staticmethod
    def component_mul(vec1, vec2):
        """Multiply the components of the vectors and return the result."""
        new_vec = Vector2()
        new_vec.X = vec1.X * vec2.X
        new_vec.Y = vec1.Y * vec2.Y
        return new_vec

    @staticmethod
    def component_div(vec1, vec2):
        """Divide the components of the vectors and return the result."""
        new_vec = Vector2()
        new_vec.X = vec1.X / vec2.X
        new_vec.Y = vec1.Y / vec2.Y
        return new_vec


class DrawableObject(object):
    def draw(self, console):
        pass

    def clear(self, console):
        pass


class GameObject(DrawableObject):
    def __init__(self,
                 coord: Vector2,
                 char: str ='@',
                 color: tuple=(255, 255, 255),
                 name: str='unnamed',
                 blocks: bool=False,
                 _id: str=None,
                 tags=list()
                 ):
        self._id = _id
        self.coord = coord
        self.char = char
        self.color = color
        self.blocks = blocks
        self.name = name
        self.object_pool = None
        self.tags = tags
        self.z_index = 1
        self.context = None

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "GameObject {tags} {name} _id={_id} coord={coord} char={char} color={color} blocks={blocks}".format(
                tags=self.tags, name=self.name, _id=self._id, coord=self.coord, char=self.char, color=self.color,
                blocks=self.blocks
                )

    @staticmethod
    def load(yaml_file=None, hard_values=None):
        if yaml_file:
            with open(yaml_file) as stream:
                values = yaml.safe_load(stream)

            if not values:
                raise RuntimeError("File could not be read")
        else:
            values = hard_values

        if values["color"] in [a for a in dir(Colors) if "__" not in a]:
            color = eval("Colors." + values["color"])
        else:
            color = Colors.dark_crimson

        return GameObject(
            coord=Vector2.zero(),
            char=values["char"],
            color=color,
            name=values["name"],
            blocks=values["blocks"],
            tags=values["tags"]
            )

    def set_z_index(self, value):
        self.z_index = value

    def draw(self, console):
        console.draw_char(self.coord.X, self.coord.Y, self.char, bg=None, fg=self.color)

    def clear(self, console):
        console.draw_char(self.coord.X, self.coord.Y, ' ', bg=None, fg=self.color)


class BasicMonsterAI(object):
    def __init__(self, interest_tag='player'):
        self.owner = None
        self.interest_tag=interest_tag
        self.visible_tiles_ref = None

    # AI for a basic monster.
    def take_turn(self):
        # a basic monster takes its turn. If you can see it, it can see you
        monster = self.owner
        visible_tiles = self.owner.collision_handler.map.get_visible_tiles()

        if (monster.coord.X, monster.coord.Y) in visible_tiles:
            closest_point_of_interest = self.get_closest_point_of_interest()
            pos = closest_point_of_interest["coord"] - self.owner.coord
            pos = (abs(pos.X) + abs(pos.Y))
            # move towards player if far away
            if pos > 1:
                monster.move_towards(closest_point_of_interest['obj'].coord)

            # close enough, attack! (if the player is still alive.)
            elif closest_point_of_interest['obj'].fighter.hp > 0:
                monster.fighter.attack(closest_point_of_interest['obj'])

    def get_closest_point_of_interest(self):
        points_of_interest = self.owner.object_pool.find_by_tag(self.interest_tag)
        closest_point_of_interest = {'obj': None, 'dist': 1000000, 'coord': Vector2.zero()}

        for poi in points_of_interest:
            dist = Vector2.distance(self.owner.coord, poi.coord)
            if dist < closest_point_of_interest['dist']:
                closest_point_of_interest['dist'] = dist
                closest_point_of_interest['obj'] = poi
                closest_point_of_interest['coord'] = poi.coord

        return closest_point_of_interest


class ConfusedMonsterAI(object):
    # AI for a temporarily confused monster (reverts to previous AI after a while).
    def __init__(self, old_ai, num_turns=5):
        self.owner = None
        self.old_ai = old_ai
        self.num_turns = num_turns

    def take_turn(self):
        if self.num_turns > 0:  # still confused...
            # move in a random direction, and decrease the number of turns confused
            self.owner.move(Vector2(randint(-1, 1), randint(-1, 1)))
            self.num_turns -= 1

        else:  # restore the previous AI (this one will be deleted because it's not referenced anymore)
            self.owner.ai = self.old_ai
            send_message('The ' + self.owner.name + ' is no longer confused!', Colors.red)


class FrozenMonsterAI(object):
    # AI for a temporarily freezes monster (reverts to previous AI after a while).
    def __init__(self, old_ai, num_turns=5):
        self.owner = None
        self.old_ai = old_ai
        self.num_turns = num_turns

    def take_turn(self):
        if self.num_turns > 0:  # still confused...
            # move in a random direction, and decrease the number of turns confused
            self.num_turns -= 1

        else:  # restore the previous AI (this one will be deleted because it's not referenced anymore)
            self.owner.ai = self.old_ai
            send_message('The ' + self.owner.name + ' is no longer frozen!', Colors.red)


class DeathMethods(object):
    @staticmethod
    def player_death(player):
        """ the game ended!"""
        logger.info('You died!')
        player.game_state.set_state(EGameState.DEAD)
        # for added effect, transform the player into a corpse!
        player.char = '%'
        player.color = Colors.dark_red
        player.z_index = 0

    @staticmethod
    def monster_death(monster):
        """ transform it into a nasty corpse! it doesn't block, can't be
        attacked and doesn't move"""
        logger.info(monster.name.capitalize() + ' is dead!')
        monster.char = '%'
        monster.color = Colors.dark_red
        monster.blocks = False
        monster.fighter = None
        monster.ai = None
        monster.name = 'remains of ' + monster.name
        monster.z_index = 0
        monster.tags = ["corpse"]


class UseFunctions(object):
    @staticmethod
    def invalid_function(ref, **kwargs):
        send_message('The {} vanishes!'.format(ref.name))

    @staticmethod
    def do_nothing(ref, **kwargs):
        pass

    @staticmethod
    def cast_heal(ref, **kwargs):
        # heal the targets
        objs = ref.context.targeting(**kwargs)

        if objs:
            for obj in objs:
                if obj.fighter.hp < obj.fighter.max_hp:
                    send_message("The {}'s wounds start to feel better!", Colors.light_violet)
                    obj.fighter.heal(kwargs["heal_amount"])
                else:
                    send_message("The {} is already at full health!", Colors.light_violet)
        else:
            send_message('No targets found!', Colors.red)
            return 'cancelled'

    @staticmethod
    def cast_selfheal(ref, **kwargs):
        # heal the player
        if ref.context.player.fighter.hp == ref.context.player.fighter.max_hp:
            send_message('You are already at full health.', Colors.red)
            return 'cancelled'

        send_message('Your wounds start to feel better!', Colors.light_violet)
        ref.context.player.fighter.heal(kwargs["heal_amount"])

    @staticmethod
    def cast_lightning(ref, **kwargs):
        # find closest enemy (inside a maximum range) and damage it
        objs = ref.context.targeting(**kwargs)

        if objs:
            for obj in objs:
                # zap it!
                send_message('A lighting bolt strikes the ' + obj.name + ' with a loud thunder! The damage is '
                        + str(ref.extra_params["damage"]) + ' hit points.', Colors.light_blue)
                obj.fighter.take_damage(ref.extra_params["damage"])
        else:
            send_message('No targets found!')
            return 'canceled'

    @staticmethod
    def cast_fireball(ref, **kwargs):
        # ask the player for a target tile to throw a fireball at

        send_message('Left-click a target tile for the {}, or right-click to cancel.'.format(ref.name), Colors.light_cyan)

        objs = ref.context.targeting(**kwargs)

        if objs:
            send_message('The fireball explodes, burning everything within ' + str(kwargs["radius"]) + ' tiles!', Colors.orange)
            for obj in objs:
                # damage every fighter in range, including the player
                send_message('The ' + obj.name + ' gets burned for ' + str(kwargs["damage"]) + ' hit points.', Colors.orange)
                if obj.fighter:
                    obj.fighter.take_damage(kwargs["damage"])
        else:
            send_message('Canceled!', Colors.blue)
            return 'cancelled'

    @staticmethod
    def cast_confuse(ref, **kwargs):
        # find closest enemy in-range and confuse it
        monsters = ref.context.targeting(**kwargs)
        if monsters:  # no enemy found within maximum range
            for monster in monsters:
                # replace the monster's AI with a "confused" one; after some turns it will restore the old AI
                StatusEffects.behavior_change(target=monster, behaviour="confused", **kwargs)
                send_message('The eyes of the ' + monster.name + ' look vacant, as he starts to stumble around!',
                             Colors.light_green)
        else:
            send_message('No enemy is close enough to confuse.', Colors.red)
            return 'cancelled'

    @staticmethod
    def custom_magic(ref, **kwargs):
        targets = ref.context.targeting(**kwargs)

        if targets:  # no enemy found within maximum range
            if "status_effect" in kwargs.keys():
                status_effect = kwargs["status_effect"]
            else:
                status_effect = None

            if "heal_amount" in kwargs.keys():
                heal_amount = kwargs["heal_amount"]
            else:
                heal_amount = None
            if "damage" in kwargs.keys():
                damage = kwargs["damage"]
            else:
                damage = None

            if "flavor_text" in kwargs.keys():
                flavor_text = kwargs["flavor_text"]
            else:
                flavor_text = "The {target} was hit by {name}!"

            for target in targets:
                if status_effect:
                    status_effect(target=target, **kwargs)

                if target.fighter:
                    if damage:
                        target.fighter.take_damage(damage)
                    if heal_amount:
                        target.fighter.heal(heal_amount)

                send_message(flavor_text.format(target=target.name,name=ref.name, **kwargs),
                             Colors.light_green)
        else:
            send_message('No target found!', Colors.red)
            return 'cancelled'


class StatusEffects(object):

    @staticmethod
    def behavior_change(**kwargs):
        monster = kwargs["target"]
        behaviour = kwargs["behaviour"]

        if "number_of_turns" in kwargs.keys():
            number_of_turns = kwargs["number_of_turns"]
        else:
            number_of_turns = 5

        old_ai = monster.ai # monster.ai
        if behaviour == "confused":
            monster.ai = ConfusedMonsterAI(old_ai, number_of_turns)
        elif behaviour == "frozen":
            monster.ai = FrozenMonsterAI(old_ai, number_of_turns)

        monster.ai.owner = monster  # tell the new component who owns it


class Fighter(object):
    def __init__(self, hp, defense, power, death_function):
        self.owner = None
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        self.death_function = death_function

    def heal(self, amount):
        # heal by the given amount, without going over the maximum
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def take_damage(self, damage):
        # apply damage if possible
        if damage > 0:
            self.hp -= damage
        # check for death. if there's a death function, call it
        if self.hp <= 0:
            self.hp = 0
            function = self.death_function
            if function is not None:
                function(self.owner)

    def attack(self, target):
        # a simple formula for attack damage
        damage = self.power - target.fighter.defense

        if damage > 0:
            # make the target take some damage
            send_message(self.owner.name.capitalize() +
                         ' attacks ' + target.name + ' for ' + str(damage) + ' hit points.',
                         Colors.light_blue)
            # print(self.owner.name.capitalize() + ' attacks ' + target.name + ' for ' + str(damage) + ' hit points.')
            target.fighter.take_damage(damage)
        else:
            send_message(self.owner.name.capitalize() + ' attacks ' + target.name + ' but it has no effect!',
                         Colors.light_blue)
            # print(self.owner.name.capitalize() + ' attacks ' + target.name + ' but it has no effect!')

    @staticmethod
    def load(yaml_file=None, hard_values=None):
        if yaml_file:
            with open(yaml_file) as stream:
                values = yaml.safe_load(stream)

            if not values:
                raise RuntimeError("File could not be read")
        else:
            values = hard_values

        death_function = None

        if "death_function" in values.keys():
            if values["death_function"] in [a for a in dir(DeathMethods) if "__" not in a]:
                death_function = eval("DeathMethods." + values["death_function"])

        return Fighter(
            values["hp"],
            values["defense"],
            values["power"],
            death_function
        )


class Character(GameObject):
    def __init__(self,
                 coord: Vector2=None,
                 char: str="@",
                 color: tuple=(255, 255, 255),
                 name='unnamed',
                 fighter=None,
                 ai=None,
                 blocks=True,
                 _id: str=None,
                 collision_handler=None,
                 torch=10,
                 tags=list(),
                 game_state=None,
                 inventory=None
            ):
        super(Character, self).__init__(coord=coord, char=char, color=color, name=name, blocks=blocks, _id=_id, tags=tags)

        self.torch = torch
        self.collision_handler = collision_handler
        self.game_state = game_state
        self.fighter = copy.copy(fighter)

        if self.fighter:
            # let the fighter component know who owns it
            self.fighter.owner = self

        self.ai = copy.copy(ai)
        if self.ai:
            # let the AI component know who owns it
            self.ai.owner = self

        self.inventory = inventory

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "Character {name} _id={_id} coord={coord} char={char} color={color}".format(
            name=self.name, _id=self._id, coord=self.coord, char=self.char, color=self.color
        )

    def move(self, step: Vector2):
        if self.collision_handler:
            direction = self.coord + step
            print(direction)
            if self.collision_handler.is_blocked(*direction):
                return

        self.coord = direction

    def get_inventory(self):
        return self.inventory

    def move_or_attack(self, step):
        """
        Decides for movement or attack, and return if the field of view has to be recomputed
        :param step:
        :return fov_recompute flag:
        """
        fov_recompute = False

        # try to find an attackable object on the coordinates the player is moving to/attacking

        target = self.collision_handler.collides_with(self, (self.coord + step).X, (self.coord + step).Y)

        # attack if target found, move otherwise
        if target is not None and target.fighter:
            #print('The ' + target.name + ' laughs at your puny efforts to attack him!')
            self.fighter.attack(target)
        else:
            self.move(step)
            fov_recompute = True

        return fov_recompute

    def move_towards(self, target: Vector2):
        result = PathFinding.breadth_first_search(self.collision_handler.map, self.coord.as_tuple(), target.as_tuple())
        print(result)
        coord = Vector2(*result[1])

        self.move(coord-self.coord)

    @staticmethod
    def load(yaml_file=None, hard_values=None, coord=Vector2.zero(), collision_handler=None, game_state=None, inventory=None):
        if yaml_file:
            with open(yaml_file) as stream:
                values = yaml.safe_load(stream)

            if not values:
                raise RuntimeError("File could not be read")
        else:
            values = hard_values

        fighter = None
        if values["fighter"]:
            fighter = Fighter.load(hard_values=values["fighter"])

        if values["color"] in [a for a in dir(Colors) if "__" not in a]:
            color = eval("Colors." + values["color"])
        else:
            color = Colors.white

        ai = None
        if "ai" in values.keys():
            ai = BasicMonsterAI(interest_tag=values["ai"]["interest_tag"])

        torch = 0
        if "torch" in values.keys():
            torch = values["torch"]

        if inventory:
            inventory = list()

        return Character(
            coord=coord,
            char=values["char"],
            color=color,
            name=values["name"],
            fighter=fighter,
            ai=ai,
            blocks=values["blocks"],
            collision_handler=collision_handler,
            torch=torch,
            tags=values["tags"],
            game_state=game_state,
            inventory=inventory
        )


class Item(GameObject):
    def __init__(self,
                 coord: Vector2=None,
                 char: str="!",
                 color: tuple=(255, 255, 255),
                 name='unnamed item',
                 blocks=False,
                 _id: str=None,
                 tags=list(),
                 use_function=None,
                 extra_params=None
            ):
        super(Item, self).__init__(coord=coord, char=char, color=color, name=name, blocks=blocks, _id=_id, tags=tags)
        self.use_function=use_function
        self.extra_params=extra_params
        self.player = None

    def use(self):
        # just call the "use_function" if it is defined
        if self.use_function is None:
            send_message('The ' + self.name + ' cannot be used. It vanishes!', color=Colors.azure)
        else:
            if self.use_function(self, **self.extra_params) != 'cancelled' and self.context.player.get_inventory():
                self.context.player.get_inventory().remove(self)  # destroy after use, unless it was cancelled for some reason
                self.context = None

    def pick_up(self, player):
        # add to the player's inventory and remove from the map
        if player.get_inventory() is not None:
            if len(player.get_inventory()) >= 26:
                send_message('Your inventory is full, cannot pick up ' + self.name + '.', Colors.red)
            else:
                self.context = player.context
                player.get_inventory().append(self)
                send_message('You picked up a ' + self.name + '!', Colors.green)
                return True
        return False

    def drop(self):
        self.coord = self.context.player.coord
        self.context.object_pool.append(self)
        self.context.player.get_inventory().remove(self)
        self.context = None
        send_message('You droped ' + self.name + '!', Colors.yellow)

    @staticmethod
    def load(yaml_file=None, hard_values=None, coord=Vector2.zero(), collision_handler=None):
        if yaml_file:
            with open(yaml_file) as stream:
                values = yaml.safe_load(stream)

            if not values:
                raise RuntimeError("File could not be read")
        else:
            values = hard_values

        color = Colors.white
        if values["color"] in [a for a in dir(Colors) if "__" not in a]:
            color = eval("Colors." + values["color"])

        if values["use_function"] in [a for a in dir(UseFunctions) if "__" not in a]:
            use_function = eval("UseFunctions." + values["use_function"])
        else:
            logger.error("Could not find use_function {}".format(values["use_function"]))
            use_function = UseFunctions.do_nothing

        if "extra_params" in values.keys() and "status_effect" in values["extra_params"].keys():
            if values["extra_params"]["status_effect"] in [a for a in dir(StatusEffects) if "__" not in a]:
                values["extra_params"]["status_effect"] = eval("StatusEffects." +  values["extra_params"]["status_effect"])

        return Item(
            coord=coord,
            char=values["char"],
            color=color,
            name=values["name"],
            blocks=values["blocks"],
            tags=values["tags"],
            use_function=use_function,
            extra_params=values["extra_params"]
        )