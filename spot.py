# curl -g 'https://api.binance.com/api/v3/ticker/price'
import csv, os
import requests
import datetime as dt
filedir = os.path.dirname(__file__)
os.chdir("./" if filedir=="" else filedir)
import config

dirname = config.dirname

def sendTelegram(text):
    prefix = os.uname()[1] + __file__ + ":"
    params = {'chat_id': config.telegramchatid, 'text': prefix+text, 'parse_mode': 'HTML'}
    resp = requests.post('https://api.telegram.org/bot{}/sendMessage'.format(config.telegramtoken), params)
    resp.raise_for_status()

''' ---------------------------------------------------------------------------------------------
 Http Request
'''

def get_prices():
    url = "https://api.binance.com/api/v3/ticker/price"
    headers = {'Content-Type': 'application/json'}
    resp = requests.get(url,headers=headers)
    print(resp.status_code)
    if resp.status_code!=200:
        sendTelegram("error with %s %d" % (url,resp.status_code))
    ymdstr = dt.datetime.utcnow()
    diclist = resp.json()
    for i in diclist:
        symbol, price = i['symbol'], float(i['price'])
        if 'USDT'!=symbol[-4:]: # on Dec 15th 2023 04:55, BUSD stopped being quoted
            continue
        dic = {'dt': ymdstr, 'price':price}
        filename = dirname + "/spot/" + symbol + ".csv"
        fileexists = os.path.isfile(filename)
        with open(filename, 'a') as f:
            w = csv.writer(f)
            if fileexists == False:
                w.writerow(dic.keys())
            w.writerow(dic.values())

def get_futprices():
    url = "https://testnet.binancefuture.com/dapi/v1/ticker/price"
    headers = {'Content-Type': 'application/json'}
    resp = requests.get(url,headers=headers)
    print(resp.status_code)
    diclist = resp.json()
    for i in diclist:
        try:
            filename = dirname + "/fut/" + i['symbol'] + ".csv"
            fileexists = os.path.isfile(filename)
            with open(filename, 'a') as f:
                w = csv.writer(f)
                if fileexists == False:
                    w.writerow(i.keys())
                w.writerow(i.values())
        except:
            pass

get_prices()
get_futprices()
