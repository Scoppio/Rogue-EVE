from yaml import load, dump
import logging
import numbers
from models import GameObjects
from utils import Colors

logger = logging.getLogger('Rogue-EVE')

yaml_test = """
type: Character
args:
    char: o
    color: dark_fuchsia
    name: orc
    ai: 
        BasicMonsterAI:
            interest_tag: player
    fighter: 
        Fighter:
            hp: 10
            defense: 0
            power: 3
            death_function: monster_death
    tags: 
        - monster
        - orc
        - small
weight: 3.0
"""
le_test = load(yaml_test)

def le_obj(**value):
    for key, value in value.items():
        obj = "GameObjects." + key + "("
        for key, value in value.items():
            if key == "death_function":
                if value in [a for a in dir(GameObjects.DeathMethods) if "__" not in a]:
                    obj = obj + key + "=GameObjects.DeathMethods." + value + ","
                else:
                    logger.error("An error occurred, the death method is not valid " + value)
            elif type(value) == str:
                obj = obj + key + "='" + value + "',"
            else:
                obj = obj + key + "=" + str(value) + ","
        obj = obj[:-1] + ")"
        a = eval(obj)
        return a

BB = None
CC = None

def args_object(**kwargs):
    odict = dict()
    for key, value in kwargs.items():
        if key == "ai":
            odict[key] = le_obj(**value)
        if key == "fighter":
            odict[key] = le_obj(**value)
        if key == "color":
            if value in [a for a in dir(Colors) if "__" not in a]:
                odict[key] = eval("Colors." + value)
            else:
                logger.error("An error occurred, the color is not valid " + value)
        else:
            if key not in odict.keys():
                odict[key] = value
    return odict

def create_object(**kwargs):
    output_dict = dict()
    for key, value in kwargs.items():
        if key == "type":
            if value in dir(GameObjects) and "__" not in value:
                output_dict["obj_template"] = eval("GameObjects."+value)
            else:
                logger.error("An error occurred, the GameObject is not valid " + value)
        if key == "args":
            output_dict[key] = args_object(**value)
        if key == "weight":
            if isinstance(value, numbers.Number) and value > 0:
                output_dict[key] = value
            else:
                logger.error("An error occurred, the weight is not valid " + value)
    return output_dict

al = create_object(**le_test)

print(al)