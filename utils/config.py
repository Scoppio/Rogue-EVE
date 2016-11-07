import tcod as libtcod
import configparser
import os

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
MAP_HEIGHT = SCREEN_HEIGHT-17 #43

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

# number of frames to wait after moving/attacking
PLAYER_SPEED = 2
DEFAULT_SPEED = 3
DEFAULT_ATTACK_SPEED = 20

# sizes and coordinates relevant for the GUI
BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
# message log
MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1

SERVER_CONNECTION = config.getboolean('SERVER', 'CONNECT')

# Game messages
game_msgs = []
