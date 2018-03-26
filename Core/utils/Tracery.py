import tracery
from tracery.modifiers import base_english

"""Pitch, use Tracery to randomly create monsters, items, magic spells and levels"""

rules = {
    'origin': '#hello.capitalize#, #location#!',
    'hello': ['hello', 'greetings', 'howdy', 'hey'],
    'location': ['world', 'solar system', 'galaxy', 'universe']
}

grammar = tracery.Grammar(rules)
grammar.add_modifiers(base_english)
print(grammar.flatten("#origin#")) # prints, e.g., "Hello, world!"