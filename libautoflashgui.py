# Technicolour modem flash and unlock script by Mark Smith (Whirlpool)
# Distributed under GPLv3
# Credits to DanielO for the initial work on using SRPv6 to log into these modems (see links below)
# 
# Please see the comments in autoflashgui.py for full details

import mysrp as srp
from urllib.parse import urlencode

import binascii, json, urllib, bs4, socket, time
from robobrowser import RoboBrowser

def srp6authenticate(br, host, username, password):
    br.open('http://' + host)
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
