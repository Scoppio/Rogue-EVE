# from utils.config import *
# import tcod as libtcod
# import random
# import math

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
