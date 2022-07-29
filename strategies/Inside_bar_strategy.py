import pandas as pd
import pandas_ta as pdta


class InsideBar():
    def __init__(self):
        # parameters
        self.min_price = 1000000
        self.max_price = 0
        self.direction = None
        self.pos_opened = False

        self.plot_indicators_dict = {}

        # delay for initial indicators calculation
        self.simulation_delay_period = 2

    def next(self, dataframe, client):
        # put here all indicators you want to plot in Gregtraider
        self.plot_indicators_dict = {}
        self.client = client
        # write stuff here
        self.find_inside_bar(dataframe)

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
        if not self.length_filter(dataframe):
            return
        # direction filter
        self.direction = self.close_direction_filter(dataframe)
        if self.direction == 'down':
            self.open_trsh = dataframe['Low'][self.inside_bar_idx] - 0.05 * self.inside_bar_length
            self.subscribe_price(1000)
        elif self.direction == 'up':
            self.open_trsh = dataframe['High'][self.inside_bar_idx] + 0.05 * self.inside_bar_length
            self.subscribe_price(1000)

    # filters if inside bar is 2 times smaller than outside
    def length_filter(self, dataframe):
        self.inside_bar_length = dataframe['High'][self.inside_bar_idx] - dataframe['Low'][self.inside_bar_idx]
        self.outside_bar_length = dataframe['High'][self.outside_bar_idx] - dataframe['Low'][self.outside_bar_idx]
        return self.outside_bar_length >= 2 * self.inside_bar_length

    # checks if close prise is close enough to one of the candle edges
    def close_direction_filter(self, dataframe):
        if dataframe['Close'][self.inside_bar_idx] - dataframe['Low'][self.inside_bar_idx] < 0.25 * self.inside_bar_length:
            return 'down'
        elif dataframe['High'][self.inside_bar_idx] - dataframe['Close'][self.inside_bar_idx] < 0.25 * self.inside_bar_length:
            return 'up'
        return None

    def process_tick_subscribe_data(self, msg):
        actual_price = msg['data']['bid']
        print(actual_price)
        if actual_price < self.min_price:
            self.min_price = actual_price
        elif actual_price > self.max_price:
            self.max_price = actual_price

        if not self.pos_opened:
            self.open_pos_if_necessary(actual_price)
        else:
            self.calculate_stoploss_ald_close_if_necessary(actual_price)

    def open_pos_if_necessary(self, actual_price):
        # opening position if price pierces threshold
        if self.direction == 'up' and actual_price > self.open_trsh:
            print('open long')
            self.open_long()
            self.pos_opened = True
        elif self.direction == 'down' and actual_price < self.open_trsh:
            print('open short')
            self.open_short()
            self.pos_opened = True

    def calculate_stoploss_ald_close_if_necessary(self, actual_price):
        if self.direction == 'up':
            stoploss = self.max_price - 0.5 * self.inside_bar_length
            if actual_price < stoploss:
                print('close long')
                # dać jakieś id transakcji?
                self.close_long()
                self.unsubscribe_price()
        elif self.direction == 'down':
            stoploss = self.min_price + 0.5 * self.inside_bar_length
            if actual_price > stoploss:
                print('close short')
                self.close_short()
                self.unsubscribe_price()

    def unsubscribe_price(self):
        self.min_price = 1000000
        self.max_price = 0
        self.pos_opened = False

    def open_long(self):
        pass

    def open_short(self):
        pass

    def close(self):
        pass

    def subscribe_price(self):
        pass
