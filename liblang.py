# Technicolour modem flash and unlock script by Mark Smith (Whirlpool)
# Distributed under GPLv3
# Multilanguage interface code based on adbtools2 program code
# adbtools home page: https://github.com/digiampietro/adbtools2

# This file is used to import the multilanguage code into all the scripts as required.

import os, locale
from pathlib import Path
import gettext

# ********************************** Define multi-langauge support
def language_set(lan):
    global _
    if os.path.isdir(os.path.join(mydir, 'locale', lan)):
        slan = gettext.translation('autoflashgui', localedir=os.path.join(os.getcwd(), 'locale'), languages=[lan])
        slan.install()
        # Convert local to global
        _loc = _
        _ = _loc
    else:
        _ = lambda s: s

def language_default(argv):
    lan = 'en'
    try:
        if argv[1] == '-l':
            lan = argv[2]
    except:
        (lancode, lanenc) = locale.getdefaultlocale()
        lancode2=lancode[0:2]
        if os.path.isdir(os.path.join(mydir, 'locale', lancode)):
            lan = lancode
        if os.path.isdir(os.path.join(mydir, 'locale', lancode2)):
            lan = lancode2
        else:
            lan = 'en'
    return lan

def init_language(argv, path, language):
    global mydir
    mydir = path[0] # os.path.dirname(path[0])
    global lan
    if language is not None:
        lan = language
    else:
        lan = language_default(argv)
    language_set(lan) 
    print (_('UI language = ') + lan)
