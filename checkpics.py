import requests
import datetime as dt
import os
import pandas as pd
filedir = os.path.dirname(__file__)
os.chdir("./" if filedir=="" else filedir)
import config
def get_metadata():
    return {'Creator':os.uname()[1] +":"+__file__+":"+str(dt.datetime.utcnow())}
    
def sendTelegram(text):
    prefix = os.uname()[1] + __file__ + ":"
    params = {'chat_id': config.telegramchatid, 'text': prefix+text, 'parse_mode': 'HTML'}
    resp = requests.post('https://api.telegram.org/bot{}/sendMessage'.format(config.telegramtoken), params)
    resp.raise_for_status()

def geturllastmodts(url):
    x = requests.head(url, headers=headers)
    ts = pd.to_datetime(x.headers['Last-Modified']).timestamp()
    del x
    return ts

def getblogentries():
    url = "https://www.markowitzoptimizer.pro/blog"
    x = requests.get(url, headers=headers)
    if x.status_code!=200:
        raise Exception("ERR: %s %d" % (query, x.status_code))
    parsed_body = html.fromstring(x.text)
    del x
    hrefs = set([href for href in parsed_body.xpath('//a/@href') if href[:6]=='/blog/'])
    print("found %d blog entries" % len(hrefs))
    return hrefs

def getimglist(href):
    url = "https://www.markowitzoptimizer.pro/"+href
    x = requests.get(url, headers=headers)
    if x.status_code!=200:
        raise Exception("ERR: %s %d" % (query, x.status_code))
    parsed_body = html.fromstring(x.text)
    del x
    imgs = parsed_body.xpath('//img[@alt="img"]/@src')
    return imgs

def getblogimgts(href):
    imgts = {}
    imgs = getimglist(href)
    oldpng = set(pd.read_csv("oldimg.csv")["img"])
    print("INFO: found %d img in %s                  " % (len(imgs),href), end="\r")
    for img in imgs:
        if img[-4:] not in [".png",".svg"]:
            continue
        if img in oldpng:
            continue
        try:
            imgts[img] = geturllastmodts("https://www.markowitzoptimizer.pro/"+img)
        except KeyError:
            pass
    df = pd.DataFrame(data={"img":imgts.keys(),"ts":imgts.values()})
    df["href"] = href
    df["retrieved"] = dt.datetime.utcnow()
    return df

def getallarticlepicdates():
    hrefs = getblogentries()
    dflist = []
    #pnglist = pd.read_csv("pnglist.csv")
    for i,href in enumerate(hrefs):
        print("INFO: getting %d/%d %s                       " % (i,len(hrefs),href),end="\r")
        dflist.append(getblogimgts(href))
    df = pd.concat(dflist)
    return df

def checkallpics(days=31):
    pnglist = getallarticlepicdates()
    pnglist.to_csv("pnglist.csv",index=False)
    tscut = dt.datetime.utcnow().timestamp()-3600*24*days
    pnglist["updated"] = pd.to_datetime([dt.date.fromtimestamp(ts) for ts in pnglist["ts"]])
    oldpng = pnglist.loc[(pnglist["ts"]<tscut) & (pnglist.img.str.contains(".png|.svg"))]
    oldpng.to_csv("pngold.csv",index=False)
    for i,o in oldpng.iterrows():
        sendTelegram(str(o))
    
if __name__ == "__main__":
    try:
        checkallpics()
    except Exception as e:
        sendTelegram("ERR:"+str(e))

