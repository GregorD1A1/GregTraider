from strategies.strategy_1_2_3 import Strategy123
from strategies.Inside_bar_strategy import InsideBar
from online_trading_APIs.xtb.download_csv_xtb import get_dataframe
from online_trading_APIs.xtb.xAPIConnector import login, APIStreamClient
from datetime import datetime, timedelta
from online_trading_APIs.xtb.passes import userId, password
import time


class OnlineStrategy(InsideBar):
    def __init__(self, symbol, period, decimal_places, volume):#, min_structure_height):
        super().__init__() #min_structure_height=min_structure_height)

        self.symbol = symbol
        self.decimal_places = decimal_places
        self.volume = volume
        self.period = period

        # some starting time from long ago
        self.transaction_time = datetime.now() - timedelta(weeks=4)

    def open_long(self, volume=0.01, stop_loss=0, take_profit=0):
        self.trade_transaction(self.symbol, type=0, cmd=0, volume=volume, stoploss=stop_loss, takeprofit=take_profit)

        self.transaction_time = datetime.now()

    def open_short(self, volume=0.01, stop_loss=0, take_profit=0):
        self.trade_transaction(self.symbol, type=0, cmd=1, volume=volume, stoploss=stop_loss, takeprofit=take_profit)

        self.transaction_time = datetime.now()

    def close(self):
        arguments = {'openedOnly': True}
        resp = self.client.commandExecute('getTrades', arguments)
        # iterujemy przez listę słowników z pozycjami
        for position in resp['returnData']:
            # sprawdzamy, czy mamy taką pozycję
            if position['symbol'] == self.symbol:
                order_nr = position['order']
                self.trade_transaction(self.symbol, type=2, order=order_nr)

    def no_pos_open_last_time(self, nr_steps):
        # calculating time offset between data bars
        # substracting half of period as provision for inaccuraccy
        close_offset_time = timedelta(minutes=nr_steps * self.period - self.period / 2)

        if datetime.now() - self.transaction_time > close_offset_time:
            return True
        else:
            return False

    # API related fcns
    def opened_pos_dir(self):
        arguments = {'openedOnly': True}
        resp = self.client.commandExecute('getTrades', arguments)
        # iterujemy przez listę słowników z pozycjami
        for position in resp['returnData']:
            # sprawdzamy, czy mamy taką pozycję
            if position['symbol'] == self.symbol:
                if position['cmd'] == 0:
                    return 'buy'
                elif position['cmd'] == 1:
                    return 'sell'
        return False

    ## type: 0 - open, 2 - close; cmd: 0 - buy, 1 - sell
    def trade_transaction(self, symbol, type, cmd=0, order=0, volume=0.01, stoploss=0, takeprofit=0):
        stoploss = round(stoploss, self.decimal_places)
        takeprofit = round(takeprofit, self.decimal_places)
        tradeTransInfo = {
            "cmd": cmd,
            "order": order,
            "price": 10,
            "symbol": symbol,
            "type": type,
            "volume": volume,
            "sl": stoploss,
            "tp": takeprofit,
        }
        arguments = {'tradeTransInfo': tradeTransInfo}
        self.client.commandExecute('tradeTransaction', arguments)

    def subscribe_price(self, interval_ms):
        print('subskrybuję')
        self.client, ssid = login(userId, password)
        self.sclient = APIStreamClient(ssId=ssid, tickFun=self.process_tick_subscribe_data)
        self.sclient.subscribePrice(self.symbol, interval_ms)



    def unsubscribe_price(self):
        print('odsubskrybowuję')
        super().unsubscribe_price()
        self.sclient.disconnect()
        self.client.disconnect()


def wait_for_not_to_frequent_sending_requests(prev_time):
    while time.perf_counter() - prev_time < 0.1:
        time.sleep(0.05)

def trading_strategies(strategy_list):
    # optimalization, to not login for empty intervals
    if not strategy_list:
        return
    # write down your own login data and comment login data import at top of file
    client, ssid = login(userId, password)
    # set timeout for requests to avoid program suspension if server is not responding
    client.timeout = 100

    # initializing time difference counter
    time_prev_request = time.perf_counter() - 1

    for strategy in strategy_list:
        # to avoid "request too often" error
        wait_for_not_to_frequent_sending_requests(time_prev_request)

        data = get_dataframe(client, strategy.symbol, strategy.period, 500000)

        # not sendinhg requests too frequent staff
        time_prev_request = time.perf_counter()
        wait_for_not_to_frequent_sending_requests(time_prev_request)

        strategy.next(data, client)

        # final time measuring
        time_prev_request = time.perf_counter()

    client.close()