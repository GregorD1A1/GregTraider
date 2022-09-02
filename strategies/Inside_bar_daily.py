import pandas as pd
import pandas_ta as pdta
from online_trading_APIs.xtb.download_csv_xtb import get_dataframe
from strategies.utilities import atr_based_stoploss
from datetime import date, timedelta
import logging


# logger properties
logger = logging.getLogger("jsonSocket")
FORMAT = '[%(asctime)-15s] %(message)s'
logging.basicConfig(format=FORMAT)


class InsideBarDailyBase():
    def __init__(self, symbol, period):
        # parameters
        self.direction = None

        self.symbol = symbol
        self.period = period
        self.transaction_state = 'closed'
        self.direction = None

    def next(self, dataframe_logic, client, ssid):
        # put here all indicators you want to plot in Gregtraider
        self.plot_indicators_dict = {}
        self.dataframe_logic = dataframe_logic

        self.find_inside_bar(self.dataframe_logic)

    def find_inside_bar(self, dataframe):
        # to avoid calculations if during handling opened position
        if self.transaction_state == 'opened':
            return
        logger.info('checking strategy for ' + self.symbol)
        current_bar_idx, prev_bar_idx = self.get_bar_indexes(dataframe)
        # check if current bar is inside bar
        if not (dataframe['Low'][current_bar_idx] >= dataframe['Low'][prev_bar_idx] and \
                dataframe['High'][current_bar_idx] <= dataframe['High'][prev_bar_idx]):
            return
        self.inside_bar_idx = current_bar_idx
        self.outside_bar_idx = prev_bar_idx

        # length filter
        self.calculate_bar_lengthes(dataframe)
        #if not self.length_filter():
        #    return
        logger.info('Raw inside bar found, ' + self.symbol)
        # direction filter
        self.direction = self.close_price_direction_filter(dataframe)
        if self.direction is None: return
        logger.info('Filtered inside bar found, ' + self.symbol)
        if self.direction == 'down':# and self.slient == None # check if some price not subscribed already
            self.open_trsh = dataframe['Low'][self.inside_bar_idx] - 0.02 * self.inside_bar_length
            self.opposite_trsh = dataframe['High'][self.inside_bar_idx]
            self.transaction_state = 'ready for open'
        elif self.direction == 'up':
            self.open_trsh = dataframe['High'][self.inside_bar_idx] + 0.02 * self.inside_bar_length
            self.opposite_trsh = dataframe['Low'][self.inside_bar_idx]
            self.transaction_state = 'ready for open'

    # filters if inside bar is 2 times smaller than outside
    def length_filter(self):
        return self.outside_bar_length >= 2 * self.inside_bar_length

    def calculate_bar_lengthes(self, dataframe):
        self.inside_bar_length = dataframe['High'][self.inside_bar_idx] - dataframe['Low'][self.inside_bar_idx]
        self.outside_bar_length = dataframe['High'][self.outside_bar_idx] - dataframe['Low'][self.outside_bar_idx]

    # checks if close prise is close enough to one of the candle edges
    def close_price_direction_filter(self, dataframe):
        if dataframe['Close'][self.inside_bar_idx] - dataframe['Low'][self.inside_bar_idx] < 0.35 * self.inside_bar_length:
            return 'down'
        elif dataframe['High'][self.inside_bar_idx] - dataframe['Close'][self.inside_bar_idx] < 0.35 * self.inside_bar_length:
            return 'up'
        return None

    def get_bar_indexes(self, dataframe):
        new_bar_day = date.today() - timedelta(days=1)
        # if yesterday was market closed
        new_bar_day, new_bar_day_str = self.find_nearest_available_day(dataframe, new_bar_day)

        previous_day = new_bar_day - timedelta(days=1)
        previous_day, previous_day_str = self.find_nearest_available_day(dataframe, previous_day)

        current_bar_idx = dataframe[dataframe['DateTime'] == new_bar_day_str].index.tolist()[0]
        prev_bar_idx = dataframe[dataframe['DateTime'] == previous_day_str].index.tolist()[0]
        return current_bar_idx, prev_bar_idx

    def find_nearest_available_day(self, dataframe, day):
        day_str = day.strftime('%H:%M %d.%m.%y')
        i = 0
        while day_str not in dataframe['DateTime'].values:
            day = day - timedelta(days=1)
            day_str = day.strftime('%H:%M %d.%m.%y')
            i += 1
            if i > 10:
                raise Exception('No last bar found')
        return day, day_str


