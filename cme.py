import requests
import datetime as dt
import os, json, time
import csv
import sqlite3
import config
import pytz
from pathlib import Path
filedir = os.path.dirname(__file__)
os.chdir("./" if filedir=="" else filedir)
def isCMEClosed():
    t1 = dt.datetime.now(pytz.timezone("America/Chicago"))
    dow = t1.weekday()
    return dow==5 or (dow==4 and t1.hour>17) or (dow==6 and t1.hour<18)
if isCMEClosed():
    print("INFO: market closed")
    exit()
dirname = config.dirname
DATABASE= "cme.db"

outputdir = dirname+"cmecsv/"
Path(outputdir).mkdir(parents=True, exist_ok=True)

def sendTelegram(text):
    prefix = os.uname()[1] + __file__ + ":"
    params = {'chat_id': config.telegramchatid, 'text': prefix+text, 'parse_mode': 'HTML'}
    resp = requests.post('https://api.telegram.org/bot{}/sendMessage'.format(config.telegramtoken), params)
    resp.raise_for_status()
''' ---------------------------------------------------------------------------------------------
 SQLite utils
'''
class DBObj(object):
    def __init__(self):
        self.db = sqlite3.connect(dirname + "/" + DATABASE)

g = DBObj()

def cursor_col_names(cursor):
    return [description[0] for description in cursor.description]

def insert_df_to_table(df, tablename, cols):
    df[cols].to_sql(name=tablename+'_tmp', con=g.db, if_exists='replace',index=False)
    sql = 'insert or replace into '+tablename+' ('+','.join(cols)+') select '+','.join(cols)+' from '+tablename+'_tmp'
    g.db.execute(sql)
    g.db.execute('drop table '+tablename+'_tmp')

def init_sql_schema():
    print("init sql tables")
    f = open("schema.sql", mode='r') 
    g.db.cursor().executescript(f.read())
    f.close()
    g.db.commit()


''' ---------------------------------------------------------------------------------------------
 Http Request
'''
# import os, csv, json
# productdic = {}
# for filename in [f for f in os.listdir() if f[-5:]==".json"]:
#     with open(filename,"r") as f:
#         myjson = json.load(f)
#         idic = myjson["quotes"][0]
#         productdic[idic["productId"]] = (idic["productCode"],idic["productName"])
# dic = {}
# for k in sorted(productdic.keys()):
#     dic[k] = productdic[k]
futurecodes = {19: ('HE', 'Lean Hog Futures'),
    22: ('LE', 'Live Cattle Futures'),
    37: ('6A', 'Australian Dollar Futures'),
    42: ('6B', 'British Pound Futures'),
    48: ('6C', 'Canadian Dollar Futures'),
    58: ('6E', 'Euro FX Futures'),
    69: ('6J', 'Japanese Yen Futures'),
    75: ('6M', 'Mexican Peso Futures'),
    133: ('ES', 'E-mini S&P 500 Futures'),
    300: ('ZC', 'Corn Futures'),
    303: ('ZT', '2-Year T-Note Futures'),
    316: ('ZN', '10-Year T-Note Futures'),
    320: ('ZS', 'Soybean Futures'),
    323: ('ZW', 'Chicago SRW Wheat Futures'),
    329: ('ZF', '5-Year T-Note Futures'),
    425: ('CL', 'Crude Oil Futures'),
    437: ('GC', 'Gold Futures'),
    438: ('HG', 'Copper Futures'),
    444: ('NG', 'Henry Hub Natural Gas Futures'),
    458: ('SI', 'Silver Futures'),
    8478: ('BTC', 'Bitcoin Futures'),
    9024: ('MBT', 'Micro Bitcoin Futures')}
 
def get_json_via_requests(code):
    # https://www.cmegroup.com/CmeWS/mvc/Quotes/Future/9024/G?quoteCodes=null&_=1621683984865
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux armv7l) AppleWebKit/537.36 (KHTML, like Gecko) Raspbian Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
        "Upgrade-Insecure-Requests": "1"
    }
    url = 'https://www.cmegroup.com/CmeWS/mvc/Quotes/Future/%d/G' % code
    x = requests.get(url, headers = headers)
    print(x.status_code)
    if x.status_code!=200:
        sendTelegram("error %s %d" % (url,x.status_code))
    return x.json()
    
