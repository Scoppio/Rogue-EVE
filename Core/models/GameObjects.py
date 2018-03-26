import numbers
import math
import logging
import copy
import yaml
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
            # print("closes point of interest for tag {} {}".format(self.interest_tag, closest_point_of_interest))

            # move towards player if far away
            if closest_point_of_interest['dist'] >= 2:
                monster.move_towards(closest_point_of_interest['obj'].coord)

            # close enough, attack! (if the player is still alive.)
            elif closest_point_of_interest['obj'].fighter.hp > 0:
                monster.fighter.attack(closest_point_of_interest['obj'])

    def get_closest_point_of_interest(self):
        points_of_interest = self.owner.object_pool.find_by_tag(self.interest_tag)
        closest_point_of_interest = {'obj': None, 'dist': 1000000}
        for poi in points_of_interest:
            dist = Vector2.distance(self.owner.coord, poi.coord)
            if dist < closest_point_of_interest['dist']:
                closest_point_of_interest['dist'] = dist
                closest_point_of_interest['obj'] = poi

        return closest_point_of_interest


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


class Fighter(object):
    def __init__(self, hp, defense, power, death_function):
        self.owner = None
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        self.death_function = death_function

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
            if self.collision_handler.is_blocked((self.coord + step).X, (self.coord + step).Y):
                return

        self.coord = self.coord + step

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
        # vector from this object to the target, and distance
        distance = Vector2.distance(self.coord, target)

        # normalize it to length 1 (preserving direction), then round it and
        # convert to integer so the movement is restricted to the map grid
        dx = int(round((target - self.coord).X / distance))
        dy = int(round((target - self.coord).Y / distance))
        self.move(Vector2(dx, dy))

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
                 object_pool=None
            ):
        super(Item, self).__init__(coord=coord, char=char, color=color, name=name, blocks=blocks, _id=_id, tags=tags)
        self.object_pool=object_pool

    def pick_up(self, player):
        # add to the player's inventory and remove from the map
        if player.get_inventory() is not None:
            if len(player.get_inventory()) >= 26:
                send_message('Your inventory is full, cannot pick up ' + self.name + '.', Colors.red)
            else:
                player.get_inventory().append(self)
                send_message('You picked up a ' + self.name + '!', Colors.green)
                return True
        return False

    @staticmethod
    def load(yaml_file=None, hard_values=None, coord=Vector2.zero(), collision_handler=None):
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
            color = Colors.white

        return Item(
            coord=coord,
            char=values["char"],
            color=color,
            name=values["name"],
            blocks=values["blocks"],
            tags=values["tags"]
        )