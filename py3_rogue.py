# http://www.roguebasin.com/index.php?title=Complete_Roguelike_Tutorial,_using_python%2Blibtcod,_part_4

import tcod as libtcod
import configparser
import threading
import random
import socket
import time
import json
import math
import os


tLock = threading.Lock()

config = configparser.RawConfigParser()

if not os.path.isfile('settings.cfg'):
    #actual size of the window
    config.add_section('UI')
    config.set('UI', 'SCREEN_WIDTH', '80')
    config.set('UI', 'SCREEN_HEIGHT', '60')
    config.add_section('GAME-CONFIG')
    config.set('GAME-CONFIG', 'FPS', '20')
    config.set('GAME-CONFIG', 'ROOM_MAX_SIZE', '10')
    config.set('GAME-CONFIG', 'ROOM_MIN_SIZE', '6')
    config.set('GAME-CONFIG', 'MAX_ROOMS', '30')
    config.set('GAME-CONFIG', 'OLD_SCHOOL', 'false')
    config.set('GAME-CONFIG', 'MAX_ROOM_MONSTER', '3')
    config.add_section('GFX')
    config.set('GFX', 'TORCH_RADIUS', '10')
    config.set('GFX', 'EXPLORED_MEMORY', 'true')
    config.add_section('SERVER')
    config.set('SERVER', 'HOST', '127.0.0.1')
    config.set('SERVER', 'PORT', '5000')
    config.set('SERVER', 'CONNECT', 'false') #not online by default

    # Writing our configuration file to 'example.cfg'
    with open('settings.cfg', 'w') as configfile:
        config.write(configfile)

config.read('settings.cfg')

SCREEN_WIDTH = config.getint('UI', 'SCREEN_WIDTH')
SCREEN_HEIGHT = config.getint('UI', 'SCREEN_HEIGHT')

MAP_WIDTH = SCREEN_WIDTH #80
MAP_HEIGHT = SCREEN_HEIGHT-5 #55

LIMIT_FPS = config.getint('GAME-CONFIG', 'FPS')  #20 frames-per-second maximum

ROOM_MAX_SIZE = config.getint('GAME-CONFIG', 'ROOM_MAX_SIZE')
ROOM_MIN_SIZE = config.getint('GAME-CONFIG', 'ROOM_MIN_SIZE')
MAX_ROOMS =  config.getint('GAME-CONFIG', 'MAX_ROOMS')
OLD_SCHOOL =  config.getboolean('GAME-CONFIG', 'OLD_SCHOOL')
MAX_ROOM_MONSTER = config.getint('GAME-CONFIG', 'MAX_ROOM_MONSTER')

FOV_ALGO = 0
FOV_LIGHT_WALLS = True
TORCH_RADIUS = config.getint('GFX', 'TORCH_RADIUS')
EXPLORED_MEMORY = config.getboolean('GFX', 'EXPLORED_MEMORY')


SERVER_CONNECTION = config.getboolean('SERVER', 'CONNECT')

color_dark_wall = libtcod.Color(0,0,100)
color_dark_ground = libtcod.Color(50,50,150)
color_light_wall = libtcod.Color(130, 110, 50)
color_light_ground = libtcod.Color(200,180,50)

libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)

con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'python/libtcod tutorial', False)

libtcod.sys_set_fps(LIMIT_FPS) #for RT-ONLY

fov_recompute = True

