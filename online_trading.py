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

        # some starting time from long ago
        self.transaction_time = datetime.now() - timedelta(weeks=4)

    # implement next functions with your broker API
    def open_long(self):
        self.transaction_time = datetime.now()
        pass

    def open_short(self):
        self.transaction_time = datetime.now()
        pass

    def close_long(self):
        pass

    def close_short(self):
        pass

    def no_pos_open_last_time(self, nr_steps):
        # obliczanie odstępu czasowego z odstępu między słupkami
        # odejmujemy pół okresu jako zapas na niedokładność
        close_offset_time = timedelta(minutes=nr_steps * self.period - self.period / 2)

        if datetime.now() - self.transaction_time > close_offset_time:
            return True
        else:
            return False


def trading():
    client, ssid = login()

    data = get_dataframe(client, symbol, period, 500000)
    strategy.next(data, client)

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
