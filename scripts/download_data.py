# IMPORTS
import pandas as pd
import math
import os
import json
import time
from datetime import timedelta, datetime
from dateutil import parser
from tqdm import tqdm_notebook #(Optional, used for progress-bars)
import click

#import aiohttp
import asyncio

from binance.client import Client
from binance.streams import BinanceSocketManager
from binance.enums import *

# DO NOT INCLUDE because it has function klines_to_df with the same name but different implementation (name conflict)
#from common.utils import *
from service.App import *

"""
The script is intended for retrieving data from binance server: klines, server info etc.

Links:
https://sammchardy.github.io/binance/2018/01/08/historical-data-download-binance.html
https://sammchardy.github.io/kucoin/2018/01/14/historical-data-download-kucoin.html
"""

### CONSTANTS
binsizes = {"1m": 1, "5m": 5, "1h": 60, "1d": 1440}
batch_size = 750

symbols = ["XBTUSD", "ETHUSD", "XRPZ18", "LTCZ18", "EOSZ18", "BCHZ18", "ADAZ18", "TRXZ18"]

App.client = Client(api_key=App.config["api_key"], api_secret=App.config["api_secret"],tld=App.config["api_tld"])


#
# Historic data
#

@click.command()
@click.option('--config_file', '-c', type=click.Path(), default='', help='Configuration file name')
@click.option('--futures', '-f', default=False, help='Download futures data')
def main(config_file, futures):
    """
    Retrieving historic klines from binance server.

    Client.get_historical_klines
    """
    load_config(config_file)

    symbol = App.config["symbol"]
    tld = App.config["api_tld"]
    freq = "1m"
    save = True
    data_path = Path(App.config["data_folder"])
    if not data_path.is_dir():
        os.mkdir(data_path)

    start_dt = datetime.now()
    print(f"Start downloading klines...")

    print(f"Downloader parameters. Symbol {symbol}. Frequency: {freq}. Save: {save}. Futures: {futures}.")

    if futures:
        filename = f"{symbol}-{freq}-futurs.csv"
    else:
        filename = f"{symbol}-{freq}-klines.csv"
    file_path = (data_path / filename).resolve()

    if file_path.is_file():
        data_df = pd.read_csv(file_path)
        data_df['timestamp'] = pd.to_datetime(data_df['timestamp'])
        print(f"File found. Downloaded data will be appended to the existing file {file_path}")
    else:
        data_df = pd.DataFrame()
        print(f"File not found. All data will be downloaded and stored in newly created file.")

    oldest_point, newest_point = minutes_of_new_data(symbol, freq, data_df)

    delta_min = (newest_point - oldest_point).total_seconds() / 60

    available_data = math.ceil(delta_min / binsizes[freq])

    if oldest_point == datetime.strptime(App.config['start_date'], '%d %b %Y'):
        print('Downloading all available %s data for %s. Be patient..!' % (freq, symbol))
    else:
        print('Downloading %d minutes of new data available for %s, i.e. %d instances of %s data.' % (delta_min, symbol, available_data, freq))

    klines_type=HistoricalKlinesType.SPOT
    if futures:
        klines_type=HistoricalKlinesType.FUTURES
    klines = App.client.get_historical_klines(
        symbol,
        freq,
        oldest_point.strftime("%d %b %Y %H:%M:%S"),
        newest_point.strftime("%d %b %Y %H:%M:%S"),
        klines_type=klines_type
    )

    data_df = klines_to_df(klines, data_df)

    if save:
        data_df.to_csv(file_path)

    print('All caught up..!')

    elapsed = datetime.now() - start_dt
    print(f"Finished downloading data in {int(elapsed.total_seconds())} seconds.")

    return data_df


#
# Static data
#

def get_exchange_info():
    """
    Client.get_exchange_info
    /api/v1/exchangeInfo
    """
    exchange_info = App.client.get_exchange_info()

    with open("exchange_info.json", "w") as file:
        json.dump(exchange_info, file, indent=4)  # , sort_keys=True

    return


def get_account_info():
    orders = App.client.get_all_orders(symbol='BTCUSDT')
    trades = App.client.get_my_trades(symbol='BTCUSDT')
    info = App.client.get_account()
    status = App.client.get_account_status()
    details = App.client.get_asset_details()


def get_market_info():
    depth = App.client.get_order_book(symbol='BTCUSDT')


#
# Utility
#

