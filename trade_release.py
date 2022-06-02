from xAPIConnector import login
from download_csv import get_dataframe
from RSI_strategy import RSI1
import time
import schedule
import numpy as np
import pandas as pd
import pandas_ta as pdta
from datetime import datetime, timedelta


# pobieramy dane o najnowszej historii instrumentu
def get_data(symbol, period, client):
    arguments = {'info': {
        'period': period,
        'start': (time.time() - 64000) * 1000,
        # ta duża liczba to pół roku w sekundach, mnożymy razy 1000 bo potrzebujemy wyniku w milisekundach
        'symbol': symbol
    }}

    resp = client.commandExecute('getChartLastRequest', arguments=arguments)
    decimal_places = resp['returnData']['digits']
    decimal_places_divider = 10 ** decimal_places

    dane = []
    # pętla, obliczająca cenę zamknęcia i tworząca listę z datami i cenami zamknięcia
    for record in resp['returnData']['rateInfos']:
        dane.append({'DatoCzas': record['ctmString'].replace(',', ''),
                     'Open': record['open'] / decimal_places_divider,
                     'Close': (record['open'] + record['close']) / decimal_places_divider,
                     'Low': (record['open'] + record['high']) / decimal_places_divider,
                     'High': (record['open'] + record['low']) / decimal_places_divider,
                     'Volume': record['vol']
                     })
    dane = dane[::-1]

    return dane


class RSIRelease():
    def __init__(self, symbol, period):
        self.rsi_period = 14
        self.default_low_rsi_trsh = 30
        self.default_high_rsi_trsh = 70
        self.rsi_low_trsh_max = 60
        self.rsi_high_trsh_min = 40
        self.rsi_low_trsh_min = 20
        self.rsi_high_trsh_max = 70
        self.close_offset = 10
        self.rsi_peak_detection_offset = 8
        self.ema_period = 200
        self.rsi_per_ema_angle_coeff1 = 100000
        self.rsi_per_ema_angle_coeff2 = 25000

        # obliczanie odstępu czasowego z odstępu między słupkami
        # odejmujemy pół okresu jako zapas na niedokładność
        self.close_offset_time = timedelta(minutes=self.close_offset * period - period / 2)

        # początkowy czas, bardzo dawni
        self.czas_transakcji = datetime.now() - timedelta(weeks=4)
        self.symbol = symbol

    def next(self, dataframe, client):
        # kalkulacja wskaźników
        self.rsi = pdta.rsi(dataframe['Close'], length=14)
        self.ema = pdta.ema(dataframe['Close'], length=250)
        self.kat_pochylenia_ema = self.ema.diff() / self.ema
        self.kat_pochylenia_ema_smoothed = pdta.sma(self.kat_pochylenia_ema, length=10)
        self.client = client

        # akcje
        self.if_close_long()
        self.if_close_short()
        self.if_open_long()
        self.if_open_short()
        
    # sprawdza, czy otwierać pozycję długą
    def if_open_long(self):
        # kupujemy w dołku RSI
        if self.rsi.iloc[-2] < self.lower_trsh() and self.rsi.iloc[-1] > \
                self.rsi.iloc[-2] + self.rsi_peak_detection_offset:
            # by nie otwierać natychmiast po poprzedniej transakcji i nie otwierać przeciw mocnemu trendowi
            if datetime.now() - self.czas_transakcji > self.close_offset_time:
                self.open_long()

    # sprawdza, czy otwierać pozycję krótką
    def if_open_short(self):
        # Sprzedajemy na szczycie RSI
        if self.rsi.iloc[-2] > self.upper_trsh() and self.rsi.iloc[-1] < \
                self.rsi.iloc[-2] - self.rsi_peak_detection_offset:

            # by nie otwierać natychmiast po poprzedniej transakcji
            if datetime.now() - self.czas_transakcji > self.close_offset_time:
                self.open_short()

    # sprawdza, czy zamykać pozycję długą
    def if_close_long(self):
        # Sprzedajemy w dołku RSI
        if self.rsi.iloc[-2] > self.upper_trsh() and self.rsi.iloc[-1] < self.rsi.iloc[-2]:
            print('dzik1')
            # zamykamy pozycję długą
            if self.opened_pos_dir() == 'buy':
                print('dzik2')
                self.close_long()

    # sprawdza, czy zamykać pozycję krótką
    def if_close_short(self):
        # Kupujemy na szczycie RSI
        if self.rsi.iloc[-2] < self.lower_trsh() and self.rsi.iloc[-1] > self.rsi.iloc[-2]:
            print('dzik1')
            # zamykamy pozycję krótką
            if self.opened_pos_dir() == 'sell':
                print('dzik2')
                self.close_short()

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
            print('dzik3')
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
            print('dzik3')
            # sprawdzamy, czy mamy taką pozycję
            if position['symbol'] == self.symbol:
                if position['cmd'] == 1:
                    order_nr = position['order']
                    self.trade_transaction(self.symbol, type=2, order=order_nr)

    # obliczenie progów RSI w zależności od kątu pochylenia EMA
    def upper_trsh(self):
        # górny
        if self.kat_pochylenia_ema_smoothed.iloc[-1] >= 0:
            trsh = self.default_high_rsi_trsh + \
                   self.kat_pochylenia_ema_smoothed.iloc[-1] * self.rsi_per_ema_angle_coeff2
            # próg górny, by nie składał transakcji na szczytkach trendu zgodnie z trendem
            if trsh > self.rsi_high_trsh_max: trsh = self.rsi_high_trsh_max
            return trsh
        # dolny
        else:
            trsh = self.default_high_rsi_trsh + self.kat_pochylenia_ema_smoothed.iloc[-1] * self.rsi_per_ema_angle_coeff1
            # próg górny, by nie składał transakcji na szczytkach trendu zgodnie z trendem
            if trsh < self.rsi_high_trsh_min: trsh = self.rsi_high_trsh_min
            return trsh

    def lower_trsh(self):
        # dolny
        if self.kat_pochylenia_ema_smoothed.iloc[-1] <= 0:
            trsh = self.default_low_rsi_trsh + self.kat_pochylenia_ema_smoothed.iloc[-1] * self.rsi_per_ema_angle_coeff2
            # próg górny, by nie składał transakcji na szczytkach trendu zgodnie z trendem
            if trsh < self.rsi_low_trsh_min: trsh = self.rsi_low_trsh_min
            return trsh
        # górny
        else:
            trsh = self.default_low_rsi_trsh + self.kat_pochylenia_ema_smoothed.iloc[-1] * self.rsi_per_ema_angle_coeff1
            # próg górny, by nie składał transakcji na szczytkach trendu zgodnie z trendem
            if trsh > self.rsi_low_trsh_max: trsh = self.rsi_low_trsh_max
            return trsh

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


period = 5
symbol = 'US30'
strategy = RSIRelease(symbol, period)
trading()

schedule.every(5).minutes.do(trading)
while True:
    schedule.run_pending()
    time.sleep(1)
