import os
import datetime as dt
import sqlite3
import config
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
dirname = config.dirname
remotedir = config.remotedir
outdir = dirname + '/pics/'

def logPrice():
    print("logprice")
    for si in ['BTC', 'ETH', 'AR']:
        si += "BUSD"
        filename = dirname + "/spot/" + si + ".csv"
        df = pd.read_csv(filename)[['dt','price']]
        df['dt'] = pd.to_datetime(df['dt'])
        # df           = df.set_index('dt')
        plt.plot(df['dt'].to_numpy(),np.log(df['price']/df.iloc[-1]['price']), label=si[:-4])
    plt.gcf().autofmt_xdate()
    plt.title("log Price rebased\n%s" % str(df['dt'].iloc[-1])[:16])
    plt.legend()
    plt.savefig(outdir + "ARWEAVE-rt.png")
    plt.close()

def pca_usd():
    print("pca usd")
    tickers = pd.read_csv(dirname+"/topcap.csv")["ticker"]
    roffset = 60*24*90 + 2
    si = "BTC"
    si += "BUSD"
    filename = dirname + "/spot/" + si + ".csv"
    dfbtc = pd.read_csv(filename).tail(roffset)[['dt','price']]
    dfbtc.rename(columns={'price': si}, inplace=True)
    dfbtc   = dfbtc.set_index('dt')
    for si in tickers:
        if si=="BTC":
            continue
        si += "BUSD"
        if 1:
            filename = dirname + "/spot/" + si + ".csv"
            df = pd.read_csv(filename).tail(roffset)[['dt','price']]
            df.rename(columns={'price': si}, inplace=True)
            df   = df.set_index('dt')
            dfbtc = dfbtc.merge(df, on="dt")
    diff = np.log(dfbtc).diff()
    sd = {}
    means = {}
    offset = 60*24*90
    for si in tickers:
        si += "BUSD"
        means[si] = np.mean(diff[si][-offset:])*60*24*365
        sd[si] = np.std(diff[si][-offset:])*np.sqrt(60*24*365)
    ret = pd.DataFrame(data={'symbol':list(sd.keys()), 'means':list(means.values()), 'sd':list(sd.values())})
    ret['sharpe'] = ret['means']/ret['sd']
    ret = ret.sort_values(by="sharpe", ascending=False)
    print("ret usd")
    ret.to_html(outdir + "retspot-usd-rt.html")

    for j in range(14):
        print("close log price %d" %j)
        si = "BTCBUSD"
        plt.plot(pd.to_datetime(dfbtc.index).to_numpy(),np.log(dfbtc[si]/dfbtc.iloc[-1][si]), label=si[:-4])
        si = "ETHBUSD"
        plt.plot(pd.to_datetime(dfbtc.index).to_numpy(),np.log(dfbtc[si]/dfbtc.iloc[-1][si]), label=si[:-4])
        n = j*4
        for i in range(n, n+4):
            r = ret.iloc[i]
            si = r['symbol']
            plt.plot(pd.to_datetime(dfbtc.index).to_numpy(),np.log(dfbtc[si]/dfbtc.iloc[-1][si]), label=si[:-4])
        plt.gcf().autofmt_xdate()
        plt.legend()
        plt.title("log price\n%s" % dfbtc.index[-1][:16])
        plt.savefig(outdir + "cryptoaltlogprice%0d.png" % j)
        plt.close()

    nonzero = diff.columns[np.sum(np.abs(diff[1:]))>0]
    cov = diff[nonzero].dropna().corr()#*60*24*365
    w,v = np.linalg.eigh(cov)

    plt.bar(np.arange(len(w)),sorted(np.sqrt(w), reverse=True))
    plt.title("PCA Eigenvalue Sqrt Size\n%s" % dfbtc.index[-1][:16])
    plt.savefig(outdir + "pcaeigenvalue-rt.png")
    plt.close()
    for i in range(1,3):
        plt.bar(np.arange(len(w)), v.T[-i]*np.sqrt(w[-i]), label="pca %d" %(i))
    plt.xticks(np.arange(len(w)),[p[:-4] for p in nonzero], rotation='vertical')
    plt.title("Correlation PCA on Top Mkt Cap Crypto\n%s" % dfbtc.index[-1][:16])
    plt.legend()
    plt.savefig(outdir + "pcavector-rt.png")
    print("pca vector")
    plt.close()

    nsd = [sd[p] for p in nonzero]
    weights = v.T[-1]/nsd
    weights /= np.sum(weights)
    weights = (np.abs(weights)>=sorted(np.abs(weights))[-20])*weights
    weights /= np.sum(weights)
    weights1 = weights

    weights = v.T[-2]/nsd
    weights = ((weights)>=sorted((weights))[-20])*weights
    weights /= np.sum(weights)

    plt.bar(np.arange(len(w)),weights1, label="pca1")
    plt.bar(np.arange(len(w)),weights, label="pca2")
    plt.xticks(np.arange(len(w)),[p[:-4] for p in nonzero], rotation='vertical')
    plt.title(" Portfolio PCA Top Contributors\n%s" % dfbtc.index[-1][:16])
    plt.legend()
    plt.savefig(outdir + "pcaweights.png")
    print("pca weights")
    plt.close()
    data = pd.DataFrame({'name':nonzero,'pca1weight':weights1,'pca2weight':weights, "sd":nsd })
    data.to_html(outdir + "pcaweights-usd-rt.html")
    return diff, data, sd 