class Object:
    # generic class object: player, monster, item, stairs
    # it is always represented by a character on screen.
    def __init__(self, x, y, char, name, color, blocks = False, fighter=None, ai=None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.fighter = fighter
        if self.fighter:
            self.fighter.owner = self

        self.ai = ai
        if self.ai:
            self.ai.owner = self

    def move(self, dx, dy):
        #move by a given amount
        if not is_blocked(self.x + dx, self.y + dy):
            if not map[self.x + dx][self.y + dy].blocked: # collision detection
                self.x += dx
                self.y += dy

    def move_towards(self, target_x, target_y):
        # vector from target to object and distance.
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # normalize preserving direction and round it
        # so the movement is restricted to map grid and to 1 step only
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        print(dx, dy)
        self.move(dx, dy)

    def distance_to(self, other):
        # return the distance to another object
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def draw(self):
        # set the color and then draw the character that represents this object at its position
        if libtcod.map_is_in_fov(fov_map, self.x, self.y):
            libtcod.console_set_default_foreground(con, self.color)
            libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)

    def clear(self):
        # erase the character that represents this object
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

class Tile:
    # a tile of the map and its properties
    def __init__(self, blocked, block_sight = None):
        self.blocked = blocked

        # by default, if a tile is blocked, it also blocks sight
        if block_sight is None: block_sight = blocked
        self.block_sight = block_sight
        self.explored = False

class Rect:
    # a rectangle - origin is at top-left
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self):
        # returns the center of the rectangle hur dur
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return (center_x, center_y)

    def intersects(self, other):
        # returns true if this rectangle intersects with another one
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and 
                self.y1 <= other.y2 and self.y2 >= other.y1)

# Monster/item classes

class Fighter:
    # combat-related properties and methods
    def __init__(self, hp=1, defense=0, power=0, dodge=0, luck=0):
        self.max_hp = hp
        self.hp = hp
        self.defende = defense
        self.power = power
        self.dodge = dodge
        self.luck = luck

class BasicMonster(object):
    """docstring for BasicMonster"""
    def __init__(self, *arg, **kwarg):
        super(BasicMonster, self).__init__()
        self.arg = arg
        self.kwarg = kwarg

    def take_turn(self):
        # a basic monster takes its turn.
        monster = self.owner
        
        # if you can see the monster, it can see you
        # also, he may have somekind of superpower that allows him to see you at N distance
        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
            # move towards player if he is far away
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.x, player.y)
                print("{} moves towards player".format(monster.name) )
                print("monster x:{} y:{} - player x:{} y{}".format(monster.x, monster.y, player.x, player.y))

            # if it is close enough, attack! (if the player is alive)
            elif player.fighter.hp > 0:
                print ( "the attack of the {} bounces of your shiny metal armor".format(monster.name))

# IA classes
class AdvancedMonster(object):
    """docstring for BlindMonster"""
    def __init__(self, sense = 0, reach = 2):
        super(BlindMonster, self).__init__()
        if reach < 2:
            reach = 2
        self.sense = sense
        self.reach = reach

    def take_turn(self):
        # a basic monster takes its turn.
        monster = self.owner
        
        # if you can see the monster, it can see you
        # also, he may have somekind of superpower that allows him to see you at N distance

        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y) or (monster.distance_to(player) <= monster.sense and monster.sense > 0):
            # move towards player if he is far away
            if monster.distance_to(player) >= self.reach:
                monster.move_towards(player.x, player.y)
                
            # if it is close enough, attack! (if the player is alive)
            elif player.fighter.hp > 0:
                print ( "the attack of the {} bounces of your shiny metal armor".format(monster.name))


def create_room(room):
    global map
    # go through the tiles in the rectangle and make them passable

    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            map[x][y].blocked = False
            map[x][y].block_sight = False

