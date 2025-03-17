import requests
import datetime as dt
import json,os,traceback
import numpy as np
from matplotlib import pyplot as plt
from pathlib import Path
filedir = os.path.dirname(__file__)
os.chdir("./" if filedir=="" else filedir)
import config

# see https://github.com/CryptoFacilities/REST-v3-Python/tree/master
outputdir = "krakenpics/" 
baseurl = "https://futures.kraken.com"

def get_metadata():
    return {'Creator':os.uname()[1] +":"+__file__+":"+str(dt.datetime.utcnow())}
    
def sendTelegram(text):
    prefix = os.uname()[1] + ":"+ __file__ + ":"
    params = {'chat_id': config.telegramchatid, 'text': prefix+text, 'parse_mode': 'markdown'}
    resp = requests.post('https://api.telegram.org/bot{}/sendMessage'.format(config.telegramtoken), params)
    resp.raise_for_status()
   
def get_fixed_fut_symbols():
    url = baseurl+'/derivatives/api/v3/instruments'
    resp = requests.get(url) #,params=params)
    if resp.status_code!=200:
        raise sendTelegram("ERR: %s %d" % (url,resp.status_code))
        raise Exception("ERR: %s %d" % (url,resp.status_code))
    result = json.loads(resp.text)
    del resp
    return [d['symbol'] for d in result['instruments']]#

def get_fut_by_ccy(symbols):
    fut_by_ccy = {}
    for s in symbols:
        if s.startswith("FI_") and s[-4:-2] in ["03","06","09","12"]:
            ccy = s[s.index("_")+1:s.rindex("_")]
            if fut_by_ccy.get(ccy) is None:
                fut_by_ccy[ccy] = [s]
            else:
                fut_by_ccy[ccy].append(s)
    for s in symbols:
        ccy = s[s.index("_")+1:]
        if ccy in fut_by_ccy.keys() and s[:3] in ['PI_','PF_']:
            fut_by_ccy[ccy] = [s]+fut_by_ccy[ccy]
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

def tostr(b):
    if np.abs(b)<1:
        return "%.2f%%" % (b*100)
    elif np.abs(b)<10:
        return "%.2f" % b
    elif np.abs(b)<100:
        return "%.1f" % b
    return "%.0f" % b
    
def plot_order_book(ob,symbol,color,bid,ask):
    factor = (bid+ask)/2 if symbol[:3]=="PF_" else 1
    x = np.transpose(ob['bids'])
    plt.step(np.log10(x[0]),np.log10(np.cumsum(x[1])*factor),where='post',label="%s %s-%s" % (symbol,tostr(bid),tostr(ask)),color=color)
    x = np.transpose(ob['asks'])
    plt.step(np.log10(x[0]),np.log10(np.cumsum(x[1])*factor),where='post',color=color)
    
def plot_all_order_books(fut_by_ccy,ob_by_symbol):
    outputdir = "krakenpics/"
    Path(outputdir).mkdir(parents=True, exist_ok=True)
    for ccy in fut_by_ccy.keys():
        colors = ["blue","orange","green","red","cyan"]
        obdates = []
        if len(fut_by_ccy[ccy])>len(colors):
            sendTelegram("too many fut:"+str(fut_by_ccy[ccy]))
            return
        for i,symbol in enumerate(fut_by_ccy[ccy]):
            obdate,ob = ob_by_symbol[symbol]
            if len(ob['bids'])==0:
                print("INFO:skipping no bid"+symbol)
                continue
            if len(ob['asks'])==0:
                print("INFO:skipping no ask"+symbol)
                continue
            bid,ask = get_bidoffer(ob)
            if symbol[:3]=="PF_":
                bid0 = bid
                ask0 = ask
            else:
                bid=bid/bid0-1
                ask=ask/ask0-1
            plot_order_book(ob,symbol,colors[i],bid,ask)
            obdates.append(obdate)
        mindate = np.min(obdates)
        maxdate = np.max(obdates)
        delay = (maxdate-mindate)
        plt.title("%s %s+%.0f\"" %(ccy,str(mindate),delay.total_seconds()))
        plt.legend()
        plt.xlabel("log10 quote")
        plt.ylabel("log10 USD")
        plt.savefig(outputdir+"ob-%s.svg"% ccy,metadata=get_metadata())
        #plt.show()
        plt.close()

if __name__ == "__main__":
    linkhtml = " [Kraken Futures](https://www.markowitzoptimizer.pro/blog/69)"
    try:
        symbols = get_fixed_fut_symbols()
        fut_by_ccy = get_fut_by_ccy(symbols)
        ob_by_symbol = get_orderbooks(fut_by_ccy)
        plot_all_order_books(fut_by_ccy,ob_by_symbol)
        os.system("rsync -avuzhe ssh %s %s" % (outputdir,config.remotedir+'/'+outputdir))
        sendTelegram("updated "+linkhtml)
    except Exception as e:
        msg = "ERR:"+str(e)+traceback.format_exc()+linkhtml
        sendTelegram(msg)
