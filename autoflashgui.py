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

import mysrp as srp
from urllib.parse import urlencode
import tkinter as tk

try:
    import binascii, json, urllib, bs4, socket, time
    from robobrowser import RoboBrowser

except ImportError or ModuleNotFoundError:
    print("The robobrowser module is missing.  You *may* need admin/root priviliges if you proceed with installing it here.")
    install=input("Install? (Y/n): ")
    if install == "" or install == "Y" or install == "y":
        import pip
        pip.main(["install", "robobrowser" ])
        import binascii, json, urllib, bs4, socket, time
        from robobrowser import RoboBrowser
    else:
        print("""This script can't run without the modules installed.  "pip install robobrowser" to continue.""")
        input()
        sys.exit(1)

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

def srp6authenticate(br, host, username, password):
    r = br.open('http://' + host)
    token = br.find(lambda tag: tag.has_attr('name') and tag['name'] == 'CSRFtoken')['content']
    #print('Got CSRF token: ' + token)

    usr = srp.User(username, password, hash_alg = srp.SHA256, ng_type = srp.NG_2048)
    uname, A = usr.start_authentication()
    #print(binascii.hexlify(A))

    br.open('http://' + host + '/authenticate', method='post', data = urlencode({'CSRFtoken' : token, 'I' : uname, 'A' : binascii.hexlify(A)}))
    #print(br.response)
    j = json.decoder.JSONDecoder().decode(br.parsed.decode())
    #print('Challenge rceived: ' + str(j))

    M = usr.process_challenge(binascii.unhexlify(j['s']), binascii.unhexlify(j['B']))
    #print(binascii.hexlify(M))
    br.open('http://' + host + '/authenticate', method='post', data = urlencode({'CSRFtoken' : token, 'M' : binascii.hexlify(M)}))
    #print(br.response)
    j = json.decoder.JSONDecoder().decode(br.parsed.decode())
    #print('Got response ' + str(j))

    usr.verify_session(binascii.unhexlify(j['M']))
    if not usr.authenticated():
        print('Failed to authenticate')
        return False

    print('Authenticated OK')
    return True

def runCommand(br, host, token, activeMethod, activeCommand, ddnsService):
    print("Sending command: " + activeCommand)
    if activeMethod == 'Ping':
        postdata = {'CSRFtoken': token, 'action': 'PING', 'ipAddress': ':::::::;' + activeCommand + ';', 'NumberOfRepetitions': '3', 'DataBlockSize': '64'}
        urlpostfix = '/modals/diagnostics-ping-modal.lp'
    elif activeMethod == 'DDNS':
        postdata = {'CSRFtoken': token, 'action': 'SAVE', 'ddns_domain': 'test.com;' + activeCommand + ';',
            'DMZ_enable': '0', 'DMZ_destinationip': '','upnp_status':'0',
            'upnp_natpmp':'0', 'upnp_secure_mode':'1', 'ddns_enabled':'1', 'ddns_service_name':ddnsService,
            'ddns_usehttps':'0', 'ddns_username':'invalid', 'ddns_password':'invalid',
            'fromModal':'YES'}
        urlpostfix = '/modals/wanservices-modal.lp'
    else:
        raise Exception("Unknown method " + activeMethod + " please check input in GUI")
    
    r = br.session.post('http://' + host + urlpostfix, data=postdata)
    br._update_state(r)
    
    return br.response.ok


