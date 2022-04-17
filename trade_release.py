from xAPIConnector import login
from download_csv import get_dataframe
from RSI_strategy import RSI1
import time
import schedule
import numpy as np
import pandas as pd
import pandas_ta as pdta


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


class RSIRelease(RSI1):
    def __init__(self, dataframe):
        super(RSIRelease, self).__init__()
        self.rsi = pdta.rsi(dataframe['Close'], length=14)
        self.ema = pdta.ema(dataframe['Close'], length=250)


def trading():
    # logujemy się
    client, ssid = login()

    data = get_dataframe(client, 'US500', 5, 500000)
    strategy = RSIRelease(data)

    # odpinamy się
    client.disconnect()


trading()

schedule.every(5).minutes.do(trading)
while True:
    # Checks whether a scheduled task
    # is pending to run or not
    schedule.run_pending()
    time.sleep(1)