def create_h_tunnel(x1, x2, y):
    global map
    # horizontal tunnel

    for x in range(min(x1,x2), max(x1, x2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False

def create_v_tunnel(y1, y2, x):
    global map
    # horizontal tunnel

    for y in range(min(y1,y2), max(y1, y2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False

def place_objects(room):
    # choose random number of monsters
    num_monsters = random.randint(0, MAX_ROOM_MONSTER)

    for i in range(num_monsters):
        # choose random spot for monster
        x = random.randint(room.x1, room.x2)
        y = random.randint(room.y1, room.y2)
        if not is_blocked(x, y):
            choice = random.randint(0, 100)
            
            if choice < 20:
                # create imp
                fighter_component = Fighter(hp=2, defense=0, power=1)
                ai_component = BasicMonster()
                monster = Object(x, y, 'm', 'imp', libtcod.desaturated_red, blocks=True,
                    fighter = fighter_component, ai = ai_component)

            elif choice < 20+40:
                # create an orc
                fighter_component = Fighter(hp=10, defense=0, power=3)
                ai_component = BasicMonster()
                monster = Object(x, y, 'o', 'orc', libtcod.desaturated_green, blocks=True,
                    fighter = fighter_component, ai = ai_component)

            elif choice < 20+40+20:
                # create troll
                fighter_component = Fighter(hp=16, defense=1, power=4)
                ai_component = BasicMonster()
                monster = Object(x, y, 'T', 'troll', libtcod.darker_green, blocks=True,
                    fighter = fighter_component, ai = ai_component)

            elif choice < 20+40+20+5:
                # create vampire
                fighter_component = Fighter(hp=25, defense=3, power=6)
                ai_component = BasicMonster()
                monster = Object(x, y, 'V', 'vampire', libtcod.darker_red, blocks=True,
                    fighter = fighter_component, ai = ai_component)
            else:
                continue

            objects.append(monster)

def is_blocked(x, y):
    #test the map title for blockness
    if map[x][y]. blocked:
        return True

    #now check for any blocking objects
    for object in objects:
        if object.blocks and object.x == x and object.y == y:
            return True

    return False

def handle_keys():
    global fov_recompute
    key = libtcod.console_check_for_keypress()

    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # ALT+Enter: toggle Fullscreen
        # libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen()) # sugest not using it
        print("Fullscreen offline")

    elif key.vk == libtcod.KEY_ESCAPE:
        return 'exit'

    if game_state == "playing":
        #movement keys
        if libtcod.console_is_key_pressed(libtcod.KEY_UP):
            player_move_or_attack(0,-1)
            fov_recompute = True

        elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
            player_move_or_attack(0,1)
            fov_recompute = True

        elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
            player_move_or_attack(-1,0)
            fov_recompute = True

        elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
            player_move_or_attack(1,0)
            fov_recompute = True
    else:
        return "didnt-take-turn"

def player_move_or_attack(dx, dy):
    global fov_recompute

    x = player.x + dx
    y = player.y + dy

    # try to find a valid target for attacks
    target = None
    for object in objects:
        if object.x == x and object.y == y:
            target = object
            break

    # attack if target found, move if otherwise
    if target is not None:
        print("The", target.name, "laughs at your puny efforts to attack him!")

    else:
        player.move(dx, dy)
        fov_recompute = True


def comm( message, time_window):
    print("starting comm")
    while True:
        e = json.dumps(message)
        try:
            s.send(e.encode())
        except:
            # print('FAILED TO DELIVER')
            pass
        time.sleep(time_window)

def make_map():
    global map

    # fill map with "unblocked" tiles
    map = [[ Tile(True)
        for y in range(MAP_HEIGHT)]
            for x in range(MAP_WIDTH)]

        # create two rooms
    rooms = []
    num_rooms = 0

    for r in range(MAX_ROOMS):
        # random width and height
        w = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        # random position inside map boundaries
        x = random.randint(0, MAP_WIDTH - w - 1)
        y = random.randint(0, MAP_HEIGHT - h - 1)

        new_room = Rect(x, y, w, h)

        failed = False
        # search if we find any rooms that intersect here
        for other_room in rooms:
            if new_room.intersects(other_room):
                failed = True
                break

        if not failed:
            # case the room is valid

            create_room(new_room)

            (new_x, new_y) = new_room.center()

            if num_rooms == 0:
                player.x = new_x
                player.y = new_y
                print(new_x,new_y)

            else:
                # all rooms after the first get a tunnel that connects to the last one
                (prev_x, prev_y) = rooms[num_rooms-1].center()

                if random.randint(0,1) == 1:
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                else:
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)

            place_objects(new_room)
            rooms.append(new_room)
            num_rooms += 1

def render_all():
    global fov_recompute
    # draw all objects in the list

    if fov_recompute:
        # recompute FOV only when needed
        fov_recompute = False
        libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)

    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            visible = libtcod.map_is_in_fov(fov_map, x, y)
            wall = map[x][y].block_sight
            if not visible:
                if map[x][y].explored: # in case it was explored
                    if wall:
                        if OLD_SCHOOL:
                            libtcod.console_set_default_foreground(con, color_dark_wall)
                            libtcod.console_put_char(con, x, y, ':', libtcod.BKGND_NONE)
                        else:
                            libtcod.console_set_char_background(con, x, y, color_dark_wall, libtcod.BKGND_SET)
                    else:
                        if OLD_SCHOOL:
                            libtcod.console_set_default_foreground(con, color_dark_ground)
                            libtcod.console_put_char(con, x, y, '-', libtcod.BKGND_NONE)
                        else:
                            libtcod.console_set_char_background(con, x, y, color_dark_ground, libtcod.BKGND_SET)
            else:
                if wall:
                    if OLD_SCHOOL:
                        libtcod.console_set_default_foreground(con, color_light_wall)
                        libtcod.console_put_char(con, x, y, '#', libtcod.BKGND_NONE)
                    else:
                        libtcod.console_set_char_background(con, x, y, color_light_wall, libtcod.BKGND_SET)

                else:
                    if OLD_SCHOOL:
                        libtcod.console_set_default_foreground(con, color_light_ground)
                        libtcod.console_put_char(con, x, y, '.', libtcod.BKGND_NONE)
                    else:
                        libtcod.console_set_char_background(con, x, y, color_light_ground, libtcod.BKGND_SET)
                        
                map[x][y].explored = True

    for object_ in objects:
        object_.draw()

    libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)   # first visible change, writing the chars directly 
                                                                            # in this screen made the error that was present
                                                                            # before disappear, where the '@' would not show before
                                                                            # the first key stroke for movement


fighter_component = Fighter(hp = 30, defense=2, power=5)
player = Object(0, 0, '@', 'player', libtcod.white, blocks=True, fighter = fighter_component)

objects = [player]

game_state = "playing"

player_action = None

make_map()

fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
for y in range(MAP_HEIGHT):
    for x in range(MAP_WIDTH):
        libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)

