from xAPIConnector import login
import time
import pandas as pd


def get_dataframe(client, symbol, period=5, back_time=500000):
    arguments = {'info': {
        'period': period,
        'start': (time.time() - back_time) * 1000,
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

    return pd.DataFrame(dane, columns=['DatoCzas', 'Close', 'Open', 'Low', 'High', 'Volume'])


if __name__ == '__main__':
    symbol = 'US500'
    period = 5
    client, ssid = login()

    dataframe = get_dataframe(symbol=symbol, period=period, back_time=10000000, client=client)
    dataframe.to_csv(f'historical_data/{symbol}_{period}m.csv', index=False)

    client.disconnect()
