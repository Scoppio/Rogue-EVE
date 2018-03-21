import os
from yaml import load, YAMLError
import logging
import numbers
from models import GameObjects
from utils import Colors

logger = logging.getLogger('Rogue-EVE')

yaml_test = """
---
- type: Character
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
- type: Character
  args:
      char: T
      color: dark_blue
      name: Troll
      ai:
          BasicMonsterAI:
              interest_tag: player
      fighter:
          Fighter:
              hp: 20
              defense: 1
              power: 5
              death_function: monster_death
      tags:
          - monster
          - troll
          - big
  weight: 1.0
"""


def _le_obj(**value):
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


def _args_object(**kwargs):
    odict = dict()
    for key, value in kwargs.items():
        if key == "ai":
            odict[key] = _le_obj(**value)
        if key == "fighter":
            odict[key] = _le_obj(**value)
        if key == "color":
            if value in [a for a in dir(Colors) if "__" not in a]:
                odict[key] = eval("Colors." + value)
            else:
                logger.error("An error occurred, the color is not valid " + value)
        else:
            if key not in odict.keys():
                odict[key] = value
    return odict


def _deserialize_yaml(**kwargs):
    output_dict = dict()
    for key, value in kwargs.items():
        if key == "type":
            if value in dir(GameObjects) and "__" not in value:
                output_dict["obj_template"] = eval("GameObjects."+value)
            else:
                logger.error("An error occurred, the GameObject is not valid " + value)
        if key == "args":
            output_dict[key] = _args_object(**value)
        if key == "weight":
            if isinstance(value, numbers.Number) and value > 0:
                output_dict[key] = value
            else:
                logger.error("An error occurred, the weight is not valid " + value)
    return output_dict

def loadGameObjectFromFile(file: str):
    with open(file, 'r') as stream:
        try:
            le_test = load(stream)
        except YAMLError as exc:
            logger.error("Error while running yaml parser", exc)
            raise YAMLError("Error while running yaml parser", exc)

    output = list()
    for item in le_test:
        al = _deserialize_yaml(**item)
        output.append(al)
    return output


if __name__ == '__main__':
    le_test = load(filename)
    print(le_test)
    output = list()
    for item in le_test:
        al = _deserialize_yaml(**item)
        output.append(al)

    print(output)
