import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as si

# S: spot price, K: strike, T=time to maturity in years, r: risk neutral rate, sigma: volatility
def black_scholes_premium(S, K, T, r, sigma):
    df = np.exp(-r * T) 
    if T<1e-8 or sigma<1e-8:
        call = max(S-K*df, 0.)
        vega = 0
    else:
        sqt = np.sqrt(T)
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqt)
        d2 = d1 - sigma * sqt
        call = S * si.norm.cdf(d1, 0.0, 1.0) - K * si.norm.cdf(d2, 0.0, 1.0) * df
        vega = S * si.norm.pdf(d1, 0.0, 1.0) * sqt 
    put  =  call + K*df-S # use call-put parity for the put
    return call, put, vega
    
def binomial_tree_pricer(r,q,sigma,T,n,S,payoff,american=True,showArrowDebreu=False):
    if showArrowDebreu and n>6:
        print("WARN: you asked to print all tree state price but n is big, turning off printing")
        showArrowDebreu = False
    dt = T/n
    up  = np.exp(sigma*np.sqrt(dt))
    p0 = (up * np.exp((r-q) * dt) - 1) / (up**2 - 1) 
    p1 = 1 - p0
    df = np.exp(-r * dt)
    # initial values at time T
    if showArrowDebreu:
        print("p0=%f u=%f p1=%f d=%f df=%f" % (p0,up,p1,1/up,df))
        print("t","x","arrow-debreu price")
    p = np.zeros(n+1)
    for i in range(n+1): # i from 0 to n incl
        p[i] = payoff(S * up**(2*i - n))
        if showArrowDebreu:
            print(n,i,p[i])
    # move to earlier times
    for j in range(n-1,-1,-1): # j from n-1 to 0 incl
        for i in range(j+1): # i from 0 to j incl
            # discounted expected value of exdiv price
            p[i] = (p0 * p[i+1] + p1 * p[i])*df
            # american payoff
            if american:
                early_exercise = payoff(S * up**(2*i - j))
                p[i] = max(early_exercise,p[i])
            if showArrowDebreu:
                print(j,i,p[i])
    return p[0]

# ---------------------------------------------------------------------------
# display Arrow Debreu Prices
#
r = 0.05
q = 0.02
sigma = 0.15
T = 1/12
n = 2
S = 50
K = S*1.01
print("binomial tree ex-div payoff=S")
binomial_tree_pricer(r,q,sigma,T,n,S,lambda S: S,american=False,showArrowDebreu=True)
print("binomial tree american payoff=S")
binomial_tree_pricer(r,q,sigma,T,n,S,lambda S: S,american=True,showArrowDebreu=True)
print("binomial tree with european put payoff=max(K-S)")
binomial_tree_pricer(r,q,sigma,T,n,S,lambda S: max(K-S,0),american=False,showArrowDebreu=True)
print("binomial tree with american put payoff=max(K-S)")
binomial_tree_pricer(r,q,sigma,T,n,S,lambda S: max(K-S,0),american=True,showArrowDebreu=True)
n = 300

# ---------------------------------------------------------------------------
# numerical precision
#
call,put,_ = black_scholes_premium(S*np.exp(-q*T), K, T, r, sigma)
nbs = [1,2,3,4,5,10,50,100,200,500,1000,2000,5000]
err = {}
for n in nbs:
    err[n] = np.log10(np.abs((call-binomial_tree_pricer(r,q,sigma,T,n,S,lambda S: max(S-K,0),american=False))/K))
n = 300
plt.plot(err.values(),label="error relative to spot")
plt.axhline(y=np.log10(call/S),color="red",label="option price")
plt.xlabel("nb of time steps")
plt.ylabel("log10 relative error")
ax = plt.gca()
ax.set(xticks=range(len(nbs)), xticklabels=nbs)
plt.legend()
plt.title("Binomial Tree Convergence")
plt.show()

# ---------------------------------------------------------------------------
# american vs european pricing, black formula
#
print("risk neutral r=%f dividend yield q=%f" % (r,q))
call,put,_ = black_scholes_premium(S*np.exp(-q*T), K, T, r, sigma)
print("black-scholes formula call=%f put=%f" % (call,put))
print("european call binomial=%f"%binomial_tree_pricer(r,q,sigma,T,n,S,lambda S: max(S-K,0),american=False))
print("american call binomial=%f"%binomial_tree_pricer(r,q,sigma,T,n,S,lambda S: max(S-K,0),american=True))
print("european put binomial=%f"%binomial_tree_pricer(r,q,sigma,T,n,S,lambda S: max(K-S,0),american=False))
print("american put binomial=%f"%binomial_tree_pricer(r,q,sigma,T,n,S,lambda S: max(K-S,0),american=True))
# ---------------------------------------------------------------------------
# comparison with 0 div yield
#
q = 0.00
print("risk neutral r=%f dividend yield q=%f" % (r,q))
call,put,_ = black_scholes_premium(S*np.exp(-q*T), K, T, r, sigma)
print("black-scholes formula call=%f put=%f" % (call,put))
print("european call binomial=%f"%binomial_tree_pricer(r,q,sigma,T,n,S,lambda S: max(S-K,0),american=False))
print("american call binomial=%f"%binomial_tree_pricer(r,q,sigma,T,n,S,lambda S: max(S-K,0),american=True))
print("european put binomial=%f"%binomial_tree_pricer(r,q,sigma,T,n,S,lambda S: max(K-S,0),american=False))
print("american put binomial=%f"%binomial_tree_pricer(r,q,sigma,T,n,S,lambda S: max(K-S,0),american=True))
# ---------------------------------------------------------------------------
# comparison with 0 div yield and 0 risk neutral rate
#
r = 0.00
print("risk neutral r=%f dividend yield q=%f" % (r,q))
call,put,_ = black_scholes_premium(S*np.exp(-q*T), K, T, r, sigma)
print("black-scholes formula call=%f put=%f" % (call,put))
print("european call binomial=%f"%binomial_tree_pricer(r,q,sigma,T,n,S,lambda S: max(S-K,0),american=False))
print("american call binomial=%f"%binomial_tree_pricer(r,q,sigma,T,n,S,lambda S: max(S-K,0),american=True))
print("european put binomial=%f"%binomial_tree_pricer(r,q,sigma,T,n,S,lambda S: max(K-S,0),american=False))
print("american put binomial=%f"%binomial_tree_pricer(r,q,sigma,T,n,S,lambda S: max(K-S,0),american=True))
