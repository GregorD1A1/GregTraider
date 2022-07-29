from online_trading_APIs.xtb.xAPIConnector import login
from online_trading_APIs.xtb.passes import userId, password
import time
import pandas as pd
from datetime import datetime


def get_dataframe(client, symbol, period=5, back_time=500000):
    arguments = {'info': {
        'period': period,
        'start': (time.time() - back_time) * 1000,
        'symbol': symbol
    }}

    resp = client.commandExecute('getChartLastRequest', arguments=arguments)

    decimal_places = resp['returnData']['digits']
    decimal_places_divider = 10 ** decimal_places

    data = []
    # loop for calculating the closing price and creating a list with dates and closing prices
    for record in resp['returnData']['rateInfos']:
        datoczas_object = datetime.strptime(record['ctmString'], '%b %d, %Y, %I:%M:%S %p')
        datoczas_str = datoczas_object.strftime('%H:%M %d.%m.%y')
        data.append({'DateTime': datoczas_str,
                     'Open': record['open'] / decimal_places_divider,
                     'Close': (record['open'] + record['close']) / decimal_places_divider,
                     'High': (record['open'] + record['high']) / decimal_places_divider,
                     'Low': (record['open'] + record['low']) / decimal_places_divider,
                     'Volume': record['vol']
                     })

    return pd.DataFrame(data, columns=['DateTime', 'Close', 'Open', 'Low', 'High', 'Volume'])


if __name__ == '__main__':
    # symbol of instrument
    symbol = 'US2000'
    # new bar period in minutes
    period = 1440

    client, ssid = login(userId, password)

    dataframe = get_dataframe(symbol=symbol, period=period, back_time=10000000, client=client)
    dataframe.to_csv(f'../../historical_data/{symbol}_{period}m.csv', index=False)

    client.disconnect()