def minutes_of_new_data(symbol, freq, data):
    if len(data) > 0:  
        #old = parser.parse(data["timestamp"].iloc[-1])
        old = data["timestamp"].iloc[-1]
    else:
        #old = datetime.strptime('1 Aug 2019', '%d %b %Y')
        old = datetime.strptime('1 Jan 2017', '%d %b %Y')

    # List of tuples like this: [1569728580000, '8156.65000000', '8156.66000000', '8154.75000000', '8155.32000000', '4.63288700', 1569728639999, '37786.23994297', 74, '3.18695100', '25993.68396886', '0']
    new_info = App.client.get_klines(symbol=symbol, interval=freq)
    new = pd.to_datetime(new_info[-1][0], unit='ms')
    
    return old, new


# NOTE: this function is different from same in trade.utils
def klines_to_df(klines, df):

    data = pd.DataFrame(klines, columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore' ])
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
    dtypes = {
        'open': 'float64', 'high': 'float64', 'low': 'float64', 'close': 'float64', 'volume': 'float64',
        'close_time': 'int64',
        'quote_av': 'float64',
        'trades': 'int64',
        'tb_base_av': 'float64',
        'tb_quote_av': 'float64',
        'ignore': 'float64',
    }
    data = data.astype(dtypes)

    if df is None or len(df) == 0:
        df = data
    else: 
        df = df.append(data)


    # Drop duplicates
    df = df.drop_duplicates(subset=["timestamp"])
    #df = df[~df.index.duplicated(keep='last')]  # alternatively, drop duplicates in index

    df.set_index('timestamp', inplace=True)

    return df


#
# Streaming functions (do not work - for test purposes)
#

# !!! DOES NOT WORK - do not use
async def get_futures_klines_all(symbol, freq, tld, save = False):
    """
    https://binance-docs.github.io/apidocs/testnet/en/#kline-candlestick-data
    https://api.binance.com - production
    https://testnet.binancefuture.com - test
    GET /fapi/v1/exchangeInfo: to get a list of symbolc
    GET /fapi/v1/klines: symbol*, interval*, startTime, endTime, limit
    """

    filename = f"{symbol}-{freq}-futures.csv"

    if os.path.isfile(filename): 
        data_df = pd.read_csv(filename)
    else: 
        data_df = pd.DataFrame()

    # INFO:
    # API-keys are passed into the Rest API via the X-MBX-APIKEY header
    # curl -H "X-MBX-APIKEY: vmPUZE6mv9SD5VNHk4HlWFsOr6aKE2zvsw0MuIgwCIPy6utIco14y7Ju91duEh8A"
    # API-secret is used to create a HMAC SHA256 signature and then pass it in the signature parameter
    #[linux]$ echo -n "symbol=LTCBTC&side=BUY&type=LIMIT&timeInForce=GTC&quantüity=1&price=0.1&recvWindow=5000&timestamp=1499827319559" | openssl dgst -sha256 -hmac "API-secret"
    #(stdin)= c8db56825ae71d6d79447849e617115f4a920fa2acdcab2b053c4b2838bd6b71 - signature

    import hmac
    import hashlib
    import urllib.parse

    headers = {"X-MBX-APIKEY": binance_api_key}

    params = {}
    query = urllib.parse.urlencode(params)  # These our parameters passed in url
    signature = hmac.new(
        binance_api_secret.encode("utf8"), 
        query.encode("utf8"), 
        digestmod=hashlib.sha256
        ).hexdigest()
    params["signature"] = signature  # We simply add signature to the parametes

    #
    # Test connection (ping server): GET /fapi/v1/ping
    #
    url = "https://api.binance.{tld}/fapi/v1/exchangeInfo"
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, params=params) as response:
            print(response.status)
            result = await response.json()

    print(result)

    #
    # /fapi/v1/klines: symbol*, interval*, startTime, endTime, limit
    #

    start = 1483228800000  # 1483228800000 2017
    end = 1569888000000  # 1569888000000 2019-10-7, 1569888000000 - 2019-10-1

    params = {"symbol": symbol, "interval": freq, "startTime": start, "endTime": end}
    query = urllib.parse.urlencode(params)  # These our parameters passed in url
    signature = hmac.new(
        binance_api_secret.encode("utf8"), 
        query.encode("utf8"), 
        digestmod=hashlib.sha256
        ).hexdigest()
    params["signature"] = signature  # We simply add signature to the parametes

    url = "https://api.binance.{tld}/fapi/v1/klines"

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, params=params) as response:
            print(response.status)
            klines = await response.json()

    data_df = klines_to_df(klines, None)

    if save: 
        data_df.to_csv(filename)

    pass


