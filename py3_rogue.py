# http://www.roguebasin.com/index.php?title=Complete_Roguelike_Tutorial,_using_python%2Blibtcod,_part_4

from utils.utils import message
from utils.config import *
import tcod as libtcod
import threading
import random
import socket
import time
import json
import math
import os

tLock = threading.Lock()

# all configs were transfered to config.py file

color_dark_wall = libtcod.Color(0,0,100)
color_dark_ground = libtcod.Color(50,50,150)
color_light_wall = libtcod.Color(130, 110, 50)
color_light_ground = libtcod.Color(200,180,50)

libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)

libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'Roguelike libtcod - tutorial', False)

# for RT-ONLY
libtcod.sys_set_fps(LIMIT_FPS)

#create the list of game messages and their colors, starts empty

fov_recompute = True

class Object:
    # generic class object: player, monster, item, stairs
    # it is always represented by a character on screen.
    def __init__(self, x, y, char, name, color, blocks = False, fighter=None, ai=None, speed = DEFAULT_SPEED):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks

        self.speed = speed
        self.wait = 0

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
                self.wait = self.speed

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

    def send_to_back(self):
        # make this object be drawn first, so all others appear above it if
        # they're in the same tile.
        global objects
        objects.remove(self)
        objects.insert(0, self)

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
    def __init__(self, hp=1, defense=0, power=0, dodge=0, luck=0, attack_speed=DEFAULT_ATTACK_SPEED, death_function=None):
        self.death_function = death_function
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        self.dodge = dodge
        self.luck = luck
        self.attack_speed = attack_speed

    def take_damage(self, damage):
        # apply damage if possible
        if damage > 0:
            self.hp -= damage

        if self.hp <= 0:
            function = self.death_function
            if function is not None:
                function(self.owner)

    def attack(self, target):
        # Luck mechanic - if you are lucy, maybe you can land that hit ;)
        multiplier = 2 if sum([1 if random.randint(0,10) == 10 else 0 for _ in range(self.luck)]) else 1
        # a simple formula for attack damage
        damage = self.power * multiplier - target.fighter.defense

        # simple formula for dodge
        damage = damage if not sum([1 if random.randint(0,10) == 10 else 0 for _ in range(target.fighter.dodge)]) else 0

        if damage > 0:
            if multiplier == 2:
                print( self.owner.name.capitalize() + ' lands a critical hit at ' + target.name + ' for ' + str(damage) + ' hit points.')
            else:
                print( self.owner.name.capitalize() + ' attacks ' + target.name + ' for ' + str(damage) + ' hit points.')
            target.fighter.take_damage(damage)
        else:
            print( self.owner.name.capitalize() + ' attacks ' + target.name + ' but it has no effect!')

        self.owner.wait = self.attack_speed

# IA classes
class BasicMonster(object):
    """docstring for BasicMonster"""

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
                monster.fighter.attack(player)
                #print ( "the attack of the {} bounces of your shiny metal armor".format(monster.name))

class AdvancedMonster(object):
    """docstring for BlindMonster"""
    def __init__(self, sense = 0, reach = 2):
        super(BlindMonster, self).__init__()
        self.sense = sense
        self.reach = reach if reach < 2 else 2

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
                monster.fighter.attack(player)
                #print ( "the attack of the {} bounces of your shiny metal armor".format(monster.name))


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
                fighter_component = Fighter(hp=2, defense=0, power=1, death_function=monster_death)
                ai_component = BasicMonster()
                monster = Object(x, y, 'm', 'imp', libtcod.desaturated_red, blocks=True,
                    fighter = fighter_component, ai = ai_component)

            elif choice < 20+40:
                # create an orc
                fighter_component = Fighter(hp=10, defense=0, power=3, death_function=monster_death)
                ai_component = BasicMonster()
                monster = Object(x, y, 'o', 'orc', libtcod.desaturated_green, blocks=True,
                    fighter = fighter_component, ai = ai_component)

            elif choice < 20+40+20:
                # create troll
                fighter_component = Fighter(hp=16, defense=1, power=4, death_function=monster_death)
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
    global key
    #key = libtcod.console_check_for_keypress()

    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # ALT+Enter: toggle Fullscreen
        # libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen()) # sugest not using it
        print("Fullscreen offline")

    elif key.vk == libtcod.KEY_ESCAPE:
        return 'exit'

    if game_state == "playing":
        if player.wait > 0:
            player.wait -= 1
            return
        #movement keys
        if key.vk == libtcod.KEY_UP:
            player_move_or_attack(0,-1)

        elif key.vk == libtcod.KEY_DOWN:
            player_move_or_attack(0,1)

        elif key.vk == libtcod.KEY_LEFT:
            player_move_or_attack(-1,0)

        elif key.vk == libtcod.KEY_RIGHT:
            player_move_or_attack(1,0)

    else:
        return "didnt-take-turn"


