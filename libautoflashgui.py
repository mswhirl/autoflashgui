# Technicolour modem flash and unlock script by Mark Smith (Whirlpool)
# Forked to make a version that will work with Vodafone Ultrahub (VANT-9) and Ultrahub plus (VBNT-Z) from New Zealand
# Forked at: https://github.com/jameskeenan295/autoflashgui
# Distributed under GPLv3
# Credits to DanielO for the initial work on using SRPv6 to log into these modems (see links below)
# 
# Please see the comments in autoflashgui.py for full details

import mysrp as srp
from urllib.parse import urlencode
import binascii, json, time, sys, traceback, datetime
from robobrowser import RoboBrowser
import liblang

# init_language():
# Call this function with sys.argv and sys.path as the paramaters.
# When used as a library, these are not available in the current context
def init_language(argv, path, language):
    liblang.init_language(argv, path, language)
    global _
    _ = liblang._

def srp6authenticate(br, host, username, password):
    try:
        debugData = []
        print('{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ' GETing http://' + host)
        br.open('http://' + host)
        print('{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ' Got http://' + host)
        token = br.find(lambda tag: tag.has_attr('name') and tag['name'] == 'CSRFtoken')['content']
        debugData.append('Got CSRF token: ' + token)
        print('{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ' Got initial (unauthenticated) CSRFtoken: ' + token)
        usr = srp.User(username, password, hash_alg = srp.SHA256, ng_type = srp.NG_2048)
        uname, A = usr.start_authentication()
        debugData.append(_("A value ") + str(binascii.hexlify(A)))
        
        br.open('http://' + host + '/authenticate', method='post', data = urlencode({'CSRFtoken' : token, 'I' : uname, 'A' : binascii.hexlify(A)}))
        debugData.append("br.response " + str(br.response))
        j = json.decoder.JSONDecoder().decode(br.parsed.decode())
        debugData.append(_("Challenge received: ") + str(j))

        M = usr.process_challenge(binascii.unhexlify(j['s']), binascii.unhexlify(j['B']))
        debugData.append(_("M value ") + str(binascii.hexlify(M)))
        br.open('http://' + host + '/authenticate', method='post', data = urlencode({'CSRFtoken' : token, 'M' : binascii.hexlify(M)}))
        debugData.append("br.response " + str(br.response))
        j = json.decoder.JSONDecoder().decode(br.parsed.decode())
        debugData.append("Got response " + str(j))

        if 'error' in j:
            raise Exception(_("Unable to authenticate (check password?), message:"), j)
        
        usr.verify_session(binascii.unhexlify(j['M']))
        if not usr.authenticated():
            raise Exception(_("Unable to authenticate"))
        
        print('{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ' Authentication successful' + token)
        return True

    except Exception:
        print('{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ' ' + _("Authentication failed, debug values are: ") + str(debugData))
        print('{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ' ' + _("Exception: ") + str(sys.exc_info()[0]))
        traceback.print_exc()
        raise
        
def runCommand(br, host, token, activeMethod, activeCommand, ddnsService):
    if activeMethod == 'Ping':
        postdata = {'CSRFtoken': token, 'action': 'PING', 'ipAddress': ':::::::;' + activeCommand, 'NumberOfRepetitions': '3', 'DataBlockSize': '64'}
        urlpostfix = '/modals/diagnostics-ping-modal.lp'
    elif activeMethod == 'AdvancedDDNS':
        postdata = {'CSRFtoken': token, 'action': 'SAVE', 'ddns_domain': 'test.com;' + activeCommand,
            'DMZ_enable': '0', 'DMZ_destinationip': '','upnp_status':'0',
            'upnp_natpmp':'0', 'upnp_secure_mode':'1', 'ddns_enabled':'1', 'ddns_service_name':ddnsService,
            'ddns_usehttps':'0', 'ddns_username':'invalid', 'ddns_password':'invalid',
            'fromModal':'YES'}
        urlpostfix = '/modals/wanservices-modal.lp'
    elif activeMethod == 'BasicDDNS':
        postdata = {
            'ddns_enabled':['_DUMMY_', '_TRUE_'], 
            'ddns_service_name':ddnsService, 
            'ddns_domain': ':::::::;' + activeCommand,
            'ddns_username':'invalid',
            'ddns_password':'invalid',
            'action': 'SAVE',
            'CSRFtoken': token
        }
        urlpostfix = '/dyndns.lp'
    elif activeMethod == 'VodafoneDDNS': # DGA0130 Vodafone NZ VANT-9 Ultra Hub
        postdata = {
            'ddnsStatus': '1',
            'ddnsService': ddnsService,
            'ddnsDomain': 'test.com;' + activeCommand,
            'ddnsUsrname': 'admin',
            'ddnsPswrd': 'notarealpassword',
            'securedns': '0',
            'action': 'SAVE',
            'CSRFtoken': token
            }
        urlpostfix = '/modals/dns-ddns.lp'
    elif activeMethod == 'VodafoneDDNS2': # DNA0130 Vodafone NZ VBNT-Z Ultrahub Plus
        postdata = {
            'ddnsStatus': '1',
            'ddnsService': ddnsService,
            'ddnsDomain': 'test.com;' + activeCommand,
            'ddnsUsrname': 'admin',
            'ddnsPswrd': 'notarealpassword',
            'securedns': '0',
            'action': 'SAVE',
            'CSRFtoken': token
            }
        urlpostfix = '/modals/internet/dns_ddns.lp'
    else:
        raise Exception(_("Unknown method ") + activeMethod + _(" please check input in GUI"))
    
    print('{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + " Sending command: " + activeCommand)
    r = br.session.post('http://' + host + urlpostfix, data=postdata)
    print('{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ' Response: ' + str(br.response))
    br._update_state(r)
    
    return br.response.ok


def mainScript(host, username, password, flashFirmware, upgradeFilename, flashSleepDelay, activeMethod, activeCommand, splitCommand, ddnsService, connectRetryDelay, interCommandDelay):
    br = RoboBrowser(history=True, parser="html.parser", timeout=15)

    print('{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ' ' + _("Authenticating"))
    srp6authenticate(br, host, username, password)
    print('{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ' GETing : http://' + host + ' to aquire authenticated CSRFtoken')
    br.open('http://' + host)
    print('{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ' GET completed: ' + str(br.response))
    if activeMethod == 'VodafoneDDNS' or activeMethod == 'VodafoneDDNS2':
        token = br.find(lambda tag: tag.has_attr('name') and tag.has_attr('type') and tag['name'] == 'CSRFtoken')['value']
    else:
        token = br.find(lambda tag: tag.has_attr('name') and tag['name'] == 'CSRFtoken')['content']
    print('{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ' Got authenticated CSRFtoken: ' + token)
    success = False
    if flashFirmware:
        print('{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ' Flash Firmware option is enabled. Activemethod = ' + activeMethod)
        if activeMethod == 'VodafoneDDNS': # DGA0130 Vodafone NZ VANT-9 Ultra Hub
            upgradeurlpostfix = '/modals/upgrade.lp?action=upgradefw'
        elif activeMethod == 'VodafoneDDNS2': # DNA0130 Vodafone NZ VBNT-Z Ultrahub Plus
            upgradeurlpostfix = '/modals/settings/firmwareUpdate.lp?action=upgradefw'
        else:
            upgradeurlpostfix = '/modals/gateway-modal.lp?action=upgradefw'
        filedata = {'CSRFtoken': token, 'upgradefile': ('test.rbi', open(upgradeFilename, 'rb'))}
        print('{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ' POSTing firmware to: ' + 'http://' + host + upgradeurlpostfix)
        r = br.session.post('http://' + host + upgradeurlpostfix, files=filedata)
        print('{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ' Fimrware POST completed: ' + str(br.response))
        br._update_state(r)
        print(r.text)
        if r.text == '{ "success":"true" }':
            print('{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ' ' + _("Modem reports flashing commenced successfully"))
            success = True
            print('{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ' ' + _("Waiting for reboot... Sleeping for %s s") % (flashSleepDelay))
            time.sleep(int(flashSleepDelay))
    else:
        success = True

    if success:
        backUp = False
        attempt = 0
        while not backUp:
            attempt += 1
            print('{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ' ' + _("Connect attempt %i") % (attempt))
            try:
                br.open('http://' + host)
                print ('{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ' Response: ' + str(br.response))
                if br.response.ok:
                    backUp = True
            except Exception:
                print('{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ' ' + _('Failed to connect, attempt %i.  Retrying') % (attempt))
                time.sleep(int(connectRetryDelay))
                pass

        print('{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ' ' + _("Modem up"))

    if not splitCommand:
        runCommand(br, host, token, activeMethod, activeCommand, ddnsService)
    else:
        print('{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ' ' + _("Splitting command up using semicolons"))
        for subCommand in [s for s in activeCommand.split(';') if len(s) > 0]:
            runCommand(br, host, token, activeMethod, subCommand, ddnsService)
            print('{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ' ' + _("Sleeping...") + str(int(interCommandDelay)) + ' seconds')
            time.sleep(int(interCommandDelay))

    result = '{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ' ' + _("Please try a ssh connection now to ") + host + _(" with username root and password root (change password immediately with passwd!)  Rebooting your modem now is recommended to stop any services that have been disabled.")
    print(result)
    return result
