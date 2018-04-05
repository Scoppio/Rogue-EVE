from enum import Enum


class EMessage(Enum):
    GAIN_XP = 1
    TAKE_DAMAGE = 2
    LEVEL_UP = 3
    MONSTERS_LEVEL_UP = 4


class EEquipmentSlot(Enum):
    ARMOR = 0
    HELMET = 1
    LEFT_HAND = 2
    RIGHT_HAND = 3
    LEGS = 4
    BOOTS = 5
    AMULET = 6
    RING = 7

class EGameState(Enum):
    LOADING = 0
    PAUSED = 1
    MENU = 2
    PLAYING = 3
    DEAD = 99


class EAction(Enum):
    EXIT = 0
    DIDNT_TAKE_TURN = 1
    MOVE_UP = 2
    MOVE_DOWN = 3
    MOVE_LEFT = 4
    MOVE_RIGHT = 5
    MOVE_DIAGONAL_UR = 6
    MOVE_DIAGONAL_DR = 7
    MOVE_DIAGONAL_DL = 8
    MOVE_DIAGONAL_UL = 9
    WAITING = 10
    DEAD = 99


class MapTypes(Enum):
    RANDOM = 0
    CONSTRAINT = 1
    CONSTRUCTIVE1 = 2
    CONSTRUCTIVE2 = 3
    CONSTRUCTIVE3 = 4


class Cardinals(Enum):
    NORTH = 0
    SOUTH = 1
    EAST = 2
    WEST = 3