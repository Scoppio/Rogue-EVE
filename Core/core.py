import tdl
import os


class IdGenerator:
    class __IdGenerator:
        def __init__(self, arg):
            self.val = arg
            self._id_counter = 0

        def __str__(self):
            return repr(self) + self.val

        def request_id(self):
            self._id_counter += 1
            return self._id_counter
    instance = None

    def __init__(self, arg):
        if not IdGenerator.instance:
            IdGenerator.instance = IdGenerator.__IdGenerator(arg)
        else:
            IdGenerator.instance.val = arg

    def __getattr__(self, name):
        return getattr(self.instance, name)


igGen = IdGenerator(None)

class ColliderObj(object):
    def __init__(self):
        pass


class Character(ColliderObj):
    def __init__(self):
        super(Character, self).__init__()
        self.tag = "Character"
        self.id = igGen.request_id()
        self.life = 0
        self.mana = 0
        self.X = 10
        self.Y = 10
        self.sign = "@"
        self.color = (255, 255, 255)


def draw_char(character: Character, console):
    console.draw_char(character.X, character.Y, character.sign, bg=None, fg=character.color)

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20

font = os.path.join("assets", "arial10x10.png")

tdl.set_font(font, greyscale=True, altLayout=True)

console = tdl.init(width=SCREEN_WIDTH, height=SCREEN_HEIGHT, title="Roguelike", fullscreen=False)

player = Character()

while not tdl.event.is_window_closed():
    draw_char(player, console)

    tdl.flush()



