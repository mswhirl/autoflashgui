# Technicolour modem flash and unlock script by Mark Smith (Whirlpool)
# Distributed under GPLv3
# Credits to DanielO for the initial work on using SRPv6 to log into these modems (see links below)
# Requirements:
# python 3 (developed on 3.7.1 x64)
# pip install robobrowser
# mysrp as from https://forums.whirlpool.net.au/user/20499  https://forums.whirlpool.net.au/forum-replies.cfm?t=2596180 https://gist.github.com/DanielO/76c6c337ff09f6011f408427df376e68 
# a copy of the firmware file in the firmware directory
# Multilanguage interface code based on adbtools2 program code
# adbtools home page: https://github.com/digiampietro/adbtools2
# Please see defaults.ini for the settings.

import tkinter as tk
import os, sys, time, socket, tkinter.filedialog, liblang, libautoflashgui
from pathlib import Path

firmwarePath = 'firmware'

def getDefaults(verbose=True):
    config = {}
    global defaultMethods
    defaultMethods = {}
    if verbose:
        print(_('Reading config...'))
    with open('defaults.ini', "r", 1048576, encoding='utf8') as f:
        for line in f:
            if verbose:
                print(_('Line: ') + line.strip())
            if not line.startswith("#"):
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

        tk.Label(self, text=_('Load Default:')).grid(row=rowOffset, column=1, sticky=tk.W)
        self.defaultListText = defaultMethods.keys()
        self.defaultList = tk.StringVar()
        self.defaultList.set(self.defaults['startupVariant'])
        self.default = tk.OptionMenu(self, self.defaultList, *self.defaultListText, command=self.variantChange)
        self.default.grid(row=rowOffset, column=2, sticky=tk.W)
        rowOffset += spacing

        tk.Label(self, text=_('Target IP:')).grid(row=rowOffset, column=1, sticky=tk.W)
        self.host = tk.Entry(self, width=w)
        self.host.insert(0, self.defaults['host'])
        self.host.grid(row=rowOffset, column=2, sticky=tk.W)
        rowOffset += spacing

        tk.Label(self, text=_('Username:')).grid(row=rowOffset, column=1, sticky=tk.W)
        self.username = tk.Entry(self, width=w)
        self.username.insert(0, self.defaults['username'])
        self.username.grid(row=rowOffset, column=2, sticky=tk.W)
        rowOffset += spacing

        tk.Label(self, text=_('Password:')).grid(row=rowOffset, column=1, sticky=tk.W)
        self.password = tk.Entry(self, width=w)
        self.password.insert(0, self.defaults['password'])
        self.password.grid(row=rowOffset, column=2, sticky=tk.W)
        rowOffset += spacing

        tk.Label(self, text=_('Firmware File Name:')).grid(row=rowOffset, column=1, sticky=tk.W)
        self.firmwarefile = tk.Entry(self, width=w)
        self.firmwarefile.insert(0, self.defaults['upgradeFilename'])
        self.firmwarefile.grid(row=rowOffset, column=2, sticky=tk.W)
        rowOffset += spacing

        self.pickFileButton = tk.Button(self, text=_('Browse for Firmware File'), command=self.pickFirmware, width=w)
        self.pickFileButton.grid(row=rowOffset, column=2, sticky=tk.W)
        rowOffset += spacing

        self.flashfirmware = tk.IntVar()
        self.flashfirmware.set(self.defaults['flashFirmware'])
        tk.Checkbutton(self, text=_('Flash firmware?'), variable=self.flashfirmware, width=w).grid(row=rowOffset, column=2, sticky=tk.W)
        rowOffset += spacing

        self.expertMode = tk.IntVar()
        self.expertMode.set(self.defaults['expertMode'])
        tk.Checkbutton(self, text=_("I really truly know what I'm doing and I want to mess with the commands to tweak the firmware and I promise not to ask for help. :)  I understand that if the unsplit (if selected) or split command is too long (suspected limit of about 245 on TG799) or if I use special characters it may fail.  Avoid using & or ; (except splitting commands, unless escaped as a character code?)."), variable=self.expertMode, command=self.expertModeSwitch, width=w, height=6, anchor=tk.W, justify=tk.LEFT, wraplength=400).grid(row=rowOffset, column=2, sticky=tk.W)
        rowOffset += spacing

        self.commandEval = tk.StringVar()
        tk.Label(self, text=_('Command:')).grid(row=rowOffset, column=1, sticky=tk.W)
        self.command = tk.Entry(self, width=w, textvariable=self.commandEval)
        self.command.bind('<Key>', (lambda _: self.commandChange()))
        self.command.insert(0, defaultMethods[self.defaultList.get()][2])
        self.command.config(state='readonly')
        self.command.grid(row=rowOffset, column=2, sticky=tk.W)
        rowOffset += spacing

        self.lengthSummary = tk.Label(self, text='length goes here')
        self.lengthSummary.grid(row=rowOffset, column=2, sticky=tk.W)
        rowOffset += spacing

        tk.Label(self, text=_('Execution Method:')).grid(row=rowOffset, column=1, sticky=tk.W)
        self.methodActionListText = ['Ping', 'AdvancedDDNS', 'BasicDDNS']
        self.methodActionList = tk.StringVar()
        self.methodAction = tk.OptionMenu(self, self.methodActionList, *self.methodActionListText)
        self.methodActionList.set(defaultMethods[self.defaultList.get()][0])        
        self.methodAction.config(state='disabled')
        self.methodAction.grid(row=rowOffset, column=2, sticky=tk.W)
        rowOffset += spacing

        tk.Label(self, text=_('DDNS Service:')).grid(row=rowOffset, column=1, sticky=tk.W)
        self.ddnsService = tk.Entry(self, width=w)
        self.ddnsService.insert(0, defaultMethods[self.defaultList.get()][1])
        self.ddnsService.config(state='readonly')
        self.ddnsService.grid(row=rowOffset, column=2, sticky=tk.W)
        rowOffset += spacing

        self.splitActive = tk.IntVar()
        self.splitActive.set(self.defaults['splitCommand'])
        tk.Checkbutton(self, text=_('Split the given command on semicolons to try and use shorter commands with a 5 second delay between commands.  If an individual command fails it should not affect subsequent commands.'), variable=self.splitActive, width=w, height=4, anchor=tk.W, justify=tk.LEFT, wraplength=400).grid(row=rowOffset, column=2, sticky=tk.W)
        rowOffset += spacing

        self.runButton = tk.Button(self, text=_('Run'), command=self.run, width=w)
        self.runButton.grid(row=rowOffset, column=2, sticky=tk.W)
        rowOffset += spacing

        tk.Label(self, text=_('Status:')).grid(row=rowOffset, column=1, sticky=tk.W)
        self.status = tk.Label(self, text=_('Check the console window for detailed status or major failures (exceptions - try re-running a few times)'), width=w, height=5, anchor=tk.W, justify=tk.LEFT, wraplength=400)
        self.status.grid(row=rowOffset, column=2, sticky=tk.W)
        
        self.commandChange()
        self.expertModeSwitch()
        return

    def variantChange(self, value):
        print(_('Selected new variant '), value)
        self.command.config(state='normal')
        self.command.delete(0, tk.END)
        self.command.insert(0, defaultMethods[value][2])
        self.methodAction.config(state='normal')
        self.methodActionList.set(defaultMethods[value][0])
        self.ddnsService.config(state='normal')
        self.ddnsService.delete(0, tk.END)
        self.ddnsService.insert(0, defaultMethods[value][1])

        if not self.expertMode.get():
            self.command.config(state='readonly')
            self.methodAction.config(state='disabled')
            self.ddnsService.config(state='readonly')

        self.commandChange()

    def pickFirmware(self):
        fileName = tk.filedialog.askopenfilename(initialdir=firmwarePath, title=_('Please select firmware'), filetypes = [(_('RBI files'), '*.rbi')])
        self.firmwarefile.delete(0, tk.END)
        self.firmwarefile.insert(0, fileName)

    def expertModeSwitch(self):
        newSetting = self.expertMode.get()
        if newSetting == False:
            self.command.config(state='normal')
            self.command.delete(0, tk.END)
            self.command.insert(0, defaultMethods[self.defaultList.get()][2])
            self.command.config(state='readonly')
            self.methodAction.config(state='normal')
            self.methodActionList.set(defaultMethods[self.defaultList.get()][0])
            self.methodAction.config(state='disabled')
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
        
        # Next line replaced due to language library restrictions where it can't handle standard substitution formatting?
        #self.lengthSummary.config(text=_('Overall %i, split maximum %i') % (overallLen, maxLen))
        self.lengthSummary.config(text=_('Overall ') + str(overallLen)  + _(', split maximum ') + str(maxLen))
        return True


    def run(self):
        self.status.config(text=_('Check the console window for detailed status or major failures'))
        if self.flashfirmware.get() == True and not os.path.exists(self.firmwarefile.get()):
            self.status.config(text=_('Firmware flashing enabled but firmware file name does not exist!'))
            return
        res = libautoflashgui.mainScript(self.host.get(), self.username.get().encode(), self.password.get().encode(), self.flashfirmware.get(), self.firmwarefile.get(), self.flashSleepDelay, self.methodActionList.get(), self.command.get(), self.splitActive.get(), self.ddnsService.get(), self.connectRetryDelay, self.interCommandDelay)
        self.status.config(text=res)
        return

if __name__=='__main__':
    socket.setdefaulttimeout(5)
    # clear screen
    if sys.platform.startswith('win'):
        os.system("cls")
    else:
        os.system("clear")

    # Workaround for py2exe/pyinstaller to fix the path against the exe file for the multilanguage stuff
    print(sys.argv, sys.path, os.getcwd())
    defaultPath = os.path.dirname(sys.argv[0])
    if defaultPath == '' or defaultPath == None or not os.path.isdir(defaultPath):
        sys.argv[0] = os.path.join(os.getcwd(), sys.argv[0])
        sys.path.insert(0, os.getcwd())
    print(sys.argv, sys.path, os.getcwd())

    defaults = getDefaults(False)
    if 'language' in defaults.keys():
        language = defaults['language']
    else:
        language = None
    
    liblang.init_language(sys.argv, sys.path, language)
    _ = liblang._
    lan = liblang.lan
    libautoflashgui.init_language(sys.argv, sys.path, language)
    
    app = Application()
    appversion="16.02.2018"
    app.master.title(_('Technicolor modem flash/unlock utility (v. ') + appversion + _(') - By Mark Smith'))
    app.mainloop()
