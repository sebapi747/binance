# curl -g 'https://api.binance.com/api/v3/ticker/price'
import csv, os
import requests
import datetime as dt
import sqlite3
import config

dirname = config.dirname
DATABASE= "quotes.db"

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

def get_prices():
    url = "https://api.binance.com/api/v3/ticker/price"
    headers = {'Content-Type': 'application/json'}
    resp = requests.get(url,headers=headers)
    print(resp.status_code)
    ymdstr = dt.datetime.utcnow()
    diclist = resp.json()
    for i in diclist:
        symbol, price = i['symbol'], float(i['price'])
        if 'BUSD'!=symbol[-4:]:
            continue
        g.db.execute('insert into quotes (dt, symbol, price) values (?, ?, ?)', [ymdstr, symbol, price])
        dic = {'dt': ymdstr, 'price':price}
        filename = dirname + "/spot/" + symbol + ".csv"
        fileexists = os.path.isfile(filename)
        with open(filename, 'a') as f:
            w = csv.writer(f)
            if fileexists == False:
                w.writerow(dic.keys())
            w.writerow(dic.values())
    g.db.commit()

def get_futprices():
    url = "https://testnet.binancefuture.com/dapi/v1/ticker/price"
    headers = {'Content-Type': 'application/json'}
    resp = requests.get(url,headers=headers)
    print(resp.status_code)
    diclist = resp.json()
    for i in diclist:
        try:
            g.db.execute('insert into futures (time, symbol, price, ps) values (?, ?, ?, ?)', [i['time'], i['symbol'], i['price'], i['ps']])
            filename = dirname + "/fut/" + i['symbol'] + ".csv"
            fileexists = os.path.isfile(filename)
            with open(filename, 'a') as f:
                w = csv.writer(f)
                if fileexists == False:
                    w.writerow(i.keys())
                w.writerow(i.values())
        except:
            pass
    g.db.commit()

def cleanup():
    g.db.execute('delete from quotes where symbol not like "%BUSD"')
    g.db.commit()
    g.db.execute('vacuum')

#init_sql_schema()
get_prices()
get_futprices()
#cleanup()
