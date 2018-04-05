import os
from models.EnumStatus import EMessage

a = {}
a[EMessage.GAIN_XP] = 100

if EMessage.GAIN_XP in a.keys():
    print("gain xp", a[EMessage.GAIN_XP])