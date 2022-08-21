from online_trading_APIs.xtb.online_trading_xtb import OnlineStrategy
from strategies.Inside_bar_daily import InsideBarDailyBase
from online_trading_APIs.xtb.download_csv_xtb import get_dataframe
import time
from datetime import datetime
from online_trading_APIs.xtb.passes import userId, password
from online_trading_APIs.xtb.xAPIConnector import login


def create_base_strategy_list(instruments):
    strategy_list = []
    for instrument in instruments:
        symbol = instrument
        period = instruments[instrument]['period_base']
        strategy = InsideBarDailyBase(symbol, period)
        strategy_list.append(strategy)

    return strategy_list


def create_frequent_strategy_list(instruments, base_strategy_list):
    strategy_list = []
    for nr, instrument in enumerate(instruments):
        symbol = instrument
        period = instruments[instrument]['period_freq']
        decimal_places = instruments[instrument]['decimal_places']
        volume = instruments[instrument]['volume']
        base_strategy = base_strategy_list[nr]
        strategy = OnlineStrategy(symbol, period, decimal_places, volume, base_strategy=base_strategy)
        strategy_list.append(strategy)

    return strategy_list


def wait_for_not_too_frequent_sending_requests(prev_time):
    while time.perf_counter() - prev_time < 0.1:
        time.sleep(0.05)

def trading_strategies(strategy_list, client, ssid):
    # initializing time difference counter
    time_prev_request = time.perf_counter() - 1

    for strategy in strategy_list:
        # to avoid "request too often" error
        wait_for_not_too_frequent_sending_requests(time_prev_request)

        data = get_dataframe(client, strategy.symbol, strategy.period, 500000)

        # not sending requests too frequent staff
        time_prev_request = time.perf_counter()
        wait_for_not_too_frequent_sending_requests(time_prev_request)

        strategy.next(data, client, ssid)

        # final time measuring
        time_prev_request = time.perf_counter()

if __name__ == '__main__':
    instruments_inside_bar = {
        # metal commodities
        'GOLD':  {'period_base': 1440, 'period_freq': 5, 'volume': 0.05, 'decimal_places': 2},
        'SILVER': {'period_base': 1440, 'period_freq': 5, 'volume': 0.02, 'decimal_places': 3},
        # energy commodities
        'OIL':   {'period_base': 1440, 'period_freq': 5, 'volume': 0.02, 'decimal_places': 2},
        'OIL.WTI': {'period_base': 1440, 'period_freq': 5, 'volume': 0.02, 'decimal_places': 2},
        'NATGAS':   {'period_base': 1440, 'period_freq': 5, 'volume': 0.01, 'decimal_places': 3},
        'GASOLINE': {'period_base': 1440, 'period_freq': 5, 'volume': 0.02, 'decimal_places': 2},
        # agricultural commodities
        'SOYBEAN': {'period_base': 1440, 'period_freq': 5, 'volume': 0.01, 'decimal_places': 2},
        'COFFEE': {'period_base': 1440, 'period_freq': 5, 'volume': 0.01, 'decimal_places': 2},
        # indexes Europe
        'NED25': {'period_base': 1440, 'period_freq': 5, 'volume': 0.01, 'decimal_places': 2},
        'SUI20': {'period_base': 1440, 'period_freq': 5, 'volume': 0.01, 'decimal_places': 0},
        'DE30': {'period_base': 1440, 'period_freq': 5, 'volume': 0.01, 'decimal_places': 1},
        'EU50': {'period_base': 1440, 'period_freq': 5, 'volume': 0.11, 'decimal_places': 1},
        'W20': {'period_base': 1440, 'period_freq': 5, 'volume': 0.3, 'decimal_places': 1},
        # indexes America
        'US100': {'period_base': 1440, 'period_freq': 5, 'volume': 0.02, 'decimal_places': 2},
        # indexes Asia and Oceania
        'AUS200': {'period_base': 1440, 'period_freq': 5, 'volume': 0.02, 'decimal_places': 0},
        'JAP225': {'period_base': 1440, 'period_freq': 5, 'volume': 0.01, 'decimal_places': 0},
        'CH50cash': {'period_base': 1440, 'period_freq': 5, 'volume': 0.01, 'decimal_places': 1},
        # krypto
        'ETHEREUM': {'period_base': 1440, 'period_freq': 5, 'volume': 0.1, 'decimal_places': 3},
        'TRON': {'period_base': 1440, 'period_freq': 5, 'volume': 2500, 'decimal_places': 5},

                              }

    # define strategy for every instrumewnt and period
    base_strategy_list = create_base_strategy_list(instruments_inside_bar)
    frequent_strategy_list = create_frequent_strategy_list(instruments_inside_bar, base_strategy_list)

    # initializing value of previous minute of trading
    prev_minute = None
    prev_hour = None

    # write down your own login data and comment login data import at top of file
    client, ssid = login(userId, password)
    # set timeout for requests to avoid program suspension if server is not responding
    client.timeout = 100

    while True:
        current_minute = datetime.now().time().minute
        current_hour = datetime.now().time().hour
        # to not repeat trading for same minute
        # main trading staff


        if current_hour == 2 and current_hour != prev_hour:
            trading_strategies(base_strategy_list, client, ssid)

        if current_minute % 5 == 0 and current_minute != prev_minute:
            trading_strategies(frequent_strategy_list, client, ssid)

        prev_minute = current_minute
        prev_hour = current_hour
        time.sleep(10)

    # make something to exit loop manually and close socket
    client.disconnect()
