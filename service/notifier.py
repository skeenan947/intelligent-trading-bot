import os
import sys
import asyncio
from numpy import nan
import requests

from service.App import *
from common.utils import *

from prometheus_client import Gauge

# Define gauges
asset_quote_gauge = Gauge('trading_bot_asset_quote', 'Asset quote', ['symbol','base_asset'])
portfolio_balance_gauge = Gauge('trading_bot_portfolio_balance', 'Portfolio Balance', ['symbol'])
trade_score_gauge = Gauge('trading_bot_trade_score', 'Signal to buy, hold, or sell', ['symbol','base_asset'])


async def notify_telegram():
    status = App.status
    signal = App.signal
    notification_threshold = App.config["signaler"]["notification_threshold"]
    symbol = App.config["symbol"]
    base_asset =  App.config["base_asset"]
    quote_asset =  App.config["quote_asset"]
    close_price = signal.get('close_price')

    signal_side = signal.get("side")
    score = signal.get('score')

    # How many steps of the score
    score_step_length = 0.05
    score_steps = np.abs(score) // score_step_length

    if score_steps < notification_threshold:
        return

    if score > 0:
        sign = "📈" * int(score_steps - notification_threshold + 1)  # 📈 >
    elif score < 0:
        sign = "📉" * int(score_steps - notification_threshold + 1)  # 📉 <
    else:
        sign = ""

    # Crypto Currency Symbols: https://github.com/yonilevy/crypto-currency-symbols
    if base_asset == "BTC":
        symbol_sign = "₿"
    elif base_asset == "ETH":
        symbol_sign = "Ξ"
    else:
        symbol_sign = base_asset

    message = f"{symbol_sign} {int(close_price):,} {sign} Score: {score:+.2f}"
    message = message.replace("+", "%2B")  # For Telegram to display plus sign

    #if signal_side in ["BUY", "SELL"]:
    #    message = f"*{message}. SIGNAL: {signal_side}*"

    bot_token = App.config["telegram_bot_token"]
    chat_id = App.config["telegram_chat_id"]

    url = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + chat_id + '&parse_mode=markdown&text=' + message

    try:
        response = requests.get(url)
        #response_json = response.json()
    except Exception as e:
        print(f"Error sending notification: {e}")

async def notify_console():
    status = App.status
    signal = App.signal
    notification_threshold = App.config["signaler"]["notification_threshold"]
    symbol = App.config["symbol"]
    base_asset =  App.config["base_asset"]
    quote_asset =  App.config["quote_asset"]
    close_price = signal.get('close_price')

    signal_side = signal.get("side")
    score = signal.get('score')

    # How many steps of the score
    score_step_length = 0.05
    score_steps = np.abs(score) // score_step_length

    if score_steps < notification_threshold:
        return

    if score > 0:
        sign = "📈" * int(score_steps - notification_threshold + 1)  # 📈 >
    elif score < 0:
        sign = "📉" * int(score_steps - notification_threshold + 1)  # 📉 <
    else:
        sign = ""

    # Crypto Currency Symbols: https://github.com/yonilevy/crypto-currency-symbols
    if base_asset == "BTC":
        symbol_sign = "₿"
    elif base_asset == "ETH":
        symbol_sign = "Ξ"
    else:
        symbol_sign = base_asset

    message = f"{symbol_sign} {int(close_price):,} {sign} Score: {score:+.2f}"

    print(message)
    file1 = open("trade-output.txt", "a")  # append mode
    file1.write(f"{message}\n")
    file1.close()

async def notify_prometheus():
    status = App.status
    signal = App.signal
    symbol = App.config["symbol"]
    buy_threshold = App.config["signaler"]["model"]["buy_threshold"]
    sell_threshold = App.config["signaler"]["model"]["sell_threshold"]
    base_asset =  App.config["base_asset"]
    quote_asset =  App.config["quote_asset"]
    close_price = signal.get('close_price')

    signal_side = signal.get("side")
    score = signal.get('score')

    if(score is None or score == 'nan' or score == 'NaN' or score is nan):
        score = 0
    if(sell_threshold < score < buy_threshold):
        signal_type = 'HOLD'
    if score > buy_threshold:
        signal_type = "BUY"
    elif score < sell_threshold:
        signal_type = "SELL"

    trade_score_gauge.labels(symbol, base_asset).set(score)

    asset_quote_gauge.labels(symbol, base_asset).set(close_price)

    portfolio_balance_gauge.labels(base_asset).set((float(App.base_quantity) * float(close_price)))
    portfolio_balance_gauge.labels(quote_asset).set(App.quote_quantity)


if __name__ == '__main__':
    pass
