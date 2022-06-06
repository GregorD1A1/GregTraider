import time
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


class RSIStrategy():
    def __init__(self):
        self.rsi_period = 14
        self.default_low_rsi_trsh = 30
        self.default_high_rsi_trsh = 70
        self.rsi_low_trsh_max = 60
        self.rsi_high_trsh_min = 40
        self.rsi_low_trsh_min = 20
        self.rsi_high_trsh_max = 70
        self.close_offset = 10
        self.rsi_peak_detection_offset = 8
        self.ema_period = 250
        self.rsi_per_ema_angle_coeff1 = 100000
        self.rsi_per_ema_angle_coeff2 = 25000
        self.plot_indicators_dict = {'rsi': None, 'ema': None, 'rsi_upper_trsh': None, 'rsi_lower_trsh': None}

        # odstęp, po którym ma zacząć się symulacja w przypadku backtradingu
        self.simulation_delay_period = max(self.rsi_period, self.ema_period)

    def next(self, dataframe, client):
        # kalkulacja wskaźników
        self.rsi = pdta.rsi(dataframe['Close'], length=self.rsi_period)
        self.ema = pdta.ema(dataframe['Close'], length=self.ema_period)
        self.kat_pochylenia_ema = self.ema.diff() / self.ema
        self.kat_pochylenia_ema_smoothed = pdta.sma(self.kat_pochylenia_ema, length=10)
        self.rsi_upper_trsh = self.upper_trsh()
        self.rsi_lower_trsh = self.lower_trsh()

        self.plot_indicators_dict = {'rsi': self.rsi.iloc[-1], 'ema': self.ema.iloc[-1], 'rsi_upper_trsh': self.rsi_upper_trsh,
                                     'rsi_lower_trsh': self.rsi_lower_trsh}

        self.client = client

        self.if_close_long()
        self.if_close_short()
        self.if_open_long()
        self.if_open_short()
        
    # sprawdza, czy otwierać pozycję długą
    def if_open_long(self):
        # kupujemy w dołku RSI
        if self.rsi.iloc[-2] < self.rsi_lower_trsh and self.rsi.iloc[-1] > \
                self.rsi.iloc[-2] + self.rsi_peak_detection_offset:
            # by nie otwierać natychmiast po poprzedniej transakcji i nie otwierać przeciw mocnemu trendowi
            if self.no_pos_open_last_time(self.close_offset):
                self.open_long()
                print('open long')
                #return True

    # sprawdza, czy otwierać pozycję krótką
    def if_open_short(self):
        # Sprzedajemy na szczycie RSI
        if self.rsi.iloc[-2] > self.rsi_upper_trsh and self.rsi.iloc[-1] < \
                self.rsi.iloc[-2] - self.rsi_peak_detection_offset:

            # by nie otwierać natychmiast po poprzedniej transakcji
            if self.no_pos_open_last_time(self.close_offset):
                self.open_short()
                print('open short')
                #return True

    # sprawdza, czy zamykać pozycję długą
    def if_close_long(self):
        # Sprzedajemy w dołku RSI
        if self.rsi.iloc[-2] > self.rsi_upper_trsh and self.rsi.iloc[-1] < self.rsi.iloc[-2]:
            # zamykamy pozycję długą
            if self.opened_pos_dir() == 'buy':
                self.close_long()
                print('close long')
                #return True

    # sprawdza, czy zamykać pozycję krótką
    def if_close_short(self):
        # Kupujemy na szczycie RSI
        if self.rsi.iloc[-2] < self.rsi_lower_trsh and self.rsi.iloc[-1] > self.rsi.iloc[-2]:
            # zamykamy pozycję krótką
            if self.opened_pos_dir() == 'sell':
                self.close_short()
                print('close short')
                #return True

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

    def open_long(self):
        pass

    def open_short(self):
        pass

    def close_long(self):
        pass

    def close_short(self):
        pass

    def opened_pos_dir(self):
        pass

    def no_pos_open_last_time(self, steps_offset):
        pass
