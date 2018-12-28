# Technicolour modem flash and unlock script by Mark Smith (Whirlpool)
# Distributed under GPLv3
# Credits to DanielO for the initial work on using SRPv6 to log into these modems (see links below)
# Requirements:
# python 3 (developed on 3.6.4 x64)
# pip install robobrowser
# mysrp as from https://forums.whirlpool.net.au/user/20499  https://forums.whirlpool.net.au/forum-replies.cfm?t=2596180 https://gist.github.com/DanielO/76c6c337ff09f6011f408427df376e68 
# a copy of the firmware file in the current directory

#NOTE: the default ssh password will be 'root'.  It's not a parameter as it would be hard to encode all special characters people might use, so just log in and change it!
# the following is an example of defaults.ini.  If you don't include all the mandatory defaultXXXXXX keys as shown the program will fail!
##defaultHost=10.0.0.138
##defaultUsername=admin
##defaultPassword=
##defaultUpgradeFilename=vant-f_CRF687-16.3.7567-660-RG.rbi
##defaultStartupVariant=TG799/TG797 Telstra
##defaultFlashFirmware=0
##defaultFlashSleepDelay=120
##defaultConnectRetryDelay=5
##defaultInterCommandDelay=5
##variant=TG799/TG797 Telstra,Ping,dyndns.com,echo "root:root"|chpasswd;sed -i -e "s/'0'/'1'/" -e "s/'off'/'on'/" /etc/config/dropbear;/etc/init.d/cwmpd disable;/etc/init.d/cwmpdboot disable;/etc/init.d/wifi-doctor-agent disable;/etc/init.d/hotspotd disable;killall -9 hotspotd cwmpd cwmpdboot watchdog-tch wifi-doctor-agent dropbear;/etc/init.d/dropbear start
##variant=iiNet,Ping,dyndns.com,uci set dropbear.@dropbear[0].PasswordAuth='on';uci set dropbear.@dropbear[0].RootPasswordAuth='on';uci set dropbear.@dropbear[0].enable='1';uci commit;echo -e "root\nroot"|passwd;/etc/init.d/dropbear restart
##variant=MyRepublic,Ping,dyndns.com,echo "root:root"|chpasswd;sed -i -e "s/'0'/'1'/" -e "s/'off'/'on'/" /etc/config/dropbear;/etc/init.d/cwmpd stop;/etc/init.d/cwmpd disable;/etc/init.d/cwmpdboot disable;killall dropbear;dropbear
##variant=Tiscali,Ping,dyndns.com,sed -i 's#root:/bin/false#root:/bin/ash#' /etc/passwd;uci set dropbear.@dropbear[0].PasswordAuth='on';uci set dropbear.@dropbear[0].Interface='lan';uci set dropbear.@dropbear[0].RootPasswordAuth='on';uci set dropbear.@dropbear[0].enable='1';uci commit;echo -e "root\nroot"|passwd;/etc/init.d/dropbear restart
##variant=DGA4130 AGTEF 1.0.3,Ping,dyndns.com,sed -i '1croot:x:0:0:root:/root:/bin/ash' /etc/passwd;uci set dropbear.@dropbear[0].RootPasswordAuth='on';uci set dropbear.@dropbear[0].enable='1';uci commit;echo -e "root\nroot"|passwd;/etc/init.d/dropbear restart
##variant=DGA4132 AGTHP 1.0.3,DDNS,dyndns.it,sed -i 's#root:/bin/false#root:/bin/ash#' /etc/passwd;uci set dropbear.lan.enable=1;uci set dropbear.lan.RootPasswordAuth=on;uci commit;echo -e "root\nroot"|passwd;/etc/init.d/dropbear restart

import tkinter as tk
import libautoflashgui, socket

# Multilanguage interface code based on adbtools2 program code
# adbtools home page: https://github.com/digiampietro/adbtools2


import os
import sys
import time
import ctypes
import os.path
import locale
import ctypes
import uuid

from pathlib import Path

import gettext

os.system("cls") # clear screen

# ********************************** Define startup folder

