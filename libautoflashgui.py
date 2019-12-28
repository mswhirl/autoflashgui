# Technicolour modem flash and unlock script by Mark Smith (Whirlpool)
# Forked to make a version that will work with Vodafone Ultrahub (VANT-9) and Ultrahub plus (VBNT-Z) from New Zealand
# Forked at: https://github.com/jameskeenan295/autoflashgui
# Distributed under GPLv3
# Credits to DanielO for the initial work on using SRPv6 to log into these modems (see links below)
# 
# Please see the comments in autoflashgui.py for full details

import mysrp as srp
from urllib.parse import urlencode
import binascii, json, urllib, socket, time, sys
from robobrowser import RoboBrowser
import liblang
from bs4 import BeautifulSoup

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
        br.open('http://' + host)
        token = br.find(lambda tag: tag.has_attr('name') and tag['name'] == 'CSRFtoken')['content']
        debugData.append('Got CSRF token: ' + token)

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

        return True

    except Exception:
        print(_("Authentication failed, debug values are: ") + str(debugData))
        print(_("Exception: ") + str(sys.exc_info()[0]))
        traceback.print_exc()
        raise
        
def runCommand(br, host, token, activeMethod, activeCommand, ddnsService):
    print("Sending command: " + activeCommand)
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
    elif activeMethod == 'VodafoneDDNS':
        postdata = {
            'ddnsStatus': '1',
            'ddnsService': ddnsService,
            'ddnsDomain': 'testzz2.com;' + activeCommand,
            'ddnsUsrname': 'admin',
            'ddnsPswrd': 'notarealpassword',
            'securedns': '0',
            'action': 'SAVE',
            'CSRFtoken': token
            }
        urlpostfix = '/modals/dns-ddns.lp'
    elif activeMethod == 'VodafoneDDNS_http':
        import http.server, socketserver, threading
        Handler = http.server.SimpleHTTPRequestHandler
        port = 8000
        def start_server(path, port=80):
            httpd = socketserver.TCPServer(("", port), Handler)
            httpd.serve_forever()
        # Start the http server in a new thread so we can continue executing our commands
        daemon = threading.Thread(name='daemon_server',
                                  target=start_server,
                                  args=('.', port))
        daemon.setDaemon(True) # Set as a daemon so it will be killed once the main thread is dead.
        daemon.start()
        postdata = {
            'ddnsStatus': '1',
            'ddnsService': ddnsService,
            'ddnsDomain': 'testzz2.com;' + activeCommand,
            'ddnsUsrname': 'admin',
            'ddnsPswrd': 'notarealpassword',
            'securedns': '0',
            'action': 'SAVE',
            'CSRFtoken': token
            }
        urlpostfix = '/modals/dns-ddns.lp'
    else:
        raise Exception(_("Unknown method ") + activeMethod + _(" please check input in GUI"))
    
    r = br.session.post('http://' + host + urlpostfix, data=postdata)
    print(r)
    print(r.content)
    br._update_state(r)
    
    return br.response.ok


def mainScript(host, username, password, flashFirmware, upgradeFilename, flashSleepDelay, activeMethod, activeCommand, splitCommand, ddnsService, connectRetryDelay, interCommandDelay):
    br = RoboBrowser(history=True, parser="html.parser")

    success = False
    if flashFirmware:
        print(_("Authenticating"))
        srp6authenticate(br, host, username, password)
        br.open('http://' + host)
        token = br.find(lambda tag: tag.has_attr('name') and tag['name'] == 'CSRFtoken')['content']
        print(_("Sending flash command to modem"))
        filedata = {'CSRFtoken': token, 'upgradefile': (upgradeFilename, open(upgradeFilename, 'rb'))}
        r = br.session.post('http://' + host + '/modals/gateway-modal.lp?action=upgradefw', files=filedata)
        br._update_state(r)
        print(r.text)
        if r.text == '{ "success":"true" }':
            print(_("Modem reports flashing commenced successfully"))
            success = True
            print(_("Waiting for reboot... Sleeping for %s s") % (flashSleepDelay))
            time.sleep(int(flashSleepDelay))
    else:
        success = True

    if success:
        backUp = False
        attempt = 0
        while not backUp:
            attempt += 1
            print(_("Connect attempt %i") % (attempt))
            try:
                br.open('http://' + host)
                print (br.response)
                if br.response.ok:
                    backUp = True
            except Exception:
                print(_('Failed to connect, attempt %i.  Retrying') % (attempt))
                time.sleep(int(connectRetryDelay))
                pass

        print(_("Modem up"))

    print(_("Authenticating"))
    srp6authenticate(br, host, username, password)
    print('GETing http://' + host + ' to aquire CSRFtoken')
    response = br.session.get('http://' + host)
    print(br.response)
    print('got it')
    # note: there was a bug with br.response.content (and br.find) that prevented finding the CSRF token directly from br.find, so we have to use response, and beautifulsoup. Same thing, just a few more lines of code.
    soup = BeautifulSoup(response.content, 'html.parser')
    token = soup.find(lambda tag: tag.has_attr('name') and tag['name'] == 'CSRFtoken')['value'] # VANT-9 & VBNT-Z CSRFtoken is embeded in javascript and uses 'value' instead of 'content'

    if not splitCommand:
        runCommand(br, host, token, activeMethod, activeCommand, ddnsService)
    else:
        print(_("Splitting command up using semicolons"))
        for subCommand in [s for s in activeCommand.split(';') if len(s) > 0]:
            runCommand(br, host, token, activeMethod, subCommand, ddnsService)
            print(_("Sleeping..."))
            time.sleep(int(interCommandDelay))

    result = _("Please try a ssh connection now to ") + host + _(" with username root and password root (change password immediately with passwd!)  Rebooting your modem now is recommended to stop any services that have been disabled.")
    print(result)
    return result
