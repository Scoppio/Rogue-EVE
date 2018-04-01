from random import randint, uniform, choice
import itertools
import yaml
import os
from models import GameObjects
from models.EnumStatus import MapTypes, Cardinals
from models.GameObjects import DrawableObject, Vector2
import logging

logger = logging.getLogger('Rogue-EVE')


class Tile(object):
    """a tile of the map and its properties"""
    def __init__(self, blocked, x, y, block_sight=None):
        self.blocked = blocked
        self.explored = False
        self.x = x
        self.y = y
        self.id = (x, y)

        # by default, if a tile is blocked, it also blocks sight
        if block_sight is None:
            block_sight = blocked

        self.block_sight = block_sight

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return f"<Tile blocked={self.blocked} x={self.x} y={self.y}>"

class TileMap(DrawableObject):
    def __init__(self, map, rooms, color_dark_wall, color_light_wall, color_dark_ground, color_light_ground, legacy_mode):
        self.tile_map = map
        self.rooms = rooms
        self.height = len(map[0])
        self.width = len(map)
        self.color_dark_wall = color_dark_wall
        self.color_light_wall = color_light_wall
        self.color_dark_ground = color_dark_ground
        self.color_light_ground = color_light_ground
        self.legacy_mode = legacy_mode
        self.visible_tiles = None
        logger.info("Tilemap created with {} rooms".format(len(self.rooms)))

    def get_tile_by_id(self, id):
        x, y = id
        return self.tile_map[x][y]

    def get_tile_id(self, x, y):
        return (x, y)

    def set_visible_tiles(self, visible_tiles):
        self.visible_tiles = visible_tiles

    def in_bounds(self, id):
        (x, y) = id
        return 0 <= x < self.width and 0 <= y < self.height

    def passable(self, id):
        tile = self.get_tile_by_id(id)
        return not tile.blocked

    def neighbors(self, id):
        (x, y) = id
        results = [(x + 1, y), (x, y - 1), (x - 1, y), (x, y + 1)]
        if (x + y) % 2 == 0: results.reverse()  # aesthetics
        results = filter(self.in_bounds, results)
        results = filter(self.passable, results)
        return results

    def draw_with_color(self):
        self.legacy_mode = False

    def set_legacy_mode(self):
        self.legacy_mode = True

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_map(self):
        return self.tile_map

    def get_visible_tiles(self):
        return self.visible_tiles

    def get_rooms(self):
        return self.rooms

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "<TileMap height={height} width={width} legacy_mode={alt_print}>" \
            .format(height=self.height, width=self.width, alt_print=self.legacy_mode)

    def totals(self):
        total_tiles = list(itertools.chain(*self.tile_map))
        total_explored = sum([tile.explored for tile in total_tiles])
        logger.debug("Total explored: {}".format(total_explored))

    def is_visible_tile(self, x=None, y=None):
        if x >= self.width or x < 0:
            return False
        elif y >= self.height or y < 0:
            return False
        elif self.tile_map[x][y].blocked:
            return False
        elif self.tile_map[x][y].block_sight:
            return False
        else:
            return True

    def draw(self, console):
        for x in range(self.width):
            for y in range(self.height):
                visible = (x, y) in self.visible_tiles
                wall = self.tile_map[x][y].block_sight
                explored = self.tile_map[x][y].explored

                if visible:
                    self.tile_map[x][y].explored = True

                bg_color = None
                fg_color = None
                char = None
                if not visible:
                    if explored:
                        if wall:
                            if not self.legacy_mode:
                                bg_color = self.color_dark_wall
                            else:
                                fg_color = self.color_dark_wall
                                char = '#'

                        else:
                            if not self.legacy_mode:
                                bg_color = self.color_dark_ground
                            else:
                                fg_color = self.color_dark_ground
                                char = '.'
                elif visible:
                    if wall:
                        if not self.legacy_mode:
                            bg_color = self.color_light_wall
                        else:
                            fg_color = self.color_light_wall
                            char = '#'

                    else:
                        if not self.legacy_mode:
                            bg_color = self.color_light_ground
                        else:
                            fg_color = self.color_light_ground
                            char = '.'

                console.draw_char(x, y, char, fg=fg_color, bg=bg_color)
        self.totals()


