import pandas as pd
import pandas_ta as pdta


class Strategy123():
    def __init__(self):
        self.prev_point_1_idx = None
        # parameters
        self.nr_of_bars_to_check_minimum = 80
        self.min_formation_len = 6
        self.max_formation_len = 20
        self.min_formation_height = 2.5

        self.plot_indicators_dict = {}

        # delay for initial indicators calculation
        self.simulation_delay_period = self.nr_of_bars_to_check_minimum

    def next(self, dataframe, client):
        # put here all indicators you want to plot in Gregtraider
        self.plot_indicators_dict = {}
        self.client = client
        # write stuff here
        self.open_123(dataframe)

    def open_123(self, dataframe):
        current_idx = dataframe.index[-1]

        point_1_idx = self.find_point_1(dataframe, current_idx)
        if point_1_idx is None:
            return

        if point_1_idx == self.prev_point_1_idx:
            return
        self.prev_point_1_idx = point_1_idx

        point_2_idx = self.find_point_2(dataframe, point_1_idx, current_idx)
        if point_2_idx is None:
            return

        point_3_idx = self.find_point_3(dataframe, point_1_idx, point_2_idx, current_idx)
        if point_3_idx is None:
            return

        print('opening long position...')
        self.open_long()

    def find_point_1(self, dataframe, current_idx):
        minimum_idx = dataframe['Low'][-self.nr_of_bars_to_check_minimum:].idxmin()

        if current_idx - self.max_formation_len <= minimum_idx <= current_idx - self.min_formation_len:
            # check movement strength
            if dataframe['High'][minimum_idx-40: minimum_idx].idxmax() > 4 * self.min_formation_height:
                return minimum_idx
        return None

    def find_point_2(self, dataframe, point_1_idx, current_idx):
        max_idx = dataframe['High'][point_1_idx: current_idx].idxmax()

        # check formation height
        if dataframe['High'][max_idx] - dataframe['Low'][point_1_idx] >= self.min_formation_height:
            if self.confim_point_2(dataframe, max_idx):
                return max_idx
        return None

    def find_point_3(self, dataframe, point_1_idx, point_2_idx, current_idx):
        potential_point_3_idx = dataframe['Low'][point_2_idx: current_idx].idxmin()

        if dataframe['Low'][potential_point_3_idx] > dataframe['Low'][point_1_idx]:
            if self.confim_point_3(dataframe, potential_point_3_idx):
                return potential_point_3_idx
        return None


    def confim_point_2(self, dataframe, point_2_idx):
        if dataframe['High'][point_2_idx: point_2_idx + 4].idxmin() != point_2_idx:
            if dataframe['Low'][point_2_idx: point_2_idx + 4].idxmin() != point_2_idx:
                return True
        return False

    def confim_point_3(self, dataframe, point_3_idx):
        if dataframe['High'][point_3_idx: point_3_idx + 4].idxmax() != point_3_idx:
            if dataframe['Low'][point_3_idx: point_3_idx + 4].idxmax() != point_3_idx:
                return True
        return False

    def open_long(self):
        pass

    def open_short(self):
        pass

    def close(self):
        pass
