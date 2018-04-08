import tracery
import random
from utils import Colors
from tracery.modifiers import base_english

"""Pitch, use Tracery to randomly create monsters, items, magic spells and levels"""

base_character_yaml = """  - type: Character
    weight: 1.0
    params:
        char: #char#
        color: #color#
        name: #name.capitalize#
        ai:
            interest_tag: player
        fighter:
            hp: {fighter_hp}
            defense: {fighter_defense}
            power: {fighter_power}
            xp: {fighter_xp}
            death_function: monster_death
        tags:
            - monster
            - #monster_type#
            - #size#
            - #life_state#"""

alphabet = "a b c d e f g h i j k l m n o p q r s t u v w x y z"
alpha = alphabet.upper().split() + alphabet.split()

colors = [color for color in dir(Colors) if "__" not in color]


def generate_monster():
    fighter_hp = random.randint(10, 45)
    fighter_power = random.randint(3,5)
    fighter_defense = random.randint(0,3)
    fighter_xp = fighter_hp + fighter_power*fighter_defense

    yaml_string = base_character_yaml.format(fighter_hp=fighter_hp, fighter_power=fighter_power,
                                             fighter_defense=fighter_defense, fighter_xp=fighter_xp)

    rules = {
        'origin': yaml_string,
        'monster_type': ['brute', 'bloat', 'ghostly', 'undead', 'constructo', 'alien', 'fantastical', 'robot', 'weird'],
        'name': ['#pre.capitalize# zombie', 'kobold #post#', 'orc #post#', '#pre.capitalize# gnome', 'skeleton #post#',
                 '#pre.capitalize# slime', '#pre.capitalize# lich #post#'],
        'pre': ['great', 'sage', 'angry', 'mad', 'ravaging', 'savage', 'glutonous', 'red', 'blue', 'purple', 'smart',
                'ravenous', 'evil'],
        'post' : ['berserker', 'from hell', 'archer', 'mage', 'wizard', 'ranger', 'assassin', 'cook', 'soldier',
                  'warrior', 'janitor'],
        'color': colors,
        'char': alpha,
        'size': ['small', 'large', 'medium'],
        'life_state': ['mortal']
    }

    grammar = tracery.Grammar(rules)
    grammar.add_modifiers(base_english)
    print(grammar.flatten("#origin#"))


def generate_consumable_item():
    pass


def generate_attack_item():
    pass


def generate_defense_item():
    pass


def generate_magic_attack_item():
    pass


def generate_magic_defense_item():
    pass


def generate_ring_or_amulet():
    pass

if __name__ == '__main__':
    print("---")
    print("monsters:")
    for _ in range(25):
        generate_monster()