total = 0

TO_NEXT_LEVEL = 100;
 
factor = 0.95;
 
levels = 20;
 
for level in range(levels):
    print "Level %2d  |  %10d |  %10d |" % (level, total, TO_NEXT_LEVEL)
    total += TO_NEXT_LEVEL;
    TO_NEXT_LEVEL = TO_NEXT_LEVEL * (1 + (factor ** level))