import requests
import time
import os
filedir = os.path.dirname(__file__)
os.chdir("./" if filedir=="" else filedir)
import config
dirname = config.dirname 
    
def sendTelegram(text):
    params = {'chat_id': config.telegramchatid, 'text': os.uname()[1] +":"+__file__+":"+text, 'parse_mode': 'markdown'}  
    resp = requests.post('https://api.telegram.org/bot{}/sendMessage'.format(config.telegramtoken), params)
    resp.raise_for_status()
    
def calculate_nexo_tier(usdt_balance, nexo_balance, nexo_price):
    """
    Calculate Nexo loyalty tier based on portfolio composition
    Returns: tier_name, nexo_ratio, total_portfolio_value, platinum_breakeven_price
    """
    # Calculate values
    nexo_value = nexo_balance * nexo_price
    total_portfolio_value = usdt_balance + nexo_value
    
    # Check if portfolio meets minimum $5000 requirement
    if total_portfolio_value < 5000:
        # Calculate price needed to reach $5000 total portfolio
        price_for_5k = (5000 - usdt_balance) / nexo_balance if nexo_balance > 0 else float('inf')
        return "BASE (Under $5k)", 0, total_portfolio_value, price_for_5k
    
    # Calculate NEXO ratio (NEXO vs rest of portfolio)
    rest_of_portfolio = total_portfolio_value - nexo_value
    if rest_of_portfolio == 0:  # Avoid division by zero
        nexo_ratio = 100
    else:
        nexo_ratio = (nexo_value / rest_of_portfolio) * 100
    
    # Calculate price where Platinum is lost (drops to 10% ratio)
    # Formula: (nexo_balance * breakeven_price) / rest_of_portfolio = 0.10
    # Solving for breakeven_price: breakeven_price = (0.10 * rest_of_portfolio) / nexo_balance
    if nexo_balance > 0 and rest_of_portfolio > 0:
        platinum_breakeven_price = (0.10 * rest_of_portfolio) / nexo_balance
    else:
        platinum_breakeven_price = float('inf')  # Can't calculate
    
    # Determine tier
    if nexo_ratio >= 10:
        return "PLATINUM", nexo_ratio, total_portfolio_value, platinum_breakeven_price
    elif nexo_ratio >= 5:
        return "GOLD", nexo_ratio, total_portfolio_value, platinum_breakeven_price
    elif nexo_ratio >= 1:
        return "SILVER", nexo_ratio, total_portfolio_value, platinum_breakeven_price
    else:
        return "BASE", nexo_ratio, total_portfolio_value, platinum_breakeven_price

def check_nexo_price():
    try:
        response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=NEXOUSDT')
        data = response.json()
        price = float(data['price'])
        
        # Your balances (update these values as needed)
        USDT_BALANCE = 67309
        NEXO_BALANCE = 6197
        
        # Calculate tier and target price
        tier, nexo_ratio, total_value, platinum_breakeven = calculate_nexo_tier(USDT_BALANCE, NEXO_BALANCE, price)
        
        # Format the message
        if price < 1.0:
            base_message = f"❌ NEXO ${price:.3f} | {tier} ({nexo_ratio:.1f}%)"
        else:
            base_message = f"✅ NEXO ${price:.3f} | {tier} ({nexo_ratio:.1f}%)"
        
        # Add platinum safety margin info
        if tier == "PLATINUM" and platinum_breakeven != float('inf'):
            safety_margin = ((price - platinum_breakeven) / price) * 100
            safety_message = f" | Safe until <${platinum_breakeven:.3f} ({safety_margin:+.1f}%)"
        elif tier != "PLATINUM" and platinum_breakeven != float('inf'):
            needed_increase = ((platinum_breakeven - price) / price) * 100
            safety_message = f" | Need >${platinum_breakeven:.3f} for Platinum ({needed_increase:+.1f}%)"
        else:
            safety_message = ""
            
        full_message = base_message + safety_message
        print(full_message)
        sendTelegram(full_message)
            
    except Exception as e:
        sendTelegram(f"⚠️ Error: {e}")

# Run once
check_nexo_price()
