from strategies.strategy_1_2_3 import Strategy123
from strategies.Inside_bar_strategy import InsideBar
from strategies.Inside_bar_daily import  InsideBarDailyFrequent
from online_trading_APIs.xtb.xAPIConnector import APIStreamClient
from datetime import datetime, timedelta
import time


class OnlineStrategy(InsideBarDailyFrequent):
    def __init__(self, symbol, period, decimal_places, volume, **kwargs):#, min_structure_height):
        super().__init__(**kwargs) #min_structure_height=min_structure_height)

        self.symbol = symbol
        self.decimal_places = decimal_places
        self.volume = volume
        self.period = period
        self.signature = f'{self.__class__.__base__.__name__}_{self.symbol}_{self.period}m'
        self.can_unsubscribe_price_flag = False

        # some starting time from long ago
        self.transaction_time = datetime.now() - timedelta(weeks=4)

    def next(self, dataframe, client, ssid):
        self.client = client
        self.ssid = ssid
        if self.can_unsubscribe_price_flag:
            self.unsubscribe_price()
        super().next(dataframe)

    def open_long(self, volume=0.01, stop_loss=0, take_profit=0):
        self.trade_transaction(self.symbol, type=0, cmd=0, volume=volume, stoploss=stop_loss, takeprofit=take_profit)

        self.transaction_time = datetime.now()

    def open_short(self, volume=0.01, stop_loss=0, take_profit=0):
        self.trade_transaction(self.symbol, type=0, cmd=1, volume=volume, stoploss=stop_loss, takeprofit=take_profit)

        self.transaction_time = datetime.now()

    def close(self):
        arguments = {'openedOnly': True}
        resp = self.client.commandExecute('getTrades', arguments)
        print(f'chcę zamknąć pozycję: {self.signature}')
        # iterujemy przez listę słowników z pozycjami
        for position in resp['returnData']:
            print(f"mamy wśród aktywnych pozycji: {position['customComment']}")
            # sprawdzamy, czy mamy taką pozycję
            if position['customComment'] == self.signature:
                print(f'zamykam: {self.signature}')
                order_nr = position['order']
                self.trade_transaction(self.symbol, type=2, order=order_nr)

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
            "customComment": self.signature,
        }
        arguments = {'tradeTransInfo': tradeTransInfo}
        self.client.commandExecute('tradeTransaction', arguments)

    def subscribe_price(self, interval_ms):
        print('subskrybuję ' + self.symbol)
        # check if not overwriting existing client
        self.sclient = APIStreamClient(ssId=self.ssid, tickFun=self.process_tick_subscribe_data)
        self.sclient.subscribePrice(self.symbol, interval_ms)

    def unsubscribe_price(self):
        print('odsubskrybowuję ' + self.symbol)
        self.can_unsubscribe_price_flag = False
        self.sclient.unsubscribePrice(self.symbol)
        print(self.sclient)
        self.sclient.disconnect()
        print(self.sclient)
        self.transaction_state = 'ready for open'
