from enum import Enum


class EGameState(Enum):
    LOADING = 0
    PAUSED = 1
    MENU = 2
    PLAYING = 3


class EAction(Enum):
    EXIT = 0
    DIDNT_TAKE_TURN = 1
    MOVE_UP = 2
    MOVE_DOWN = 3
    MOVE_LEFT = 4
    MOVE_RIGHT = 5
    DEAD = 99


class MapTypes(Enum):
    RANDOM = 0
    CONSTRAINT = 1
    CONSTRUCTIVE1 = 2
    CONSTRUCTIVE2 = 3
    CONSTRUCTIVE3 = 4