class MapConstructor(object):
    def __init__(self, width, height, max_number_of_rooms):
        self.width = width
        self.height = height
        self.color_dark_wall = (0, 0, 100)
        self.color_light_wall = (130, 110, 50)
        self.color_dark_ground = (50, 50, 150)
        self.color_light_ground = (200, 180, 50)
        self.rooms= []
        self.room_max_size = 10
        self.room_min_size = 6
        self.max_rooms = max_number_of_rooms
        self.tile_set = []
        self.starting_tile = None

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

    def make_random_map(self, strategy: str="random", maximum_number_of_tries=100, legacy_mode=False):
        if strategy is MapTypes.RANDOM:
            return self._random_strategy(maximum_number_of_tries, legacy_mode)
        elif strategy is MapTypes.CONSTRAINT:
            raise NotImplementedError("Only the default random method is implemented by now")
        elif strategy is MapTypes.CONSTRUCTIVE1:
            return self._constructive_strategy(strategy, maximum_number_of_tries, legacy_mode)
        elif strategy is MapTypes.CONSTRUCTIVE2:
            raise NotImplementedError("Only the default random method is implemented by now")
        elif strategy is MapTypes.CONSTRUCTIVE3:
            raise NotImplementedError("Only the default random method is implemented by now")
        else:
            # default value is random strategy
            return self._random_strategy(maximum_number_of_tries, legacy_mode)

    def add_starting_tile_template(self, starting_tile):
        self.starting_tile = starting_tile
        return self

    def add_tile_template_folder(self, folder):
        for file in os.listdir(folder):
            self.tile_set.append(os.path.join(folder, file))
        return self

    def add_tile_template(self, tile_template):
        self.tile_set.append(tile_template)
        return self

    def _constructive_strategy(self, strategy, maximum_number_of_tries, legacy_mode):

        def room_has_no_intersections(_room):
            for r in self.rooms:
                if _room.intersect(r) or _room.x2 >= self.width and _room.y2 >= self.height:
                        return False
            return True

        def try_to_attach_room(new_room_tile):
            for attachment in [att for att in room_attachments if att.attached is None]:
                for new_room_attachment in new_room_tile.attachments:
                    if attachment.can_attach(new_room_attachment):
                        x = attachment.x
                        y = attachment.y
                        if attachment.cardinal == Cardinals.SOUTH:
                            x = x - new_room_attachment.x - 1
                            y = y
                        if attachment.cardinal == Cardinals.NORTH:
                            y = y - new_room.get_height()-1
                            x = x - new_room_attachment.x - 1
                        if attachment.cardinal == Cardinals.EAST:
                            y = y - new_room_attachment.y - 1
                            x = x
                        if attachment.cardinal == Cardinals.WEST:
                            x = x - new_room.get_width() - 1
                            y = y - new_room_attachment.y - 1
                        h, w = y + new_room.get_height(), x + new_room.get_width()
                        if x >= 0 and y >= 0 and h < self.height and w < self.width:
                            new_room_tile.setting_new_position(x, y)
                            if room_has_no_intersections(new_room_tile):
                                attachment.attach(new_room_attachment)
                                return True
            return False

        room_attachments = []
        failure = 0
        # if strategy == MapTypes.CONSTRUCTIVE1:
        #     maximum_number_of_tries = 50
        # if strategy == MapTypes.CONSTRUCTIVE2:
        #     maximum_number_of_tries = 75
        # if strategy == MapTypes.CONSTRUCTIVE3:
        #     maximum_number_of_tries = 150

        for n in range(maximum_number_of_tries):
            if len(self.rooms) >= self.max_rooms:
                break

            if not self.rooms:
                new_room = Room.load(self.starting_tile)
                x = randint(0, self.width - new_room.get_width() - 1)
                y = randint(0, self.height - new_room.get_height() - 1)
                new_room.setting_new_position(x, y)
                room_attachments = new_room.get_attachments()
                self.rooms.append(new_room)
            else:
                new_room = Room.load(choice(self.tile_set))

                if try_to_attach_room(new_room):
                    self.rooms.append(new_room)
                    new_attachments = new_room.get_attachments()
                    room_attachments.extend(new_attachments)
                    failure = 0
                else:
                    failure += 1
            if failure > 100 and len(self.rooms) <= 3:
                self.rooms = []

        # Here we can start to "paint" the map
        my_map = [[Tile(True, x, y)
                   for y in range(self.height)]
                  for x in range(self.width)]

        # build rooms
        for idx, room in enumerate(self.rooms):
            internals = room.get_internals()
            for n, x in enumerate(range(room.x1, room.x2)):
                for m, y in enumerate(range(room.y1, room.y2)):
                    try:
                        if internals[m][n] == "#":
                            my_map[x][y].blocked = True
                            my_map[x][y].block_sight = True
                        else:
                            my_map[x][y].blocked = False
                            my_map[x][y].block_sight = False
                    except IndexError as e:
                        logger.error("Index error X={} Y={} M={} N={}".format(x,y,m,n))

        return TileMap(
            my_map, self.rooms, self.color_dark_wall, self.color_light_wall,
            self.color_dark_ground, self.color_light_ground, legacy_mode
        )

    def _random_strategy(self, maximum_number_of_tries, legacy_mode):
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

        # fill map with "unblocked" tiles
        my_map = [[Tile(True, x, y)
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
                    self._create_h_tunnel(my_map, prev_vector.X, new_vector.X, prev_vector.Y)
                    self._create_v_tunnel(my_map, prev_vector.Y, new_vector.Y, new_vector.X)
                else:
                    # first move vertically, then horizontally
                    self._create_v_tunnel(my_map, prev_vector.Y, new_vector.Y, prev_vector.X)
                    self._create_h_tunnel(my_map, prev_vector.X, new_vector.X, new_vector.Y)

        return TileMap(my_map, self.rooms, self.color_dark_wall, self.color_light_wall,
                       self.color_dark_ground, self.color_light_ground, legacy_mode)

    @staticmethod
    def _create_h_tunnel(my_map, x1, x2, y):
        # build horzontal tunnels
        for x in range(min(x1, x2), max(x1, x2) + 1):
            my_map[x][y].blocked = False
            my_map[x][y].block_sight = False

    @staticmethod
    def _create_v_tunnel(my_map, y1, y2, x):
        # build vertical tunnels
        for y in range(min(y1, y2), max(y1, y2) + 1):
            my_map[x][y].blocked = False
            my_map[x][y].block_sight = False


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

    def get_height(self):
        return self.y2 - self.y1

    def get_width(self):
        return self.x2 - self.x1

    def intersect(self, other):
        # returns true if this rectangle intersects with another one
        # which happens only if all the following conditions are true

        cond1 = self.x1 < other.x2
        cond2 = self.x2 > other.x1
        cond3 = self.y1 < other.y2
        cond4 = self.y2 > other.y1

        return cond1 and cond2 and cond3 and cond4


class Attachment(object):
    def __init__(self, x, y, cardinal):
        self.x = x
        self.y = y
        self.cardinal = cardinal
        self.attached = None

    def can_attach(self, other):
        if other.cardinal == Cardinals.SOUTH and self.cardinal == Cardinals.NORTH:
                return True
        if other.cardinal == Cardinals.NORTH and self.cardinal == Cardinals.SOUTH:
                return True
        if other.cardinal == Cardinals.EAST and self.cardinal == Cardinals.WEST:
                return True
        if other.cardinal == Cardinals.WEST and self.cardinal == Cardinals.EAST:
                return True
        return False

    def attach(self, other):
        self.attached = other
        other.attached = self

    def detach(self):
        self.attached = None


class Room(Rect):
    def __init__(self, x, y, w, h, attachments, internals):
        super(Room, self).__init__(x=x, y=y, w=w, h=h)
        self.attachments = attachments
        self.internals = internals

    def setting_new_position(self, x, y):
        w = self.get_width()
        h = self.get_height()
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def _match_attachments(self, other):
        test_cardinal = set()
        for attachment in other.attachments:
            if attachment.cardinal == Cardinals.EAST:
                test_cardinal.add(Cardinals.WEST)
            if attachment.cardinal == Cardinals.WEST:
                test_cardinal.add(Cardinals.EAST)
            if attachment.cardinal == Cardinals.NORTH:
                test_cardinal.add(Cardinals.SOUTH)
            if attachment.cardinal == Cardinals.SOUTH:
                test_cardinal.add(Cardinals.NORTH)

        return any(t in [att.cardinal for att in self.attachments] for t in test_cardinal)

    def does_attach(self, other):
        if type(other) == Room:
            return self._match_attachments(other)
        else:
            return False

    def get_attachments(self):
        attachments = [Attachment(att.x + self.x1+1, att.y + self.y1+1, att.cardinal) for att in self.attachments]
        return attachments

    def attachment_choices(self, attachment):
        ret = []
        for att in self.attachments:
            if att.cardinal == Cardinals.EAST and attachment.cardinal == Cardinals.WEST:
                ret.append(att)
            if att.cardinal == Cardinals.WEST and attachment.cardinal == Cardinals.EAST:
                ret.append(att)
            if att.cardinal == Cardinals.NORTH and attachment.cardinal == Cardinals.SOUTH:
                ret.append(att)
            if att.cardinal == Cardinals.SOUTH and attachment.cardinal == Cardinals.NORTH:
                ret.append(att)
        return ret

    def get_internals(self):
        return self.internals

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "<Room x1={x1} y1={y1} x2={x2} y2={y2}>" \
            .format(x1=self.x1, x2=self.x2, y1=self.y1, y2=self.y2)

    @staticmethod
    def get_cardinal(x, y, w, h):
        if x == 0:
            return Cardinals.WEST
        if x == w - 1:
            return Cardinals.EAST
        if y == 0:
            return Cardinals.NORTH
        if y == h - 1:
            return Cardinals.SOUTH
        raise ReferenceError('The attachment is not posed on a border!', x, y, w, h)

    @staticmethod
    def load(yaml_file=None, hard_values=None):
        if yaml_file:
            with open(yaml_file) as stream:
                values = yaml.safe_load(stream)

            if not values:
                raise RuntimeError("File could not be read")
        else:
            values = hard_values

        attachments = []

        room = values["room_tiles"]
        map = room["map"]
        height = len(map)
        width = len(map[0])
        for y in range(height):
            for x in range(width):
                if map[y][x] == "A":
                    try:
                        attachments.append(Attachment(x, y, Room.get_cardinal(x, y, width, height)))
                    except Exception as e:
                        print(e)
                        raise RuntimeError(room["name"] + " failed to load an attachment")

        internals = map

        logging.debug("Loading tile template {}".format(room["name"]))

        return Room(
                x=0,
                y=0,
                h=height,
                w=width,
                attachments=attachments,
                internals=internals
            )


class MapObjectsConstructor(object):
    """MapObjectsConstructor is a special factory that receives the templates of monsters and items,
    and automatically populates the map necessary objects with the proper references for those newly added
    objects to the map, collision handler and object pool
    """
    def __init__(self, tile_map=None, object_pool=None, collision_handler=None, object_templates=list(), max_monster_per_room: int=0, max_items_per_room: int=0, game_instance=None):
        print("starting object constructor")
        if game_instance:
            self.tile_map = game_instance.map
            self.object_pool = game_instance.object_pool
            self.collision_handler = game_instance.collision_handler
        else:
            self.tile_map = tile_map
            self.object_pool = object_pool
            self.collision_handler = collision_handler

        self.object_templates = object_templates
        self.max_monsters_per_room = max_monster_per_room
        self.max_items_per_room=max_items_per_room

    def _append_template(self, obj):
        """Runs the proper safe evals on the object to create the template and add to the template list"""
        if obj["type"] in [a for a in dir(GameObjects) if "__" not in a]:
            obj_template = eval("GameObjects." + obj["type"])
            self.object_templates.append((obj_template, obj["params"], obj["weight"]))
        else:
            logger.warning("Object {} is not recognizable as a GameObject", obj["type"])

    def load_object_templates(self, yaml_file):
        """Load an yaml object with the template for the level"""
        print("Loading objects template")
        logger.info("Loading objects template")

        with open(yaml_file) as stream:
            template = yaml.safe_load(stream)

        if not template:
            raise RuntimeError("File could not be read")

        if "map-data" in template.keys():
            if template["map-data"]["max-room-items"]:
                logger.info("max-room-items: {}".format(template["map-data"]["max-room-items"]))
                self.max_items_per_room = template["map-data"]["max-room-items"]

            if template["map-data"]["max-room-monsters"]:
                logger.info("max-room-monsters: {} ".format(template["map-data"]["max-room-monsters"]))
                self.max_monsters_per_room = template["map-data"]["max-room-monsters"]

        if "items" in template.keys():
            for obj in template["items"]:
                self._append_template(obj)

        if "monsters" in template.keys():
            for obj in template["monsters"]:
                self._append_template(obj)

        return MapObjectsConstructor(self.tile_map, self.object_pool, self.collision_handler,
                                     self.object_templates, self.max_monsters_per_room, self.max_items_per_room)

    def _append_object_template(self, level_template, key):
        if key in level_template.keys():
            for obj in level_template[key]:
                if obj["type"] in [a for a in dir(GameObjects) if "__" not in a]:
                    obj_template = eval("GameObjects." + obj["type"])

                    self.object_templates.append((obj_template, obj["params"], obj["weight"]))
                else:
                    logger.warning("Object {} is not recognizable as a GameObject", obj["type"])

    def load_level_template(self, yaml_file):

        with open(yaml_file) as stream:
            level_template = yaml.safe_load(stream)

        if not level_template:
            raise RuntimeError("File could not be read")

        self._append_object_template(level_template, "items")
        self._append_object_template(level_template, "monsters")

        self.max_monsters_per_room = level_template["max-room-monsters"]
        self.max_items_per_room =  level_template["max-room-items"]

        return MapObjectsConstructor(self.tile_map, self.object_pool, self.collision_handler,
                                     self.object_templates, self.max_monsters_per_room, self.max_items_per_room)

    def set_max_objects_per_room(self, value):
        self.max_monsters_per_room = value
        return MapObjectsConstructor(self.tile_map, self.object_pool, self.collision_handler,
                                     self.object_templates, self.max_monsters_per_room, self.max_items_per_room)

    def set_max_items_per_room(self, value):
        self.max_items_per_room = value
        return MapObjectsConstructor(self.tile_map, self.object_pool, self.collision_handler,
                                     self.object_templates, self.max_monsters_per_room, self.max_items_per_room)

    def get_random_object_template(self, tag):
        filtered_template_list = [template for template in self.object_templates if tag in template[1]["tags"]]

        total = sum(w for _, _, w in filtered_template_list)
        r = uniform(0, total)
        upto = 0
        for obj_template, argument_template, weight in filtered_template_list:
            if upto + weight >= r:
                return obj_template.load(hard_values=argument_template)
            upto += weight
        else:
            assert False, "List is empty"

    def populate_room(self, room):
        self._place_object(room, self.max_items_per_room, "item", 2)
        self._place_object(room, self.max_monsters_per_room, "monster", 1)

    def _place_object(self, room, max_objects, tag, z_index):
        num_objects = randint(0, max_objects)
        print("Trying to put {} from {} max {} on room {}".format(num_objects, max_objects, tag, room))
        for i in range(num_objects):
            # choose random spot for this object
            if type(room) == Room:
                print("It is a proper room")
                internals = room.internals
                positions = []
                for y in range(len(internals)):
                    for x in range(len(internals[0])):
                        if internals[y][x] != "#":
                            positions.append(Vector2(x + room.x1,y + room.y1))
                tries = 3
                coord = choice(positions)
                while(tries):
                    if not self.collision_handler.is_blocked(coord.X, coord.Y):
                        coord = choice(positions)
                        tries -= 1
                        print("could not add monster to map", room, coord, tries)
                    else:
                        print("monster placed", room, coord, tries)
                        tries = 0

            else:
                print("It is just a rect!")
                coord = Vector2(randint(room.x1+1, room.x2-1), randint(room.y1+1, room.y2-1))

            if not self.collision_handler.is_blocked(coord.X, coord.Y):
                print("Adding monster to map")
                prototype = self.get_random_object_template(tag)
                prototype.coord = coord
                prototype.collision_handler = self.collision_handler
                self.object_pool.append(prototype)
            else:
                print("could not add monster to map", room, coord)

    def populate_map(self):
        for idx, room in enumerate(self.tile_map.get_rooms()):
            if idx:
                self.populate_room(room)