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
