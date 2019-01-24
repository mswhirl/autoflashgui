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
##variant=DGA4132 AGTHP 1.0.3,AdvancedDDNS,dyndns.it,sed -i 's#root:/bin/false#root:/bin/ash#' /etc/passwd;uci set dropbear.lan.enable=1;uci set dropbear.lan.RootPasswordAuth=on;uci commit;echo -e "root\nroot"|passwd;/etc/init.d/dropbear restart

import tkinter as tk
import tkinter.filedialog
import libautoflashgui, socket

# Multilanguage interface code based on adbtools2 program code
# adbtools home page: https://github.com/digiampietro/adbtools2
import os, sys, time
from pathlib import Path
import liblang

firmwarePath = 'firmware'

def getDefaults():
    config = {}
    global defaultMethods
    defaultMethods = {}
    print(_("Reading config..."))
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
        self.createWidgets()

    def createWidgets(self):
        rowOffset = 0
        spacing = 1 * 10 # Interval of 10
        w = 64
		

        tk.Label(self, text=_('Modem profile:')).grid(row=rowOffset, column=1)
        self.defaultListText = defaultMethods.keys()
        self.defaultList = tk.StringVar()
        self.defaultList.set(self.defaults['startupVariant'])
        self.default = tk.OptionMenu(self, self.defaultList, *self.defaultListText, command=self.variantChange)
        self.default.grid(row=rowOffset, column=2)
        rowOffset += spacing

        tk.Label(self, text=_('Target IP:')).grid(row=rowOffset, column=1)
        self.host = tk.Entry(self, width=w)
        self.host.grid(row=rowOffset, column=2)
        rowOffset += spacing

        tk.Label(self, text=_('Username:')).grid(row=rowOffset, column=1)
        self.username = tk.Entry(self, width=w)
        self.username.grid(row=rowOffset, column=2)
        rowOffset += spacing

        tk.Label(self, text=_('Password:')).grid(row=rowOffset, column=1)
        self.password = tk.Entry(self, width=w)
        self.password.grid(row=rowOffset, column=2)
        rowOffset += spacing

        tk.Label(self, text=_('Firmware File Name:')).grid(row=rowOffset, column=1)
        self.firmwarefile = tk.Entry(self, width=w)
        self.firmwarefile.grid(row=rowOffset, column=2)
        rowOffset += spacing

        self.pickFileButton = tk.Button(self, text=_('Select firmware file'), command=self.pickFirmware, width=54)
        self.pickFileButton.grid(row=rowOffset, column=2)
        rowOffset += spacing

        self.flashfirmware = tk.IntVar()
        tk.Checkbutton(self, text=_("Flash firmware?"), variable=self.flashfirmware, width=w).grid(row=rowOffset, column=2)
        rowOffset += spacing

        self.expertmode = tk.IntVar()
        self.expertmode.set(1)
        tk.Checkbutton(self, text=_("I really truly know what I'm doing and I want to mess with the commands to tweak the firmware and I promise not to ask for help. :)  I understand that if the unsplit (if selected) or split command is too long (suspected limit of about 245 on TG799) or if I use special characters it may fail.  Avoid using & or ; (except splitting commands, unless escaped as a character code?)."), variable=self.expertmode, command=self.expertmodeswitch, width=w, height=6, anchor=tk.W, justify=tk.LEFT, wraplength=400).grid(row=rowOffset, column=2)
        rowOffset += spacing

        self.commandEval = tk.StringVar()
        tk.Label(self, text=_('Command:')).grid(row=rowOffset, column=1)
        self.command = tk.Entry(self, width=w, textvariable=self.commandEval)
        self.command.bind('<Key>', (lambda _: self.commandChange()))
        self.command.grid(row=rowOffset, column=2)
        rowOffset += spacing

        self.lengthSummary = tk.Label(self, text='length goes here')
        self.lengthSummary.grid(row=rowOffset, column=2)
        rowOffset += spacing

        tk.Label(self, text=_('Ping,\nAdvancedDDNS,\nBasicDDNS:')).grid(row=rowOffset, column=1)
        self.methodAction = tk.Entry(self, width=16)
        self.methodAction.grid(row=rowOffset, column=2)
        rowOffset += spacing

        tk.Label(self, text=_('DDNS Service:')).grid(row=rowOffset, column=1)
        self.ddnsService = tk.Entry(self, width=w)
        self.ddnsService.grid(row=rowOffset, column=2)
        rowOffset += spacing

        self.splitActive = tk.IntVar()
        self.splitActive.set(1)
        tk.Checkbutton(self, text=_("Split the given command on semicolons to try and use shorter commands with a 5 second delay between commands.  If an individual command fails it should not affect subsequent commands."), variable=self.splitActive, width=w, height=4, anchor=tk.W, justify=tk.LEFT, wraplength=400).grid(row=rowOffset, column=2)
        rowOffset += spacing

        self.runButton = tk.Button(self, text=_('Run'), command=self.run, width=54)
        self.runButton.grid(row=rowOffset, column=2)
        rowOffset += spacing

        tk.Label(self, text=_('Status:')).grid(row=rowOffset, column=1)
        self.status = tk.Label(self, text=_('Check the console window for detailed status or major failures (exceptions - try re-running a few times)'), width=w, height=5, anchor=tk.W, justify=tk.LEFT, wraplength=400)
        self.status.grid(row=rowOffset, column=2)
        
        self.host.insert(0, self.defaults['host'])
        self.username.insert(0, self.defaults['username'])
        self.password.insert(0, self.defaults['password'])
        self.firmwarefile.insert(0, self.defaults['upgradeFilename'])
        self.flashfirmware.set(self.defaults['flashFirmware'])
        self.command.insert(0, defaultMethods[self.defaultList.get()][2])
        self.command.config(state='readonly')
        self.methodAction.insert(0, defaultMethods[self.defaultList.get()][0])
        self.methodAction.config(state='readonly')
        self.ddnsService.insert(0, defaultMethods[self.defaultList.get()][1])
        self.ddnsService.config(state='readonly')
        self.commandChange()
        return

    def variantChange(self, value):
        print(_("Selected new profile "), value)
        self.command.config(state='normal')
        self.command.delete(0, tk.END)
        self.command.insert(0, defaultMethods[value][2])
        self.methodAction.config(state='normal')
        self.methodAction.delete(0, tk.END)
        self.methodAction.insert(0, defaultMethods[value][0])
        self.ddnsService.config(state='normal')
        self.ddnsService.delete(0, tk.END)
        self.ddnsService.insert(0, defaultMethods[value][1])

        if not self.expertmode.get():
            self.command.config(state='readonly')
            self.methodAction.config(state='readonly')
            self.ddnsService.config(state='readonly')

        self.commandChange()

    def pickFirmware(self):
        fileName = tk.filedialog.askopenfilename(initialdir=firmwarePath, title=_("Please select firmware"), filetypes = [(_('RBI files'), '*.rbi')])
        self.firmwarefile.delete(0, tk.END)
        self.firmwarefile.insert(0, fileName)

    def expertmodeswitch(self):
        newSetting = self.expertmode.get()
        if newSetting == False:
            self.command.config(state='normal')
            self.command.delete(0, tk.END)
            self.command.insert(0, defaultMethods[self.defaultList.get()][2])
            self.command.config(state='readonly')
            self.methodAction.config(state='normal')
            self.methodAction.delete(0, tk.END)
            self.methodAction.insert(0, defaultMethods[self.defaultList.get()][0])
            self.methodAction.config(state='readonly')
            self.ddnsService.config(state='normal')
            self.ddnsService.delete(0, tk.END)
            self.ddnsService.insert(0, defaultMethods[self.defaultList.get()][1])
            self.ddnsService.config(state='readonly')
        else:
            self.command.config(state='normal')
            self.methodAction.config(state='normal')
            self.ddnsService.config(state='normal')
        self.commandChange()
        return

    def commandChange(self):
        overallLen = len(self.command.get())
        maxLen = 0
        try:
            maxLen = max([len(l) for l in [s for s in self.command.get().split(';') if len(s) > 0]])
        except:
            maxLen = overallLen
        
        self.lengthSummary.config(text=_('Overall characters: ') + str (overallLen) + _(' - max characters for line: ') + str (maxLen))
        return True


    def run(self):
        self.status.config(text=_('Check the console window for detailed status or major failures'))
        res = libautoflashgui.mainScript(self.host.get(), self.username.get().encode(), self.password.get().encode(), self.flashfirmware.get(), self.firmwarefile.get(), self.flashSleepDelay, self.methodAction.get(), self.command.get(), self.splitActive.get(), self.ddnsService.get(), self.connectRetryDelay, self.interCommandDelay)
        self.status.config(text=res)
        return

if __name__=='__main__':
    socket.setdefaulttimeout(5)
    # clear screen
    if sys.platform.startswith('win'):
        os.system("cls")
    else:
        os.system("clear")

    liblang.init_language()
#    _ = liblang._
    lan = liblang.lan

    app = Application()
    appversion="21.01.2018"
    app.master.title(_("Technicolor modem flash/unlock utility (v. ") + appversion + _(") - By Mark Smith"))
    app.mainloop()