def mainScript(host, username, password, flashFirmware, upgradeFilename, flashSleepDelay, activeMethod, activeCommand, splitCommand, ddnsService, connectRetryDelay, interCommandDelay):
    br = RoboBrowser(history=True, parser="html.parser")

    success = False
    if flashFirmware:
        print("Authenticating")
        srp6authenticate(br, host, username, password)
        br.open('http://' + host)
        token = br.find(lambda tag: tag.has_attr('name') and tag['name'] == 'CSRFtoken')['content']
        print("Sending flash command to modem")
        filedata = {'CSRFtoken': token, 'upgradefile': (upgradeFilename, open(upgradeFilename, 'rb'))}
        r = br.session.post('http://' + host + '/modals/gateway-modal.lp?action=upgradefw', files=filedata)
        br._update_state(r)
        print(r.text)
        if r.text == '{ "success":"true" }':
            print("Modem reports flashing commenced successfully")
            success = True
            print("Waiting for reboot... Sleeping for %s s" % (flashSleepDelay))
            time.sleep(int(flashSleepDelay))
    else:
        success = True

    if success:
        backUp = False
        attempt = 0
        while not backUp:
            attempt += 1
            print("Connect attempt %i" % (attempt))
            try:
                br.open('http://' + host)
                print (br.response)
                if br.response.ok:
                    backUp = True
            except Exception:
                print('Failed to connect, attempt %i.  Retrying' % (attempt))
                time.sleep(int(connectRetryDelay))
                pass

        print("Modem up")

    print("Authenticating")
    srp6authenticate(br, host, username, password)
    br.open('http://' + host)
    token = br.find(lambda tag: tag.has_attr('name') and tag['name'] == 'CSRFtoken')['content']

    if not splitCommand:
        runCommand(br, host, token, activeMethod, activeCommand, ddnsService)
    else:
        print("Splitting command up using semicolons")
        for subCommand in [s for s in activeCommand.split(';') if len(s) > 0]:
            runCommand(br, host, token, activeMethod, subCommand, ddnsService)
            print("Sleeping...")
            time.sleep(int(interCommandDelay))

    result = "Please try a ssh connection now to " + host + " with username root and password root (change password immediately with passwd!)  Rebooting your modem now is recommended to stop any services that have been disabled."
    print(result)
    return result

