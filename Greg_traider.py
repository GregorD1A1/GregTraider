from strategies import RSIStrategy
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go


class BackTest(RSIStrategy):
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
            self.date_time = row['DateTime']
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
        profit = self.cash - self.true_cash
        self.true_cash = self.cash
        self.owned_volume = 0
        self.close_long_times.append(self.date_time)

    def close_short(self):
        self.cash += self.close_price * self.owned_volume
        profit = self.cash - self.true_cash
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
        self.plot_data_df = pd.DataFrame(columns=['DateTime', 'Close'] +
                                                 [key for key in self.plot_indicators_dict] + ['Cash', 'True cash'])

    def add_data_for_plotting(self, index, row):
        self.plot_data_df.loc[index] = [self.date_time, self.close_price] + \
                [self.plot_indicators_dict[key] for key in self.plot_indicators_dict] + [self.cash, self.true_cash]

    def plot_lines(self):
        cash_row = 1
        main_graph_row = 2
        momentum_row = 6
        self.plot_data_df = self.plot_data_df.set_index('DateTime')
        plot_layout = [[{}],
                      [{'rowspan': 4}],
                      [None],
                      [None],
                      [None],
                      [{'rowspan': 2}],
                      [None]]
        fig = make_subplots(rows=7, cols=1, shared_xaxes=True, vertical_spacing=0.005, specs=plot_layout)
        # dodajemy poszczególne linie w odpowiednich miejscach
        fig.add_trace(go.Scatter(x=self.plot_data_df.index, y=self.plot_data_df['Cash'], name='Cash'),
                      row=cash_row, col=1)
        fig.add_trace(go.Scatter(x=self.plot_data_df.index, y=self.plot_data_df['True cash'], name='True cash'),
                      row=cash_row, col=1)
        fig.add_trace(go.Scatter(x=self.plot_data_df.index, y=self.plot_data_df['Close'], name='Close'),
                      row=main_graph_row, col=1)
        fig.add_trace(go.Scatter(x=self.plot_data_df.index, y=self.plot_data_df['rsi'], name='RSI'),
                      row=momentum_row, col=1)
        fig.add_trace(go.Scatter(x=self.plot_data_df.index, y=self.plot_data_df['rsi_upper_trsh'], name='Upper Trsh'),
                      row=momentum_row, col=1)
        fig.add_trace(go.Scatter(x=self.plot_data_df.index, y=self.plot_data_df['rsi_lower_trsh'], name='Lower Trsh'),
                      row=momentum_row, col=1)

        fig = self.add_transaction_symbols(fig)

        # set plot to maximize the screen
        fig.update_layout(margin={'t': 0, 'l': 0, 'r': 0, 'b': 0}, showlegend=True)

        fig.show()

    def add_transaction_symbols(self, fig):
        # if you want to commit to the project, you can change lines to someting more estetical, like triangles.
        # also you can make it scalable according to the plot size
        for time in self.open_long_times:
            self.draw_transaction_line(fig, time, "RoyalBlue")
        for time in self.open_short_times:
            self.draw_transaction_line(fig, time, "IndianRed")
        for time in self.close_long_times:
            self.draw_transaction_line(fig, time, "IndianRed")
        for time in self.close_short_times:
            self.draw_transaction_line(fig, time, "RoyalBlue")

        return fig

    def draw_transaction_line(self, fig, x_coord, color):
        price = self.plot_data_df[self.plot_data_df.index == x_coord]['Close']
        fig.add_shape(type='line', xref="x", yref="y", x0=x_coord, y0=float(price - 0.5), x1=x_coord,
                      y1=float(price + 0.5), row=2, col=1,
                      line=dict(color=color, width=2))
        return fig

if __name__ == '__main__':
    backtrader = BackTest('historical_data/EOS_60m.csv')
    backtrader.run_simulation()