def get_json_via_curl(code):
    # see https://www.cmegroup.com/markets/products.html#search=Futures&sortDirection=desc&sortField=oi
    curlcmd = '''
    curl 'https://www.cmegroup.com/CmeWS/mvc/quotes/v2/%d?isProtected&_t=1729499259205' \
      -H 'authority: www.cmegroup.com' \
      -H 'accept-language: en-US,en;q=0.9' \
      -H 'sec-ch-ua: "Not_A Brand";v="8", "Chromium";v="120"' \
      -H 'sec-ch-ua-mobile: ?0' \
      -H 'sec-ch-ua-platform: "Linux"' \
      -H 'sec-fetch-dest: document' \
      -H 'sec-fetch-mode: navigate' \
      -H 'sec-fetch-site: none' \
      -H 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7' \
      -H 'cache-control: max-age=0' \
      -H 'sec-fetch-user: ?1' \
      -H 'upgrade-insecure-requests: 1' \
      -H 'user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36' \
      --compressed --silent > cmecurl/cmecurl%d.json
    ''' % (code,code)
    try:
        os.system(curlcmd)
        with open("cmecurl/cmecurl%d.json" % code,"r") as f:
            out = json.load(f)
    except Exception as e:
        raise Exception("ERR:cme fut pb for code=%d err=%s" % (code,str(e)))
    return out

def fraction32quote(last):
    quote = last.split("'")
    if len(quote[1])!=3:
        raise Exception("ERR: quote format unexpected for 32th %s" % last)
    thirtysecondth = float(quote[1][:2])
    if thirtysecondth>=32:
        raise Exception("ERR: cannot understand 32th fraction quote %s %s %d" % (quote[1],last,thirtysecondth))
    last = quote[1][2]
    if last=='+':
        last = 0.5
    else:
        if last<'0' or last>'7':
            raise Exception("ERR: cannot understand 3rd 32th quote=%s" % last)
        last = 0.1 * int(last)
    thirtysecondth += last
    return float(quote[0])+thirtysecondth/32

def fractionquote(last):
    lastsplit = last.split("'")
    if len(lastsplit)==1:
        return float(lastsplit[0])
    if len(lastsplit[1])>1:
        return fraction32quote(last)
    if float(lastsplit[1])>7:
        raise Exception("ERR problem reading 8th quote with "+last)
    return float(lastsplit[0])+float(lastsplit[1])/8
    
def get_fut(code,symbol):
    jsondata = get_json_via_curl(code)
    #jsondata = get_json_via_requests(code)
    cols = ['code', 'expirationMonth','last']
    for r in jsondata['quotes']:
        dic = {}
        for c in cols:
            dic[c] = r[c]
        if dic['last'] == '-':
            continue
        dic['last'] = fractionquote(dic['last'])
        dic['volume'] = float(r['volume'].replace(',','',-1))
        updated = r['updated']
        updated = updated.replace(" CT<br /> ", " ")
        dic['updated'] = str(dt.datetime.strptime(updated[:19], '%Y-%m-%dT%H:%M:%S'))
        dic['expiry'] = str((dt.datetime.strptime(r['lastTradeDate'][:19],'%Y-%m-%dT%H:%M:%S')))
        i = dic
        try:
            # this insertion will throw exception due to unique index if data already there
            g.db.execute('insert into cmefut (code, expirationMonth, last, volume, updated, expiry) values (?, ?, ?, ?, ?, ?)', 
                [i['code'], i['expirationMonth'], i['last'], i['volume'], i['updated'], i['expiry']])
            filename = "%s%s.csv" % (outputdir,symbol)
            fileexists = os.path.isfile(filename)
            with open(filename, 'a') as f:
                w = csv.writer(f)
                if fileexists == False:
                    w.writerow(dic.keys())
                    print("INFO: creating output file %s" % filename)
                w.writerow(dic.values())
        except Exception as e:
            print("ERR: %s %s" %(str(e),str(dic)))
            pass
    g.db.commit()

if __name__ == "__main__":
    #init_sql_schema()
    errmsg  = ""
    for code,(symbol,desc) in futurecodes.items():
        try:
            print(code,symbol,desc)
            get_fut(code,symbol)
            time.sleep(3)
        except Exception as e:
            errmsg += "\nERR: %s" % str(e)
    print(errmsg)
    sendTelegram(errmsg)

    