class Application(tk.Frame):
    def __init__(s, master=None):
        tk.Frame.__init__(s, master)
        s.grid()
        s.defaults = getDefaults()
        s.flashFirmwre = s.defaults['flashFirmware']
        s.flashSleepDelay = s.defaults['flashSleepDelay']
        s.interCommandDelay = s.defaults['interCommandDelay']
        s.connectRetryDelay = s.defaults['connectRetryDelay']
        s.expertMode = False
        s.createWidgets()

    def createWidgets(s):
        tk.Label(s, text='Target IP:').grid(row=0, column=1)
        s.host = tk.Entry(s, width=64)
        s.host.grid(row=0, column=2)

        tk.Label(s, text='Username:').grid(row=10, column=1)
        s.username = tk.Entry(s, width=64)
        s.username.grid(row=10, column=2)

        tk.Label(s, text='Password:').grid(row=20, column=1)
        s.password = tk.Entry(s, width=64)
        s.password.grid(row=20, column=2)

        tk.Label(s, text='Firmware File Name:').grid(row=30, column=1)
        s.firmwarefile = tk.Entry(s, width=64)
        s.firmwarefile.grid(row=30, column=2)

        s.flashfirmware = tk.IntVar()
        tk.Checkbutton(s, text="Flash firmware?", variable=s.flashfirmware, width=64).grid(row=40, column=2)

        s.expertmode = tk.IntVar()
        tk.Checkbutton(s, text="I really truly know what I'm doing and I want to mess with the commands to tweak the firmware and I promise not to ask for help. :)  I understand that if the unsplit (if selected) or split command is too long (suspected limit of about 245 on TG799) or if I use special characters it may fail.  Avoid using & or ; (except splitting commands, unless escaped as a character code?).", variable=s.expertmode, command=s.expertmodeswitch, width=64, height=5, anchor=tk.W, justify=tk.LEFT, wraplength=400).grid(row=50, column=2)
        s.commandEval = tk.StringVar()
        tk.Label(s, text='Command:').grid(row=60, column=1)
        s.command = tk.Entry(s, width=64, textvariable=s.commandEval)
        s.command.bind('<Key>', (lambda _: s.commandChange()))
        s.command.grid(row=60, column=2)

        s.lengthSummary = tk.Label(s, text='length goes here')
        s.lengthSummary.grid(row=70, column=2)

        tk.Label(s, text='Ping or DDNS:').grid(row=80, column=1)
        s.methodAction = tk.Entry(s, width=16)
        s.methodAction.grid(row=80, column=2)

        tk.Label(s, text='DDNS Service:').grid(row=90, column=1)
        s.ddnsService = tk.Entry(s, width=64)
        s.ddnsService.grid(row=90, column=2)

        s.splitActive = tk.IntVar()
        s.splitActive.set(1)
        tk.Checkbutton(s, text="Split the given command on semicolons to try and use shorter commands with a 5 second delay between commands.  If an individual command fails it should not affect subsequent commands.", variable=s.splitActive, width=64, height=3, anchor=tk.W, justify=tk.LEFT, wraplength=400).grid(row=100, column=2)

        s.runButton = tk.Button(s, text='Run', command=s.run, width=64)
        s.runButton.grid(row=110, column=2)

        tk.Label(s, text='Status:').grid(row=120, column=1)
        s.status = tk.Label(s, text='Check the console window for detailed status or major failures (exceptions - try re-running a few times)', width=64, height=4, anchor=tk.W, justify=tk.LEFT, wraplength=400)
        s.status.grid(row=120, column=2)

        tk.Label(s, text='Select to change to correct defaults:').grid(row=0, column=3)

        s.method = tk.StringVar()
        s.method.set(s.defaults['startupVariant'])

        rowOffset = 10
        for method in defaultMethods.keys():
            s.b = tk.Radiobutton(s, text=method, variable=s.method, value=method, command=s.methodchange).grid(row=rowOffset,column=3)
            rowOffset += 10

        s.host.insert(0, s.defaults['host'])
        s.username.insert(0, s.defaults['username'])
        s.password.insert(0, s.defaults['password'])
        s.firmwarefile.insert(0, s.defaults['upgradeFilename'])
        s.flashfirmware.set(s.defaults['flashFirmware'])
        s.command.insert(0, defaultMethods[s.defaults['startupVariant']][2])
        s.command.config(state='readonly')
        s.methodAction.insert(0, defaultMethods[s.defaults['startupVariant']][0])
        s.methodAction.config(state='readonly')
        s.ddnsService.insert(0, defaultMethods[s.defaults['startupVariant']][1])
        s.ddnsService.config(state='readonly')
        s.commandChange()
        return

    def expertmodeswitch(s):
        newSetting = s.expertmode.get()
        if newSetting == False:
            s.command.config(state='normal')
            s.command.delete(0, tk.END)
            s.command.insert(0, defaultMethods[s.method.get()][2])
            s.command.config(state='readonly')
            s.methodAction.config(state='normal')
            s.methodAction.delete(0, tk.END)
            s.methodAction.insert(0, defaultMethods[s.method.get()][0])
            s.methodAction.config(state='readonly')
            s.ddnsService.config(state='normal')
            s.ddnsService.delete(0, tk.END)
            s.ddnsService.insert(0, defaultMethods[s.method.get()][1])
            s.ddnsService.config(state='readonly')
        else:
            s.command.config(state='normal')
            s.methodAction.config(state='normal')
            s.ddnsService.config(state='normal')
        s.commandChange()
        return

    def methodchange(s):
        s.command.config(state='normal')
        s.command.delete(0, tk.END)
        s.command.insert(0, defaultMethods[s.method.get()][2])
        s.methodAction.config(state='normal')
        s.methodAction.delete(0, tk.END)
        s.methodAction.insert(0, defaultMethods[s.method.get()][0])
        s.ddnsService.config(state='normal')
        s.ddnsService.delete(0, tk.END)
        s.ddnsService.insert(0, defaultMethods[s.method.get()][1])

        if not s.expertmode.get():
            s.command.config(state='readonly')
            s.methodAction.config(state='readonly')
            s.ddnsService.config(state='readonly')

        s.commandChange()
        return
 
    def commandChange(s):
        overallLen = len(s.command.get())
        maxLen = 0
        try:
            maxLen = max([len(l) for l in [s for s in s.command.get().split(';') if len(s) > 0]])
        except:
            maxLen = overallLen
        
        s.lengthSummary.config(text='Overall %i, split maximum %i' % (overallLen, maxLen))

        return True


    def run(s):
        s.status.config(text='Check the console window for detailed status or major failures')
        res = mainScript(s.host.get(), s.username.get().encode(), s.password.get().encode(), s.flashfirmware.get(), s.firmwarefile.get(), s.flashSleepDelay, s.methodAction.get(), s.command.get(), s.splitActive.get(), s.ddnsService.get(), s.connectRetryDelay, s.interCommandDelay)
        s.status.config(text=res)
        return

socket.setdefaulttimeout(5)
app = Application()
app.master.title('Technicolour modem flash and unlock utility by Mark Smith.  License: GPLv3.')
app.mainloop()