def check_market_stream():
    """
    Streams: 
    - depth (order book): 
        1) Order book price and quantity depth updates used to locally keep an order book
        2) Top 20 levels of bids and asks
    - kline: The kline/candlestick stream pushes updates to the current klines/candlestick every second
    - ticker, 
    - trade, 
    """
    bm = BinanceSocketManager(App.client)

    # trade socket (one event for each new trade - quote intensive)
    conn_key = bm.start_trade_socket('BTCUSDT', message_fn)
    # {'e': 'trade', 'E': 1570114844102, 's': 'BTCUSDT', 't': 185892444, 'p': '8090.33000000', 'q': '0.00247300', 'b': 682929714, 'a': 682929708, 'T': 1570114844098, 'm': False, 'M': True}

    # depths sockets: either partial book or diff response
    # partial book response
    #conn_key = bm.start_depth_socket('BTCUSDT', message_fn, depth=BinanceSocketManager.WEBSOCKET_DEPTH_5)
    # Output: {'lastUpdateId': 1142001769, 'bids': [['8097.09000000', '0.02469400'], ['8097.07000000', '0.13411300'], ['8097.02000000', '2.00000000'], ['8097.01000000', '0.55502000'], ['8096.91000000', '0.29088400']], 'asks': [['8099.01000000', '0.02640000'], ['8099.02000000', '0.06944200'], ['8099.07000000', '0.08537200'], ['8099.28000000', '0.50000000'], ['8100.54000000', '0.00372200']]}
    # depth diff response
    #conn_key = bm.start_depth_socket('BTCUSDT', message_fn)

    # kline socket
    conn_key = bm.start_kline_socket('BTCUSDT', message_fn, interval=KLINE_INTERVAL_30MINUTE)
    # {'e': 'kline', 'E': 1570114725899, 's': 'BTCUSDT', 'k': {'t': 1570113000000, 'T': 1570114799999, 's': 'BTCUSDT', 'i': '30m', 'f': 185878257, 'L': 185891547, 'o': '8114.88000000', 'c': '8102.91000000', 'h': '8124.50000000', 'l': '8065.00000000', 'v': '1888.20453300', 'n': 13291, 'x': False, 'q': '15291535.03269335', 'V': '1004.09638500', 'Q': '8131835.50527485', 'B': '0'}}

    # Aggregated Trade Socket
    #conn_key = bm.start_aggtrade_socket('BTCUSDT', message_fn)
    # Trade Socket
    #conn_key = bm.start_trade_socket('BTCUSDT', message_fn)

    # Symbol ticker Socket
    #conn_key = bm.start_symbol_ticker_socket('BTCUSDT', message_fn)
    # Output: {'e': '24hrTicker', 'E': 1570114641432, 's': 'BTCUSDT', 'p': '-157.27000000', 'P': '-1.907', 'w': '8247.56704052', 'x': '8247.57000000', 'c': '8090.30000000', 'Q': '0.07074700', 'b': '8089.03000000', 'B': '0.09080800', 'a': '8090.29000000', 'A': '2.00000000', 'o': '8247.57000000', 'h': '8393.00000000', 'l': '8060.00000000', 'v': '28067.68120000', 'q': '231490082.36887328', 'O': 1570028241429, 'C': 1570114641429, 'F': 185628703, 'L': 185890956, 'n': 262254}

    # Ticker Socket
    #conn_key = bm.start_ticker_socket(message_fn)

    # Mini Ticker Socket
    # by default updates every second
    #conn_key = bm.start_miniticker_socket(message_fn)
    # this socket can take an update interval parameter
    # set as 5000 to receive updates every 5 seconds
    #conn_key = bm.start_miniticker_socket(message_fn, 5000)

    #
    # then start the socket manager
    #
    bm.start()

    time.sleep(10)

    # Close individual socket
    bm.stop_socket(conn_key)

    # stop all sockets and end the manager call close after doing this a start call would be required to connect any new sockets.
    bm.close()

    # to exist, stop twisted reactor loop - otherwise the code will NOT exist when you expect
    from twisted.internet import reactor
    reactor.stop()


def message_fn(msg):
    #print(f"Message type: {msg['e']}")
    print(msg)


def check_market_stream_multiplex():
    """
    Symbols in socket name must be lowercase i.e bnbbtc@aggTrade, neobtc@ticker
    """
    bm = BinanceSocketManager(App.client)
    conn_key = bm.start_multiplex_socket(['bnbbtc@aggTrade', 'neobtc@ticker'], multiples_fn)


def multiples_fn(msg):
    print("stream: {} data: {}".format(msg['stream'], msg['data']))


def check_user_stream():
    """
    User streams (requires extra authentication): 
    - Account Update Event - Return account updates
    - Order Update Event - Returns individual order updates
    - Trade Update Event - Returns individual trade updates
    """
    bm = BinanceSocketManager(App.client)

    # The Manager handles keeping the socket alive.
    bm.start_user_socket(user_message_fn)


def user_message_fn(msg):
    print(f"Message type: {msg['e']}")
    print(msg)


if __name__ == '__main__':
    main()
