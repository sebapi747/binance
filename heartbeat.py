import os
import requests
import config
filedir = os.path.dirname(__file__)
os.chdir("./" if filedir=="" else filedir)

def sendTelegram(text):
    prefix = os.uname()[1] + __file__ + ":"
    params = {'chat_id': config.telegramchatid, 'text': prefix+text, 'parse_mode': 'HTML'}
    resp = requests.post('https://api.telegram.org/bot{}/sendMessage'.format(config.telegramtoken), params)
    resp.raise_for_status()

def checkheartbeat():
    for h in ["gaia","themis","darkstar","hermes","horus"]:
        os.system("fping %s > resolved.%s" % (h,h))
        with open("resolved.%s" % h,"r") as f:
            line = f.readline()
            if "alive" in line:
                print("INFO:",line)
            else:
                print("ERR:",line)
                sendTelegram("%s not found amongst hosts" % h)
                        
checkheartbeat()
