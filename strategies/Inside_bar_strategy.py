import pandas as pd
import pandas_ta as pdta
from strategies.utilities import atr_based_stoploss


class InsideBar():
    def __init__(self):
        # parameters
        self.min_price = 10000000
        self.max_price = 0
        self.direction = None
        self.transaction_state = 'ready for open'

        self.plot_indicators_dict = {}

        # delay for initial indicators calculation
        self.simulation_delay_period = 2

    def next(self, dataframe):
        # put here all indicators you want to plot in Gregtraider
        self.plot_indicators_dict = {}
        self.dataframe = dataframe

        # check if it needs to unsubscribe something
        if self.can_unsubscribe_price_flag:
            self.unsubscribe_price()

        self.find_inside_bar(dataframe)

    def find_inside_bar(self, dataframe):
        print(f'Checking {self.symbol} {self.period}m')
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
        if self.direction is None: return
        print('inside bar found ' + self.symbol)
        if self.direction == 'down':# and self.slient == None # check if some price not subscribed already
            self.open_trsh = dataframe['Low'][self.inside_bar_idx] - 0.05 * self.inside_bar_length
            self.opposite_trsh = dataframe['High'][self.outside_bar_idx]
            self.subscribe_price(1000)
        elif self.direction == 'up':
            self.open_trsh = dataframe['High'][self.inside_bar_idx] + 0.05 * self.inside_bar_length
            self.opposite_trsh = dataframe['Low'][self.outside_bar_idx]
            self.subscribe_price(1000)

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

    def process_tick_subscribe_data(self, msg):
        print(f'state: {self.transaction_state}, {self.symbol}')
        if self.transaction_state == 'closed':
            return

        actual_price = msg['data']['bid']
        if actual_price < self.min_price:
            self.min_price = actual_price
        elif actual_price > self.max_price:
            self.max_price = actual_price
        if self.transaction_state == 'ready for open':
            self.open_pos_if_necessary(actual_price)
        elif self.transaction_state == 'opened':
            self.calculate_stoploss_and_close_if_necessary(actual_price)

    def open_pos_if_necessary(self, actual_price):
        print("cena: " + str(actual_price) + " próg: " + str(round(self.open_trsh, 4)) + ' ' + self.symbol)
        # opening position if price pierces threshold
        if self.direction == 'up':
            if actual_price > self.open_trsh:
                print('open long')
                # set platform stoploss for case of errors or server problems
                self.open_long(volume=self.volume, stop_loss=self.min_price - self.inside_bar_length * 0.2)
                self.transaction_state = 'opened'
            elif actual_price < self.opposite_trsh:
                self.transaction_state = 'closed'
                self.finish_subscription()
        elif self.direction == 'down':
            if actual_price < self.open_trsh:
                print('open short')
                # set platform stoploss for case of errors or server problems
                self.open_short(volume=self.volume)#, stop_loss=self.max_price + self.inside_bar_length * 0.2)
                self.transaction_state = 'opened'
            elif actual_price > self.opposite_trsh:
                self.transaction_state = 'closed'
                self.finish_subscription()

    def calculate_stoploss_and_close_if_necessary(self, actual_price):
        if self.direction == 'up':
            stoploss = self.max_price - atr_based_stoploss(self.dataframe, 20, 0.5)
            if actual_price < stoploss:
                print('close long')
                self.close()
                self.finish_subscription()
        elif self.direction == 'down':
            stoploss = self.min_price + 0.5 * atr_based_stoploss(self.dataframe, 20, 0.5)
            if actual_price > stoploss:
                print('close short')
                self.close()
                self.finish_subscription()

    def finish_subscription(self):
        self.min_price = 10000000
        self.max_price = 0
        self.can_unsubscribe_price_flag = True
