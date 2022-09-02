import pandas as pd
import pandas_ta as pdta


def atr_stoploss_margin(dataframe, multiplier, atr_period=20):
    atr = pdta.atr(dataframe.High, dataframe.Low, dataframe.Close, length=atr_period).iloc[-1]

    return atr * multiplier
