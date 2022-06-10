from strategies import RSIStrategy
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go


class BackTrading(RSIStrategy):
    def __init__(self, data_path):
        super().__init__()
        #self.strategy = RSIStrategy()

        self.input_data = pd.read_csv(data_path)

        self.cash = 0
        # true cash is summarical value of all assets
        self.true_cash = self.cash
        self.operating_volume = 1
        self.owned_volume = 0
        self.moment_transakcji = -1000
        self.plot_memory_init()

        # lists with transaction moments
        self.open_long_times = []
        self.open_short_times = []
        self.close_long_times = []
        self.close_short_times = []

    def run_simulation(self):
        for self.index, row in self.input_data.iterrows():
            # offset for initial data gather for strategy
            if self.index < self.simulation_delay_period:
                continue

            self.close_price = row['Close']
            self.date_time = row['DatoCzas']
            # wykonanie strategii
            self.next(self.input_data[:self.index + 1], client=None)
            self.add_data_for_plotting(self.index - self.simulation_delay_period, row)

        self.plot_lines()

    def open_long(self):
        self.cash -= self.close_price * self.operating_volume
        self.owned_volume += self.operating_volume
        self.moment_transakcji = self.index
        self.open_long_times.append(self.date_time)

    def open_short(self):
        self.cash += self.close_price * self.operating_volume
        self.owned_volume -= self.operating_volume
        self.moment_transakcji = self.index
        self.open_short_times.append(self.date_time)

    def close_long(self):
        self.cash += self.close_price * self.owned_volume
        self.true_cash = self.cash
        self.owned_volume = 0
        self.close_long_times.append(self.date_time)

    def close_short(self):
        self.cash += self.close_price * self.owned_volume
        self.true_cash = self.cash
        self.owned_volume = 0
        self.close_short_times.append(self.date_time)

    def no_pos_open_last_time(self, steps_offset):
        if self.index - self.moment_transakcji > steps_offset:
            return True
        else:
            return False

    def opened_pos_dir(self):
        if self.owned_volume > 0:
            return 'buy'
        elif self.owned_volume < 0:
            return 'sell'
        else:
            return False

    ## plotting functions
    def plot_memory_init(self):
        self.plot_data_df = pd.DataFrame(columns=['DatoCzas', 'Close'] +
                                                 [key for key in self.plot_indicators_dict] + ['Cash', 'True cash'])

    def add_data_for_plotting(self, index, row):
        self.plot_data_df.loc[index] = [row['DatoCzas'], row['Close']] + \
                [self.plot_indicators_dict[key] for key in self.plot_indicators_dict] + [self.cash, self.true_cash]

    def plot_lines(self):
        self.plot_data_df = self.plot_data_df.set_index('DatoCzas')
        plot_layout = [[{}],
                      [{'rowspan': 4}],
                      [None],
                      [None],
                      [None],
                      [{'rowspan': 2}],
                      [None]]
        fig = make_subplots(rows=7, cols=1, shared_xaxes=True, vertical_spacing=0.005, specs=plot_layout)
        # dodajemy poszczególne linie w odpowiednich miejscach
        fig.add_trace(go.Scatter(x=self.plot_data_df.index, y=self.plot_data_df['Cash'], name='Cash'), row=1, col=1)
        fig.add_trace(go.Scatter(x=self.plot_data_df.index, y=self.plot_data_df['True cash'], name='True cash'),
                      row=1, col=1)
        fig.add_trace(go.Scatter(x=self.plot_data_df.index, y=self.plot_data_df['Close'], name='Close'), row=2, col=1)
        fig.add_trace(go.Scatter(x=self.plot_data_df.index, y=self.plot_data_df['rsi'], name='RSI'), row=6, col=1)
        fig.add_trace(go.Scatter(x=self.plot_data_df.index, y=self.plot_data_df['rsi_upper_trsh'], name='Upper Trsh'),
                      row=6, col=1)
        fig.add_trace(go.Scatter(x=self.plot_data_df.index, y=self.plot_data_df['rsi_lower_trsh'], name='Lower Trsh'),
                      row=6, col=1)

        fig = self.add_transaction_symbols(fig)

        # set plot to maximize the screen
        # kompaktowe wyświetlanie legendy do dopracowania
        fig.update_layout(margin={'t': 0, 'l': 0, 'r': 0, 'b': 0}, showlegend=False)

        fig.show()

    def add_transaction_symbols(self, fig):
        fig.update_layout(
                shapes=[dict(x0=date_time, x1=date_time, y0=0.25, y1=1, xref='x', yref='paper',
                         line_color='rgb(100, 200, 100)', line_width=0.5) for date_time in self.open_long_times] +
                        [dict(x0=date_time, x1=date_time, y0=0.25, y1=1, xref='x', yref='paper',
                             line_color='rgb(200, 100, 100)', line_width=0.5) for date_time in self.open_short_times] +
                        [dict(x0=date_time, x1=date_time, y0=0.25, y1=1, xref='x', yref='paper',
                             line_color='rgb(200, 0, 100)', line_width=1) for date_time in self.close_long_times] +
                        [dict(x0=date_time, x1=date_time, y0=0.25, y1=1, xref='x', yref='paper',
                             line_color='rgb(0, 200, 100)', line_width=1) for date_time in self.close_short_times])

        return fig

if __name__ == '__main__':
    backtrader = BackTrading('historical_data/EOS_60m.csv')
    backtrader.run_simulation()
