from online_trading_APIs.xtb.online_trading_xtb import OnlineStrategy, trading_strategies
import time
from datetime import datetime


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


def trading_all_strategies(strategy_list, trading_periods, current_minute):
    for trading_period in trading_periods:
        if current_minute % trading_period == 0:
            # filtering strategies for that interval
            filtered_strategy_list = list(filter(lambda strategy: (strategy.period == trading_period), strategy_list))
            # main trading function
            trading_strategies(filtered_strategy_list)


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

    instruments_inside_bar = {'GOLD':  {'period': 60, 'volume': 0.02, 'decimal_places': 2},
                   'OIL':   {'period': 5, 'volume': 0.02, 'decimal_places': 2},
                   'OIL.WTI': {'period': 30, 'volume': 0.02, 'decimal_places': 2},
                   'SILVER': {'period': 15, 'volume': 0.02, 'decimal_places': 3},
}

    # define strategy for every instrumewnt and period
    strategy_list = create_strategy_list(instruments_inside_bar)

    # possible trading intervals in minutes.
    # currently should be not bigger then 60, cause of comparing with datetime minutes.
    trading_periods = [5, 15, 30, 60]

    # initializing value of previous minute of trading
    prev_minute = None

    while True:
        current_minute = datetime.now().time().minute
        # to not repeat trading for same minute
        if current_minute == prev_minute:
            continue
        # main trading staff
        trading_all_strategies(strategy_list, trading_periods, current_minute)

        prev_minute = current_minute
        time.sleep(10)
