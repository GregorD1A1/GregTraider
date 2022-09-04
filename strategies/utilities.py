import pandas as pd
import pandas_ta as pdta


def atr_based_stoploss(dataframe, atr_period, multiplier):
    atrs = pdta.atr(dataframe['High'], dataframe['Low'], dataframe['Close'], length=atr_period)
    atr = atrs.iloc[-1]

    return atr * multiplier