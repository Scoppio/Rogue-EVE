from random import randint
 
class Character:
  def __init__(self):
    self.name = ""
    self.health = 1
    self.health_max = 1

  def do_damage(self, enemy):
    damage = min(max(randint(0, self.health) - randint(0, enemy.health), 0), enemy.health)
    enemy.health = enemy.health - damage

    if damage == 0:
      print ("{} evades {}'s attack.".format(enemy.name, self.name))

    else:
      print ("{} hurts {}!".format(self.name, enemy.name))

    return enemy.health <= 0
 

class Enemy(Character):
  def __init__(self, player):
    Character.__init__(self)
    self.name = 'a goblin'
    self.health = randint(1, player.health)
 

class Player(Character):
  def __init__(self):
    Character.__init__(self)
    self.state = 'normal'
    self.health = 10
    self.health_max = 10

  def quit(self):
    print ("{} can't find the way back home, and dies of starvation.\nR.I.P.".format(self.name))
    self.health = 0
  
  def help(self):
    for keys in Commands.keys():
      print (keys)
  
  def status(self): 
    print ("{}'s health: {}/{}".format(self.name, self.health, self.health_max))
  
  def tired(self):
    print ("{} feels tired.".format(self.name))
    self.health = max(1, self.health - 1)
  
  def rest(self):
    if self.state != 'normal':
      print ("{} can't rest now!".format(self.name))
      self.enemy_attacks()

    else:
      print ("{} rests.".format(self.name))
      if randint(0, 1):
        self.enemy = Enemy(self)
        print ("{} is rudely awakened by {}!".format(self.name, self.enemy.name))
        self.state = 'fight'
        self.enemy_attacks()

      else:
        if self.health < self.health_max:
          self.health = self.health + 1

        else:
          print ("{} slept too much.".format(self.name))
          self.health = self.health - 1

  def explore(self):
    if self.state != 'normal':
      print ("{} is too busy right now!".format(self.name))
      self.enemy_attacks()

    else:
      print ("{} explores a twisty passage.".format(self.name))
      if randint(0, 1):
        self.enemy = Enemy(self)
        print ("{} encounters {}!".format(self.name, self.enemy.name))
        self.state = 'fight'

      else:
        if randint(0, 1):
          self.tired()

  def flee(self):
    if self.state != 'fight':
      print ("{} runs in circles for a while.".format(self.name))
      self.tired()

    else:
      if randint(1, self.health + 5) > randint(1, self.enemy.health):
        print ("{} flees from {}.".format(self.name, self.enemy.name))
        self.enemy = None
        self.state = 'normal'

      else:
        print ("{} couldn't escape from {}!".format(self.name, self.enemy.name))
        self.enemy_attacks()


  def attack(self):
    if self.state != 'fight': 
      print ("{} swats the air, without notable results.".format(self.name))
      self.tired()

    else:
      if self.do_damage(self.enemy):
        print ("{} executes {}!".format(self.name, self.enemy.name))
        self.enemy = None
        self.state = 'normal'
        if randint(0, self.health) < 10:
          self.health = self.health + 1
          self.health_max = self.health_max + 1
          print ("{} feels stronger!".format(self.name))

      else: 
        self.enemy_attacks()


  def enemy_attacks(self):
    if self.enemy.do_damage(self): print ("{} was slaughtered by {}!!!\nR.I.P.".format(self.name, self.enemy.name))
 
Commands = {
  'quit': Player.quit,
  'help': Player.help,
  'status': Player.status,
  'rest': Player.rest,
  'explore': Player.explore,
  'flee': Player.flee,
  'attack': Player.attack,
  }
 
p = Player()
p.name = input("What is your character's name? ")
print ("(type help to get a list of actions)\n")
print (" {} enters a dark cave, searching for adventure.".format(p.name))
 
while(p.health > 0):
  line = input("> ")
  args = line.split()
  if len(args) > 0:
    commandFound = False
    for c in Commands.keys():
      if args[0] == c[:len(args[0])]:
        Commands[c](p)
        commandFound = True
        break
    if not commandFound:
      print ("{} doesn't understand the suggestion.".format(p.name))