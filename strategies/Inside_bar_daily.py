import pandas as pd
import pandas_ta as pdta
from online_trading_APIs.xtb.download_csv_xtb import get_dataframe


class InsideBarBase():
    def __init__(self, symbol, period):
        # parameters
        self.direction = None

        self.symbol = symbol
        self.period = period
        self.transaction_state = 'closed'
        self.direction = None

    def next(self):
        # put here all indicators you want to plot in Gregtraider
        self.plot_indicators_dict = {}
        self.dataframe_logic = get_dataframe(self.client, self.symbol, self.period)

        self.find_inside_bar(self.dataframe_logic)

    def find_inside_bar(self, dataframe):
        current_bar_idx = dataframe.index[-1]
        prev_bar_idx = dataframe.index[-2]

        # check if current bar is inside bar
        if not (dataframe['Low'][current_bar_idx] > dataframe['Low'][prev_bar_idx] and \
                dataframe['High'][current_bar_idx] < dataframe['High'][prev_bar_idx]):
            return
        self.inside_bar_idx = current_bar_idx
        self.outside_bar_idx = prev_bar_idx

        # length filter
        self.calculate_bar_lengthes(dataframe)
        #if not self.length_filter(dataframe):
        #    return
        # direction filter
        self.direction = self.close_price_direction_filter(dataframe)
        if self.direction == 'down':# and self.slient == None # check if some price not subscribed already
            self.open_trsh = dataframe['Low'][self.inside_bar_idx] - 0.05 * self.inside_bar_length
            self.opposite_trsh = dataframe['High'][self.outside_bar_idx]
            self.transaction_state = 'ready for open'
        elif self.direction == 'up':
            self.open_trsh = dataframe['High'][self.inside_bar_idx] + 0.05 * self.inside_bar_length
            self.opposite_trsh = dataframe['Low'][self.outside_bar_idx]
            self.transaction_state = 'ready for open'

    # filters if inside bar is 2 times smaller than outside
    def length_filter(self, dataframe):
        return self.outside_bar_length >= 2 * self.inside_bar_length

    def calculate_bar_lengthes(self, dataframe):
        self.inside_bar_length = dataframe['High'][self.inside_bar_idx] - dataframe['Low'][self.inside_bar_idx]
        self.outside_bar_length = dataframe['High'][self.outside_bar_idx] - dataframe['Low'][self.outside_bar_idx]

    # checks if close prise is close enough to one of the candle edges
    def close_price_direction_filter(self, dataframe):
        if dataframe['Close'][self.inside_bar_idx] - dataframe['Low'][self.inside_bar_idx] < 0.25 * self.inside_bar_length:
            return 'down'
        elif dataframe['High'][self.inside_bar_idx] - dataframe['Close'][self.inside_bar_idx] < 0.25 * self.inside_bar_length:
            return 'up'
        return None


class InsideBarFrequent():
    def __init__(self, **kwargs):
        # parameters
        self.min_price = 10000000
        self.max_price = 0

        self.plot_indicators_dict = {}

        self.period = 5
        self.base_strategy = kwargs['base_strategy']

    def next(self, dataframe_frequent):
        print(f'state: {self.base_strategy.transaction_state}, {self.symbol}')
        if self.base_strategy.transaction_state == 'closed':
            return
        actual_price = dataframe_frequent['Close'][-1]
        if actual_price < self.min_price:
            self.min_price = actual_price
        elif actual_price > self.max_price:
            self.max_price = actual_price

        if self.base_strategy.transaction_state == 'ready for open':
            self.open_pos_if_necessary(actual_price)
        elif self.base_strategy.transaction_state == 'opened':
            self.calculate_stoploss_and_close_if_necessary(actual_price)

    def open_pos_if_necessary(self, actual_price):
        # opening position if price pierces threshold
        if self.base_strategy.direction == 'up':
            if actual_price > self.base_strategy.open_trsh:
                print('open long')
                # set platform stoploss for case of errors or server problems
                self.open_long(volume=self.volume, stop_loss=self.min_price - self.base_strategy.inside_bar_length * 0.05)
                self.base_strategy.transaction_state = 'opened'
            elif actual_price < self.base_strategy.opposite_trsh:
                self.base_strategy.transaction_state = 'closed'
                self.finish_subscription()
        elif self.base_strategy.direction == 'down':
            if actual_price < self.base_strategy.open_trsh:
                print('open short')
                # set platform stoploss for case of errors or server problems
                self.open_short(volume=self.volume, stop_loss=self.max_price + self.base_strategy.inside_bar_length * 0.05)
                self.base_strategy.transaction_state = 'opened'
            elif actual_price > self.base_strategy.opposite_trsh:
                self.base_strategy.transaction_state = 'closed'
                self.finish_subscription()

    def calculate_stoploss_and_close_if_necessary(self, actual_price):
        if self.base_strategy.direction == 'up':
            stoploss = self.max_price - 0.5 * self.base_strategy.inside_bar_length
            if actual_price < stoploss:
                print('close long')
                self.close()
                self.finish_subscription()
        elif self.base_strategy.direction == 'down':
            stoploss = self.min_price + 0.5 * self.base_strategy.inside_bar_length
            if actual_price > stoploss:
                print('close short')
                self.close()
                self.finish_subscription()

    def finish_subscription(self):
        self.min_price = 10000000
        self.max_price = 0
        self.can_unsubscribe_price_flag = True
        self.base_strategy.transaction_state = 'closed'
