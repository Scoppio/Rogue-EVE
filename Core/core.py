import tdl
import os
import uuid


#########################################
# Constants
#########################################

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20


class ColliderObj(object):
    def __init__(self, id, X=0, Y=0, sign='@', color=(255, 255, 255)):
        if id is None:
            self.id = uuid.uuid4()
        else:
            self.id = id
        self.tag = "Collider"
        self.X = X
        self.Y = Y
        self.sign = sign
        self.color = color


class Character(ColliderObj):
    def __init__(self, id=None, X=0, Y=0, life=0, mana=0, sign="@", color=(255, 255, 255)):
        super(Character, self).__init__(id, X, Y, sign, color)
        self.tag = "Character"
        self.life = life
        self.mana = mana


def draw_char(character: Character, console):
    console.draw_char(character.X, character.Y, character.sign, bg=None, fg=character.color)


def clear_char(character: Character, console):
    console.draw_char(character.X, character.Y, ' ', bg=None, fg=character.color)


def handle_keys(movable_object):
    """
    #realtime

    keypress = False
    for event in tdl.event.get():
        if event.type == 'KEYDOWN':
           user_input = event
           keypress = True
    if not keypress:
        return
    """
    # turn-based
    user_input = tdl.event.key_wait()

    if user_input.key == 'ENTER' and user_input.alt:
        # Alt+Enter: toggle fullscreen
        tdl.set_fullscreen(not tdl.get_fullscreen())

    elif user_input.key == 'ESCAPE':
        return True  # exit game
    # movement keys
    if user_input.key == 'UP':
        movable_object.Y -= 1

    elif user_input.key == 'DOWN':
        movable_object.Y += 1

    elif user_input.key == 'LEFT':
        movable_object.X -= 1

    elif user_input.key == 'RIGHT':
        movable_object.X += 1

    return False


def main():
    font = os.path.join("assets", "arial10x10.png")

    tdl.set_font(font, greyscale=True, altLayout=True)

    console = tdl.init(width=SCREEN_WIDTH, height=SCREEN_HEIGHT, title="Roguelike", fullscreen=False)

    player = Character(None, SCREEN_WIDTH//2 , SCREEN_HEIGHT//2)

    while not tdl.event.is_window_closed():

        draw_char(player, console)
        tdl.flush()
        clear_char(player, console)

        exit_game = handle_keys(player)
        if exit_game:
            break

if __name__ == '__main__':
    main()