def get_names_under_mouse():
    global mouse

    (x, y) = (mouse.cx, mouse.cy)
    names = [obj.name for obj in objects if obj.x == x and obj.y == y and
                                libtcod.map_is_in_fov(fov_map, obj.x, obj.y)]
    names = ', '.join(names)  #join the names, separated by commas
    return names.capitalize()

def player_move_or_attack(dx, dy):
    global fov_recompute

    x = player.x + dx
    y = player.y + dy

    # try to find a valid target for attacks
    target = None
    for object in objects:
        if object.fighter and object.x == x and object.y == y:
            target = object
            break

    # attack if target found, move if otherwise
    if target is not None:
        player.fighter.attack(target)
        #print("The", target.name, "laughs at your puny efforts to attack him!")

    else:
        player.move(dx, dy)
        fov_recompute = True

def player_death(player):
    # You are dead
    global game_state
    print("You died")

    game_state = "dead"

    #for added effect, transform the player into a corpse!
    player.char = '%'
    player.color = libtcod.dark_red

def monster_death(monster):
    #transform it into a nasty corpse! it doesn't block, can't be
    #attacked and doesn't move
    print (monster.name.capitalize(),'is dead!')
    monster.char = '%'
    monster.color = libtcod.dark_red
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of ' + monster.name
    monster.send_to_back()


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

def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
    #render a bar (HP, experience, etc). first calculate the width of the bar
    bar_width = int(float(value) / maximum * total_width)

    #render the background first
    libtcod.console_set_default_background(panel, back_color)
    libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)

    #now render the bar on top
    libtcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)

    #finally, some centered text with the values
    libtcod.console_set_default_foreground(panel, libtcod.white)
    text = name + ': ' + str(value) + '/' + str(maximum)
    libtcod.console_print_ex(panel, x + total_width // 2, y, libtcod.BKGND_NONE, libtcod.CENTER, text)

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

    # Draw everything before the player
    for object_ in objects:
        if object_ != player:
            object_.draw()

    # Player is drawn last, always
    player.draw()

    libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)   # first visible change, writing the chars directly
                                                                            # in this screen made the error that was present
                                                                            # before disappear, where the '@' would not show before
                                                                            # the first key stroke for movement
    # deprecated
    # show the player's stats
    # libtcod.console_set_default_foreground(con, libtcod.white)
    # libtcod.console_print_ex(con, 1, SCREEN_HEIGHT - 2, libtcod.BKGND_NONE, libtcod.LEFT,
    #     'HP: ' + str(player.fighter.hp) + '/' + str(player.fighter.max_hp))
    #print the game messages, one line at a time

    # prepare to render the GUI panel
    libtcod.console_set_default_background(panel, libtcod.black)
    libtcod.console_clear(panel)

    y = 1
    for (line, color) in game_msgs:
        libtcod.console_set_default_foreground(panel, color)
        libtcod.console_print_ex(panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
        y += 1

    # show the player's health bar
    render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp,
        libtcod.light_red, libtcod.darker_red)

    # display names of objects under the mouse
    libtcod.console_set_default_foreground(panel, libtcod.light_gray)
    libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse())

    # blit the contents of "panel" to the root console
    libtcod.console_blit(panel, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, PANEL_Y)


# communication with the server
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


# =======================
# Setup
mouse = libtcod.Mouse()
key = libtcod.Key()

# Panels
con = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)
panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)

# game world
fighter_component = Fighter(hp = 30, defense=2, power=5, dodge=1, luck=1, death_function=player_death)
player = Object(0, 0, '@', 'player', libtcod.white, blocks=True, fighter = fighter_component, speed=PLAYER_SPEED)

objects = [player]

game_state = "playing"

player_action = None

make_map()

fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
[libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight,
    not map[x][y].blocked) for y in range(MAP_HEIGHT) for x in range(MAP_WIDTH)]
#for y in range(MAP_HEIGHT):
#    for x in range(MAP_WIDTH):
#        libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)

# ========================

# Connect the game to the server
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
message('Welcome stranger! Prepare to perish in the Tombs of the Ancient Kings.', libtcod.red)
# main game loop
while not libtcod.console_is_window_closed():

    if SERVER_CONNECTION: # update the player position and status to send to the server at FPS rate.
        message["player"]["x"] = player.x
        message["player"]["y"] = player.y
        message["time"] = time.ctime()

    # Before rendering screen, verify mouse or keyboard event
    libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,key,mouse)

    render_all()

    libtcod.console_flush()

    for object_ in objects:
        object_.clear()


    player_action = handle_keys()
    if player_action == 'exit':
        break

    if game_state == 'playing': # and player_action != 'didnt-take-turn':
        for object in objects:
            if object.ai:
                if object.wait > 0:
                    object.wait -= 1
                else:
                    object.ai.take_turn()
