import requests
import datetime as dt
import json,os
import numpy as np
from matplotlib import pyplot as plt
from pathlib import Path
filedir = os.path.dirname(__file__)
os.chdir("./" if filedir=="" else filedir)
import config

# see https://github.com/CryptoFacilities/REST-v3-Python/tree/master
outputdir = "krakenpics/" 
baseurl = "https://futures.kraken.com"

def sendTelegram(text):
    prefix = os.uname()[1] + __file__ + ":"
    params = {'chat_id': config.telegramchatid, 'text': prefix+text, 'parse_mode': 'HTML'}
    resp = requests.post('https://api.telegram.org/bot{}/sendMessage'.format(config.telegramtoken), params)
    resp.raise_for_status()
   
def get_fixed_fut_symbols():
    url = baseurl+'/derivatives/api/v3/instruments'
    resp = requests.get(url) #,params=params)
    if resp.status_code!=200:
        sendTelegram("ERR: %s %d" % (url,resp.status_code))
        raise Exception("ERR: %s %d" % (url,resp.status_code))
    result = json.loads(resp.text)
    del resp
    return [d['symbol'] for d in result['instruments'] if d['symbol'].startswith("FI_") and d['symbol'][-4:-2] in ["03","06","09","12"]]

def get_fut_by_ccy(symbols):
    fut_by_ccy = {}
    for s in symbols:
        ccy = s[s.index("_")+1:s.rindex("_")]
        if fut_by_ccy.get(ccy) is None:
            fut_by_ccy[ccy] = [s]
        else:
            fut_by_ccy[ccy].append(s)
    return fut_by_ccy

def get_order_book(symbol):
    url=baseurl+"/derivatives/api/v3/orderbook"
    resp = requests.get(url,params={'symbol':symbol})
    if resp.status_code!=200:
        sendTelegram("ERR: %s %d" % (url,resp.status_code))
        raise Exception("ERR: %s %d" % (url,resp.status_code))
    obdate = dt.datetime.strptime(resp.headers['Date'], "%a, %d %b %Y %H:%M:%S %Z")
    result = json.loads(resp.text)
    del resp
    return obdate,result['orderBook']

def get_orderbooks(fut_by_ccy):
    ob_by_symbol = {}
    for ccy in fut_by_ccy.keys():
        for i,symbol in enumerate(fut_by_ccy[ccy]):
            ob_by_symbol[symbol] = get_order_book(symbol)
    return ob_by_symbol

def get_bidoffer(ob):
    bid,ask = ob['bids'][0][0],ob['asks'][0][0]
    return bid,ask

def plot_order_book(ob,symbol,color,obdate):
    bid,ask = get_bidoffer(ob)
    x = np.transpose(ob['bids'])
    plt.step(x[0],np.cumsum(x[1]),where='post',label="%s %.0f-%.0f %s" % (symbol,bid,ask,str(obdate)),color=color)
    x = np.transpose(ob['asks'])
    plt.step(x[0],np.cumsum(x[1]),where='post',color=color)
    
def plot_all_order_books(fut_by_ccy,ob_by_symbol):
    Path(outputdir).mkdir(parents=True, exist_ok=True)
    for ccy in fut_by_ccy.keys():
        colors = ["blue","orange","green","red"]
        for i,symbol in enumerate(fut_by_ccy[ccy]):
            obdate,ob = ob_by_symbol[symbol]
            plot_order_book(ob,symbol,colors[i],obdate)
        plt.title(ccy)
        plt.legend()
        plt.savefig(outputdir+"ob-%s.svg"% ccy)
        plt.close()

if __name__ == "__main__":
    symbols = get_fixed_fut_symbols()
    fut_by_ccy = get_fut_by_ccy(symbols)
    ob_by_symbol = get_orderbooks(fut_by_ccy)
    plot_all_order_books(fut_by_ccy,ob_by_symbol)
    os.system("rsync -avuzhe ssh %s %s" % (outputdir,config.remotedir+'/'+outputdir))
