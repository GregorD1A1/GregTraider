import time
import pandas as pd
from datetime import datetime


# implement you function to get historical data from your broker here
def get_dataframe(symbol, period=5, back_time=500000):

    # function should return pandas dataframe with columns: ['DateTime', 'Close', 'Open', 'Low', 'High', 'Volume']
    return


if __name__ == '__main__':
    # symbol of instrument
    symbol = 'OIL'
    # new bar period in minutes
    period = 5


    dataframe = get_dataframe(symbol=symbol, period=period, back_time=10000000)
    dataframe.to_csv(f'../../historical_data/{symbol}_{period}m.csv', index=False)
