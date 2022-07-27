import pandas as pd
import pandas_ta as pdta


class Strategy():
    def __init__(self):
        # parameters


        self.plot_indicators_dict = {}

        # delay for initial indicators calculation
        self.simulation_delay_period = None

    def next(self, dataframe, client):
        # put here all indicators you want to plot in Gregtraider
        self.plot_indicators_dict = {}
        self.client = client
        # write stuff here


    def open_long(self):
        pass

    def open_short(self):
        pass

    def close(self):
        pass