def pca_btc(diff,sd):
    print("pca btc")
    a = pd.DataFrame(diff[diff.columns[1:]])
    for c in a.columns:
        a[c] = diff[c] - diff['BTCBUSD']
    nonzero = a.columns[np.sum(np.abs(a[1:]))>0]
    cov = a[nonzero].dropna().corr()#*60*24*365
    w,v = np.linalg.eigh(cov)

    sd_btc = {}
    for c in diff.columns[1:]:
        sd_btc[c] = np.std(a[c])*np.sqrt(60*24*365)
        
    plt.bar(np.arange(len(w)),sorted(np.sqrt(np.clip(w,0,1e300)), reverse=True))
    plt.title("PCA Eigenvalue Sqrt Size (BTC)\n%s" % diff.index[-1][:16])
    plt.savefig(outdir + "pcaeigenvalue-btc-rt.png")
    plt.close()
    for i in range(1,3):
        plt.bar(np.arange(len(w)), v.T[-i]*np.sqrt(w[-i]), label="pca %d" %(i))
    plt.xticks(np.arange(len(w)),[p[:-4] for p in nonzero], rotation='vertical')
    plt.title("Correlation PCA on Top Mkt Cap Crypto (BTC)\n%s" % diff.index[-1][:16])
    plt.legend()
    plt.savefig(outdir + "pcavector-btc-rt.png")
    plt.close()
    print("pca vector")

    weights = v.T[-1]/list(sd_btc.values())
    weights /= np.sum(weights)
    weights = (np.abs(weights)>=sorted(np.abs(weights))[-20])*weights
    weights /= np.sum(weights)
    weights1 = weights

    weights = v.T[-2]/list(sd_btc.values())
    weights = (np.abs(weights)>=sorted(np.abs(weights))[-20])*weights
    weights /= np.sum(weights)

    plt.bar(np.arange(len(w)),weights1, label="pca1")
    plt.bar(np.arange(len(w)),weights, label="pca2")
    plt.xticks(np.arange(len(w)),[p[:-4] for p in nonzero], rotation='vertical')
    plt.title(" Portfolio PCA Top Contributors (BTC)\n%s" % diff.index[-1][:16])
    plt.legend()
    plt.savefig(outdir + "pcaweights-btc-rt.png")
    print("pca weights")
    plt.close()
    data = pd.DataFrame({'name':a.columns,'pca1weight':weights1,'pca2weight':weights, "sd":list(sd.values())[1:], "sd_btc":list(sd_btc.values()) })
    data.to_html(outdir + "pcaweights-btc-rt.html")
    return data

logPrice()
diff,_, sd = pca_usd()
pca_btc(diff,sd)
os.system('rsync -avzhe ssh %s %s' % (outdir, remotedir))