# ========================

# Connect the game to a server
if SERVER_CONNECTION:
    message = {"player" : {"x":player.x, "y":player.y, "id":42}, "time": time.ctime()}

    try:
        host = config.get("SERVER","HOST")
        port = config.getint("SERVER", "PORT")

        s = socket.socket()
        s.connect((host,port))
        message = "handshake!"
        s.send(message.encode())
        data = s.recv(1024)
        print("Received from server:", str(data))
        comm1 = threading.Thread(target=comm, args=(message, 2))
        comm1.start()
    except Exception as e:
        SERVER_CONNECTION = False
        print("Server could not be reached")
        print(e)
# ========================

# main game loop
while not libtcod.console_is_window_closed():

    #libtcod.console_set_default_foreground(0, libtcod.white)
    #libtcod.console_put_char(con, playerx, playery, '@', libtcod.BKGND_NONE)

    if SERVER_CONNECTION: # update the player position and status to send to the server at FPS rate.
        message["player"]["x"] = player.x
        message["player"]["y"] = player.y
        message["time"] = time.ctime()

    render_all()

    libtcod.console_flush()

    for object_ in objects:
        object_.clear()


    player_action = handle_keys()
    if player_action == 'exit':
        break

    if game_state == 'playing' and player_action != 'didnt-take-turn':
        for object in objects:
            if object.ai:
                object.ai.take_turn()
