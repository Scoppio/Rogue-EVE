import uuid
import numbers
import math
from random import randint
import logging

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
        return "<Vector2 X=" + str(self.X) + " Y=" + str(self.Y) + ">"

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
            self.X /= length
            self.Y /= length
        else:
            print("Length 0, cannot normalize.")

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
            return ((vec1.X * vec2.X) + (vec1.Y * vec2.Y))
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
    def __init__(self, coord: Vector2, char: str ='@', color: tuple=(255, 255, 255), _id: str=None):
        if _id:
            self._id = _id
        else:
            self._id = uuid.uuid4()

        self.coord = coord
        self.char = char
        self.color = color

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "<GameObject _id={_id} coord={coord} char={char} color={color}>" \
            .format(_id=self._id, coord=self.coord, char=self.char, color=self.color)

    def draw(self, console):
        console.draw_char(self.coord.X, self.coord.Y, self.char, bg=None, fg=self.color)

    def clear(self, console):
        console.draw_char(self.coord.X, self.coord.Y, ' ', bg=None, fg=self.color)


class Character(GameObject):
    def __init__(self, coord: Vector2, life: int=0, mana: int=0, char: str="@", color: tuple=(255, 255, 255),
                 blocks=True, _id: str=None, collision_handler=None):
        super(Character, self).__init__(coord, char, color, _id)
        self.life = life
        self.mana = mana
        self.collision_handler = collision_handler
        self.blocks = blocks

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "<Character _id={_id} coord={coord} char={char} color={color} life={life} mana={mana}>" \
            .format(_id=self._id, coord=self.coord, char=self.char, color=self.color, life=self.life, mana=self.mana)

    def move(self, step: Vector2):
        if self.collision_handler:
            if self.collision_handler.is_blocked((self.coord + step).X, (self.coord + step).Y):
                return

        self.coord = self.coord + step


class Tile(object):
    # a tile of the map and its properties
    def __init__(self, blocked, block_sight=None):
        self.blocked = blocked

        # by default, if a tile is blocked, it also blocks sight
        if block_sight is None:
            block_sight = blocked

        self.block_sight = block_sight


class TileMap(DrawableObject):
    def __init__(self, map, rooms, dark_color, not_so_dark_color):
        self.tile_map = map
        self.rooms = rooms
        self.height = len(map)
        self.width = len(map[0])
        self.dark_color = (0, 0, 100)
        self.not_so_dark_color = (50, 50, 150)
        self.legacy_mode = False

    def draw_with_color(self):
        self.legacy_mode = False

    def draw_with_chars(self):
        self.legacy_mode = True

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_map(self):
        return self.tile_map

    def get_rooms(self):
        return self.rooms

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "<TileMap height={height} width={width} legacy_mode={alt_print}>" \
            .format(height=self.height, width=self.width, alt_print=self.legacy_mode)

    def draw(self, console):
        for x in range(len(self.tile_map)):
            for y in range(len(self.tile_map[0])):
                wall = self.tile_map[x][y].block_sight
                bg_color = None
                fg_color = None
                char = None
                if wall:
                    if not self.legacy_mode:
                        bg_color = self.not_so_dark_color
                    else:
                        fg_color = self.not_so_dark_color
                        char = '#'

                else:
                    if not self.legacy_mode:
                        bg_color = self.dark_color
                    else:
                        fg_color = self.dark_color
                        char = '.'

                console.draw_char(x, y, char, fg=fg_color, bg=bg_color)


class MapConstructor(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.dark_color = (0, 0, 100)
        self.not_so_dark_color = (50, 50, 150)
        self.rooms= []
        self.room_max_size = 10
        self.room_min_size = 6
        self.max_rooms = 30

    def set_width(self, width):
        self.width = width
        return self

    def set_height(self, height):
        self.height = height
        return self

    def get_width(self, width):
        return self.width

    def get_height(self, height):
        return self.height

    def set_dark_color(self, color):
        self.dark_color = color
        return self

    def set_not_so_dark_color(self, color):
        self.not_so_dark_color = color
        return self

    def add_room(self, room, ignore_intersection=False):
        if len(self.rooms) < self.max_rooms:
            if not ignore_intersection:
                for other_room in self.rooms:
                    if room.intersect(other_room):
                        logger.error("<MapConstructor rooms={} max_rooms={} error={}>".format(
                            len(self.rooms), self.max_rooms, '"Room intersects with other rooms')
                        )
                        return self

            self.rooms.append(room)
        else:
            logger.warning("<MapConstructor rooms={} max_rooms={}>".format(len(self.rooms), self.max_rooms))
        return self

    def _create_random_room(self):
        # random width and height
        w = randint(self.room_min_size, self.room_max_size)
        h = randint(self.room_min_size, self.room_max_size)
        # random position without going out of the boundaries of the map
        x = randint(0, self.width - w - 1)
        y = randint(0, self.height - h - 1)

        # "Rect" class makes rectangles easier to work with
        return Rect(x, y, w, h)

    def populate_with_random_rooms(self, maximum_number_of_tries=100):
        for _ in range(maximum_number_of_tries):
            new_room = self._create_random_room()

            # run through the other rooms and see if they intersect with this one
            failed = False
            for other_room in self.rooms:
                if new_room.intersect(other_room):
                    logger.warning("<MapConstructor rooms={} max_rooms={} error={}>".format(
                        len(self.rooms), self.max_rooms, '"Could not fit new random room inside'))
                    failed = True
                    break

            if not failed:
                self.add_room(new_room)

        return self

    def build_map(self):
        # build horzontal tunnels
        def create_h_tunnel(x1, x2, y):
            for x in range(min(x1, x2), max(x1, x2) + 1):
                my_map[x][y].blocked = False
                my_map[x][y].block_sight = False

        # build vertical tunnels
        def create_v_tunnel(y1, y2, x):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                my_map[x][y].blocked = False
                my_map[x][y].block_sight = False

        # fill map with "unblocked" tiles
        my_map = [[Tile(True)
                   for y in range(self.height)]
                  for x in range(self.width)]

        # build rooms
        for idx, room in enumerate(self.rooms):
            for x in range(room.x1 + 1, room.x2):
                for y in range(room.y1 + 1, room.y2):
                    my_map[x][y].blocked = False
                    my_map[x][y].block_sight = False

            new_vector = room.center()
            if idx:
                prev_vector = self.rooms[idx - 1].center()

                # draw a coin (random number that is either 0 or 1)
                if randint(0, 1):
                    # first move horizontally, then vertically
                    create_h_tunnel(prev_vector.X, new_vector.X, prev_vector.Y)
                    create_v_tunnel(prev_vector.Y, new_vector.Y, new_vector.X)
                else:
                    # first move vertically, then horizontally
                    create_v_tunnel(prev_vector.Y, new_vector.Y, prev_vector.X)
                    create_h_tunnel(prev_vector.X, new_vector.X, new_vector.Y)

        return TileMap(my_map, self.rooms, self.dark_color, self.not_so_dark_color)


class Rect(object):
    # a rectangle on the map. used to characterize a room.
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "<Rect x1={x1} y1={y1} x2={x2} y2={y2}>"\
            .format(x1=self.x1, x2=self.x2, y1=self.y1, y2=self.y2)

    def center(self):
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return Vector2(center_x, center_y)

    def intersect(self, other):
        # returns true if this rectangle intersects with another one
        # which happens only if all the following conditions are true

        cond1 = self.x1 <= other.x2
        cond2 = self.x2 >= other.x1
        cond3 = self.y1 <= other.y2
        cond4 = self.y2 >= other.y1

        return cond1 and cond2 and cond3 and cond4