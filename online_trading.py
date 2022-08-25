from online_trading_APIs.xtb.online_trading_xtb import OnlineStrategy
from online_trading_APIs.xtb.download_csv_xtb import get_dataframe
import time
from datetime import datetime
from online_trading_APIs.xtb.passes import userId, password
from online_trading_APIs.xtb.xAPIConnector import login


def create_strategy_list(instruments):
    strategy_list = []
    for instrument in instruments:
        symbol = instrument
        period = instruments[instrument]['period']
        decimal_places = instruments[instrument]['decimal_places']
        volume = instruments[instrument]['volume']
        #min_structure_height = instruments[instrument]['min_height']
        strategy = OnlineStrategy(symbol, period, decimal_places, volume)#, min_structure_height=min_structure_height)
        strategy_list.append(strategy)

    return strategy_list

def trading_all_strategies(strategy_list, trading_periods, current_minute, client, ssid):
    for trading_period in trading_periods:
        if current_minute % trading_period == 0:
            # filtering strategies for that interval
            filtered_strategy_list = list(filter(lambda strategy: (strategy.period == trading_period), strategy_list))
            # main trading function
            trading_strategies(filtered_strategy_list, client, ssid)

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
    instruments = {'UK100': {'period': 5, 'volume': 0.03, 'decimal_places': 1, 'min_height': 15},
                   'US500': {'period': 5, 'volume': 0.01, 'decimal_places': 1, 'min_height': 6},
                   'DE30':  {'period': 5, 'volume': 0.01, 'decimal_places': 1, 'min_height': 25},
                   'FRA40': {'period': 30, 'volume': 0.01, 'decimal_places': 1, 'min_height': 45},
                   'SPA35': {'period': 15, 'volume': 0.01, 'decimal_places': 0, 'min_height': 25},
                   'OIL':   {'period': 5, 'volume': 0.02, 'decimal_places': 2, 'min_height': 0.75},
                   'OIL.WTI': {'period': 30, 'volume': 0.02, 'decimal_places': 2, 'min_height': 2.2},
                   'JAP225': {'period': 30, 'volume': 0.01, 'decimal_places': 0, 'min_height': 250},
                   'SILVER': {'period': 30, 'volume': 0.02, 'decimal_places': 3, 'min_height': 0.2},
                   'GOLD':  {'period': 5, 'volume': 0.02, 'decimal_places': 2, 'min_height': 3},
                   'NED25': {'period': 15, 'volume': 0.01, 'decimal_places': 2, 'min_height': 4},
                   'SUI20': {'period': 15, 'volume': 0.01, 'decimal_places': 0, 'min_height': 50},
                   'US100': {'period': 30, 'volume': 0.01, 'decimal_places': 2, 'min_height': 90},
                   'W20':   {'period': 30, 'volume': 0.10, 'decimal_places': 1, 'min_height': 18},}

    instruments_inside_bar = {
        'GOLD':  {'period': 60, 'volume': 0.02, 'decimal_places': 2},
        'SILVER': {'period': 60, 'volume': 0.02, 'decimal_places': 3},
        'OIL':   {'period': 60, 'volume': 0.02, 'decimal_places': 2},
        'OIL.WTI': {'period': 30, 'volume': 0.02, 'decimal_places': 2},
        'US500': {'period': 60, 'volume': 0.01, 'decimal_places': 1},
        'US100': {'period': 30, 'volume': 0.01, 'decimal_places': 2},
        'NED25': {'period': 60, 'volume': 0.01, 'decimal_places': 2},
        'SUI20': {'period': 60, 'volume': 0.01, 'decimal_places': 0},
        'DE30': {'period': 30, 'volume': 0.01, 'decimal_places': 1},
        'FRA40': {'period': 60, 'volume': 0.01, 'decimal_places': 1},
        'W20':   {'period': 60, 'volume': 0.1, 'decimal_places': 1},
        'JAP225': {'period': 60, 'volume': 0.01, 'decimal_places': 0},
        'UK100': {'period': 60, 'volume': 0.01, 'decimal_places': 1},
        'SPA35': {'period': 60, 'volume': 0.01, 'decimal_places': 0},
        'SOYBEAN': {'period': 60, 'volume': 0.01, 'decimal_places': 2},
    }

    instruments_crypto_weekend_test = {
                   'SANDBOX':  {'period': 5, 'volume': 200, 'decimal_places': 4},
                   'CURVEDAO':   {'period': 5, 'volume': 200.00, 'decimal_places': 4},
                   'SUSHI': {'period': 5, 'volume': 200.00, 'decimal_places': 4},
                   'COSMOS':   {'period': 5, 'volume': 200.00, 'decimal_places': 4},
                   'CARDANO':   {'period': 5, 'volume': 200.00, 'decimal_places': 4},
                   'CHILIZ': {'period': 5, 'volume': 1000, 'decimal_places': 4},
                   'CRONOS': {'period': 5, 'volume': 1000, 'decimal_places': 4},
                   'DECENTRALAND': {'period': 5, 'volume': 200, 'decimal_places': 4},
                   'ETHEREUM': {'period': 5, 'volume': 0.05, 'decimal_places': 3},
                   'ZCASH': {'period': 60, 'volume': 2.00, 'decimal_places': 2},
                   'MOONBEAM': {'period': 30, 'volume': 75.00, 'decimal_places': 4},
                   'TRON':   {'period': 5, 'volume': 2500, 'decimal_places': 5},}

    # define strategy for every instrumewnt and period
    strategy_list = create_strategy_list(instruments_inside_bar)

    # possible trading intervals in minutes.
    # currently should be not bigger then 60, cause of comparing with datetime minutes.
    trading_periods = [5, 15, 30, 60]

    # initializing value of previous minute of trading
    prev_minute = None

    # write down your own login data and comment login data import at top of file
    client, ssid = login(userId, password)
    # set timeout for requests to avoid program suspension if server is not responding
    client.timeout = 100

    while True:
        current_minute = datetime.now().time().minute
        # to not repeat trading for same minute
        if current_minute == prev_minute:
            continue
        # main trading staff
        trading_all_strategies(strategy_list, trading_periods, current_minute, client, ssid)

        prev_minute = current_minute
        time.sleep(10)

    # make something to exit loop manually and close socket
    client.disconnect()
