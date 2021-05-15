# curl -g 'https://api.binance.com/api/v3/ticker/price'
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
        g.db.execute('insert into quotes (dt, symbol, price) values (?, ?, ?)', [ymdstr, symbol, price])
    g.db.commit()

''' ---------------------------------------------------------------------------------------------
 read data (requires pandas)
'''
def read_data():
    df = pd.read_sql_query("select * from quotes", g.db)
    print(df)

#init_sql_schema()
get_prices()
