import tcod as libtcod
#actual size of the window
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 60

MAP_HEIGHT = 55
MAP_WIDTH = 80

LIMIT_FPS = 20  #20 frames-per-second maximum

color_dark_wall = libtcod.Color(0,0,100)
color_dark_ground = libtcod.Color(50,50,150)


libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)

con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'python/libtcod tutorial', False)

libtcod.sys_set_fps(LIMIT_FPS) #for RT-ONLY

class Object:
    # generic class object: player, monster, item, stairs
    # it is always represented by a character on screen.
    def __init__(self, x, y, char, color):
        self.x = x
        self.y = y
        self.char = char
        self.color = color

    def move(self, dx, dy):
        #move by a given amount

        if not map[self.x + dx][self.y + dy].blocked: # collision detection
            self.x += dx
            self.y += dy

    def draw(self):
        # set the color and then draw the character that represents this object at its position
        libtcod.console_set_default_foreground(con, self.color)
        libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)

    def clear(self):
        # erase the character that represents this object
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

class Tile:
    # a tile of the map and its properties
    def __init__(self, blocked, block_sight = None):
        self.border = None

class Rect:
    # a rectangle - origin is at top-left
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
        self.w = w
        self.h = h

class Line:
    # a line
    def __init__(self, x,y,l,a='h',start_end_char='+'):
        self.x1 = x
        self.y1 = y
        self.a = a
        if a == 'h':
            self.x2 = x + l
            self.y2 = y
        else: # a == 'v':
            self.x2 = x
            self.y2 = y + l

        self.start_end_char = start_end_char

def create_ocon_list(window, line_separator=True, list_=list()):
    global ocon
    # create the rectangle
    
    create_window(window)

    #count the number of rows
    if line_separator:
        number_of_lines = (len(list_)*2+1)
        every_n_lines = 2
    else:
        number_of_lines = (len(list_)+2)
        every_n_lines = 1
    
    if number_of_lines > window.h:
        print ('failure, list too long to be created')
        return

    max_width = window.w-2

    for y, text in zip(range(window.y1+1, window.y1+number_of_lines, every_n_lines),  list_):
        #print the header, with auto-wrap
        libtcod.console_set_default_foreground(ocon, libtcod.white)
        #libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
        libtcod.console_print_ex(ocon, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
        print(y, text)
        if line_separator:
            line = Line(x=window.x1, y=y+1, l=window.w, a='h')
            create_line(line)

        # add text line with character width limitation


def create_ocon_dataframe(window, *args):
    pass

def create_line(line):
    global ocon
    if line.a=='h':
        for x in range(line.x1, line.x2):
                ocon[x][line.y1].border = "-"
    else:
        for y in range(line.y1, line.y2):
            ocon[line.x1][y].border = "|"

    ocon[line.x1][line.y1].border = line.start_end_char
    ocon[line.x2][line.y2].border = line.start_end_char

def create_window(window):
    global ocon
    # go through the tiles in the rectangle and make them passable

    for x in range(window.x1, window.x2):
        for y in [window.y1, window.y2]:
            ocon[x][y].border = "-"
    for y in range(window.y1, window.y2):
        for x in [window.x1, window.x2]:
            ocon[x][y].border = "|"

    ocon[window.x1][window.y1].border = "+"
    ocon[window.x1][window.y2].border = "+"
    ocon[window.x2][window.y1].border = "+"
    ocon[window.x2][window.y2].border = "+"


def handle_keys():

    key = libtcod.console_check_for_keypress()

    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # ALT+Enter: toggle Fullscreen
        # libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen()) # sugest not using it
        print("Fullscreen offline")

    elif key.vk == libtcod.KEY_ESCAPE:
        return True

    #movement keys
    if libtcod.console_is_key_pressed(libtcod.KEY_UP):
        player.move(0,-1)

    elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
        player.move(0,1)

    elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
        player.move(-1,0)

    elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
        player.move(1,0)

def make_ocon():
    global ocon

    # fill map with "unblocked" tiles
    ocon = [[ Tile(False)
        for y in range(MAP_HEIGHT)]
            for x in range(MAP_WIDTH)]

    window1 = Rect(0,0,MAP_WIDTH-1,MAP_HEIGHT-1)
    window2 = Rect(0,0,25,MAP_HEIGHT-1)
    create_window(window1)
    create_ocon_list(window2, list_=['Name', 'Charsheet', 'People and Places', 'Mailbox', 'Journal',
                                    'Contracts', 'Map', 'Assets', 'Wallet', 'Help'])
    #window3 = Rect(0,0,25,2)
    #window4 = Rect(0,2,25,2)
    #window5 = Rect(0,4,25,2)
    #create_window(window2)
    #create_window(window3)
    #create_window(window4)
    #create_window(window5)


def render_all():
    # draw all objects in the list

    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            border = ocon[x][y].border
            if border:
                libtcod.console_put_char(con, x, y, border, libtcod.BKGND_NONE)
            else:
                libtcod.console_put_char(con, x, y, ' ', libtcod.BKGND_NONE)

    for object_ in objects:
        object_.draw()

    libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)   # first visible change, writing the chars directly 
                                                                            # in this screen made the error that was present
                                                                            # before disappear, where the '@' would not show before
                                                                            # the first key stroke for movement

player = Object(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, '@', libtcod.white)
npc = Object(SCREEN_WIDTH//2 - 5, SCREEN_HEIGHT//2 - 5, '@', libtcod.yellow)

objects = [npc, player]

make_ocon()

while not libtcod.console_is_window_closed():

    #libtcod.console_set_default_foreground(0, libtcod.white)
    #libtcod.console_put_char(con, playerx, playery, '@', libtcod.BKGND_NONE)

    render_all()
    libtcod.console_flush()
    # libtcod.console_put_char(con, playerx, playery, ' ', libtcod.BKGND_NONE)

    for object_ in objects:
        object_.clear()

    exit = handle_keys()
    if exit:
        break