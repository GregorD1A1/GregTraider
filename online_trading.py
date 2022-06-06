from strategies import RSIStrategy
from download_csv import get_dataframe
import schedule
from xAPIConnector import login
import time
from datetime import datetime, timedelta


class OnlineStrategy(RSIStrategy):
    def __init__(self, symbol, period):
        super().__init__()

        self.symbol = symbol
        self.period = period

        # początkowy czas, bardzo dawni
        self.czas_transakcji = datetime.now() - timedelta(weeks=4)

    def open_long(self):
        self.trade_transaction(self.symbol, type=0, cmd=0)

        self.czas_transakcji = datetime.now()

    def open_short(self):
        self.trade_transaction(self.symbol, type=0, cmd=1)

        self.czas_transakcji = datetime.now()

    def close_long(self):
        arguments = {'openedOnly': True}
        resp = self.client.commandExecute('getTrades', arguments)
        # iterujemy przez listę słowników z pozycjami
        for position in resp['returnData']:
            # sprawdzamy, czy mamy taką pozycję
            if position['symbol'] == self.symbol:
                if position['cmd'] == 0:
                    order_nr = position['order']
                    self.trade_transaction(self.symbol, type=2, order=order_nr)

    def close_short(self):
        arguments = {'openedOnly': True}
        resp = self.client.commandExecute('getTrades', arguments)
        # iterujemy przez listę słowników z pozycjami
        for position in resp['returnData']:
            # sprawdzamy, czy mamy taką pozycję
            if position['symbol'] == self.symbol:
                if position['cmd'] == 1:
                    order_nr = position['order']
                    self.trade_transaction(self.symbol, type=2, order=order_nr)

    def no_pos_open_last_time(self, nr_steps):
        # obliczanie odstępu czasowego z odstępu między słupkami
        # odejmujemy pół okresu jako zapas na niedokładność
        close_offset_time = timedelta(minutes=nr_steps * self.period - self.period / 2)

        if datetime.now() - self.czas_transakcji > close_offset_time:
            return True
        else:
            return False

    # funkcje, związane z API
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
    def trade_transaction(self, symbol, type, cmd=0, order=0, volume=0.01):
        tradeTransInfo = {
            "cmd": cmd,
            "order": order,
            "price": 10,
            "symbol": symbol,
            "type": type,
            "volume": volume
        }
        arguments = {'tradeTransInfo': tradeTransInfo}
        self.client.commandExecute('tradeTransaction', arguments)


def trading():
    # logujemy się
    client, ssid = login()

    data = get_dataframe(client, symbol, period, 500000)
    strategy.next(data, client)

    # odpinamy się
    client.disconnect()


if __name__ == '__main__':
    period = 1
    symbol = 'EOS'
    strategy = OnlineStrategy(symbol, period)
    trading()

    schedule.every(1).minutes.do(trading)
    while True:
        schedule.run_pending()
        time.sleep(1)
