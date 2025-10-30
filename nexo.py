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
    
def check_nexo_price():
    try:
        response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=NEXOUSDT')
        data = response.json()
        price = float(data['price'])
        
        if price < 1.0:
            sendTelegram(f"❌ Nexo fell below 1 - Current price: ${price:.2f}")
        else:
            sendTelegram(f"✅ OK Nexo price ${price:.2f} above 1")
            
    except Exception as e:
        sendTelegram(f"⚠️ Error fetching price: {e}")

# Run once
check_nexo_price()
