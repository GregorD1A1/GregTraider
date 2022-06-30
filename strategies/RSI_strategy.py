import pandas as pd
import pandas_ta as pdta


class RSIStrategy():
    def __init__(self):
        self.rsi_period = 14
        self.default_low_rsi_trsh = 30
        self.default_high_rsi_trsh = 70
        self.rsi_low_trsh_max = 60
        self.rsi_high_trsh_min = 40
        self.rsi_low_trsh_min = 20
        self.rsi_high_trsh_max = 80
        self.close_offset = 10
        self.rsi_peak_detection_offset = 8
        self.ema_period = 250
        self.rsi_per_ema_angle_coeff1 = 50000
        self.rsi_per_ema_angle_coeff2 = 25000
        self.plot_indicators_dict = {'rsi': None, 'ema': None, 'rsi_upper_trsh': None, 'rsi_lower_trsh': None}

        # delay for initial indicators calculation
        self.simulation_delay_period = max(self.rsi_period, self.ema_period)

    def next(self, dataframe, client):
        # indicator calculation
        self.rsi = pdta.rsi(dataframe['Close'], length=self.rsi_period)
        self.ema = pdta.ema(dataframe['Close'], length=self.ema_period)
        self.kat_pochylenia_ema = self.ema.diff() / self.ema
        self.ema_angle_smoothed = pdta.sma(self.kat_pochylenia_ema, length=10)
        self.rsi_upper_trsh = self.upper_trsh()
        self.rsi_lower_trsh = self.lower_trsh()

        # put here all indicators you want to plot in Gregtraider
        self.plot_indicators_dict = {'rsi': self.rsi.iloc[-1], 'ema': self.ema.iloc[-1], 'rsi_upper_trsh': self.rsi_upper_trsh,
                                     'rsi_lower_trsh': self.rsi_lower_trsh}

        self.client = client

        self.if_close_long()
        self.if_close_short()
        self.if_open_long()
        self.if_open_short()
        
    # checks if to open long position
    def if_open_long(self):
        # buy at the RSI low
        if self.rsi.iloc[-2] < self.rsi_lower_trsh and self.rsi.iloc[-1] > \
                self.rsi.iloc[-2] + self.rsi_peak_detection_offset:
            # not open new position right after previous opening
            if self.no_pos_open_last_time(self.close_offset):
                self.open_long()
                print('open long')

    # checks if to open short position
    def if_open_short(self):
        # sell at RSI high
        if self.rsi.iloc[-2] > self.rsi_upper_trsh and self.rsi.iloc[-1] < \
                self.rsi.iloc[-2] - self.rsi_peak_detection_offset:

            # not open new position right after previous opening
            if self.no_pos_open_last_time(self.close_offset):
                self.open_short()
                print('open short')

    # checks if to close long position
    def if_close_long(self):
        # buy at the RSI low
        if self.rsi.iloc[-2] > self.rsi_upper_trsh and self.rsi.iloc[-1] < self.rsi.iloc[-2]:
            # closing long position
            if self.opened_pos_dir() == 'buy':
                self.close_long()
                print('close long')

    # checks if to close short position
    def if_close_short(self):
        # sell at RSI high
        if self.rsi.iloc[-2] < self.rsi_lower_trsh and self.rsi.iloc[-1] > self.rsi.iloc[-2]:
            # closing short position
            if self.opened_pos_dir() == 'sell':
                self.close_short()
                print('close short')

    # calculate RSI thresholds in dependance from ema angle
    def upper_trsh(self):
        # high trsh
        if self.ema_angle_smoothed.iloc[-1] >= 0:
            trsh = self.default_high_rsi_trsh + \
                   self.ema_angle_smoothed.iloc[-1] * self.rsi_per_ema_angle_coeff2
            if trsh > self.rsi_high_trsh_max: trsh = self.rsi_high_trsh_max
            return trsh
        # low trsh
        else:
            trsh = self.default_high_rsi_trsh + self.ema_angle_smoothed.iloc[-1] * self.rsi_per_ema_angle_coeff1
            if trsh < self.rsi_high_trsh_min: trsh = self.rsi_high_trsh_min
            return trsh

    def lower_trsh(self):
        # low trsh
        if self.ema_angle_smoothed.iloc[-1] <= 0:
            trsh = self.default_low_rsi_trsh + self.ema_angle_smoothed.iloc[-1] * self.rsi_per_ema_angle_coeff2
            if trsh < self.rsi_low_trsh_min: trsh = self.rsi_low_trsh_min
            return trsh
        # high trsh
        else:
            trsh = self.default_low_rsi_trsh + self.ema_angle_smoothed.iloc[-1] * self.rsi_per_ema_angle_coeff1
            if trsh > self.rsi_low_trsh_max: trsh = self.rsi_low_trsh_max
            return trsh

    def open_long(self):
        pass

    def open_short(self):
        pass

    def close_long(self):
        pass

    def close_short(self):
        pass

    def opened_pos_dir(self):
        pass

    def no_pos_open_last_time(self, steps_offset):
        pass
