from enum import Enum


class EMessage(Enum):
    GAIN_XP = 1
    TAKE_DAMAGE = 2
    LEVEL_UP = 3
    MONSTERS_LEVEL_UP = 4


class NoValue(Enum):
    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)


class EEquipmentSlot(NoValue):
    ARMOR = "armor"
    HELMET = "helmet"
    LEFT_HAND = "left hand"
    RIGHT_HAND = "right hand"
    BOOTS = "boots"
    AMULET = "amulet"
    RING = "ring"


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