mydir    = sys.path[0]              # not correct on exe file from pyinstaller
mydir    = os.path.dirname(os.path.realpath(__file__))

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

lan = language_default()
language_set(lan) 

print (_('UI language = ') + lan)


def getDefaults():
    config = {}
    global defaultMethods
    defaultMethods = {}
    print("Reading config...")
    with open('defaults.ini', "r", 1048576, encoding='utf8') as f:
        for line in f:
            print("Line:" + line.strip())
            type,record = line.strip().split('=',maxsplit=1)
            if type.startswith('default'):
                configKey = type.replace("default","")
                configKey = configKey[0:1].lower() + configKey[1:]
                config[configKey] = record
            elif type == 'variant':
                vName, vMethod, vDDNS, vCommand = record.split(',',maxsplit=3)
                defaultMethods[vName] = [vMethod, vDDNS, vCommand]
    return config

class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.grid()
        self.defaults = getDefaults()
        self.flashFirmwre = self.defaults['flashFirmware']
        self.flashSleepDelay = self.defaults['flashSleepDelay']
        self.interCommandDelay = self.defaults['interCommandDelay']
        self.connectRetryDelay = self.defaults['connectRetryDelay']
        self.expertMode = False
        self.createWidgets()

    def createWidgets(self):
        tk.Label(self, text=_('Target IP:')).grid(row=0, column=1)
        self.host = tk.Entry(self, width=64)
        self.host.grid(row=0, column=2)

        tk.Label(self, text=_('Username:')).grid(row=10, column=1)
        self.username = tk.Entry(self, width=64)
        self.username.grid(row=10, column=2)

        tk.Label(self, text=_('Password:')).grid(row=20, column=1)
        self.password = tk.Entry(self, width=64)
        self.password.grid(row=20, column=2)

        tk.Label(self, text=_('Firmware File Name:')).grid(row=30, column=1)
        self.firmwarefile = tk.Entry(self, width=64)
        self.firmwarefile.grid(row=30, column=2)

        self.flashfirmware = tk.IntVar()
        tk.Checkbutton(self, text=_("Flash firmware?"), variable=self.flashfirmware, width=64).grid(row=40, column=2)

        self.expertmode = tk.IntVar()
        tk.Checkbutton(self, text=_("I really truly know what I'm doing and I want to mess with the commands to tweak the firmware and I promise not to ask for help. :)  I understand that if the unsplit (if selected) or split command is too long (suspected limit of about 245 on TG799) or if I use special characters it may fail.  Avoid using & or ; (except splitting commands, unless escaped as a character code?)."), variable=self.expertmode, command=self.expertmodeswitch, width=64, height=5, anchor=tk.W, justify=tk.LEFT, wraplength=400).grid(row=50, column=2)
        self.commandEval = tk.StringVar()
        tk.Label(self, text=_('Command:')).grid(row=60, column=1)
        self.command = tk.Entry(self, width=64, textvariable=self.commandEval)
        self.command.bind('<Key>', (lambda _: self.commandChange()))
        self.command.grid(row=60, column=2)

        self.lengthSummary = tk.Label(self, text='length goes here')
        self.lengthSummary.grid(row=70, column=2)

        tk.Label(self, text=_('Ping, AdvancedDDNS, BasicDDNS:')).grid(row=80, column=1)
        self.methodAction = tk.Entry(self, width=16)
        self.methodAction.grid(row=80, column=2)

        tk.Label(self, text=_('DDNS Service:')).grid(row=90, column=1)
        self.ddnsService = tk.Entry(self, width=64)
        self.ddnsService.grid(row=90, column=2)

        self.splitActive = tk.IntVar()
        self.splitActive.set(1)
        tk.Checkbutton(self, text=_("Split the given command on semicolons to try and use shorter commands with a 5 second delay between commands.  If an individual command fails it should not affect subsequent commands."), variable=self.splitActive, width=64, height=3, anchor=tk.W, justify=tk.LEFT, wraplength=400).grid(row=100, column=2)

        self.runButton = tk.Button(self, text=_('Run'), command=self.run, width=64)
        self.runButton.grid(row=110, column=2)

        tk.Label(self, text=_('Status:')).grid(row=120, column=1)
        self.status = tk.Label(self, text=_('Check the console window for detailed status or major failures (exceptions - try re-running a few times)'), width=64, height=4, anchor=tk.W, justify=tk.LEFT, wraplength=400)
        self.status.grid(row=120, column=2)

        tk.Label(self, text=_('Select to change to correct defaults:')).grid(row=0, column=3)

        self.method = tk.StringVar()
        self.method.set(self.defaults['startupVariant'])

        rowOffset = 10
        for method in defaultMethods.keys():
            tk.Radiobutton(self, text=method, variable=self.method, value=method, command=self.methodchange).grid(row=rowOffset,column=3)
            rowOffset += 10

        self.host.insert(0, self.defaults['host'])
        self.username.insert(0, self.defaults['username'])
        self.password.insert(0, self.defaults['password'])
        self.firmwarefile.insert(0, self.defaults['upgradeFilename'])
        self.flashfirmware.set(self.defaults['flashFirmware'])
        self.command.insert(0, defaultMethods[self.defaults['startupVariant']][2])
        self.command.config(state='readonly')
        self.methodAction.insert(0, defaultMethods[self.defaults['startupVariant']][0])
        self.methodAction.config(state='readonly')
        self.ddnsService.insert(0, defaultMethods[self.defaults['startupVariant']][1])
        self.ddnsService.config(state='readonly')
        self.commandChange()
        return

    def expertmodeswitch(self):
        newSetting = self.expertmode.get()
        if newSetting == False:
            self.command.config(state='normal')
            self.command.delete(0, tk.END)
            self.command.insert(0, defaultMethods[self.method.get()][2])
            self.command.config(state='readonly')
            self.methodAction.config(state='normal')
            self.methodAction.delete(0, tk.END)
            self.methodAction.insert(0, defaultMethods[self.method.get()][0])
            self.methodAction.config(state='readonly')
            self.ddnsService.config(state='normal')
            self.ddnsService.delete(0, tk.END)
            self.ddnsService.insert(0, defaultMethods[self.method.get()][1])
            self.ddnsService.config(state='readonly')
        else:
            self.command.config(state='normal')
            self.methodAction.config(state='normal')
            self.ddnsService.config(state='normal')
        self.commandChange()
        return

    def methodchange(self):
        self.command.config(state='normal')
        self.command.delete(0, tk.END)
        self.command.insert(0, defaultMethods[self.method.get()][2])
        self.methodAction.config(state='normal')
        self.methodAction.delete(0, tk.END)
        self.methodAction.insert(0, defaultMethods[self.method.get()][0])
        self.ddnsService.config(state='normal')
        self.ddnsService.delete(0, tk.END)
        self.ddnsService.insert(0, defaultMethods[self.method.get()][1])

        if not self.expertmode.get():
            self.command.config(state='readonly')
            self.methodAction.config(state='readonly')
            self.ddnsService.config(state='readonly')

        self.commandChange()
        return
 
    def commandChange(self):
        overallLen = len(self.command.get())
        maxLen = 0
        try:
            maxLen = max([len(l) for l in [s for s in self.command.get().split(';') if len(s) > 0]])
        except:
            maxLen = overallLen
        
        self.lengthSummary.config(text='Overall %i, split maximum %i' % (overallLen, maxLen))

        return True


    def run(self):
        self.status.config(text=_('Check the console window for detailed status or major failures'))
        res = libautoflashgui.mainScript(self.host.get(), self.username.get().encode(), self.password.get().encode(), self.flashfirmware.get(), self.firmwarefile.get(), self.flashSleepDelay, self.methodAction.get(), self.command.get(), self.splitActive.get(), self.ddnsService.get(), self.connectRetryDelay, self.interCommandDelay)
        self.status.config(text=res)
        return


if __name__=='__main__':
    socket.setdefaulttimeout(5)
    app = Application()
    appversion="23.12.2018"
    app.master.title(_("Technicolor modem flash and unlock utility (v. ") + appversion + _(") - By Mark Smith - License: GPLv3"))
    app.mainloop()
