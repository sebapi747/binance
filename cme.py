import requests
import datetime as dt
import os, json, time
import csv
import sqlite3
import config

dirname = config.dirname
DATABASE= "cme.db"

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
futurecodes = {"mini SP":133,"micro BTC":9024,"BTC":8478,
    "Corn":300,"Soybean":320,"Chicago Wheat":323,
    "Lean Hog":19,"Live Cattle":22,
    "5Y T-Note":329,
    "Crude Oil":425,"Nat Gas":444,
    "AUD FX":37,"GBP FX":42,"CAD FX":48,"Euro FX":58,"Yen FX":69,"MXN FX":75,
    "Gold":437,"Copper":438,"Silver":458}

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
    curlcmd = '''
    curl 'https://www.cmegroup.com/CmeWS/mvc/Quotes/Future/%d/G?quoteCodes=null&_=1621683984865' \
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
      --compressed --silent > cmecurl%d.json
    ''' % (code,code)
    try:
        os.system(curlcmd)
        with open("cmecurl%d.json" % code,"r") as f:
            out = json.load(f)
    except Exception as e:
        sendTelegram("ERR:cme fut pb for code=%d err=%s" % (code,str(e)))
    return out

def fraction8quote(last):
    lastsplit = last.split("'")
    if len(lastsplit)==1:
        return float(lastsplit[0])
    if float(lastsplit[1])>7:
        raise Exception("ERR problem with "+last)
    return float(lastsplit[0])+float(lastsplit[1])/8
    
def get_fut(code):
    jsondata = get_json_via_curl(code)
    cols = ['code', 'expirationMonth','last']
    for r in jsondata['quotes']:
        dic = {}
        for c in cols:
            dic[c] = r[c]
        if dic['last'] == '-':
            continue
        dic['last'] = fraction8quote(dic['last'])
        dic['volume'] = float(r['volume'].replace(',','',-1))
        updated = r['updated']
        updated = updated.replace(" CT<br /> ", " ")
        dic['updated'] = str(dt.datetime.strptime(updated, '%H:%M:%S %d %b %Y'))
        dic['expiry'] = str((dt.datetime.strptime(r['lastTradeDate']['default24'][0:10],'%m/%d/%Y')))
        i = dic
        try:
            g.db.execute('insert into cmefut (code, expirationMonth, last, volume, updated, expiry) values (?, ?, ?, ?, ?, ?)', [i['code'], i['expirationMonth'], i['last'], i['volume'], i['updated'], i['expiry'] ])
        except Exception as e:
            print("ERR: %s %s" %(str(e),str(dic)))
            pass
    g.db.commit()

#init_sql_schema()
for fut,code in futurecodes.items():
    print(fut,code)
    get_fut(code)
    time.sleep(3)