class InsideBarDailyFrequent():
    def __init__(self, **kwargs):
        # parameters
        self.min_price = float('inf')
        self.max_price = 0

        self.plot_indicators_dict = {}

        self.period = 5
        self.base_strategy = kwargs['base_strategy']
        self.name = 'Inside_Bar_Daily'

    def next(self, dataframe_frequent):
        logger.info(f'state: {self.base_strategy.transaction_state}, {self.symbol}')
        self.dataframe = dataframe_frequent
        actual_price = dataframe_frequent['Close'].iloc[-1]
        actual_max_price = dataframe_frequent['High'].iloc[-1]
        actual_min_price = dataframe_frequent['Low'].iloc[-1]
        if actual_min_price < self.min_price:
            self.min_price = actual_min_price
        elif actual_max_price > self.max_price:
            self.max_price = actual_max_price

        if self.base_strategy.transaction_state == 'ready for open':
            self.open_pos_if_necessary(actual_price)
        elif self.base_strategy.transaction_state == 'opened':
            self.calculate_stoploss_and_close_if_necessary(actual_price)

    def open_pos_if_necessary(self, actual_price):
        # opening position if price pierces threshold
        logger.info(f'waiting for possibility to open, actual price: {actual_price}, open_trsh: '
                    f'{self.base_strategy.open_trsh}, opposite trsh: {self.base_strategy.opposite_trsh}, {self.symbol}')
        if self.base_strategy.direction == 'up':
            # second part of condition is for not opening after big price gap
            if self.base_strategy.open_trsh < actual_price < \
                    self.base_strategy.open_trsh + 0.2 * self.base_strategy.inside_bar_length:
                logger.info('open long')
                # set platform stoploss for case of errors or server problems
                self.open_long(volume=self.volume, stop_loss=self.min_price - self.base_strategy.inside_bar_length * 0.05)
                self.base_strategy.transaction_state = 'opened'
            elif actual_price < self.base_strategy.opposite_trsh or \
                    actual_price >= self.base_strategy.open_trsh + 0.2 * self.base_strategy.inside_bar_length:
                logger.info('Going wrong direction. Closing subscription')
                self.base_strategy.transaction_state = 'closed'
                self.finish_subscription()
        elif self.base_strategy.direction == 'down':
            if self.base_strategy.open_trsh > actual_price > \
                    self.base_strategy.open_trsh - 0.2 * self.base_strategy.inside_bar_length:
                logger.info('open short')
                # set platform stoploss for case of errors or server problems
                self.open_short(volume=self.volume, stop_loss=self.max_price + self.base_strategy.inside_bar_length * 0.05)
                self.base_strategy.transaction_state = 'opened'
            elif actual_price > self.base_strategy.opposite_trsh or \
                    actual_price <= self.base_strategy.open_trsh - 0.2 * self.base_strategy.inside_bar_length:
                logger.info('Going wrong direction. Closing subscription')
                self.base_strategy.transaction_state = 'closed'
                self.finish_subscription()

    def calculate_stoploss_and_close_if_necessary(self, actual_price):
        if self.base_strategy.direction == 'up':
            stoploss = self.max_price - atr_based_stoploss(self.dataframe, 20, 5)
            logger.info(f'stoploss: {stoploss}')
            if actual_price < stoploss:
                logger.info('close long')
                self.close()
                self.finish_subscription()
        elif self.base_strategy.direction == 'down':
            stoploss = self.min_price + atr_based_stoploss(self.dataframe, 20, 5)
            logger.info(f'stoploss: {stoploss}')
            if actual_price > stoploss:
                logger.info('close short')
                self.close()
                self.finish_subscription()

    def finish_subscription(self):
        self.min_price = float('inf')
        self.max_price = 0
        self.base_strategy.transaction_state = 'closed'
        logger.info('finish sub')

