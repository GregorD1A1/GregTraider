from xAPIConnector import login
import time
import pandas as pd

symbol = 'W20'
period = 60
client, ssid = login()

arguments = {'info': {
    'period': period,   # 30-minutowe odstępy
	'start': (time.time() - 64000000) * 1000,   # ta duża liczba to pół roku w sekundach, mnożymy razy 1000 bo potrzebujemy wyniku w milisekundach
	'symbol': symbol
    }}

resp = client.commandExecute('getChartLastRequest', arguments=arguments)

decimal_places = resp['returnData']['digits']
decimal_places_divider = 10 ** decimal_places

dane = []
# pętla, obliczająca cenę zamknęcia i tworząca listę z datami i cenami zamknięcia
for record in resp['returnData']['rateInfos']:
    dane.append({'DatoCzas': record['ctmString'].replace(',', ''),
                 'Open': record['open']/decimal_places_divider,
                 'Close': (record['open'] + record['close'])/decimal_places_divider,
                 'Low': (record['open'] + record['high'])/decimal_places_divider,
                 'High': (record['open'] + record['low']) / decimal_places_divider,
                 'Volume':record['vol']
                 })

dataframe = pd.DataFrame(dane, columns=['DatoCzas', 'Close', 'Open', 'Low', 'High', 'Volume'])
dataframe.to_csv(f'historical_data/{symbol}_{period}m.csv', index=False)

client.disconnect()