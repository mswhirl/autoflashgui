# Technicolour modem flash and unlock script by Mark Smith (Whirlpool)
# Distributed under GPLv3
# Multilanguage interface code based on adbtools2 program code
# adbtools home page: https://github.com/digiampietro/adbtools2

# This file is used to import the multilanguage code into all the scripts as required.

import sys, os, locale
from pathlib import Path
import gettext

# ********************************** Define multi-langauge support
def language_set(lan):
    global _
    if (os.path.isdir(mydir + '/locale/' + lan)):
        slan = gettext.translation('autoflashgui', localedir='locale', languages=[lan])
        slan.install()
    else:
        _ = lambda s: s

def language_default():
    lan = 'EN'
    try:
        if sys.argv[1] == '-l':
            lan = sys.argv[2]
            del sys.argv[1:3]
    except:
        (lancode, lanenc) = locale.getdefaultlocale()
        lancode2=lancode[0:2]
        if (os.path.isdir(mydir + '/locale/' + lancode)):
            lan = lancode
        if (os.path.isdir(mydir + '/locale/' + lancode2)):
            lan = lancode2
        else:
            lan = 'en'
    return lan

def init_language():
    global mydir
    # ********************************** Define startup folder
    mydir    = sys.path[0]              # not correct on exe file from pyinstaller
    mydir    = os.path.dirname(os.path.realpath(__file__))
    global lan
    if not 'lan' in dir():
        lan = language_default()
        language_set(lan) 
        print (_('UI language = ') + lan)
