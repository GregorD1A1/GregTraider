from strategies.strategy_1_2_3 import Strategy123
from strategies.Inside_bar_strategy import InsideBar
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go


class Position():
    def __init__(self, side, price, volume, opening_time, stop_loss=None, take_profit=None):
        self.side = side
        self.opening_price = price
        self.close_price = None
        self.volume = volume
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.opening_time = opening_time
        self.closing_time = None
        self.profit = None


class GregTrade(Strategy123):
    def __init__(self, data_path, min_structure_height):
        super().__init__(min_structure_height)
        self.input_data = pd.read_csv(data_path)

        self.cash = 0
        # true cash is summarical value of all assets
        self.true_cash = self.cash
        self.operating_volume = 1
        self.owned_volume = 0
        self.transaction_time = -1000
        # cost of transaction (spread, broker provision etc.) as part of cost. Adding that cost only for position
        # opening to be consistent with online trading
        self.transaction_costs = 0#0.001

        self.plot_memory_init()

        self.opened_positions = []
        self.closed_positions = []
        self.can_unsubscribe_price_flag = False


    def run_simulation(self):
        for self.index, row in self.input_data.iterrows():
            # offset for initial data gather for strategy
            if self.index < self.simulation_delay_period:
                continue

            self.open_price = row['Open']
            self.high_price = row['High']
            self.low_price = row['Low']
            self.close_price = row['Close']
            self.date_time = row['DateTime']
            # strategy execution
            self.next(self.input_data[:self.index + 1], client=None)
            self.add_data_for_plotting(self.index - self.simulation_delay_period, row)

        self.calculate_profit_and_ppt()
        self.plot_lines()

    def next(self, dataframe, client):
        # closing positions if stoploss/takeprofit values was pierced
        self.close_positions_by_sl_tp()
        super(GregTrade, self).next(dataframe, client)

    def open_long(self, stop_loss=None, take_profit=None, volume=0.01):
        opening_price = self.close_price * (1 + self.transaction_costs)
        self.cash -= opening_price * self.operating_volume
        position = Position('long', opening_price, self.operating_volume, opening_time=self.date_time,
                            stop_loss=stop_loss, take_profit=take_profit)
        self.opened_positions.append(position)
        self.owned_volume += self.operating_volume
        self.transaction_time = self.index

    def open_short(self, stop_loss=None, take_profit=None, volume=0.01):
        opening_price = self.close_price * (1 - self.transaction_costs)
        self.cash += opening_price * self.operating_volume
        position = Position('short', opening_price, self.operating_volume, opening_time=self.date_time,
                            stop_loss=stop_loss, take_profit=take_profit)
        self.opened_positions.append(position)
        self.owned_volume -= self.operating_volume
        self.transaction_time = self.index

    def close(self, position, final_price=None):
        if final_price is None:
            final_price = self.close_price

        position.close_price = final_price
        position.closing_time = self.date_time
        # change cash and calculate profit
        if position.side == 'long':
            self.cash += final_price * position.volume
            position.profit = final_price - position.opening_price
        else:
            self.cash -= final_price * position.volume
            position.profit = position.opening_price - final_price

        self.true_cash += position.profit
        # removing position from positions list
        self.opened_positions.remove(position)
        self.closed_positions.append(position)

    def no_pos_open_last_time(self, steps_offset):
        if self.index - self.transaction_time > steps_offset:
            return True
        else:
            return False

    def close_positions_by_sl_tp(self):
        for position in self.opened_positions:
            if position.side == 'long':
                if position.stop_loss is not None and self.low_price <= position.stop_loss:
                    self.close(position, position.stop_loss)
                elif position.take_profit is not None and self.high_price >= position.take_profit:
                    self.close(position, position.take_profit)
            else:
                if position.stop_loss is not None and self.high_price >= position.stop_loss:
                    self.close(position, position.stop_loss)
                elif position.take_profit is not None and self.low_price <= position.take_profit:
                    self.close(position, position.take_profit)

    def subscribe_price(self, _, positive_trsh, negative_trsh):
        self.negative_trsh = negative_trsh
        self.positive_trsh = positive_trsh

    def open_pos_by_subscription_or_turn_it_off(self):
        if self.high_price > self.negative_trsh and self.low_price < self.negative_trsh:
            self.finish_subscription()
        elif self.high_price > self.positive_trsh and self.low_price < self.positive_trsh:
            open_position() tylko którą?

    ## plotting functions
    def plot_memory_init(self):
        self.plot_data_df = pd.DataFrame(columns=['DateTime', 'Open', 'High', 'Low', 'Close'] +
                                                 [key for key in self.plot_indicators_dict] + ['Cash', 'True cash'])

    def add_data_for_plotting(self, index, row):
        self.plot_data_df.loc[index] = [self.date_time, self.open_price, self.high_price, self.low_price,
                self.close_price] + \
                [self.plot_indicators_dict[key] for key in self.plot_indicators_dict] + [self.cash, self.true_cash]

    def calculate_profit_and_ppt(self):
        last_date = self.plot_data_df.index[-1]
        self.final_profit = round(float(self.plot_data_df[self.plot_data_df.index == last_date]['True cash']), 2)
        self.profit_per_transaction = round(self.final_profit / len(self.closed_positions), 3) \
            if len(self.closed_positions) > 0 else 0
        nr_succes_transactions = len(list(filter(lambda transaction: transaction.profit > 0, self.closed_positions)))
        nr_unsucces_transactions = len(list(filter(lambda transaction: transaction.profit <= 0, self.closed_positions)))
        self.tps_sls = round(nr_succes_transactions / nr_unsucces_transactions, 3) if nr_unsucces_transactions > 0 \
            else 0


    ## draw functions
    def plot_lines(self):
        cash_row = 1
        main_graph_row = 2
        momentum_row = 6
        # white here indicators you want to show with apropriate rows
        indicators_to_show = {'Cash': cash_row, 'True cash': cash_row, 'High': main_graph_row,
            'Low': main_graph_row, 'Close': main_graph_row, 'Open': momentum_row}

        self.plot_data_df = self.plot_data_df.set_index('DateTime')
        plot_layout = [[{}],
                      [{'rowspan': 4}],
                      [None],
                      [None],
                      [None],
                      [{'rowspan': 2}],
                      [None]]
        self.fig = make_subplots(rows=7, cols=1, shared_xaxes=True, vertical_spacing=0.005, specs=plot_layout)
        # adding plotting lines in relevant places
        for indicator in indicators_to_show:
            self.fig.add_trace(go.Scatter(x=self.plot_data_df.index, y=self.plot_data_df[indicator], name=indicator),
                               row=indicators_to_show[indicator], col=1)

        self.add_transaction_symbols()
        self.draw_profit_and_ppt()
        # set plot to maximize the screen
        self.fig.update_layout(margin={'t': 0, 'l': 0, 'r': 0, 'b': 0}, showlegend=True)

        self.fig.show()

    def add_transaction_symbols(self):
        for position in self.closed_positions:
            if position.side == 'long':
                self.draw_transaction_line(position.opening_time, position.opening_price, "RoyalBlue")
                self.draw_transaction_line(position.closing_time, position.close_price, "IndianRed")
                self.draw_annotation(position.closing_time, position.close_price, position.profit)
            else:
                self.draw_transaction_line(position.opening_time, position.opening_price, "IndianRed")
                self.draw_transaction_line(position.closing_time, position.close_price, "RoyalBlue")
                self.draw_annotation(position.closing_time, position.close_price, position.profit)
        for position in self.opened_positions:
            if position.side == 'long':
                self.draw_transaction_line(position.opening_time, position.opening_price, "RoyalBlue")
            else:
                self.draw_transaction_line(position.opening_time, position.opening_price, "IndianRed")

    # if you want to commit to the project, you can change lines to something more estetical, like triangles.
    # also you can make it scalable according to the plot size
    def draw_transaction_line(self, x_coord, price, color):
        scale_coeff = (self.plot_data_df['Close'].max() - self.plot_data_df['Close'].min()) / 20
        self.fig.add_shape(type='line', xref="x", yref="y", x0=x_coord, y0=price - scale_coeff, x1=x_coord,
                      y1=price, row=2, col=1,
                      line=dict(color=color, width=2))

    def draw_annotation(self, x_coord, price, profit):
        profit = round(profit, 3)
        if profit > 0:
            profit = '+' + str(profit)
        self.fig.add_annotation(x=x_coord, y=price, xref='x1', yref='y2', text=profit, font_size=10, font_color='black',
                           yanchor='bottom')

    def draw_profit_and_ppt(self):
        last_date = self.plot_data_df.index[-1]
        if self.final_profit > 0:
            final_profit_str = '+' + str(self.final_profit)
            color = 'green'
        else:
            final_profit_str = str(self.final_profit)
            color = 'red'
        # as plotly uses HTML notation, using <br> as newline symbol
        output_str = 'Profit: ' + final_profit_str + '  <br>' + 'Profit per transaction: ' + str(self.profit_per_transaction) + ' <br> tps/sls: ' + str(self.tps_sls)
        self.fig.add_annotation(x=last_date, y=0.9, xref='x1', yref='paper', text=output_str, font_size=10,
                                font_color=color, showarrow=False, xanchor='right')


if __name__ == '__main__':
    backtester = GregTrade('historical_data/GOLD_60m.csv', min_structure_height=25)
    backtester.run_simulation()
