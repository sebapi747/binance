import os,json,time,sqlite3
import datetime as dt
import pandas as pd
import random
import requests
import numpy as np
import pytz
import re
import time
import matplotlib.pyplot as plt
import matplotlib as mpl
filedir = os.path.dirname(__file__)
os.chdir("./" if filedir=="" else filedir)
import config
dirname = config.dirname 
    
def sendTelegram(text):
    params = {'chat_id': config.telegramchatid, 'text': os.uname()[1] +":"+__file__+":"+text, 'parse_mode': 'markdown'}  
    resp = requests.post('https://api.telegram.org/bot{}/sendMessage'.format(config.telegramtoken), params)
    resp.raise_for_status()
    
def get_json_data(ticker):
    baseurl = 'https://api.binance.com'
    endpoint = '/api/v3/klines'
    params = {'symbol':ticker,'interval':'1m',"limit":1000}
    time.sleep(2)
    x = requests.get(url=baseurl+endpoint,params=params)
    if x.status_code!=200:
        raise Exception("ERR: %d %s %s %d" % (x.status_code,baseurl+endpoint,str(params)))
    return x.json()

def processjsontopandas(jsondata):
    colnames = ['opentime','open','high','low','close','volume','closetime','assetvolume',
                'nbtrade','takerbuybasevolume','takerbuyassetvolume','unused']
    df = pd.DataFrame(jsondata, columns=colnames, dtype=float)
    for c in ['opentime','closetime']:
        df[c] = pd.to_datetime(df[c], unit='ms')
    return df[colnames[:-1]]
    
def schema(dbfilename):
    if not os.path.exists(dbfilename):
        print("WARN: missing file %s" % dbfilename)
        #os.system("touch %s" % dbfilename)
        with sqlite3.connect(dbfilename) as con:
            con.execute('''
            create table quoteminutebar (
            opentime datetime primary key,
            open numeric,high numeric,
            low numeric,close numeric,
            volume numeric,
            closetime datetime,
            assetvolume numeric,
            nbtrade numeric,
            takerbuybasevolume numeric,takerbuyassetvolume numeric
            )''')

def insert_df_to_table(df, tablename, cols,con):
    df[cols].to_sql(name=tablename+'_tmp', con=con, if_exists='replace',index=False)
    sql = 'insert or replace into '+tablename+' ('+','.join(cols)+') select '+','.join(cols)+' from '+tablename+'_tmp'
    con.execute(sql)
    con.execute('drop table '+tablename+'_tmp')
    
def getandinsertfutpandas(ticker,dbfilename):
    df = processjsontopandas(get_json_data(ticker))
    print("INFO: %s inserting %d" % (ticker,len(df)),end="\r")
    with sqlite3.connect(dbfilename) as con:
        insert_df_to_table(df, "quoteminutebar", df.columns,con)

def inserttickersymbols(ticker):
    err = ""
    dbfilename = "%s/1minbar/%s.db" % (dirname,ticker)
    schema(dbfilename)
    with sqlite3.connect(dbfilename) as con:
        nbbefore = len(pd.read_sql("select 1 from quoteminutebar", con=con))
    try:
        getandinsertfutpandas(ticker,dbfilename)
    except Exception as e:
        err += "\n%s" % str(e)
    with sqlite3.connect(dbfilename) as con:
        nbafter = len(pd.read_sql("select 1 from quoteminutebar", con=con))
    print(err)
    print("INFO: %s: had %d quotes now %d" % (ticker,nbbefore,nbafter))
    return ticker,nbbefore,nbafter,err

def insertalltickers():
    tickers = ["BTCUSDT","ETHUSDT","LTCUSDT"]
    errors = ""
    out = "\n|ticker|before|after|\n|---|---:|---:|\n"
    for ticker in tickers:
        ticker,nbbefore,nbafter,err = inserttickersymbols(ticker)
        out += "|%s|%d|%d|\n" % (ticker,nbbefore,nbafter)
        errors += err
    sendTelegram(out+errors)

if __name__ == "__main__":
    insertalltickers()
