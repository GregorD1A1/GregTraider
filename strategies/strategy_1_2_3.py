import pandas as pd
import pandas_ta as pdta


class Strategy123():
    def __init__(self, min_structure_height):
        self.prev_point_1_time = None
        # parameters
        self.max_structure_len = 20
        self.min_structure_len = 6
        self.nrBarsToCheckMinimum = 50 + self.max_structure_len
        self.min_structure_height = min_structure_height
        self.volume = None

        self.plot_indicators_dict = {}

        # delay for initial indicators calculation
        self.simulation_delay_period = self.nrBarsToCheckMinimum

    def next(self, dataframe, client):
        # put here all indicators you want to plot in Gregtraider
        self.plot_indicators_dict = {}

        self.client = client

        # check if it needs to unsubscribe something
        if self.can_unsubscribe_price_flag:
            self.unsubscribe_price()

        self.open_1_2_3(dataframe, 'low')
        self.open_1_2_3(dataframe, 'high')

    def open_1_2_3(self, dataframe, structure_side):
        current_idx = dataframe.index[-1]

        point_1_idx = self.find_point_1(dataframe, current_idx, structure_side)
        if point_1_idx is None:
            return

        point_2_idx = self.find_point_2(dataframe, current_idx, point_1_idx, structure_side)
        if point_2_idx is None:
            return

        # looking for point 3
        if not self.check_if_current_idx_is_potential_point_3(dataframe, current_idx, point_1_idx, point_2_idx, structure_side):
            return

        if not self.confirm_strong_movement_before_point_1(dataframe, point_1_idx, point_2_idx, current_idx, structure_side):
            return

        self.structure_height = self.formation_height(dataframe, point_1_idx, point_2_idx, structure_side)
        # check if structure is high enough
        if not self.check_height(point_1_idx, current_idx):
            return

        # check if current price not lowest then point 3 minimum
        if not self.check_current_price_not_below_point_3(dataframe, current_idx, structure_side):
            return

        # check if program not looking for same formation
        point_1_time = dataframe.iloc[point_1_idx]["DateTime"]
        if point_1_time == self.prev_point_1_time:
            return

        # check if program is returning for point 3 is high enough
        if not self.check_return_height_for_point_3(dataframe, point_1_idx, point_2_idx, current_idx, structure_side):
            return

        self.calculate_stoploss_and_target_values(dataframe, point_1_idx, point_2_idx, current_idx, structure_side)

        #if structure_side == 'low' and dataframe['Close'][current_idx] < dataframe['Low'][point_2_idx]:
        #    return
        #elif structure_side == 'high' and dataframe['Close'][current_idx] > dataframe['High'][point_2_idx]:
        #    return

        self.prev_point_1_time = point_1_time

        self.subscribed_strucure_side = structure_side
        self.point_3_high = dataframe['High'][current_idx]
        self.point_3_low = dataframe['Low'][current_idx]
        if structure_side == 'low':
            self.subscribe_price(1000, self.point_3_high, self.point_3_low)
        else:
            self.subscribe_price(1000, self.point_3_low, self.point_3_high)

        print(f'Point1: {dataframe.iloc[point_1_idx]["DateTime"]}, Point2: {dataframe.iloc[point_2_idx]["DateTime"]}, '
              f'Point3: {dataframe.iloc[current_idx]["DateTime"]} '
              f'Side: {structure_side}')

    def find_point_1(self, dataframe, current_idx, structure_side):
        if structure_side == 'low':
            # leaving searching subframe in different line is good idea for debugging
            searching_subframe = dataframe['Low'].iloc[-self.nrBarsToCheckMinimum:]
            suspected_row_idx = searching_subframe.idxmin()
        else:
            searching_subframe = dataframe['High'].iloc[-self.nrBarsToCheckMinimum:]
            suspected_row_idx = searching_subframe.idxmax()

        # check if it will be good structure length
        if self.min_structure_len < current_idx - suspected_row_idx < self.max_structure_len:
            return suspected_row_idx
        return None

    def find_point_2(self, dataframe, current_idx, point1_idx, structure_side):
        if structure_side == 'low':
            # finding maximum peak from point 1 up to now excluding 2 last bars
            searching_subframe = dataframe['High'].iloc[point1_idx: current_idx-1]
            suspected_row_idx = searching_subframe.idxmax()

            # confirming point 2
            if self.confirm_high_point(dataframe, suspected_row_idx):
                return suspected_row_idx
            return None
        else:
            searching_subframe = dataframe['Low'].iloc[point1_idx: current_idx-1]
            suspected_row_idx = searching_subframe.idxmin()

            # confirming point 2
            if self.confirm_low_point(dataframe, suspected_row_idx):
                return suspected_row_idx
            return None

    def check_if_current_idx_is_potential_point_3(self, dataframe, current_idx, point1_idx, point2_idx, structure_side):
        # filtering to short structures
        if current_idx - point1_idx < self.min_structure_len:
            return False

        if structure_side == 'low':
            # finding low from point 2 up to last bar (current_idx+1 is for the current bar take place)
            searching_subframe = dataframe['Low'].iloc[point2_idx+1: current_idx+1]
            if current_idx == searching_subframe.idxmin():
                return True
        else:
            searching_subframe = dataframe['High'].iloc[point2_idx+1: current_idx+1]
            if current_idx == searching_subframe.idxmax():
                return True

        return False

    def confirm_strong_movement_before_point_1(self, dataframe, point_1_idx, point_2_idx, point_3_idx, structure_side):
        structure_height = self.formation_height(dataframe, point_1_idx, point_2_idx,  structure_side)
        structure_len = point_3_idx - point_1_idx
        if structure_side == 'low':
            searching_subframe = dataframe.iloc[point_1_idx - 3 * structure_len: point_1_idx]['High']
            if searching_subframe.max() >= dataframe.iloc[point_1_idx]['Low'] + 2 * structure_height:
                return True
        else:
            searching_subframe = dataframe.iloc[point_1_idx - 3 * structure_len: point_1_idx]['Low']
            if searching_subframe.min() <= dataframe.iloc[point_1_idx]['High'] - 2 * structure_height:
                return True
        return False

    def confirm_high_point(self, dataframe, point_idx):
        return dataframe['Low'].iloc[point_idx: point_idx + 4].idxmin() != point_idx and \
                dataframe['High'].iloc[point_idx: point_idx + 4].idxmin() != point_idx

    def confirm_low_point(self, dataframe, point_idx):
        return dataframe['High'].iloc[point_idx: point_idx + 4].idxmax() != point_idx and \
                dataframe['Low'].iloc[point_idx: point_idx + 4].idxmax() != point_idx

    def risk_profit_ratio(self, dataframe):
        current_price = dataframe['Close'].iloc[-1]

        return (current_price - self.stoploss) / (self.takeprofit - self.stoploss)

    def calculate_stoploss_and_target_values(self, dataframe, point_1_idx, point_2_idx, point_3_idx, structure_side):
        if structure_side == 'low':
            point_1_lowest_price = dataframe['Low'].iloc[point_1_idx]
            point_2_highest_price = dataframe['High'].iloc[point_2_idx]
            # take 5% offset from lowest and highest price
            self.takeprofit = point_2_highest_price - (point_2_highest_price - point_1_lowest_price) * 0.05
            self.stoploss = point_1_lowest_price - (point_2_highest_price - point_1_lowest_price) * 0.05
        else:
            point_1_highest_price = dataframe['High'].iloc[point_1_idx]
            point_2_lowest_price = dataframe['Low'].iloc[point_2_idx]
            # take 5% offset from lowest and highest price
            self.takeprofit = point_2_lowest_price + (point_1_highest_price - point_2_lowest_price) * 0.05
            self.stoploss = point_1_highest_price + (point_1_highest_price - point_2_lowest_price) * 0.05

    def formation_height(self, dataframe, point_1_idx, point_2_idx, structure_side):
        if structure_side == 'low':
            return dataframe['High'].iloc[point_2_idx] - dataframe['Low'].iloc[point_1_idx]
        else:
            return dataframe['High'].iloc[point_1_idx] - dataframe['Low'].iloc[point_2_idx]

    def check_current_price_not_below_point_3(self, dataframe, point_3_idx, structure_side):
        current_price = dataframe['Close'].iloc[-1]
        if structure_side == 'low':
            point_3_lowest_price = dataframe['Low'].iloc[point_3_idx]
            return current_price > point_3_lowest_price
        else:
            point_3_highest_price = dataframe['High'].iloc[point_3_idx]
            return current_price < point_3_highest_price

    def check_return_height_for_point_3(self, dataframe, point_1_idx, point_2_idx, point_3_idx, structure_side):
        formation_height = self.formation_height(dataframe, point_1_idx, point_2_idx, structure_side)
        if structure_side == 'low':
            return_height = dataframe['High'].iloc[point_2_idx] - dataframe['Low'].iloc[point_3_idx]
        else:
            return_height = dataframe['High'].iloc[point_3_idx] - dataframe['Low'].iloc[point_2_idx]

        return return_height > formation_height * 0.4

    def check_height(self, point_1_idx, point_3_idx):
        structure_len = point_3_idx - point_1_idx
        # every barupon minimum length adds 0,07 of minimum height to minimum height
        min_height = self.min_structure_height + \
                     (structure_len - self.min_structure_len) * 0.08 * self.min_structure_height
        return self.structure_height > min_height

    # function, that called every 1 second if price subscribed
    def process_tick_subscribe_data(self, msg):
        actual_price = msg['data']['bid']
        if self.subscribed_strucure_side == 'low':
            if actual_price > self.point_3_high:
                self.open_long(volume=self.volume, stop_loss=self.stoploss, take_profit=self.takeprofit)
                self.finish_subscription()
            elif actual_price < self.point_3_low:
                self.finish_subscription()
        elif self.subscribed_strucure_side == 'high':
            if actual_price < self.point_3_low:
                self.open_short(volume=self.volume, stop_loss=self.stoploss, take_profit=self.takeprofit)
                self.finish_subscription()
            elif actual_price > self.point_3_high:
                self.finish_subscription()

    def finish_subscription(self):
        self.subscribed_strucure_side = None
        self.can_unsubscribe_price_flag = True
